# 部署 Atoms MVP 平台

将 Atoms MVP 平台本身部署到线上，采用 **Cloudflare Pages（前端） + Render（后端）**，零成本上线。

---

## 架构

```
用户 → Cloudflare Pages (前端) → Render (后端 API)
       ├─ 自动 HTTPS              ├─ Python FastAPI
       ├─ 全球 CDN                 ├─ SQLite 数据
       └─ 免费额度（无限带宽）      └─ 免费额度 750h/月
```

---

## 第一步：部署后端到 Render

### 方式 A：render.yaml 一键部署（推荐）

1. 将代码推送到 GitHub
2. 打开 [Render Dashboard](https://dashboard.render.com/)
3. 点击 **New** → **Blueprint**
4. 连接你的 GitHub 仓库
5. Render 自动检测 `render.yaml`，创建 Web Service
6. 在 Environment 标签页填写环境变量（见下方）

### 方式 B：手动创建

1. 打开 [Render Dashboard](https://dashboard.render.com/)
2. 点击 **New** → **Web Service**
3. 连接 GitHub 仓库，配置：

| 配置项 | 值 |
|--------|-----|
| Runtime | Python 3 |
| Build Command | `pip install -r backend/requirements.txt` |
| Start Command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free |

## 环境变量（Render 端）

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_API_KEY` | 🔑 LLM API 密钥 | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 默认模型 | `deepseek-v4-flash` |
| `LLM_RACE_MODELS` | Race 模式额外模型（逗号分隔） | `deepseek-v3,deepseek-chat` |
| `JWT_SECRET` | 🔑 JWT 签名密钥（随机字符串） | `a1b2c3d4e5f6...` |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token（用于部署生成的应用） | 见下方说明 |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account ID | 见下方说明 |

> `CLOUDFLARE_API_TOKEN` 和 `CLOUDFLARE_ACCOUNT_ID` 用于一键部署生成的应用到 Cloudflare Pages，不填则前端 Deploy 按钮会报错。获取方式见 [DEPLOY_APP.md](DEPLOY_APP.md)。

> 部署成功后 Render 会分配一个 URL，如 `https://atoms-mvp-backend.onrender.com`，记下来用于下一步。

---

## 第二步：部署前端到 Cloudflare Pages

### 1. 获取 API Token 和 Account ID

- **API Token**：打开 [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens) → 创建 Token → 模板选 "Cloudflare Pages" → 复制 Token
- **Account ID**：打开 [Cloudflare Dashboard](https://dash.cloudflare.com/) → 选择你的账号 → 右侧栏复制 Account ID

### 2. 部署到 Cloudflare Pages

1. 打开 [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Pages**
2. 点击 **创建项目** → **连接到 Git**
3. 授权并选择 GitHub 仓库 `CuiZhiQuan/atoms_demo`
4. 配置构建：

| 配置项 | 值 |
|--------|-----|
| Framework preset | Vite（或 React） |
| Build command | `npm run build` |
| Build output directory | `frontend/dist` |
| Root directory | `frontend` |

5. 展开 **环境变量**，添加：

| 变量名 | 值 |
|--------|-----|
| `VITE_API_URL` | `https://atoms-mvp-backend.onrender.com` |

> ⚠️ 替换为你的 Render 后端实际地址。

6. 点击 **保存并部署**

> Cloudflare Pages 免费额度：无限带宽，每月 500 次构建。

---

## 第三步：验证

1. 打开 Cloudflare Pages 分配的 URL（如 `https://atoms-mvp.pages.dev`）
2. 注册账号 → 输入需求 → 确认 Agent 正常工作

> **注意**：Render 免费版 15 分钟无请求会休眠，首次访问可能有 30 秒冷启动延迟。

---

## 本地开发

```bash
# 终端 1：后端
python3 -m uvicorn backend.main:app --port 8000 --reload

# 终端 2：前端
cd frontend && npm run dev
```

访问 `http://localhost:5173`。