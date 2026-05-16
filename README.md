# Smart API Assistant

面向 OpenAPI / Swagger 文档的智能助手，支持自然语言问答、代码生成及 MCP 标准化工具输出。

> **OpenAPI 与 Swagger**：Swagger 是早期的品牌名，OpenAPI Specification (OAS) 是现在的行业标准名称。日常所说的 "Swagger 文档"（`swagger.json` / `swagger.yaml`）本质上就是 OpenAPI 规范文档，本项目解析和索引的对象即为此类文件。

---

## 功能特性

- **文档智能解析** — 上传 OpenAPI JSON / YAML 文件，自动提取结构化信息并生成语义 Chunk，写入向量数据库
- **自然语言问答** — 基于文档内容的 RAG 检索增强问答，支持多轮对话与上下文记忆
- **代码生成** — 根据自然语言描述生成多语言（Python、JavaScript、Go 等）API 调用代码片段
- **MCP 标准化输出** — 通过 MCP 协议对外暴露标准化工具能力，可被外部 Agent / IDE 直接调用
- **SSE 流式响应** — 对话与代码生成接口均采用 Server-Sent Events 流式输出，提升交互体验
- **分层记忆机制** — Redis 中期记忆（30min TTL）+ PostgreSQL 持久记忆，兼顾性能与可靠性

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI 网关层                               │
│  ┌──────────────┐  ┌─────────────────┐  ┌───────────────────────┐  │
│  │ 文档上传端点  │  │ /chat SSE 端点   │  │ /mcp SSE 端点         │  │
│  │  (异步任务)   │  │ (问答/代码生成)  │  │ (MCP Server 独立入口)  │  │
│  └──────────────┘  └─────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌──────────────┐    ┌─────────────────────────┐    ┌──────────────┐
│ Parser Agent │    │   LangGraph Supervisor   │    │ MCP Server   │
│ (独立链路，   │    │   (意图识别与 Agent 路由) │    │ (独立模块，  │
│  异步执行)    │    │                          │    │  不复用      │
└──────────────┘    └───────────┬─────────────┘    │  Supervisor) │
                                │                  └──────┬───────┘
              ┌─────────────────┼─────────────────┐       │
              ▼                 ▼                 ▼       │
         ┌────────┐       ┌────────┐       ┌────────┐    │
         │   QA   │       │CodeGen │       │  Tools │◄───┘
         │ Agent  │       │ Agent  │       │(预留)  │
         └────────┘       └────────┘       └────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  RAG 层(Chroma)  │  Redis(中期记忆)  │  PostgreSQL(持久记忆)  │
│  · API 文档向量   │  · 会话上下文      │  · 对话历史长期存储     │
│  · 端点/参数 Chunk│  · 多轮对话历史    │  · Redis 过期后兜底     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 层级 | 技术 / 框架 | 用途 |
|------|-------------|------|
| Web 网关 | FastAPI + Uvicorn | RESTful API 服务与 SSE 流式输出承载 |
| 前端 | Vue 3 + Vite + TypeScript | 用户交互界面 |
| Agent 编排 | LangGraph | 多 Agent 状态流转与路由决策 |
| LLM 交互 | LangChain | LLM 调用、Prompt 管理、链式封装 |
| 大模型 | DeepSeek v4-pro | 问答、代码生成、意图识别等推理任务 |
| RAG 检索 | Chroma | API 文档 Embedding 存储与相似度检索 |
| Embedding | 阿里云百炼 text-embedding-v4 | 文本向量化 |
| 中期记忆 | Redis | 会话上下文缓存、多轮对话历史 |
| 持久记忆 | PostgreSQL | 对话历史长期存储 |
| MCP 协议 | MCP Python SDK | 对外暴露标准化工具能力 |
| 部署 | Docker Compose | 一键编排基础设施与应用服务 |

---

## 项目结构

```
Smart API Assistant/
├── backend/                    # FastAPI 后端服务
│   ├── app/
│   │   ├── api/                # RESTful 路由层（端点注册、SSE 流式封装）
│   │   ├── agents/             # LangGraph Agent 定义（Supervisor、QA、CodeGen）
│   │   ├── parser/             # 文档解析独立链路（异步 Parser、Chunker、任务管理）
│   │   ├── rag/                # RAG 基础设施（Chroma、Retriever、Embedding）
│   │   ├── tools/              # 外部工具封装
│   │   ├── mcp/                # MCP Server 独立模块（SSE 服务、工具集、会话管理）
│   │   ├── memory/             # 记忆层（Redis 短期记忆、PostgreSQL 长期记忆）
│   │   ├── models/             # Pydantic 数据模型
│   │   ├── config.py           # 全局配置（环境变量、API Keys）
│   │   └── main.py             # FastAPI 应用入口与生命周期管理
│   ├── tests/                  # pytest 测试套件
│   ├── requirements.txt        # Python 依赖
│   └── Dockerfile              # 后端服务容器镜像
├── frontend/                   # Vue 3 前端应用
├── planing/                    # 需求与设计文档
│   ├── smart-api-assistant-design.md   # 系统设计方案
│   ├── 接口文档.md             # RESTful + SSE + MCP 接口定义
│   └── 前端设计.md             # 前端设计文档
├── docker-compose.yml          # 全栈部署编排
└── README.md                   # 项目说明
```

---

## 快速开始

### 环境要求

- Python >= 3.12
- Node.js >= 18（前端开发）
- Docker & Docker Compose（推荐用于全栈部署）

### 1. 克隆仓库

```bash
git clone <repository-url>
cd Smart API Assistant
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 应用配置
APP_NAME=Smart API Assistant
APP_VERSION=1.0.0
DEBUG=false

# DeepSeek LLM
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 阿里云百炼 Embedding
DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
EMBEDDING_MODEL=text-embedding-v4

# Chroma 向量数据库
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_CONNECTION=api_docs

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_SESSION_TTL=1800

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sma
POSTGRES_PASSWORD=sma_password
POSTGRES_DB=sma_db
```

### 3. 基础设施启动（Docker Compose）

```bash
# 启动 Redis、Chroma、PostgreSQL
docker compose up -d redis chroma postgres
```

### 4. 后端服务启动

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：http://localhost:8000/docs 查看自动生成的 API 文档。

### 5. 前端开发启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器默认地址：http://localhost:5173

---

## 一键全栈部署

使用 Docker Compose 一键启动所有服务（包含后端应用）：

```bash
docker compose up -d
```

服务端口映射：

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI 后端 | `8000` | RESTful API + SSE 服务 |
| Chroma | `8001` | 向量数据库 |
| Redis | `6379` | 会话缓存 |
| PostgreSQL | `5432` | 对话持久化 |

---

## API 概览

### RESTful 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/documents` | 上传 OpenAPI 文档（异步解析） |
| `GET` | `/api/v1/documents/{task_id}/status` | 查询解析任务状态 |
| `POST` | `/api/v1/chat` | 流式对话问答（SSE） |
| `POST` | `/api/v1/chat/codegen` | 流式代码生成（SSE） |
| `GET` | `/health` | 健康检查 |

### MCP Server 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/mcp/sse` | MCP SSE 连接入口 |
| `POST` | `/mcp/messages` | MCP 消息接收端点 |

> 详细的接口定义与数据模型见 [`planing/接口文档.md`](planing/接口文档.md)。

---

## 核心 Agent 说明

| Agent | 职责 | 触发条件 |
|-------|------|----------|
| **Supervisor** | 意图识别与 Agent 路由 | 所有用户请求入口 |
| **QA Agent** | 基于 RAG 的 API 文档问答 | 用户询问 API 用法、参数含义等 |
| **CodeGen Agent** | 生成多语言调用代码 | 用户要求生成代码示例 |
| **Parser Agent** | 异步解析文档并索引到向量库 | 上传 OpenAPI 文档后触发 |

---

## 测试

后端使用 pytest 进行单元测试与集成测试：

```bash
cd backend
pytest -v
```

---

## 相关文档

- [`planing/smart-api-assistant-design.md`](planing/smart-api-assistant-design.md) — 系统设计方案
- [`planing/接口文档.md`](planing/接口文档.md) — 接口定义与数据模型
- [`planing/前端设计.md`](planing/前端设计.md) — 前端设计文档

---

## License

[MIT](LICENSE)
