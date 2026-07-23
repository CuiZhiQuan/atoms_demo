# Tasks（8 小时节奏，完整功能）

> 每个 Task 完成后请勾选 `[x]`。功能完整交付，节奏紧凑并行。

## Hour 0-1：环境搭建 + 后端骨架 + 前端骨架（并行）

- [ ] **Task 1.1：项目目录 + 后端依赖 + 配置**
  - 创建 `backend/`、`frontend/`、`data/` 目录，`backend/requirements.txt`
  - `backend/.env.example`：`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
  - `.gitignore`（排除 `data/`、`node_modules/`、`__pycache__`、`.env`）
  - 验收：`pip install -r backend/requirements.txt` 成功

- [ ] **Task 1.2：FastAPI 骨架**
  - `backend/main.py`：FastAPI app + CORS + 静态文件挂载 `/workspace` + `GET /api/health`
  - 验收：`uvicorn backend.main:app` 启动，`curl localhost:8000/api/health` 返回 200

- [ ] **Task 1.3：Vite + React 前端**
  - `cd frontend && npm create vite@latest . -- --template react-ts`
  - 安装 `tailwindcss`、`zustand`
  - 验收：`npm run dev` 访问 `localhost:5173` 看到基础布局（三栏：项目列表 | Chat | Viewer 占位）

## Hour 1-2：LLM 客户端 + 工具集 + 存储（并行）

- [ ] **Task 2.1：LLM 客户端**
  - `backend/llm.py`：封装 `async def chat_stream(messages, tools)` 和 `async def chat_complete(messages, tools)`
  - 使用 LiteLLM，支持流式 + 非流式，指数退避重试，超时 120s
  - 验收：单元测试调用 LLM 返回非空文本

- [ ] **Task 2.2：工具集（Tools）**
  - `backend/tools.py`：`write_file` / `read_file` / `list_dir` / `run_shell`
  - `run_shell` 白名单 `npm`，路径限制在项目目录，超时 60s
  - 工具定义用 OpenAI function calling schema
  - 验收：`write_file` 创建文件，`run_shell("ls")` 成功

- [ ] **Task 2.3：存储层**
  - `backend/db.py`：SQLite 项目元数据 CRUD（`init_db` / `create_project` / `get_project` / `list_projects` / `delete_project`）
  - `backend/memory.py`：会话历史 JSONL 读写（`save_message` / `load_messages`）
  - 验收：创建项目后重启可查询

## Hour 2-4：4 个 Agent + 注册表 + 编排器

- [ ] **Task 3.1：Agent 基类 + 注册表**
  - `backend/agents/base.py`：Agent 基类（name / role / system_prompt / tools）
  - `backend/agents/registry.py`：`get_agent(name)` / `list_agents()`
  - 验收：`get_agent("engineer")` 返回实例

- [ ] **Task 3.2：Engineer Agent**
  - `backend/agents/engineer.py`：Alex，绑定 file + shell 工具
  - `backend/prompts/engineer.md`：全栈工程师 Prompt
  - 验收：单测验证 Agent 能写文件

- [ ] **Task 3.3：PM Agent + Architect Agent + Team Lead Agent（并行）**
  - `backend/agents/pm.py`：Emma，输出结构化 PRD JSON
  - `backend/agents/architect.py`：Bob，输出技术栈 + 目录结构 + 数据模型
  - `backend/agents/team_lead.py`：Mike，判断任务流程并分发
  - 各自 Prompt 模板在 `backend/prompts/` 下
  - 验收：每个 Agent 单独调用能输出预期结构

- [ ] **Task 3.4：Orchestrator（DAG + 三种模式）**
  - `backend/orchestrator/runner.py`：ReAct 循环核心（LLM 调用 → 解析 tool_call → 执行 → 回填 → 循环，最大 15 步）
  - `backend/orchestrator/modes.py`：`engineer_mode()` / `team_mode()` / `race_mode()`
  - Team 模式流程：`team_lead → pm → architect → engineer`
  - Race 模式：`asyncio.gather` 并发 3 个 LLM 跑 Engineer 流程
  - 验收：Team 模式跑通完整 todo 项目

## Hour 4-5：SSE 端点 + 完整 API 层

- [ ] **Task 4.1：SSE 事件协议**
  - `backend/sse.py`：事件类型 `session_start / agent_start / agent_thought / agent_end / tool_call / tool_result / file_created / file_updated / message / error / done`
  - 每个事件格式 `{type, payload, timestamp}`
  - 验收：事件流格式正确

- [ ] **Task 4.2：API 路由**
  - `POST /api/chat`：SSE 流式端点，接收 `{prompt, mode, project_id?}`
  - `GET /api/projects` / `POST /api/projects` / `DELETE /api/projects/{id}`
  - `GET /api/race/{race_id}/results` / `POST /api/race/{race_id}/select`
  - 验收：curl 测试所有端点

## Hour 5-7：前端完整实现

- [ ] **Task 5.1：SSE 客户端 + 状态管理**
  - `frontend/src/api/sse.ts`：`runStream(prompt, mode)` 用 fetch + ReadableStream
  - `frontend/src/store/chatStore.ts`：Zustand（消息列表、当前项目、模式、事件流）
  - 验收：发送请求后 console 看到事件流

- [ ] **Task 5.2：Chat UI + 消息渲染**
  - `frontend/src/components/ChatPanel.tsx`：消息列表 + 输入框 + 发送
  - `frontend/src/components/MessageBubble.tsx`：区分 user / agent，显示思考过程
  - `frontend/src/components/AgentStatus.tsx`：显示当前活跃 Agent + 状态
  - 验收：能发送消息，实时显示 Agent 回复

- [ ] **Task 5.3：App Viewer + 项目列表 + 模式选择器（并行）**
  - `frontend/src/components/AppViewer.tsx`：iframe + PC/移动切换 + 自动刷新
  - `frontend/src/components/ProjectList.tsx`：左侧项目列表，创建/选择/删除
  - `frontend/src/components/ModeSelector.tsx`：Engineer / Team / Race 下拉切换
  - 验收：项目切换正常，模式切换后请求走对应后端，文件变更时 iframe 刷新

- [ ] **Task 5.4：Race 模式 UI**
  - `frontend/src/components/RaceResults.tsx`：多份结果缩略图展示
  - 用户点击选一份，发送 `POST /api/race/{id}/select`
  - 验收：Race 模式结束后看到多份结果，选一份后继续

## Hour 7-8：README + 联调

- [ ] **Task 6.1：README + 联调**
  - README：项目简介、架构图、快速启动（本地 `uvicorn` + `npm run dev`）、模式说明、配置、FAQ
  - 端到端测试 3 个用例：
    1. "做一个 todo 列表"（Engineer 模式）
    2. "做一个博客主页"（Team 模式）
    3. "做一个计算器"（Race 模式选最佳）
  - 修复所有 bug

---

## Task Dependencies

```
Task 1.1 (环境) ─┬─→ Task 1.2 (后端骨架) ─┬─→ Task 2.2 (工具) ─┐
                └─→ Task 1.3 (前端骨架)    │                     │
                                           │  Task 2.1 (LLM) ───┤
                                           │  Task 2.3 (存储) ──┤
                                           └────────────────────┼─→ Task 3.1 (Agent 基类)
                                                                           ↓
                                                                Task 3.2 (Engineer) + Task 3.3 (PM/Arch/Lead) [并行]
                                                                           ↓
                                                                Task 3.4 (Orchestrator)
                                                                           ↓
                                                                Task 4.1 (SSE) + Task 4.2 (API) [并行]
                                                                           ↓
                                                                Task 5.1 (SSE 客户端 + Store)
                                                                           ↓
                                                  ┌─────────────────────────┼─────────────────────────┐
                                                  ↓                         ↓                         ↓
                                          Task 5.2 (Chat UI)        Task 5.3 (Viewer/列表/模式)   Task 5.4 (Race UI)
                                                                           ↓
                                                                Task 6.1 (README + 联调)
```

**关键路径**：1.1 → 1.2 → 2.2 → 3.1 → 3.2 → 3.4 → 4.1 → 5.1 → 5.2 → 6.1

**可并行任务**：
- Task 1.2 和 1.3 可并行（后端 + 前端独立搭建）
- Task 2.1、2.2、2.3 可并行（LLM / 工具 / 存储 独立模块）
- Task 3.2 和 3.3 可并行（Engineer 和 PM/Arch/Lead 独立实现）
- Task 4.1 和 4.2 可并行（SSE 协议和 API 路由可同时写）
- Task 5.2、5.3、5.4 可并行（三个前端组件独立）