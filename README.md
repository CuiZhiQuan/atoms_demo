# Atoms MVP

多智能体协作应用生成平台：用户用自然语言描述需求，AI 团队按 SOP 协作，自动生成可预览、可部署的 Web 应用。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 🤖 **4 Agent 协作** | Team Lead → PM → Architect → Engineer 流水线 |
| ⚡ **3 种执行模式** | Engineer（单 Agent）/ Team（4 Agent 协作）/ Race（并行竞速） |
| 🔐 **用户认证** | JWT 注册/登录，密码二次确认，多用户项目隔离 |
| 👁️ **实时预览** | 桌面端/移动端双视图切换，生成中显示加载动画，生成完自动刷新 |
| 📂 **源码查看** | 内置文件树 + 语法高亮，可查看生成的所有源文件 |
| 🚀 **一键部署** | 将生成的应用一键部署到 Netlify，获得公开 URL |
| 🔄 **SSE 流式推送** | Agent 状态、工具调用、文件变更实时展示 |

---

## 快速启动

### 1. 环境要求

- Python 3.9+
- Node.js 18+

### 2. 安装依赖

```bash
# 后端依赖
pip3 install -r backend/requirements.txt

# 前端依赖
cd frontend && npm install
```

### 3. 配置 LLM

```bash
cp backend/.env.example .env
```

编辑 `.env`，填入你的 LLM API Key：

```env
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
LLM_RACE_MODELS=deepseek-v3,deepseek-chat
```

### 4. 启动

```bash
# 终端 1：启动后端
python3 -m uvicorn backend.main:app --port 8000 --reload

# 终端 2：启动前端
cd frontend && npm run dev
```

访问 `http://localhost:5173`，注册账号后即可使用。

---

## 使用指南

### 注册与登录

首次使用需要注册账号：
- 用户名 ≥ 3 字符
- 密码 ≥ 6 字符，需二次确认
- 登录后获得 JWT Token，所有 API 请求自动携带 Token 鉴权

### 三种执行模式

| 模式 | 说明 | 耗时 | 适用场景 |
|------|------|------|----------|
| ⚡ **Engineer** | 单 Agent (Alex) 直接生成代码 | 30s - 2min | 简单需求（todo、计算器、落地页） |
| 🤝 **Team** | 4 Agent SOP 协作 (Mike→Emma→Bob→Alex) | 2 - 5min | 复杂需求（多页应用、仪表盘、游戏） |
| 🏁 **Race** | 3 个 LLM 并行竞速，选择最佳结果 | 2 - 5min | 对质量要求高，需要多方案对比 |

### 预览应用

Agent 生成代码后，右侧预览区自动展示应用效果：

- **生成中**：显示加载动画 "Generating app..."，状态灯黄色闪烁
- **生成完**：自动刷新 iframe 预览，状态灯绿色
- **Desktop** 模式：全宽预览
- **Mobile** 模式：375×667 手机尺寸预览
- **Source 按钮**：切换到源码查看模式

### 查看源代码

点击 `< > Source` 按钮进入源码查看：

- 左侧文件树展示所有生成的文件
- 右侧代码区带语法高亮
- 点击文件名切换查看

### 部署应用

Agent 生成应用后，点击 **🚀 Deploy** 按钮：

1. 后端自动将项目文件打包上传到 Netlify
2. 部署成功后底部显示线上 URL
3. 点击 📋 一键复制链接

> 前提：后端需配置 `NETLIFY_TOKEN` 环境变量，详见 [DEPLOY_APP.md](DEPLOY_APP.md)。

---

## 4 个核心 Agent

| Agent | 角色 | 工具 | 职责 |
|-------|------|------|------|
| **Mike** | Team Lead | ❌ | 分析需求，生成结构化任务计划（JSON），决定执行模式 |
| **Emma** | Product Manager | ❌ | 基于分析生成 PRD（目标、用户故事、功能列表、UI 需求） |
| **Bob** | Software Architect | ❌ | 设计技术架构（技术栈、目录结构、数据模型、组件树） |
| **Alex** | Senior Engineer | ✅ (4 tools) | 编写代码文件，执行 Shell 命令，输出可运行应用 |

---

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

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI + Uvicorn | 异步 Web 框架 |
| LLM 集成 | LiteLLM | 统一多模型调用接口 |
| 数据库 | SQLite + aiosqlite | 项目元数据 + 用户数据持久化 |
| 前端框架 | React 19 + TypeScript | 组件化 UI |
| 构建工具 | Vite | 快速开发与构建 |
| 样式 | Tailwind CSS | 原子化 CSS |
| 状态管理 | Zustand | 轻量状态管理 |
| 认证 | JWT (python-jose) + bcrypt | 密码哈希 + Token 鉴权 |

---

## 配置参考

完整 `.env` 配置项：

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | 🔑 LLM API 密钥 | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 默认模型（Engineer/Team 模式） | `deepseek-v4-flash` |
| `LLM_RACE_MODELS` | Race 模式额外模型（逗号分隔） | `deepseek-v3,deepseek-chat` |
| `JWT_SECRET` | 🔑 JWT 签名密钥 | `随机字符串` |
| `JWT_ALGORITHM` | JWT 加密算法 | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token 过期时间（分钟） | `1440` |
| `NETLIFY_TOKEN` | Netlify 部署 Token（可选） | `nfp_xxx` |
| `HOST` | 服务监听地址 | `0.0.0.0` |
| `PORT` | 服务端口 | `8000` |

> 详细说明见 [backend/.env.example](backend/.env.example)。

---

## API 接口

### 认证

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 注册新用户 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户信息（需 Token） |

### 对话

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | SSE 流式对话（需 Token） |

### 项目

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET | 获取项目列表（需 Token） |
| `/api/projects` | POST | 创建新项目（需 Token） |
| `/api/projects/{id}` | DELETE | 删除项目（需 Token） |
| `/api/projects/{id}/files` | GET | 获取项目源码文件（需 Token） |
| `/api/projects/{id}/deploy` | POST | 一键部署到 Netlify（需 Token） |

### Race

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/race/{race_id}/results` | GET | 获取 Race 结果（需 Token） |
| `/api/race/{race_id}/select` | POST | 选择 Race 最佳结果（需 Token） |

---

## 部署

### 平台部署

- **后端**：Render（Free 计划，750 小时/月）
- **前端**：Netlify（Free 计划，100GB 带宽/月）

详见 [DEPLOY.md](DEPLOY.md)。

### 应用部署

生成的应用可一键部署到 Netlify，详见 [DEPLOY_APP.md](DEPLOY_APP.md)。

---

## 项目结构

```
atoms_demo/
├── backend/
│   ├── agents/          # 4 个 Agent 实现
│   ├── api/             # FastAPI 路由
│   ├── orchestrator/    # 编排器（ReAct 循环 + 3 种模式）
│   ├── deploy.py        # Netlify 部署逻辑
│   ├── config.py        # 配置管理
│   ├── db.py            # SQLite 数据库
│   ├── llm.py           # LiteLLM 客户端
│   ├── auth.py          # JWT 认证
│   ├── sse.py           # SSE 事件协议
│   ├── tools.py         # Agent 工具集
│   ├── main.py          # 应用入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/         # SSE 客户端 + API 请求
│   │   ├── components/  # UI 组件
│   │   ├── store/       # Zustand 状态管理
│   │   └── App.tsx      # 根组件
│   └── package.json
├── data/                # 运行期生成（SQLite + 项目代码）
├── AGENTS.md            # Agent 系统文档
├── DEPLOY.md            # 平台部署指南
├── DEPLOY_APP.md        # 应用部署指南
├── netlify.toml         # Netlify 配置
├── render.yaml          # Render Blueprint 配置
└── README.md
```