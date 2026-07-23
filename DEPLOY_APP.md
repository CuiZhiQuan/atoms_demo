# 部署由 Atoms MVP 创建的应用

Atoms MVP 生成的应用可以通过 **🚀 Deploy** 按钮一键部署到 Vercel，获得公开访问的线上 URL。

---

## 前提条件

Atoms MVP 平台后端已配置 `VERCEL_TOKEN` 环境变量。

### 获取 Vercel Token

1. 打开 [Vercel Tokens](https://vercel.com/account/tokens)
2. 点击 **Create Token**，名称填 `atoms-mvp`
3. Scope 选择 **Full Account**
4. 复制生成的 Token（格式：`vc_xxx...`）
5. 填入 Render 的环境变量 `VERCEL_TOKEN`

> 本地开发时，在 `.env` 中添加 `VERCEL_TOKEN=vc_xxx...`

---

## 使用方式

1. Agent 生成应用后，右侧预览区工具栏出现 **🚀 Deploy** 按钮
2. 点击 Deploy → 后端自动将项目文件上传到 Vercel
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
                                            │ base64 编码
                                            │ 调用 Vercel API
                                            ▼
                                       Vercel API
                                       (创建部署)
                                            │
                                            ▼
                                       返回线上 URL
```

- 后端从 `data/projects/{id}/` 读取所有文件
- 通过 Vercel REST API 直接上传文件并创建部署
- 返回 `https://{project-name}.vercel.app` 格式的 URL