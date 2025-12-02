import os
import logging
from typing import Union, Dict, Any, Optional
from app.integrations.huggy.client import HuggyClient

logger = logging.getLogger(__name__)

class HuggyService:
    """
    Cama de Facade (Fachada) que combina métodos da API para realizar ações de negócio da Empreste Digital.
    """
    def __init__(self):

        self.client = HuggyClient()

        self.workflow_steps = {
            "WORKFLOW_STEP_AG_FORMALIZAR": os.getenv("HUGGY_WORKFLOW_STEP_AG_FORMALIZAR"),
        }

        self.flows = {
            "AUTO_DISTRIBUTION": os.getenv("HUGGY_FLOW_AUTO_DISTRIBUTION")
        }

        self.tabulations = {
            "LESS_SIX_MONTHS": os.getenv("HUGGY_TABULATION_LESS_SIX_MONTHS")
        }

    def send_message(self, chat_id: int, message_key: str, variables: Dict[str, Any] = None, file_url: Optional[str] = None, force_internal: bool = False) -> bool:
        return self.client.send_message(chat_id, message_key, variables=variables, file_url=file_url, force_internal=force_internal)

    def finish_attendance(self, chat_id: int, tabulation_id: Union[int, str], send_feedback: bool = False) -> bool:
        """
        Smart Wrapper: Tira do Workflow + Fecha com Tabulação.
        Uso Obrigatório: Deve-se passar o tabulation_id;
        """
        if not tabulation_id:
            logger.error(f"❌ Tentativa de fechar Chat {chat_id} sem Tabulação! Abortando para garantir integridade.")
            return False
        
        logger.info(f"📉 [SmartClose] Finalizando Chat {chat_id} com Tabulação {tabulation_id}...")

        self.remove_from_workflow(chat_id)

        return self.close_chat(chat_id, tabulation_id=tabulation_id, send_feedback=send_feedback)

    def remove_from_workflow(self, chat_id: int) -> bool:
        """Ação: Retirar do workflow"""
        return self.update_workflow_step(chat_id, self.API_VALUE_EXIT_WORKFLOW)
    
    def move_to_ag_formalizar(self, chat_id: int) -> bool:
        """Ação: Mover para etapa Aguardando Formalizar"""
        step_id = self.workflow_steps.get("WORKFLOW_STEP_AG_FORMALIZAR")
        if not step_id:
            logger.warning(f"⚠️ Tentativa de mover Chat {chat_id} para WORKFLOW_STEP_AG_FORMALIZAR, mas variável de ambiente não está configurada.")
            return False
        return self.update_workflow_step(chat_id, step_id)
    
    def start_auto_distribution(self, chat_id: int) -> bool:
        """
        Wrapper Semântico: Inicia o fluxo de autodistribuição.
        Útil para quando o cliente finaliza o cadastro e deve ir para um humano.
        """
        flow_id = self.flows.get("AUTO_DISTRIBUTION")

        if not flow_id:
            logger.warning("⚠️ HUGGY_FLOW_AUTO_DISTRIBUTION não configurado no .env")
            return False
        
        try:
            return self.trigger_flow(chat_id, int(flow_id))
        except ValueError:
            logger.error(f"❌ ID do Flow inválido no .env: {flow_id}")
            return False