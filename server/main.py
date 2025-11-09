import uvicorn
from fastapi import FastAPI
from server.routers import api_router
from server.server_config.database import get_db_manager
from server.server_config.settings import UVICORN_CONFIG
from server.services.agent_service import agent_manager

# 初始化 FastAPI 应用
app = FastAPI(title="知识图谱问答系统", description="基于知识图谱的智能问答系统后端API")

# 添加路由
app.include_router(api_router)

# 获取数据库连接
db_manager = get_db_manager()
driver = db_manager.driver


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "Deep Search API is running"}


@app.on_event("shutdown")
def shutdown_event():
    """应用关闭时清理资源"""
    # 关闭所有Agent资源
    agent_manager.close_all()

    # 关闭Neo4j连接
    if driver:
        driver.close()
        print("已关闭Neo4j连接")


# 启动服务器
if __name__ == "__main__":
    uvicorn.run("main:app", **UVICORN_CONFIG)
