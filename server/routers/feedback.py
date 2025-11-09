from fastapi import APIRouter
<<<<<<< HEAD
from models.schemas import FeedbackRequest, FeedbackResponse
from services.chat_service import process_feedback
from utils.performance import measure_performance
=======
from server.models.schemas import FeedbackRequest, FeedbackResponse
from server.services.chat_service import process_feedback
from server.utils.performance import measure_performance
>>>>>>> 6a74cbb (解决模块冲突问题)

# 创建路由器
router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
@measure_performance("feedback")
async def feedback(request: FeedbackRequest):
    """
    处理用户对回答的反馈
    """
    try:
        result = await process_feedback(request)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
