import json
import os
import logging

logger = logging.getLogger(__name__)

class MessageLoader:
    _messages = {}
    _loaded = False

    @classmethod
    def load(cls):
        if cls._loaded:
            return
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'messages.json')

        try:
            with open(json_path, encoding='utf-8') as f:
                cls._messages = json.load(f)
                cls._loaded = True
                logger.info("📄 [MessageLoader] Mensagens carregadas com sucesso.")
        except Exception as e:
            logger.error(f"❌ [MessageLoader] Erro crítico ao carregar messages.json: {e}")
            cls._messages = {}
    
    @classmethod
    def get(cls, key: str) -> dict:
        if not cls._loaded:
            cls.load()
        return cls._messages.get(key, {})