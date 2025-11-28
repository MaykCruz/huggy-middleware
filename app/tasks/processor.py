from app.celery_app import celery_app
from app.services.dispatcher import EventDispatcher
import logging
import httpx

logger = logging.getLogger(__name__)

@celery_app.task(
        name="process_webhook_event",
        bind=True,
        acks_late=True,
        autoretry_for=(httpx.HTTPError, ConnectionError, TimeoutError),
        retry_backoff=True,
        retry_backoff_max=60,
        max_retries=5
        )
def process_webhook_event(self, payload: dict):
    """
    Task puramente técnica.
    Recebe o payload bruto e entrega para a camada de serviço.
    """
    try:
        request_id = self.request.id
        retry_count = self.request.retries

        if retry_count > 0:
            logger.warning(f"🔄 [Task] Tentativa {retry_count + 1}/5 para Task {request_id}")

        EventDispatcher.dispatch(payload)
        return "Dispatched successfully"
    
    except Exception as e:
        # Se for um erro que definimos no autoretry_for, o Celery já cuidou.
        # Se for um erro de Lógica (Code Error), ele cai aqui e morre (não faz retry).
        logger.error(f"❌ Erro FATAL na task {self.request.id}: {str(e)}")
        # Não damos raise aqui para não gerar loop de retry em erros de código (ex: KeyError)
        # Em um sistema avançado, aqui enviaríamos para uma Dead Letter Queue.
        return f"Failed: {str(e)}"