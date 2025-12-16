FROM python:3.10-slim

# 安裝必要套件
RUN apt-get update && apt-get install -y gcc

WORKDIR /app

# 複製檔案
COPY . /app

# 安裝 requirements
RUN pip install --no-cache-dir -r requirements.txt

# 容器預設不指定 CMD，讓 Cloud Run / Cloud Run Job 自己決定