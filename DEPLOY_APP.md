# 部署由 Atoms MVP 创建的应用

Atoms MVP 生成的应用可以通过 **🚀 Deploy** 按钮一键部署到 Cloudflare Pages，获得公开访问的线上 URL。

---

## 前提条件

Atoms MVP 平台后端已配置以下环境变量：

| 变量名 | 说明 |
|--------|------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账号 ID |

### 获取 Cloudflare API Token

1. 打开 [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. 点击 **创建令牌** → 使用模板：**Cloudflare Pages**
3. 权限设置：
   - 账户资源：选择你的 Cloudflare 账户
   - 权限：`Cloudflare Pages — Edit`
4. 点击 **继续** → **创建令牌**
5. 复制生成的 Token

### 获取 Cloudflare Account ID

1. 打开 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 选择你的账户
3. 在右侧栏找到 **Account ID**，点击复制

### 配置环境变量

将以上两个值填入 Render 的环境变量：

- `CLOUDFLARE_API_TOKEN` = 你的 API Token
- `CLOUDFLARE_ACCOUNT_ID` = 你的 Account ID

> 本地开发时，在 `.env` 中添加这两个变量即可。

---

## 使用方式

1. Agent 生成应用后，右侧预览区工具栏出现 **🚀 Deploy** 按钮
2. 点击 Deploy → 后端自动将项目文件打包上传到 Cloudflare Pages
3. 部署成功后底部显示线上 URL，点击即可访问
4. 点击 📋 按钮一键复制 URL

---

## 工作原理

```
用户点击 🚀 Deploy
       │
       ▼
前端 ──POST /api/projects/{id}/deploy──▶ 后端 (Render)
                                            │
                                            │ 读取项目文件
                                            │ 打包为 zip
                                            │ 调用 Cloudflare Pages API
                                            ▼
                                       Cloudflare Pages API
                                       (创建项目 + 部署)
                                            │
                                            ▼
                                       返回线上 URL
                                       https://{name}.pages.dev
```

- 后端从 `data/projects/{id}/` 读取所有文件并打包为 zip
- 部署时自动注入 `_headers` 确保 HTML/CSS/JS 文件的 Content-Type 正确
- 通过 Cloudflare REST API 创建 Pages 项目并上传部署
- 返回 `https://{project-name}.pages.dev` 格式的 URL