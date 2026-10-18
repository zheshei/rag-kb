# RAG 企业级知识库问答系统

基于 **LangChain** 框架开发的企业级知识库问答系统。面向电商平台商品问答场景，通过浏览器进行知识库管理与知识库问答。

## 功能总览（全部里程碑完成 ✅）

| 模块 | 能力 |
| --- | --- |
| 认证 | 注册 / 登录 / 修改密码 / 当前用户；JWT + bcrypt；角色 admin / user |
| 知识库管理（仅 admin） | 文档上传（PDF / Word / TXT / MD，≤50MB）→ LangChain 解析 → 父子分块 → BGE 向量化 → Chroma 入库；列表 / 分页 / 删除 / 统计 |
| 知识库问答 | 混合检索（Chroma 向量 + BM25 关键词 + RRF 融合，可选 Rerank）→ 智谱 GLM 流式输出（SSE）→ **引用片段展示** |
| 多用户多会话（M4） | 每用户独立会话：创建 / 列表 / 重命名 / 删除；问答与引用自动落库，跨时段找回历史对话；会话级用户隔离 |
| 性能优化（M5） | 检索结果 TTL 缓存（知识库版本自动失效）、embedding 查询缓存、GZip 压缩、请求耗时监控、前端 vendor 分包、文档/会话分页、后台异步入库 |
| 管理员看板（M6） | 用户 / 文档 / 分块 / 会话 / 消息 / 向量库统计 + 最近文档列表 |

## 技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite + Chroma（向量库）+ fastembed（本地 BGE-small-zh-v1.5，CPU 推理）
- **LLM**：智谱 GLM-4-Flash（OpenAI 兼容端点，长期免费；可切换 Ollama 本地模型）
- **检索**：LangChain 加载器 / 文本分割器 + jieba BM25 + RRF 融合 + fastembed Rerank（可选）
- **前端**：Vue3 + Element Plus + Pinia + Vue Router + Vite
- **测试**：pytest（63 个用例：正常 / 边界 / 异常三类）

## 目录结构

```
RAG/
├── start.bat                  # Windows 一键启动
├── backend/
│   ├── app/
│   │   ├── main.py            # 应用入口（中间件 / 建表 / 种子 admin）
│   │   ├── core/              # 配置与安全（config / security）
│   │   ├── db/                # SQLAlchemy 会话与模型基类
│   │   ├── models/            # User / KnowledgeBase / Document / Conversation / Message
│   │   ├── schemas/           # Pydantic 请求响应模型
│   │   ├── crud/              # 数据访问层
│   │   ├── api/               # 路由与依赖（auth / kb / chat / conversation / dashboard）
│   │   └── services/          # embedding / vectorstore / ingestion / llm / retrieval / qa / cache
│   ├── tests/                 # pytest 单元测试（63 个用例）
│   ├── requirements.txt
│   └── .env                   # 智谱 API Key 等配置
├── frontend/                  # Vue3 前端（6 个页面 + 会话侧栏）
└── docs/设计文档.md            # 毕设设计文档
```

## 快速启动

### 1. 初始化环境（首次）

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 前端
cd ../frontend
npm install --registry=https://registry.npmmirror.com
```

> 说明：
> - Embedding 模型（BGE-small-zh-v1.5）首次使用自动下载，默认走 hf-mirror 国内镜像
> - 向量库 Chroma 无需外部服务，数据持久化在 `backend/data/`
> - 若使用智谱 GLM：把 API Key 填入 `backend/.env` 的 `ZHIPU_API_KEY` 后重启后端

### 2. 启动（Windows）

双击 `start.bat`，或手动：

```bash
# 后端（8000）
cd backend && .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端（5173）
cd frontend && npm run dev
```

浏览器访问 **http://localhost:5173**，管理员账号 **admin / 123456**。

### 3. 使用流程

1. 管理员登录 → **知识库管理** → 上传商品文档（等待"处理中"变"已完成"）
2. 任意用户登录 → **知识库问答** → 左侧新建会话 → 提问（回答中展示引用片段，可折叠查看原文）
3. 不同时间段登录，历史会话与消息自动恢复

## 运行测试

```bash
cd backend
.venv\Scripts\python -m pytest        # 63 passed
```

## 关键 API

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | /api/v1/auth/register | 注册 | 公开 |
| POST | /api/v1/auth/login | 登录 | 公开 |
| POST | /api/v1/auth/change-password | 改密码 | 登录 |
| POST | /api/v1/kb/documents/upload | 上传入库 | 管理员 |
| GET | /api/v1/kb/documents | 文档列表 | 管理员 |
| DELETE | /api/v1/kb/documents/{id} | 删除文档 | 管理员 |
| GET | /api/v1/kb/stats | 知识库统计 | 登录 |
| POST | /api/v1/chat/ask | 流式问答（SSE） | 登录 |
| GET/POST | /api/v1/conversations | 会话列表 / 创建 | 登录 |
| PATCH/DELETE | /api/v1/conversations/{id} | 重命名 / 删除 | 登录（本人） |
| GET | /api/v1/conversations/{id}/messages | 历史消息 | 登录（本人） |
| GET | /api/v1/dashboard/stats | 系统看板 | 管理员 |

问答接口 SSE 事件序列：`meta`（引用片段 + 会话 ID）→ `delta`（增量文本）→ `done` / `error`；问答与引用在流式结束后自动持久化。

## 性能优化（企业级）

- **检索缓存**：进程内 TTL 缓存（默认 300s / 128 条），知识库入库或删除后版本号 +1 自动失效
- **向量缓存**：相同问题不重复 embedding 推理
- **GZip 压缩** + **耗时监控**（X-Process-Time 响应头）
- **后台异步入库**：文档解析与向量化不阻塞上传请求
- **前端分包**：vue / element-plus 独立 vendor chunk
- **分页**：文档列表与会话列表均分页

## 部署说明

单机部署：SQLite + Chroma 本地文件，无需 Docker 与外部服务（适配无独显、网络受限环境）。生产环境建议：更换 `SECRET_KEY`、使用 HTTPS 反向代理（Nginx）、按需接入 Redis/PostgreSQL 扩展。
