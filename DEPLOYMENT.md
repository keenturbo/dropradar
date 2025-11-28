# DropRadar 部署指南

## 🚀 Railway 一键部署后端

### 前置要求
- Railway 账号（使用 GitHub 登录）
- 已连接 GitHub 仓库

### 部署步骤

#### 1. 登录 Railway

访问 [railway.app](https://railway.app)，使用 GitHub 登录。

#### 2. 创建新项目

```bash
railway login
```

或者直接在网页操作：

1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择 `keenturbo/dropradar`
4. Railway 会自动检测到 Dockerfile

#### 3. 配置服务

Railway 需要创建 **两个服务**：

**服务 1: PostgreSQL 数据库**
1. 在项目中点击 "+ New"
2. 选择 "Database" → "PostgreSQL"
3. Railway 会自动创建数据库并提供连接信息

**服务 2: FastAPI 后端**
1. 在项目中点击 "+ New"
2. 选择 "GitHub Repo" → `dropradar`
3. 设置 **Root Directory** 为 `backend/`
4. 配置环境变量（见下方）

#### 4. 设置环境变量

在 FastAPI 服务中添加以下环境变量：

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
BARK_KEY=your_bark_key_here
CORS_ORIGINS=*
```

**重要说明：**
- `${{Postgres.DATABASE_URL}}` 会自动引用 PostgreSQL 服务的连接字符串
- `BARK_KEY` 需要填入你的 Bark 推送 Key（可选，测试时可留空）

#### 5. 部署

点击 "Deploy"，Railway 会自动：
1. 构建 Docker 镜像
2. 运行容器
3. 分配公开 URL（如 `https://dropradar-api.railway.app`）

#### 6. 验证部署

访问生成的 URL：

```bash
https://your-service.railway.app/
```

应该看到：
```json
{
  "message": "DropRadar API is running",
  "version": "1.0.0",
  "docs": "/docs"
}
```

访问 API 文档：
```
https://your-service.railway.app/docs
```

---

## 🔧 Railway CLI 部署（高级）

如果喜欢命令行操作：

### 安装 Railway CLI

```bash
npm i -g @railway/cli
```

### 登录

```bash
railway login
```

### 初始化项目

```bash
cd backend
railway init
```

### 链接数据库

```bash
railway add --database postgres
```

### 部署

```bash
railway up
```

### 查看日志

```bash
railway logs
```

### 获取公开 URL

```bash
railway domain
```

---

## 🐳 本地 Docker 测试（可选）

在部署到 Railway 之前，可以本地测试：

### 启动完整堆栈

```bash
docker-compose up --build
```

访问：
- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 仅启动后端

```bash
docker-compose up backend postgres
```

---

## 📡 连接前端到后端

部署完成后，复制 Railway 提供的后端 URL（例如 `https://dropradar-api.railway.app`）。

在前端仓库中，需要更新 API 地址：

1. 在 Vercel 环境变量中添加：
   ```
   NEXT_PUBLIC_API_URL=https://dropradar-api.railway.app
   ```

2. 或者直接修改前端代码中的 API 地址。

---

## 🔍 故障排查

### 数据库连接失败
检查环境变量 `DATABASE_URL` 是否正确引用了 Postgres 服务。

### CORS 错误
确保后端 `CORS_ORIGINS` 包含前端域名（或设为 `*` 允许所有来源）。

### 502 Bad Gateway
后端可能崩溃，检查 Railway 日志：
```bash
railway logs
```

### 依赖安装失败
检查 `requirements.txt` 是否包含所有依赖。

---

## 💡 成本估算

**Railway 免费额度：**
- $5 免费试用额度
- 每月 500 小时执行时间
- 适合个人项目和 MVP

**升级后：**
- 按使用量计费（约 $5-20/月）
- 支持自定义域名
- 更高性能

---

## 📚 下一步

1. ✅ 部署后端到 Railway
2. ✅ 获取 API URL
3. ✅ 更新前端环境变量
4. ✅ 在 Vercel 前端测试 "Start Scan" 功能
5. ⬜ 添加 Celery 定时任务（可选）
6. ⬜ 集成真实 SEO API（付费升级）

---

## 🆘 获取帮助

- [Railway 文档](https://docs.railway.app/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [项目 GitHub Issues](https://github.com/keenturbo/dropradar/issues)
