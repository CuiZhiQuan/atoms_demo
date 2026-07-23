# 部署 Atoms MVP 平台

将 Atoms MVP 平台本身部署到线上，采用 **Netlify（前端） + Render（后端）**，零成本上线。

---

## 架构

```
用户 → Netlify (前端) → Render (后端 API)
       ├─ 自动 HTTPS     ├─ Python FastAPI
       ├─ 全球 CDN        ├─ SQLite 数据
       └─ 免费额度        └─ 免费额度 750h/月
```

---

## 第一步：部署后端到 Render

### 方式 A：render.yaml 一键部署（推荐）

1. 将代码推送到 GitHub
2. 打开 [Render Dashboard](https://dashboard.render.com/)
3. 点击 **New** → **Blueprint**
4. 连接你的 GitHub 仓库
5. Render 自动检测 `render.yaml`，创建 Web Service
6. 在 Environment 标签页填写环境变量

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

### 环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_API_KEY` | 🔑 LLM API 密钥 | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 默认模型 | `deepseek-v4-flash` |
| `LLM_RACE_MODELS` | Race 模式模型（逗号分隔） | `deepseek-v4-flash,deepseek-v3` |
| `JWT_SECRET` | 🔑 JWT 签名密钥（随机字符串） | `a1b2c3d4e5f6...` |
| `NETLIFY_TOKEN` | Netlify 部署 Token（可选） | `nfp_xxx...` |

> `NETLIFY_TOKEN` 用于一键部署生成的应用到 Netlify，不填则 Deploy 按钮不可用。

> 部署成功后 Render 会分配一个 URL，如 `https://atoms-mvp-backend.onrender.com`，记下来用于下一步。

---

## 第二步：部署前端到 Netlify

1. 打开 [Netlify](https://netlify.com)，用 GitHub 登录
2. 点击 **Add new site** → **Import an existing project**
3. 授权并选择 GitHub 仓库 `CuiZhiQuan/atoms_demo`
4. 配置构建（`netlify.toml` 会自动填写，检查确认即可）：

| 配置项 | 值 |
|--------|-----|
| Base directory | `frontend` |
| Build command | `npm run build` |
| Publish directory | `dist` |

5. 展开 **Environment Variables**，添加：

| 变量名 | 值 |
|--------|-----|
| `VITE_API_URL` | `https://atoms-mvp-backend.onrender.com` |

> ⚠️ 替换为你的 Render 后端实际地址。

6. 点击 **Deploy site**

> Netlify 免费额度：100GB 带宽/月，300 分钟构建/月。

---

## 第三步：验证

1. 打开 Netlify 分配的 URL（如 `https://atoms-mvp.netlify.app`）
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