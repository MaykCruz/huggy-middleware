from app.celery_app import celery_app
from app.services.dispatcher import EventDispatcher
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="process_webhook_event")
def process_webhook_event(payload: dict):
    """
    Task puramente técnica.
    Recebe o payload bruto e entrega para a camada de serviço.
    """
    try:
        logger.info("⚙️ [Task] Iniciando processamento via Dispatcher...")
        EventDispatcher.dispatch(payload)
        return "Dispatched successfully"
    except Exception as e:
        logger.error(f"❌ Erro no processamento da task: {str(e)}")
        raise e