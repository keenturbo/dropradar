> ⚠️ **免责声明**：本项目仅供学习和研究使用。使用爬虫功能抓取第三方网站数据可能违反其服务条款（TOS），请自行承担相关风险。建议优先使用官方 API。

----


# 📡 DropRadar - 高价值过期域名监控雷达

> 24/7 自动监控过期域名，发现高 DA 域名立即 Bark 推送到你手机

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/keenturbo/dropradar)

---

## 🎯 项目简介

**DropRadar** 是一款为 SEO 从业者、流量黑客、域名投资者打造的智能工具。它能够：

- ✅ **自动扫描**：监控 ExpiredDomains.net 等平台的过期域名
- ✅ **智能过滤**：筛选出 DA > 20、外链丰富、垃圾评分低的高价值域名
- ✅ **即时推送**：通过 Bark 推送到 iPhone，第一时间抢注
- ✅ **预测挖掘**：基于热门关键词（如 GPT、Gemini）预测潜在域名

---

## 🏗️ 技术架构

```
┌─────────────────┐
│  Vercel (免费)   │  ← 前端 Next.js 14 + Tailwind CSS
│  dropradar.app  │
└────────┬────────┘
         │ API 调用
         ↓
┌─────────────────┐
│ Railway ($5/月) │  ← 后端 FastAPI + PostgreSQL
│  API + 数据库   │
└────────┬────────┘
         │ 爬虫/API
         ↓
┌─────────────────┐
│ ExpiredDomains  │  ← 数据源（需配置 Cookie）
│ + OpenPageRank  │
└─────────────────┘
```

**核心技术栈：**
- **前端**：Next.js 14 (App Router) + Shadcn/ui
- **后端**：Python 3.10 + FastAPI + Selenium
- **数据库**：PostgreSQL
- **部署**：Vercel (前端) + Railway (后端)

---

## 🚀 快速开始

### 前置要求
- GitHub 账号
- Vercel 账号（免费）
- Railway 账号（提供信用卡，$5/月）
- Bark App（iOS，用于接收推送）

---

### 第 1 步：部署后端到 Railway

#### 1.1 创建 PostgreSQL 数据库
1. 访问 [Railway Dashboard](https://railway.app/dashboard)
2. 点击 **New Project** → **Provision PostgreSQL**
3. 复制 **Internal Database URL**（格式：`postgresql://user:pass@host:5432/db`）

#### 1.2 部署 Backend 服务
1. 在 Railway 点击 **New Service** → **GitHub Repo**
2. 选择 `keenturbo/dropradar` 仓库
3. **Root Directory** 设为 `backend`
4. **Runtime** 选择 `Docker`

#### 1.3 配置环境变量
在 Railway Backend 服务的 **Variables** 标签添加：

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
OPENPAGERANK_API_KEY=w00wkkkwo4c4sws4swggkswk8oksggsccck0go84
EXPIREDDOMAINS_COOKIE=你的Cookie值（见下方说明）
BARK_KEY=你的Bark密钥
CORS_ORIGINS=*
```

**获取 EXPIREDDOMAINS_COOKIE：**
1. 浏览器访问 https://www.expireddomains.net/login/
2. 手动登录并完成邮箱验证码
3. 按 **F12** → **Application** → **Cookies** → `https://www.expireddomains.net`
4. 复制 `reme` 和 `ExpiredDomainssessid` 两个 Cookie
5. 格式化为：`reme=xxx; ExpiredDomainssessid=yyy`

#### 1.4 获取 Railway API URL
部署完成后，复制 Railway 提供的 URL，如：
```
https://dropradar-production.up.railway.app
```

---

### 第 2 步：部署前端到 Vercel

#### 2.1 导入仓库
1. 访问 [Vercel Dashboard](https://vercel.com/new)
2. 选择 **Import Git Repository** → `keenturbo/dropradar`
3. **Root Directory** 设为 `frontend`
4. **Framework Preset** 选择 `Next.js`

#### 2.2 配置环境变量
在 Vercel 项目设置的 **Environment Variables** 添加：

```bash
NEXT_PUBLIC_API_URL=https://dropradar-production.up.railway.app
```

（替换为你的 Railway Backend URL）

#### 2.3 部署
点击 **Deploy**，等待 2-3 分钟。

---

### 第 3 步：测试完整流程

#### 3.1 访问网站
打开 Vercel 提供的 URL，如：`https://dropradar-swart.vercel.app`

#### 3.2 触发扫描
点击右上角 **"Start Scan"** 按钮，查看 Railway 后端日志：

```
✅ Cookie 登录成功！
📊 正在获取域名列表...
✅ 找到域名: example.com (DA: 35, BL: 250)
```

#### 3.3 查看结果
扫描完成后，前端表格会自动刷新，显示新抓取的域名。

---

## 🔧 高级配置

### 启用 Bark 推送

1. 在 iPhone 上安装 [Bark App](https://apps.apple.com/cn/app/bark/id1403753865)
2. 打开 App，复制你的 Bark Key（格式：`xxx/yyy`）
3. 在 Railway 环境变量中设置：
   ```
   BARK_KEY=你的Bark密钥
   ```
4. 在前端扫描时，高价值域名（DA > 40）会自动推送到手机

### 切换数据源模式

在 `backend/app/api/v1/endpoints.py` 第 51 行，可修改默认模式：

```python
mode: str = 'expireddomains'  # 可选：'mock', 'domainsdb', 'expireddomains'
```

- `mock`：模拟数据（快速测试）
- `domainsdb`：DomainDB API（需积分）
- `expireddomains`：ExpiredDomains.net 爬虫（需 Cookie）

---

## 📋 功能特性

### 当前已实现
- ✅ Cookie 自动登录（绕过验证码）
- ✅ 真实域名抓取（Namecheap Auctions 列表）
- ✅ 前端实时展示（DA、外链、垃圾评分）
- ✅ 单个删除 / 清空所有
- ✅ 数据持久化（PostgreSQL）

### 开发中
- ⏳ Bark 推送（代码已写，需手动测试）
- ⏳ 定时自动扫描（Celery Beat）
- ⏳ 高价值过滤（切换到 `/domains/expireddomains/` 列表）

### 规划中
- 📅 预测性域名生成（The Prophet 模块）
- 📅 Wayback Machine 历史检查
- 📅 付费订阅功能

---

## 🐛 常见问题

### Q1：扫描后显示"扫描完成，发现 0 个新域名"
**原因**：Cookie 失效或数据源列表为空。

**解决**：
1. 检查 Railway 日志是否显示 `✅ Cookie 登录成功`
2. 如果显示 `❌ Cookie 已失效`，需重新获取 Cookie
3. 尝试切换到 `mock` 模式测试流程

### Q2：Railway 报错 "chromedriver not found"
**原因**：Dockerfile 构建失败。

**解决**：
1. 检查 `backend/Dockerfile` 是否包含 Chrome 安装步骤
2. 重新触发部署：`git commit --allow-empty -m "rebuild" && git push`

### Q3：前端显示"无法连接到后端 API"
**原因**：环境变量配置错误。

**解决**：
1. 确认 Vercel 的 `NEXT_PUBLIC_API_URL` 是否正确
2. 测试后端是否正常：`curl https://你的railway域名/`

---

## 🚨 重要提醒

1. **ExpiredDomains.net 账户风险**：
   - 该网站禁止使用爬虫，账户可能被封
   - 建议每次扫描间隔至少 10 分钟
   - 长期方案：切换到官方 API（如 GoDaddy、DropCatch）

2. **Railway 资源消耗**：
   - Selenium + Chrome 占用内存大，$5 额度约可用 15-20 天
   - 建议只在需要时手动扫描，不要设置定时任务

3. **数据隐私**：
   - 不要在 GitHub 仓库中提交 Cookie 或 API Key
   - 所有敏感信息通过环境变量管理

---

## 📚 项目结构

```
dropradar/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/endpoints.py  # API 路由
│   │   ├── models/domain.py     # 数据库模型
│   │   ├── services/
│   │   │   ├── scanner.py       # 域名扫描器（核心）
│   │   │   └── notification.py  # Bark 推送
│   │   └── main.py              # 应用入口
│   ├── Dockerfile               # 包含 Chrome 安装
│   └── requirements.txt
├── frontend/                   # Next.js 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # 主页（域名列表）
│   │   │   └── settings/        # 设置页
│   │   └── lib/api.ts           # API 客户端
│   └── package.json
└── docker-compose.yml          # 本地开发环境
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如果你有更好的数据源或优化建议，请不吝分享。

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [ExpiredDomains.net](https://www.expireddomains.net/) - 数据来源
- [OpenPageRank](https://www.domcop.com/openpagerank/) - 域名评分 API
- [Bark](https://github.com/Finb/Bark) - iOS 推送服务
- [Railway](https://railway.app/) - 后端托管平台
- [Vercel](https://vercel.com/) - 前端托管平台

---

## 📞 联系方式

- GitHub: [@keenturbo](https://github.com/keenturbo)
- 项目地址: https://github.com/keenturbo/dropradar
- 演示地址: https://dropradar-swart.vercel.app

**如果这个项目对你有帮助，请给个 ⭐️ Star！**

---
