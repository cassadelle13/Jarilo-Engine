from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import logging

router = APIRouter(prefix="/api/v1", tags=["workflow"])
logger = logging.getLogger(__name__)
security = HTTPBearer()

# Тестовый токен для разработки (должен быть удален в продакшене)
TEST_API_KEY = "test-token-123"

class WorkflowRequest(BaseModel):
    prompt: str

@router.post("/workflows/generate")
async def generate_workflow(
    request: WorkflowRequest = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Генерирует workflow на основе текстового промта
    """
    try:
        # Временная проверка тестового токена
        if credentials.credentials != TEST_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
            
        if len(request.prompt) < 10:
            raise HTTPException(status_code=400, detail="Prompt too short")
            
        # Базовая реализация генерации workflow
        workflow = {
            "nodes": [
                {"id": "1", "type": "input", "data": {"label": request.prompt[:30]}},
                {"id": "2", "type": "process", "data": {"label": "Анализ"}},
                {"id": "3", "type": "output", "data": {"label": "Результат"}}
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3"}
            ]
        }
        
        if "анализ" in request.prompt.lower():
            workflow["nodes"][1]["data"]["label"] = "Детальный анализ"
        
        return {"status": "success", "workflow": workflow}
        
    except Exception as e:
        logger.error(f"Workflow generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
