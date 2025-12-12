import os
import base64
import httpx
import logging
import time
from app.infrastructure.token_manager import TokenManager

logger = logging.getLogger(__name__)

class FactaAuth:
    def __init__(self):
        self.base_url = os.getenv("FACTA_API_URL", "https://webservice-homol.facta.com.br")
        self.user = os.getenv("FACTA_USER")
        self.password = os.getenv("FACTA_PASSWORD")

        self.token_manager = TokenManager()

        self.SCOPE = "FACTA"

    def get_valid_token(self) -> str:
        """
        Retorna um token Bearer válido.
        Usa estratégia de Cache-First com Lock Distribuido para renovação.
        """
        token = self.token_manager.get_token(self.SCOPE)
        if token:
            return token
        
        if self.token_manager.acquire_lock(self.SCOPE):
            try:
               logger.info("🔑 [FACTA] Iniciando renovação de token na API...")
               new_token = self._request_api_token()

               self.token_manager.save_token(self.SCOPE, new_token, 3500)

               return new_token
            except Exception as e:
                self.token_manager.release_lock(self.SCOPE)
                logger.error(f"❌ [FACTA] Falha crítica na renovação: {str(e)}")
                raise e
        
        else:
            logger.info("⏳ [FACTA] Aguardando renovação por outro worker...")
            time.sleep(2)
            return self.get_valid_token()
        
    def _request_api_token(self) -> str:
        """
        Executa a chamada HTTP crua para /gera-token.
        Autenticação: Basic Auth (Base64)
        """
        url = f"{self.base_url}/gera-token"

        if not self.user or not self.password:
            raise ValueError("Credenciais FACTA_USER ou FACTA_PASSWORD não configuradas.")
        
        credentials = f"{self.user}:{self.password}"
        b64_creds = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_creds}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json" 
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                token = data.get("token")

                if not token:
                    raise ValueError("API retornou 200 mas sem campo 'token'.")
                
                return token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ [FACTA] Erro HTTP {e.response.status_code}: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"❌ [FACTA] Erro de Conexão: {str(e)}")
            raise e



