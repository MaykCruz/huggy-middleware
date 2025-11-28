import redis
import os
import logging
import json

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        redis_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        self.expire_time = 3600 * 24 # 24 horas

    def _get_key_state(self, chat_id: str):
        return f"chat:{chat_id}:state"
    
    def _get_key_context(self, chat_id: str):
        return f"chat:{chat_id}:context"
    
    def clear_session(self, chat_id: int):
        """
        Remove todo o contexto do chat do Redis.
        Usado quando recebemos 'closedChat'.
        """
        try:
            # CORREÇÃO 1: Deletar State E Contexto
            key_state = self._get_key_state(chat_id)
            key_context = self._get_key_context(chat_id)

            # Deleta as duas chaves
            self.redis_client.delete(key_state)
            deleted_count = self.redis_client.delete(key_context)

            if deleted_count > 0:
                logger.info(f"🧹 [Session] Sessão limpa para o Chat ID: {chat_id}")
            else:
                logger.debug(f"💨 [Session] Nenhuma sessão ativa encontrada para Chat ID: {chat_id}. Ignorando.")
        except Exception as e:
            logger.error(f"❌ Erro ao limpar sessão do chat {chat_id}: {str(e)}")

    def get_state(self, chat_id: int):
        # CORREÇÃO 2: Usar _get_key_state
        key = self._get_key_state(chat_id)
        val = self.redis_client.get(key)
        # IMPORTANTE: Decodificar de bytes para string para o 'if' do bot funcionar
        return val.decode("utf-8") if val else "START"
    
    def set_state(self, chat_id: int, state: str):
        # CORREÇÃO 3: Usar _get_key_state
        key = self._get_key_state(chat_id)
        self.redis_client.set(key, state, ex=self.expire_time)
    
    def set_context(self, chat_id: int, data: dict):
        """Salva dados temporários (ex: CPF)"""
        key = self._get_key_context(chat_id)
        self.redis_client.set(key, json.dumps(data), ex=self.expire_time)
    
    def get_context(self, chat_id: int) -> dict:
        """Recupera dados salvos"""
        key = self._get_key_context(chat_id)
        val = self.redis_client.get(key)
        return json.loads(val) if val else {}