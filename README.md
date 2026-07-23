# Atoms MVP

一个类 Atoms 的多智能体协作应用生成 MVP：用户用自然语言描述需求，AI 团队按 SOP 协作生成可预览的 Web 应用。

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)               │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Project  │  │  Chat Panel  │  │   App Viewer      │  │
│  │  List    │  │  (SSE/Stream)│  │  (iframe preview) │  │
│  └──────────┘  └──────────────┘  └───────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                   Backend (FastAPI)                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ 4 Agents │  │ Orchestrator │  │  Tools + Storage  │  │
│  │ Mike/Emma│  │ (3 modes)    │  │  (file/shell/sql) │  │
│  │ Bob/Alex │  │              │  │                   │  │
│  └──────────┘  └──────────────┘  └───────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                    LLM (LiteLLM)                         │
│        OpenAI / DeepSeek / 智谱 / Claude ...            │
└─────────────────────────────────────────────────────────┘
```

## 快速启动

### 1. 环境准备

```bash
# Python 3.9+
pip3 install -r backend/requirements.txt

# Node.js 18+
cd frontend && npm install
```

### 2. 配置 LLM

```bash
cp backend/.env.example .env
# 编辑 .env，填入你的 LLM API Key
```

```env
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

### 3. 启动

```bash
# 终端 1：启动后端
uvicorn backend.main:app --port 8000 --reload

# 终端 2：启动前端
cd frontend && npm run dev
```

访问 `http://localhost:5173` 即可使用。

## 执行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| ⚡ **Engineer** | 单 Agent (Alex) 直接生成代码 | 简单需求（todo、计算器） |
| 🤝 **Team** | 4 Agent 协作 (Mike→Emma→Bob→Alex) | 复杂需求（博客、Dashboard） |
| 🏁 **Race** | 3 个 LLM 并行竞速，选最佳结果 | 需要多方案对比 |

## 4 个核心 Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| **Mike** | Team Lead | 分析需求，任务分发 |
| **Emma** | Product Manager | 输出 PRD（目标、用户故事、功能列表） |
| **Bob** | Software Architect | 设计技术架构（技术栈、目录结构、数据模型） |
| **Alex** | Senior Engineer | 写代码（读写文件、运行命令） |

## 技术栈

- **后端**: FastAPI + LiteLLM + SQLite + aiosqlite
- **前端**: React 19 + TypeScript + Vite + Tailwind CSS + Zustand
- **LLM**: 支持 OpenAI 协议的所有模型（OpenAI / DeepSeek / 智谱 GLM / Claude 等）

## 项目结构

```
atoms_demo/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置加载
│   ├── llm.py               # LiteLLM 客户端
│   ├── tools.py             # Agent 工具（文件/Shell）
│   ├── db.py                # SQLite 持久化
│   ├── memory.py            # 会话历史 JSONL
│   ├── sse.py               # SSE 事件协议
│   ├── api/routes.py        # API 路由
│   ├── agents/
│   │   ├── base.py          # Agent 基类
│   │   ├── registry.py      # Agent 注册表
│   │   ├── team_lead.py     # Mike
│   │   ├── pm.py            # Emma
│   │   ├── architect.py     # Bob
│   │   └── engineer.py      # Alex
│   └── orchestrator/
│       ├── runner.py        # ReAct 循环
│       └── modes.py         # 3 种执行模式
├── frontend/
│   └── src/
│       ├── api/sse.ts       # SSE 客户端
│       ├── store/chatStore.ts # Zustand 状态管理
│       └── components/      # React 组件
├── data/                    # 运行期生成（SQLite + 项目代码）
└── .env                     # 环境变量（需自行创建）
```

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/chat` | POST | SSE 流式对话 |
| `/api/projects` | GET | 项目列表 |
| `/api/projects` | POST | 创建项目 |
| `/api/projects/{id}` | DELETE | 删除项目 |
| `/api/race/{id}/results` | GET | Race 结果 |
| `/api/race/{id}/select` | POST | 选择 Race 结果 |

## FAQ

**Q: 支持哪些 LLM？**
A: 所有兼容 OpenAI 协议的模型。在 `.env` 中配置 `LLM_BASE_URL` 和 `LLM_MODEL` 即可。

**Q: Race 模式如何使用多个模型？**
A: 在 `.env` 中设置 `LLM_RACE_MODELS=deepseek-chat,gpt-4o,claude-3-5-sonnet`（逗号分隔）。

**Q: 数据存储在哪里？**
A: 项目元数据在 `data/atoms.db`（SQLite），项目代码在 `data/projects/{id}/`。

**Q: 如何清理数据？**
A: 删除 `data/` 目录即可，重启后自动重建。

## 许可

MIT