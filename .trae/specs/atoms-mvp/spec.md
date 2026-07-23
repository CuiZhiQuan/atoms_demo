# Atoms MVP 多智能体应用生成 Demo Spec

## Why
在 **8 小时内**实现一个类 Atoms 的多智能体协作应用生成 MVP：用户用自然语言描述需求，由 AI 团队（团队负责人 / 产品经理 / 架构师 / 工程师）按 SOP 协作生成可预览、可部署的 Web 应用。所有核心功能完整交付，时间节奏按 8 小时紧凑编排。

## What Changes
- **新增** FastAPI 后端工程（基础框架 + LLM 客户端 + Agent 编排 + 工具 + 存储）
- **新增** React + Vite 前端工程（Chat UI + App Viewer + 项目列表）
- **新增** 4 个核心 Agent：team_lead（Mike）/ pm（Emma）/ architect（Bob）/ engineer（Alex）
- **新增** 3 种执行模式：Engineer 模式 / Team 模式 / Race 模式
- **新增** SSE 流式事件协议，实时推送 Agent 状态、思考、工具调用、文件变更
- **新增** 应用预览能力（静态文件服务 + iframe 嵌入，生成中显示加载动画，生成完自动刷新）
- **新增** 项目持久化（SQLite 存元数据 + 用户数据，文件系统存项目代码）
- **新增** LiteLLM 集成，支持 OpenAI 协议多模型（OpenAI/DeepSeek/智谱/Claude 等）
- **新增** JWT 用户认证（注册/登录/密码二次确认，多用户项目隔离）
- **新增** 一键部署到 Netlify（打包 zip + 自动注入 content-type 配置）
- **新增** 源码查看功能（文件树 + 语法高亮）
- **新增** `.env` 配置 + 本地直接启动（`uvicorn` + `npm run dev`）
- **新增** 平台部署指南（Netlify 前端 + Render 后端）

标记为 **非本期范围**（TODO）：
- App World 分享、社交分享
- SEO Agent、Data Analyst Agent、Researcher Agent
- Atoms Cloud / Supabase / Stripe / GitHub 集成
- 积分系统、付费方案
- 移动 App / APK 导出
- 本地项目导入
- 可视化编辑、Fix Bug 按钮

## Impact
- **新增 specs**：后端 API、Agent 编排、LLM 客户端、存储、前端 UI、流式协议、认证、部署
- **新增代码目录**：
  - `backend/`（FastAPI 服务）
  - `frontend/`（Vite + React 应用）
  - `data/`（运行期生成，SQLite + 项目代码）
  - `backend/.env.example`（环境变量模板）
  - `netlify.toml`（前端部署配置）
  - `render.yaml`（后端部署配置）
  - `README.md`（使用说明）
  - `AGENTS.md`（Agent 系统文档）
  - `DEPLOY.md`（平台部署指南）
  - `DEPLOY_APP.md`（应用部署指南）

---

## ADDED Requirements

### Requirement: 自然语言对话生成应用
系统 SHALL 提供基于自然语言的对话入口，用户输入需求描述后，触发 Agent 团队协作，最终生成可预览的 Web 应用代码。

#### Scenario: 用户首次发起请求
- **WHEN** 用户在前端 Chat 页面输入需求（例如"做一个待办事项 Web 应用"）并点击发送
- **THEN** 后端创建项目（若无），触发选中的执行模式，Agent 开始协作
- **AND** 前端通过 SSE 实时接收 Agent 状态、思考过程、工具调用结果
- **AND** 左侧项目列表立即刷新，新项目自动选中
- **AND** App Viewer 在文件生成后自动刷新预览

#### Scenario: 用户多轮迭代
- **WHEN** 用户在已有项目上继续发送消息（例如"把按钮改成蓝色"）
- **THEN** 系统保留项目上下文，Agent 读取现有代码后增量修改
- **AND** App Viewer 实时反映变更

### Requirement: 多 Agent 协作（4 个核心角色）
系统 SHALL 实现 4 个核心 Agent，按 SOP 协作完成任务：
- **Mike（team_lead）**：协调任务，把需求分发给下游 Agent
- **Emma（pm）**：分析需求，输出 PRD（含目标、用户故事、功能列表）
- **Bob（architect）**：基于 PRD 设计技术架构（技术栈、目录结构、数据模型）
- **Alex（engineer）**：基于架构落地代码（读写文件、运行命令）

#### Scenario: Team 模式协作
- **WHEN** 用户选择 Team 模式并发起请求
- **THEN** 编排器按 `team_lead → pm → architect → engineer` 顺序执行
- **AND** 每个 Agent 的输出作为下一阶段的输入
- **AND** Engineer Agent 通过 tool calling 写入文件

#### Scenario: Engineer 模式协作
- **WHEN** 用户选择 Engineer 模式
- **THEN** 只调用 `engineer` 一个 Agent，跳过 PM/Architect，直接根据需求生成代码
- **AND** 响应更快、积分消耗更少

### Requirement: 三种执行模式
系统 SHALL 提供三种执行模式供用户切换：
- **Engineer 模式**：单 Agent（Alex），适合简单需求
- **Team 模式**：4 Agent 协作，适合复杂需求
- **Race 模式**：同一提示词并行调用多个 LLM，结果出来后用户挑选最佳

#### Scenario: Race 模式执行
- **WHEN** 用户选择 Race 模式并发起请求
- **THEN** 编排器并发调用 2 个以上 LLM（默认 3 个）
- **AND** 每个 LLM 独立完成 Engineer 流程
- **AND** 全部完成后前端展示多份结果，用户选择一份继续
- **AND** 未选中的结果被清理以节省存储

### Requirement: SSE 流式事件协议
系统 SHALL 通过 SSE（Server-Sent Events）向前端实时推送执行过程。

#### Scenario: 事件流传输
- **WHEN** 后端编排器开始执行任务
- **THEN** 持续推送以下事件类型：
  - `session_start` / `session_end`
  - `agent_start` / `agent_thought` / `agent_end`
  - `tool_call` / `tool_result`
  - `file_created` / `file_updated`
  - `message`（用户可见的中间状态）
  - `error` / `done`
- **AND** 每个事件的 JSON 格式为 `{type, payload, timestamp}`

### Requirement: 应用预览（App Viewer）
系统 SHALL 提供应用预览能力，工程师生成的代码可在前端实时查看。

#### Scenario: 生成中状态
- **WHEN** Agent 正在生成代码（未完成）
- **THEN** App Viewer 显示加载动画和 "Generating app..." 文字
- **AND** 工具栏按钮隐藏，状态灯黄色闪烁

#### Scenario: 前端项目预览
- **WHEN** Engineer Agent 生成了 `index.html`
- **THEN** 后端将该项目根目录挂为静态文件服务
- **AND** 前端通过 iframe 嵌入预览
- **AND** 支持移动端 / PC 端视图切换

#### Scenario: 预览刷新
- **WHEN** Engineer Agent 写入或修改文件
- **THEN** 前端自动刷新 iframe（防抖 1 秒）

### Requirement: 多 LLM 支持（OpenAI 协议）
系统 SHALL 通过 LiteLLM 集成多 LLM Provider，配置切换无需改代码。

#### Scenario: 模型切换
- **WHEN** 用户在 `.env` 中配置 `LLM_MODEL=deepseek-chat` 或 `gpt-4o` 或 `claude-3-5-sonnet`
- **THEN** 系统自动添加 `openai/` 前缀并调用对应 Provider API
- **AND** 支持流式输出、指数退避重试、超时控制

### Requirement: 项目持久化
系统 SHALL 持久化用户项目和会话历史。

#### Scenario: 项目元数据存储
- **WHEN** 用户首次创建项目
- **THEN** 在 SQLite 中插入记录：`id, name, mode, created_at, updated_at, file_path, user_id`
- **AND** 项目代码以文件形式存到 `data/projects/{project_id}/`

#### Scenario: 会话历史持久化
- **WHEN** Agent 对话产生新消息
- **THEN** 消息以 JSON Lines 格式追加到 `data/projects/{project_id}/.atoms/session.jsonl`
- **AND** 断连/重启后可从该文件恢复会话

### Requirement: 用户认证
系统 SHALL 提供 JWT 用户认证，实现多用户项目隔离。

#### Scenario: 注册
- **WHEN** 用户输入用户名（≥3 字符）、密码（≥6 字符）和确认密码
- **THEN** 系统验证两次密码一致后创建用户
- **AND** 返回 JWT Token 供后续请求使用

#### Scenario: 登录
- **WHEN** 用户输入已注册的用户名和密码
- **THEN** 系统验证成功后返回 JWT Token
- **AND** 所有 API 请求需携带 Token 鉴权

### Requirement: 工具调用（Tool Calling）
系统 SHALL 为 Agent 提供以下工具：
- `write_file(path, content)`：写入文件
- `read_file(path)`：读取文件
- `list_dir(path)`：列出目录
- `run_shell(command, cwd)`：执行 Shell 命令（白名单 + 超时）

#### Scenario: 安全约束
- **WHEN** Agent 调用 `run_shell`
- **THEN** 仅允许白名单命令（如 `npm install`、`npm run build`）
- **AND** 路径限制在项目目录内
- **AND** 单次执行超时 60 秒

### Requirement: 一键部署到 Netlify
系统 SHALL 支持将生成的应用一键部署到 Netlify。

#### Scenario: 部署流程
- **WHEN** 用户点击 Deploy 按钮
- **THEN** 后端将项目文件打包为 zip，通过 Netlify API 创建站点并部署
- **AND** zip 中自动注入 `netlify.toml` 确保正确的 Content-Type 头
- **AND** 返回线上 URL，用户可点击访问

### Requirement: 本地启动
系统 SHALL 支持本地直接启动，无需 Docker：后端 `python3 -m uvicorn` + 前端 `npm run dev`。

#### Scenario: 启动流程
- **WHEN** 用户执行 `python3 -m uvicorn backend.main:app --port 8000` 和 `npm run dev`（前端）
- **THEN** 后端暴露 `http://localhost:8000`，前端暴露 `http://localhost:5173`
- **AND** 访问前端即可使用全部功能

### Requirement: 配置与文档
系统 SHALL 提供完整的配置示例和使用文档。

#### Scenario: 配置文件
- **WHEN** 用户首次克隆项目
- **THEN** 复制 `backend/.env.example` 为 `.env` 并填入 LLM API Key
- **AND** README 包含：技术栈介绍、快速启动、模式说明、API 接口、配置参考
- **AND** DEPLOY.md 包含平台部署指南（Netlify + Render）
- **AND** DEPLOY_APP.md 包含应用部署指南（Netlify Token 获取）

---

## MODIFIED Requirements
无（本项目从零开始，无既有 spec 修改）。

## REMOVED Requirements
无（无既有 spec 移除）。