# 使用官方 Python 3.12  slim 镜像作为基础
# slim 版本去掉了非必要组件，体积更小，适合生产部署
FROM python:3.12-slim

# 设置工作目录为 /app
# 后续所有操作（COPY、RUN）都基于此目录
WORKDIR /app

# 先单独复制 requirements.txt，利用 Docker 缓存层机制
# 如果依赖没有变化，后续构建无需重复安装，大幅加速
COPY requirements.txt .

# 安装依赖，不缓存 pip 下载文件，减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个后端代码到镜像中
COPY app/ ./app/

# 暴露 FastAPI 默认端口
EXPOSE 8000

# 容器启动时运行 Uvicorn
# --host 0.0.0.0 允许外部访问；--port 8000 绑定端口
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
