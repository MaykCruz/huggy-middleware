import logging
import os
from app.events.handlers import ClosedChatService, IncomingMessageService

logger = logging.getLogger(__name__)

class EventDispatcher:
    """
    Responsável por analisar o tipo de evento recebido da Huggy
    e direcionar para o Service correto (Use Case).
    """
    TARGET_DEPARTMENT_ID = os.getenv("HUGGY_FILTER_DEPARTMENT", "")
    TARGET_SITUATION = os.getenv("HUGGY_FILTER_SITUATION", "auto")
    TARGER_SENDER_TYPE = os.getenv("HUGGY_FILTER_SENDER_TYPE","whatsapp-enterprise")

    @staticmethod
    def _shoud_ignore(event_data: dict) -> bool:
        chat_info = event_data.get("chat", {})
        chat_id = chat_info.get("id", "unknown")

        if event_data.get("is_internal") is True or event_data.get("isInternal") is True:
            logger.debug(f"⛔ [Filter] Chat {chat_id}: Ignorada (Interna).")
            return True
        
        sender_type = event_data.get("senderType")
        if sender_type != EventDispatcher.TARGER_SENDER_TYPE:
            logger.debug(f"⛔ [Filter] Chat {chat_id}: Msg ignorada (Canal '{sender_type}').")
            return True
        
        raw_dept = chat_info.get("department")
        incoming_dept = str(raw_dept)

        if incoming_dept != EventDispatcher.TARGET_DEPARTMENT_ID:
            logger.debug(f"⛔ [Filter] Chat {chat_id}: Msg ignorada (Dept '{incoming_dept}' != '{EventDispatcher.TARGET_DEPARTMENT_ID}').")
            return True
        
        situation = chat_info.get("situation")
        if situation != EventDispatcher.TARGET_SITUATION:
            logger.debug(f"⛔ [Filter] Chat {chat_id}: Msg ignorada (Situação '{situation}' != '{EventDispatcher.TARGET_SITUATION}').")
            return True
        
        return False


    @staticmethod
    def dispatch(payload: dict):
        messages = payload.get("messages", {})
        if not messages:
            logger.warning("⚠️ Payload recebido sem bloco 'messages'. Ignorando.")
            return 
        
        event_type = next(iter(messages))
        logger.info(f"🔀 [Dispatcher] Roteando evento: {event_type}")


        content_list = messages.get(event_type, [])

        if not content_list or not isinstance(content_list, list):
            logger.warning(f"⚠️ Conteúdo de {event_type} vazio ou inválido.")
            return
        
        event_data = content_list[0]
        
        if event_type == "closedChat":
            chat_id = event_data.get("id", {})
            service = ClosedChatService()
            service.handle(chat_id)
            
        elif event_type == "receivedAllMessage":
            if EventDispatcher._shoud_ignore(event_data):
                return

            chat_id = event_data.get('chat', {}).get('id')
            logger.info(f"💬 [Dispatcher] Mensagem APROVADA para Chat ID: {chat_id}")

            service = IncomingMessageService()
            service.handle(event_data)
    
        else:
            logger.info(f"💤 Evento '{event_type}' não mapeado para ação. Ignorando.")
    