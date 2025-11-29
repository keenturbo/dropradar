from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, Base, engine
from app.api.v1 import endpoints

app = FastAPI(title="DropRadar", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库 - 重建表（删除旧表+创建新表）
Base.metadata.drop_all(bind=engine)
init_db()

# 路由
app.include_router(endpoints.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "DropRadar API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)