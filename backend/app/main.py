# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.routes import router as api_router
from app.mcp.server import mcp_router
from app.memory.redis_client import redis_client
from app.memory.postgres_client import postgres_client
from app.rag.embeddings import embedding_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器：启动时初始化数据库与向量库，关闭时释放资源。"""
    print("[startup] Smart API Assistant started")
    await postgres_client.connect()
    await postgres_client.init_tables()
    # 触发 VectorStore 连接，确保 Chroma 就绪
    from app.rag.vector_store import vector_store
    vector_store._ensure_connected()
    yield
    await redis_client.close()
    await embedding_client.close()
    await postgres_client.close()
    print("[shutdown] Resources released")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一捕获 HTTPException，映射为项目标准错误响应格式。"""
    code_map = {404: 40401, 500: 50000}
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code_map.get(exc.status_code, 50000), "data": None, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一捕获请求参数校验失败，返回 40003 错误码。"""
    return JSONResponse(
        status_code=400,
        content={"code": 40003, "data": None, "message": "请求参数校验失败"},
    )


app.include_router(api_router)
app.include_router(mcp_router)


@app.get("/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "ok", "version": settings.APP_VERSION}
