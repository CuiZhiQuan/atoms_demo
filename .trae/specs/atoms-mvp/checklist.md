# Checklist（8 小时完整功能验收）

## Hour 0-1：环境 + 骨架
- [ ] `backend/requirements.txt` 包含 fastapi、uvicorn、litellm、sse-starlette、aiosqlite、aiofiles
- [ ] `backend/.env.example` 包含 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
- [ ] `.gitignore` 排除 `data/`、`node_modules/`、`__pycache__`、`.env`
- [ ] `uvicorn backend.main:app` 启动，`/api/health` 返回 200，`/workspace/` 静态文件服务可用
- [ ] Vite 前端启动，访问 `localhost:5173` 看到三栏布局（项目列表 | Chat | Viewer 占位）

## Hour 1-2：LLM + 工具 + 存储
- [ ] `backend/llm.py` 实现 `chat_stream` 和 `chat_complete`，支持流式 + 非流式
- [ ] LiteLLM 支持指数退避重试和超时控制
- [ ] `backend/tools.py` 实现 `write_file` / `read_file` / `list_dir` / `run_shell`
- [ ] `run_shell` 有白名单限制（npm），路径限制在项目目录，超时 60s
- [ ] `backend/db.py` 实现 SQLite CRUD：`init_db` / `create_project` / `get_project` / `list_projects` / `delete_project`
- [ ] `backend/memory.py` 实现会话历史 JSONL 读写：`save_message` / `load_messages`
- [ ] 创建项目后重启可查询（数据不丢失）

## Hour 2-4：Agent + 编排器
- [ ] `backend/agents/base.py`：Agent 基类（name / role / system_prompt / tools）
- [ ] `backend/agents/registry.py`：`get_agent(name)` / `list_agents()` 正常工作
- [ ] `backend/agents/engineer.py`：Alex Agent 绑定 file + shell 工具，能根据需求写文件
- [ ] `backend/agents/pm.py`：Emma Agent 输出结构化 PRD JSON
- [ ] `backend/agents/architect.py`：Bob Agent 输出技术栈 + 目录结构 + 数据模型
- [ ] `backend/agents/team_lead.py`：Mike Agent 能判断任务流程并分发
- [ ] ReAct 循环有最大步数限制（≤ 15 步），能识别何时停止
- [ ] `engineer_mode()` 只调 Engineer Agent，快速生成代码
- [ ] `team_mode()` 按 `team_lead → pm → architect → engineer` 完整协作
- [ ] `race_mode()` 并发调用 3 个 LLM，输出多份独立结果

## Hour 4-5：SSE + API
- [ ] `POST /api/chat` 返回 `StreamingResponse`，支持 `{prompt, mode, project_id?}`
- [ ] 11 种事件类型全部覆盖：`session_start / agent_start / agent_thought / agent_end / tool_call / tool_result / file_created / file_updated / message / error / done`
- [ ] 每个事件格式 `{type, payload, timestamp}`
- [ ] `GET /api/projects` 返回项目列表
- [ ] `POST /api/projects` 创建新项目
- [ ] `DELETE /api/projects/{id}` 删除项目
- [ ] `GET /api/race/{race_id}/results` 返回 Race 结果
- [ ] `POST /api/race/{race_id}/select` 选定结果并清理未选中

## Hour 5-7：前端
- [ ] `frontend/src/api/sse.ts`：`runStream` 能正确解析 SSE 事件流
- [ ] `frontend/src/store/chatStore.ts`：Zustand 状态管理（消息、项目、模式、事件）
- [ ] ChatPanel：消息列表 + 输入框 + 发送按钮，实时显示 Agent 回复
- [ ] MessageBubble：区分 user 和 agent 消息，展示思考过程
- [ ] AgentStatus：显示当前活跃 Agent 名称和状态
- [ ] AppViewer：iframe 嵌入 + PC/移动端切换
- [ ] 收到 `file_created` / `file_updated` 事件时 iframe 自动刷新（防抖 1s）
- [ ] ProjectList：能创建 / 选择 / 删除项目
- [ ] ModeSelector：能在 Engineer / Team / Race 之间切换
- [ ] RaceResults：Race 结束后展示多份结果，用户点击选一份

## Hour 7-8：README + 联调
- [ ] README 包含：项目简介、快速启动（本地 `uvicorn` + `npm run dev`）、模式说明、配置、FAQ
- [ ] "做一个 todo 列表"（Engineer 模式）：Agent 写出 HTML + JS，iframe 中可交互
- [ ] "做一个博客主页"（Team 模式）：完整 4 Agent 协作生成
- [ ] "做一个计算器"（Race 模式）：多份结果选最佳

## 质量门禁
- [ ] 前端 TS 编译无错误
- [ ] 后端启动无致命错误
- [ ] `.env` 在 `.gitignore` 中
- [ ] 项目从零启动（删除 `data/` 后仍能正常运行）
- [ ] CORS 配置正确，前端 5173 可访问后端 8000
- [ ] Agent 调用工具时路径限制在项目目录内（无路径穿越）
- [ ] LLM API Key 仅在后端使用，前端代码不包含
- [ ] `run_shell` 白名单生效，非法命令被拒绝