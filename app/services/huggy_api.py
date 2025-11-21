import httpx
import os
import logging
from typing import Union

logger = logging.getLogger(__name__)

class HuggyClient:

    API_VALUE_EXIT_WORKFLOW = ""

    def __init__(self):
        self.api_token = os.getenv("HUGGY_API_TOKEN")
        self.base_url = "https://api.huggy.app/v3/companies/351946"

        self.steps = {
            "AG_FORMALIZAR": os.getenv("HUGGY_WORKFLOW_STEP_AG_FORMALIZAR"),
        }
        
        if not self.api_token:
            logger.warning("⚠️ HUGGY_API_TOKEN não configurado. As chamadas à API falharão.")

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def update_workflow_step(self, chat_id: int, step_id: Union[int, str]) -> bool:
        """
        Método GENÉRICO (Base).
        Executa a chamada HTTP pura.
        """
        url = f"{self.base_url}/chats/{chat_id}/workflow"
        payload = {"stepId": step_id}

        if step_id == self.API_VALUE_EXIT_WORKFLOW:
            action_name = "REMOVER do workflow"
        else:
            friendly_name = next((k for k, v in self.steps.items() if v == str(step_id)), str(step_id))
            action_name = f"mover para etapa {friendly_name}"
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.put(url, headers=self._get_headers(), json=payload)

                if response.status_code == 200:
                    logger.info(f"✅ [Huggy] Sucesso ao {action_name} (Chat {chat_id}).")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"⚠️ [Huggy] Chat {chat_id} não encontrado (404).")
                else:
                    logger.error(f"❌ [Huggy] Falha ao {action_name}: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Erro de conexão Huggy: {str(e)}")
            return False
    
    def remove_from_workflow(self, chat_id: int) -> bool:
        """Ação: Retirar do workflow"""
        return self.update_workflow_step(chat_id, self.API_VALUE_EXIT_WORKFLOW)
    
    def move_to_ag_formalizar(self, chat_id: int) -> bool:
        """Ação: Mover para etapa Aguardando Formalizar"""
        step_id = self.steps.get("AG_FORMALIZAR")
        if not step_id:
            logger.warning(f"⚠️ Tentativa de mover Chat {chat_id} para AG_FORMALIZAR, mas variável de ambiente não está configurada.")
            return False
        return self.update_workflow_step(chat_id, step_id)