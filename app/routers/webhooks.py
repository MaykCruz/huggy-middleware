from fastapi import APIRouter, HTTPException, Request
from app.tasks.processor import process_webhook_event
import logging

router = APIRouter()
logger = logging.getLogger("uvicorn")

@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Recebe o payload da Huggy e enfileira para processamento assíncrono.
    """
    try:
        payload = await request.json()

        task = process_webhook_event.delay(payload)

        logger.info(f"📨 [API] Webhook recebido e enfileirado. Task ID: {task.id}")

        return {
            "status": "received",
            "task_id": task.id,
            "message": "Event queued for background processing."
        }
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")