from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="process_webhook_event")
def process_webhook_event(payload: dict):
    """
    Task assíncrona que processará o evento.
    Pro enquanto, apenas imprime o log do worker.
    """
    event_type = payload.get("messages", {}).get("type", "unknown")
    logger.info(f"⚡ [Worker] Recebido evento do tipo: {event_type}")
    logger.info(f"📦 Payload completo: {payload}")

    return f"Processed event: {event_type}"