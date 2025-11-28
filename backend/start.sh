#!/bin/bash
set -e

echo "Starting DropRadar Backend..."

# 获取端口（Railway 会设置 PORT 环境变量）
PORT=${PORT:-8000}

echo "Starting server on 0.0.0.0:$PORT"

# 启动 uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
