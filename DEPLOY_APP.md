# 部署由 Atoms MVP 创建的应用

Atoms MVP 生成的应用可以通过 **🚀 Deploy** 按钮一键部署到 Netlify，获得公开访问的线上 URL。

---

## 前提条件

Atoms MVP 平台后端已配置 `NETLIFY_TOKEN` 环境变量。

### 获取 Netlify Token

1. 打开 [Netlify Personal Access Tokens](https://app.netlify.com/user/applications/personal)
2. 点击 **New access token**，名称填 `atoms-mvp`
3. 点击 **Generate token**
4. 复制生成的 Token（格式：`nfp_xxx...`）
5. 填入 Render 的环境变量 `NETLIFY_TOKEN`

> 本地开发时，在 `.env` 中添加 `NETLIFY_TOKEN=nfp_xxx...`

---

## 使用方式

1. Agent 生成应用后，右侧预览区工具栏出现 **🚀 Deploy** 按钮
2. 点击 Deploy → 后端自动将项目文件上传到 Netlify
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
                                            │ 调用 Netlify API
                                            ▼
                                       Netlify API
                                       (创建站点 + 部署)
                                            │
                                            ▼
                                       返回线上 URL
```

- 后端从 `data/projects/{id}/` 读取所有文件并打包为 zip
- 部署时自动注入 `netlify.toml` 确保 HTML/CSS/JS 文件的 Content-Type 正确
- 通过 Netlify REST API 创建站点并上传部署
- 返回 `https://{project-name}.netlify.app` 格式的 URL