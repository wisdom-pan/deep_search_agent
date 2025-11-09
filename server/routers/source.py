from typing import Dict
from fastapi import APIRouter, HTTPException
<<<<<<< HEAD
from models.schemas import SourceRequest, SourceResponse, SourceInfoResponse, SourceInfoBatchRequest, ContentBatchRequest
from services.kg_service import get_source_content, get_source_file_info
from utils.neo4j_batch import BatchProcessor
=======
from server.models.schemas import SourceRequest, SourceResponse, SourceInfoResponse, SourceInfoBatchRequest, ContentBatchRequest
from server.services.kg_service import get_source_content, get_source_file_info
from server.utils.neo4j_batch import BatchProcessor
>>>>>>> 6a74cbb (解决模块冲突问题)
from graphrag_agent.config.neo4jdb import get_db_manager

# 创建路由器
router = APIRouter()

# 获取单个问题的源文档
@router.post("/source", response_model=SourceResponse)
async def get_source(request: SourceRequest):
    """
    获取问题的源文档
    """
    try:
        sources = await get_source_content(request.query)
        return SourceResponse(sources=sources)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
