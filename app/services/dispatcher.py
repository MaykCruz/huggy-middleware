import logging

logger = logging.getLogger(__name__)

class EventDispatcher:
    """
    Responsável por analisar o tipo de evento recebido da Huggy
    e direcionar para o Service correto (Use Case).
    """

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
            logger.info(f"🔒 Detectado fechamento de chat. ID: {event_data.get('id', {})}")
            
        elif event_type == "receivedAllMessage":
            logger.info(f"💬 Detectada nova mensagem. Cliente: {event_data.get('chat', {}).get('id')}")
    
        else:
            logger.info(f"💤 Evento '{event_type}' não mapeado para ação. Ignorando.")
    