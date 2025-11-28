# DropRadar

**High Value Expired Domain & Traffic Interception Radar**

DropRadar 是一个自动化的数字资产套利工具，帮助 SEO 从业者、流量黑客发现高权重的过期域名，并预测性注册潜在的爆款域名。

## 核心功能

- **自动扫货**: 监控域名掉落列表
- **价值清洗**: 自动调用 SEO 接口过滤垃圾域名  
- **毫秒级通知**: 通过 Bark 推送高价值目标
- **预测性挖掘**: 基于热门科技词汇生成潜在域名组合

## 技术栈

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + Shadcn/ui
- **Backend**: FastAPI + SQLAlchemy + Celery
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Deployment**: Docker Compose

## 快速启动

### 前置要求

- Docker & Docker Compose
- Node.js 18+ (本地开发)
- Python 3.10+ (本地开发)

### 一键运行

```bash
docker-compose up --build
```

访问:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 项目结构

```
dropradar/
├── docker-compose.yml
├── backend/           # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   └── Dockerfile
└── frontend/          # Next.js
    ├── src/
    └── Dockerfile
```

## 开发路线图

- [x] Phase 1: 基础设施搭建
- [ ] Phase 2: 核心扫描逻辑
- [ ] Phase 3: 通知模块
- [ ] Phase 4: 前端交互
- [ ] Phase 5: 部署优化

## License

MIT
