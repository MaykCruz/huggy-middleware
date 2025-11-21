import redis
import os
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        redis_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        self.expire_time = 3600 * 24 # 24 horas

    def _get_key(self, chat_id: str):
        return f"chat:{chat_id}:state"
    
    def clear_session(self, chat_id: int):
        """
        Remove todo o contexto do chat do Redis.
        Usado quando recebemos 'closedChat'.
        """
        try:
            key = self._get_key(chat_id)

            deleted_count = self.redis_client.delete(key)

            if deleted_count > 0:
                logger.info(f"🧹 [Session] Sessão limpa para o Chat ID: {chat_id}")
            else:
                logger.debug(f"💨 [Session] Nenhuma sessão ativa encontrada para Chat ID: {chat_id}. Ignorando.")
        except Exception as e:
            logger.error(f"❌ Erro ao limpar sessão do chat {chat_id}: {str(e)}")

    def get_state(self, chat_id: int):
        key = self._get_key(chat_id)
        return self.redis_client.get(key) or b"START"
    
    def set_state(self, chat_id: int, state: str):
        key = self._get_key(chat_id)
        self.redis_client.set(key, state, ex=self.expire_time)
    
