import httpx
import os
import logging
from typing import Union, Dict, Any, List, Optional
from app.services.message_loader import MessageLoader

logger = logging.getLogger(__name__)

class HuggyClient:
    API_VALUE_EXIT_WORKFLOW = ""

    def __init__(self):
        self.api_token = os.getenv("HUGGY_API_TOKEN")
        self.base_url = "https://api.huggy.app/v3/companies/351946"

        self.workflow_steps = {
            "WORKFLOW_STEP_AG_FORMALIZAR": os.getenv("HUGGY_WORKFLOW_STEP_AG_FORMALIZAR"),
        }

        self.flows = {
            "AUTO_DISTRIBUTION": os.getenv("HUGGY_FLOW_AUTO_DISTRIBUTION")
        }

        self.tabulations = {
            "LESS_SIX_MONTHS": os.getenv("HUGGY_TABULATION_LESS_SIX_MONTHS")
        }
        
        if not self.api_token:
            logger.warning("⚠️ HUGGY_API_TOKEN não configurado. As chamadas à API falharão.")

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def send_message(self, chat_id: int, message_key: str, variables: Dict[str, Any] = None, file_url: Optional[str] = None, force_internal: bool = False) -> bool:
        """
        Envia uma mensagem completa (Texto, Arquivo, Botões, Interna).

        Args:
            chat_id: ID do chat.
            message_key: Chave no messages.json.
            variables: Dict para formatar o texto (ex: {'nome': 'João'}).
            file_url: URL de mídia (sobrescreve o do JSON se existir).
            force_internal: Se True, força a mensagem a ser interna.
        """
        template = MessageLoader.get(message_key)
        if not template and not message_key.startswith("DYNAMIC"):
            logger.error(f"❌ Template '{message_key}' não encontrado.")
            raise ValueError(f"Message key '{message_key}' not found.")
        
        raw_text = template.get("text", "")
        final_text = raw_text

        if variables and raw_text:
            try:
                final_text = raw_text.format(**variables)
            except KeyError as e:
                logger.error(f"⚠️ Falta variável {e} para mensagem '{message_key}'")
                final_text = raw_text
        
        
        payload = {
            "text": final_text
        }

        if "options" in template:
            payload["options"] = template["options"]

        payload_file = file_url if file_url else template.get("file")
        if payload_file:
            payload["file"] = payload_file

        is_internal = force_internal or template.get("isInternal", False)
        payload["isInternal"] = is_internal

        url = f"{self.base_url}/chats/{chat_id}/messages"

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                
                # Log rico para debug
                log_extras = []
                if "file" in payload: log_extras.append("📎 Com Arquivo")
                if "options" in payload: log_extras.append("🔘 Com Botões")
                if is_internal: log_extras.append("🔒 Interna")
                
                logger.info(f"📤 [Huggy] Msg '{message_key}' enviada. {' | '.join(log_extras)}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Erro HTTP Huggy ({e.response.status_code}): {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"❌ Erro conexão Huggy: {str(e)}")
            raise e
    
    def trigger_flow(self, chat_id: int, flow_id: int, variables: Dict[str, Any] = None) -> bool:
        """
        Dispara um Flow específico para o chat (POST /chats/{id}/flow).
        """
        url = f"{self.base_url}/chats/{chat_id}/flow"

        payload = {
            "flowId": flow_id
        }

        if variables:
            payload["variables"] = variables

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=self._get_headers(), json=payload)
                
                # 200 OK - Sucesso (Body vazio)
                if response.status_code == 200:
                    logger.info(f"⚡ [Huggy] Flow {flow_id} disparado para Chat {chat_id}.")
                    return True
                
                # 404/400 - Erros comuns
                elif response.status_code in [400, 404]:
                    logger.warning(f"⚠️ [Huggy] Falha ao disparar Flow {flow_id}: {response.text}")
                    return False
                
                else:
                    response.raise_for_status() # Lança erro para 5xx
                    return False # Nunca chega aqui, mas agrada o linter

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Erro HTTP Huggy ao disparar flow: {e.response.text}")
            return False # Aqui retornamos False para o Engine decidir o que fazer (ex: tentar outro método)
        except Exception as e:
            logger.error(f"❌ Erro conexão Huggy: {str(e)}")
            return False

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
            friendly_name = next((k for k, v in self.workflow_steps.items() if v == str(step_id)), str(step_id))
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
    
    def close_chat(self, chat_id: int, tabulation_id: Union[int, str] = None, comment: str = None, send_feedback: bool = False) -> bool:
        """
        Método Base: Fecha o chat.
        Nota: tabulation_id agora é tratado como obrigatório pela regra de negócio, 
        embora tecnicamente a função aceite, vamos forçar o uso correto.
        """
        url = f"{self.base_url}/chats/{chat_id}/close"

        payload = {
            "sendFeedback": send_feedback,
            "tabulation": str(tabulation_id)
        }

        if comment:
            payload["comment"] = comment
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.put(url, headers=self._get_headers(), json=payload)
                
                if response.status_code == 200:
                    logger.info(f"checkered_flag [Huggy] Chat {chat_id} fechado com sucesso.")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"⚠️ [Huggy] Tentativa de fechar chat {chat_id} que não existe (404).")
                    return False
                else:
                    logger.error(f"❌ [Huggy] Falha ao fechar chat {chat_id}: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Erro conexão Huggy ao fechar chat: {str(e)}")
            return False
    
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