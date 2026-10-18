"""端到端联调脚本：登录 → 上传入库（真实 BGE）→ 会话 → 权限 → 看板。"""
import time

import httpx

BASE = "http://127.0.0.1:8000/api/v1"


def show(name, ok, extra=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {extra}")


with httpx.Client(base_url=BASE, timeout=120) as c:
    # 1. 管理员登录
    r = c.post("/auth/login", json={"username": "admin", "password": "123456"})
    show("admin 登录", r.status_code == 200)
    admin_token = r.json()["access_token"]
    ah = {"Authorization": f"Bearer {admin_token}"}

    # 2. 上传样例商品文档（真实入库，BGE 向量化）
    with open("data/sample_products.txt", "rb") as f:
        r = c.post("/kb/documents/upload", headers=ah, files={"file": ("sample_products.txt", f, "text/plain")})
    show("文档上传", r.status_code == 201, f"-> doc_id={r.json()['id']} status={r.json()['status']}")
    doc_id = r.json()["id"]

    # 3. 轮询入库完成（分块写入 Chroma）
    completed = False
    for _ in range(60):
        time.sleep(2)
        r = c.get("/kb/documents", headers=ah)
        items = r.json()["items"]
        doc = next((d for d in items if d["id"] == doc_id), None)
        if doc and doc["status"] == "completed":
            completed = True
            chunk_count = doc["chunk_count"]
            break
    show("后台入库完成", completed, f"-> 分块数={chunk_count if completed else 'N/A'}")

    # 4. 统计
    r = c.get("/kb/stats", headers=ah)
    show("知识库统计", r.status_code == 200, f"-> docs={r.json()['document_count']} chunks={r.json()['chunk_count']}")

    # 5. 普通用户注册/登录
    c.post("/auth/register", json={"username": "e2e_user", "password": "e2e_pass1"})
    r = c.post("/auth/login", json={"username": "e2e_user", "password": "e2e_pass1"})
    show("普通用户注册登录", r.status_code == 200)
    user_token = r.json()["access_token"]
    uh = {"Authorization": f"Bearer {user_token}"}

    # 6. 权限：普通用户不可管理知识库
    r = c.get("/kb/documents", headers=uh)
    show("普通用户访问文档列表 403", r.status_code == 403)
    r = c.get("/kb/stats", headers=uh)
    show("普通用户访问统计 200", r.status_code == 200)

    # 7. 会话：创建 / 列表 / 消息 / 重命名 / 删除
    r = c.post("/conversations", headers=uh, json={"title": "联调会话"})
    show("创建会话", r.status_code == 201, f"-> id={r.json()['id']}")
    conv_id = r.json()["id"]
    r = c.get("/conversations", headers=uh)
    show("会话列表", r.status_code == 200 and any(x["id"] == conv_id for x in r.json()["items"]))
    r = c.get(f"/conversations/{conv_id}/messages", headers=uh)
    show("会话消息(空)", r.status_code == 200 and r.json() == [])
    r = c.patch(f"/conversations/{conv_id}", headers=uh, json={"title": "改名会话"})
    show("会话重命名", r.status_code == 200 and r.json()["title"] == "改名会话")

    # 8. 会话隔离：用户访问 admin 的会话 404
    r = c.post("/conversations", headers=ah, json={"title": "admin 私会话"})
    admin_conv = r.json()["id"]
    r = c.get(f"/conversations/{admin_conv}/messages", headers=uh)
    show("跨用户会话隔离 404", r.status_code == 404)

    # 9. 问答接口（未配置智谱 Key → 400 明确提示）
    r = c.post("/chat/ask", headers=uh, json={"question": "无线蓝牙耳机续航多久", "top_k": 3, "conversation_id": conv_id})
    show("问答接口(无Key提示)", r.status_code == 400 and "ZHIPU_API_KEY" in r.json()["detail"])

    # 10. 看板：admin 200 / user 403
    r = c.get("/dashboard/stats", headers=ah)
    show("看板(admin)", r.status_code == 200 and r.json()["users"] >= 2)
    r = c.get("/dashboard/stats", headers=uh)
    show("看板(user 403)", r.status_code == 403)

    # 11. 清理：删除联调会话
    r = c.delete(f"/conversations/{conv_id}", headers=uh)
    show("删除会话", r.status_code == 200)

print("\n端到端联调结束")
