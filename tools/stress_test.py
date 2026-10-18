"""100 并发压力测试脚本（asyncio + httpx）。

场景：
  A. 登录风暴：N 并发同时登录（bcrypt 校验 + JWT 签发）
  B. 会话/消息读取：登录后 N 并发拉会话列表 + 首个会话消息
  C. 混合负载：登录 → 会话列表 → 消息，循环 R 轮
  D. 问答链路：M 并发真实提问（外部 LLM，控制成本）

用法：
  python tools/stress_test.py --prepare 100     # 注册 100 压测用户
  python tools/stress_test.py --run 100         # 跑全部场景（默认并发 100）
"""
import argparse
import asyncio
import json
import statistics
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
PASSWORD = "Stress@123456"


def _percentile(data: list[float], p: float) -> float:
    """计算延迟列表的百分位（p=0.95 即 P95），线性插值。"""
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    return s[f] + (s[c] - s[f]) * (k - f)


def _stats(name: str, lat: list[float], errors: int) -> dict:
    """汇总一个场景的统计：请求数、错误数、QPS 与延迟分位。"""
    n = len(lat)
    total = sum(lat)
    qps = n / total if total > 0 else 0
    return {
        "场景": name,
        "请求数": n,
        "错误数": errors,
        "QPS": round(qps, 1),
        "平均(ms)": round(statistics.mean(lat) * 1000, 1) if lat else 0,
        "P50(ms)": round(_percentile(lat, 0.5) * 1000, 1),
        "P95(ms)": round(_percentile(lat, 0.95) * 1000, 1),
        "P99(ms)": round(_percentile(lat, 0.99) * 1000, 1),
        "最大(ms)": round(max(lat) * 1000, 1) if lat else 0,
    }


async def prepare_users(n: int, sem: asyncio.Semaphore):
    """预注册 n 个压测用户（stress_001~n），已存在的用户会跳过（返回 400）。"""

    async def reg(i: int):
        uname = f"stress_{i:03d}"
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=15) as c:
                    r = await c.post(BASE + "/auth/register", json={"username": uname, "password": PASSWORD})
                    return uname, r.status_code
            except Exception as e:
                return uname, f"ERR:{type(e).__name__}"

    results = await asyncio.gather(*[reg(i) for i in range(1, n + 1)])
    ok = sum(1 for _, s in results if s in (200, 201))
    exists = sum(1 for _, s in results if s == 400)
    print(f"[prepare] 注册 {n} 用户：成功 {ok} / 已存在 {exists} / 其他 {n - ok - exists}")


async def scene_login(n: int, sem: asyncio.Semaphore) -> tuple[list[float], int]:
    """场景 A：n 个不同用户同时登录（bcrypt 校验 + JWT 签发），返回延迟与错误数。"""
    lat, errs = [], 0

    async def one(i: int):
        nonlocal errs
        uname = f"stress_{i % 100 + 1:03d}"
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=30) as c:
                    t0 = time.perf_counter()
                    r = await c.post(BASE + "/auth/login", json={"username": uname, "password": PASSWORD})
                    dt = time.perf_counter() - t0
                    lat.append(dt)
                    if r.status_code != 200:
                        errs += 1
            except Exception:
                errs += 1

    await asyncio.gather(*[one(i) for i in range(n)])
    return lat, errs


async def scene_read(n: int, sem: asyncio.Semaphore, token: str) -> tuple[list[float], int]:
    """场景 B：n 个并发拉取会话列表 + 首个会话消息（模拟打开历史记录）。"""
    lat, errs = [], 0

    async def one(_i: int):
        nonlocal errs
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=30) as c:
                    h = {"Authorization": f"Bearer {token}"}
                    t0 = time.perf_counter()
                    r = await c.get(BASE + "/conversations", params={"page": 1, "page_size": 50}, headers=h)
                    if r.status_code == 200:
                        items = r.json().get("items", [])
                        if items:
                            await c.get(BASE + f"/conversations/{items[0]['id']}/messages", headers=h)
                    dt = time.perf_counter() - t0
                    lat.append(dt)
                    if r.status_code != 200:
                        errs += 1
            except Exception:
                errs += 1

    await asyncio.gather(*[one(i) for i in range(n)])
    return lat, errs


async def scene_mixed(n: int, rounds: int, sem: asyncio.Semaphore, token: str) -> tuple[list[float], int]:
    """场景 C：n 个并发 × rounds 轮循环读会话列表（持续负载下的稳定性）。"""
    lat, errs = [], 0

    async def one(_i: int):
        nonlocal errs
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=30) as c:
                    h = {"Authorization": f"Bearer {token}"}
                    for _ in range(rounds):
                        t0 = time.perf_counter()
                        r = await c.get(BASE + "/conversations", params={"page": 1, "page_size": 50}, headers=h)
                        if r.status_code != 200:
                            errs += 1
                        lat.append(time.perf_counter() - t0)
            except Exception:
                errs += 1

    await asyncio.gather(*[one(i) for i in range(n)])
    return lat, errs


async def scene_ask(n: int, sem: asyncio.Semaphore, token: str) -> tuple[list[float], int]:
    """场景 D：n 个并发真实提问（流式 SSE 调用外部 LLM，验证问答链路）。"""
    lat, errs, answers = [], 0, []

    async def one(i: int):
        nonlocal errs
        q = ["无线蓝牙耳机Pro的降噪深度是多少？", "智能手表支持哪些运动模式？", "充电宝能不能带上飞机？"][i % 3]
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=90) as c:
                    h = {"Authorization": f"Bearer {token}"}
                    t0 = time.perf_counter()
                    async with c.stream("POST", BASE + "/chat/ask", headers=h, json={"question": q, "top_k": 3}) as r:
                        buf = ""
                        full = ""
                        async for chunk in r.aiter_text():
                            buf += chunk
                            while "\n\n" in buf:
                                frame, buf = buf.split("\n\n", 1)
                                ev = "message"
                                data = ""
                                for line in frame.split("\n"):
                                    if line.startswith("event:"):
                                        ev = line[6:].strip()
                                    elif line.startswith("data:"):
                                        data += line[5:].strip()
                                if not data:
                                    continue
                                try:
                                    d = json.loads(data)
                                    if ev == "delta" and d.get("text"):
                                        full += d["text"]
                                except Exception:
                                    pass
                    dt = time.perf_counter() - t0
                    lat.append(dt)
                    answers.append(full[:30])
                    if not full or r.status_code != 200:
                        errs += 1
            except Exception:
                errs += 1

    await asyncio.gather(*[one(i) for i in range(n)])
    return lat, errs


def _print(rows: list[dict]):
    """以对齐表格打印统计结果。"""
    headers = list(rows[0].keys())
    print("\n" + " | ".join(f"{h:<10}" for h in headers))
    print("-" * (11 * len(headers)))
    for r in rows:
        print(" | ".join(f"{str(r[h]):<10}" for h in headers))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", type=int, default=0)
    ap.add_argument("--run", type=int, default=0)
    ap.add_argument("--ask", type=int, default=10)
    args = ap.parse_args()

    if args.prepare:
        await prepare_users(args.prepare, asyncio.Semaphore(10))
        return

    n = args.run or 100
    sem = asyncio.Semaphore(n)

    # 拿一个压测用户的 token 用于读接口
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(BASE + "/auth/login", json={"username": "stress_001", "password": PASSWORD})
        if r.status_code != 200:
            print("无法登录 stress_001，请先 --prepare 100")
            sys.exit(1)
        token = r.json()["access_token"]

    rows = []

    # 场景 A：登录风暴
    print(f"\n[场景A] {n} 并发登录 …")
    lat, errs = await scene_login(n, sem)
    rows.append(_stats("A.登录", lat, errs))

    # 场景 B：会话/消息读取（全部同 token 并发读）
    print(f"[场景B] {n} 并发读会话+消息 …")
    lat, errs = await scene_read(n, sem, token)
    rows.append(_stats("B.读会话+消息", lat, errs))

    # 场景 C：混合负载（30 并发 × 5 轮循环）
    print(f"[场景C] 30 并发 × 5 轮混合读 …")
    lat, errs = await scene_mixed(30, 5, asyncio.Semaphore(30), token)
    rows.append(_stats("C.混合循环读", lat, errs))

    # 场景 D：问答链路（真实 LLM，默认 10 并发）
    print(f"[场景D] {args.ask} 并发真实问答 …")
    lat, errs = await scene_ask(args.ask, asyncio.Semaphore(args.ask), token)
    rows.append(_stats("D.真实问答", lat, errs))

    _print(rows)
    print(f"\n[提示] 问答接口外部 LLM 为阿里云 qwen-plus，D 场景仅作链路验证；"
          f"A/B/C 为系统自身并发能力。")


if __name__ == "__main__":
    asyncio.run(main())
