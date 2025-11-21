import logging
from app.services.session import SessionManager
from app.services.huggy_api import HuggyClient

logger = logging.getLogger(__name__)

class ClosedChatService:
    """
    Service Orchestrator: Executa ações quando ocorre o evento 'closedChat'.
    """
    def __init__(self):
        self.session = SessionManager()
        self.huggy = HuggyClient()
    
    def handle(self, chat_id: int):
        """
        Executa o pipeline de fechamento do chat.
        """
        if not chat_id:
            logger.error("❌ [ClosedChatService] Tentativa de processar fechamento sem Chat ID.")
            return
        
        logger.info(f"📉 [ClosedChatService] Iniciando rotina para Chat ID: {chat_id}")

        self.session.clear_session(chat_id)

        success = self.huggy.remove_from_workflow(chat_id)

        if success:
            logger.info(f"✅ [ClosedChatService] Rotina finalizada com sucesso para Chat {chat_id}.")
        else:
            logger.warning(f"⚠️ [ClosedChatService] Rotina finalizada, mas API Huggy retornou erro/falha.")
