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
    
class IncomingMessageService:
    """
    Service Orchestrator: Processa mensagens recebidas (que já passaram pelo filtro).
    Sua função é extrair os dados vitais e passar para o Motor de Decisão (Engine).
    """
    def __init__(self):
        from app.services.bot_engine import BotEngine
        self.engine = BotEngine()
    
    def handle(self, event_data: dict):
        """
        Recebe o pedaço 'message' do JSON da Huggy.
        """
        chat_id = event_data.get('chat', {}).get('id')
        message_text = event_data.get('body', '').strip()

        if not chat_id:
            logger.error("❌ [MessageService] Chat ID não encontrado no evento.")
            return
        
        logger.info(f"📨 [MessageService] Processando msg no Chat {chat_id}: '{message_text}'")

        self.engine.process(chat_id, message_text)