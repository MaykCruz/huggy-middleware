import logging
from app.services.session import SessionManager
from app.services.huggy_api import HuggyClient
from app.utils.validators import validate_cpf, clean_digits

logger = logging.getLogger(__name__)

class BotEngine:
    """
    Máquina de Estados que decide o fluxo da conversa.
    """
    def __init__(self):
        self.session = SessionManager()
        self.huggy = HuggyClient()

    def process(self, chat_id: int, message_text: str):
        current_state = self.session.get_state(chat_id)
        context = self.session.get_context(chat_id)

        logger.info(f"🤖 [Engine] Chat: {chat_id} | Estado: {current_state} | Input: '{message_text}'")

        next_state = current_state

        # --- MÁQUINA DE ESTADOS ---

        # 0. Início
        if current_state == "START":
            self.huggy.send_message(chat_id, "welcome")
            next_state = "MENU_APRESENTACAO"

        # 1. Menu Inicial
        elif current_state == "MENU_APRESENTACAO":
            opt = message_text.strip()

            if opt == "1": #CLT
                self.huggy.send_message(chat_id, "ask_cpf")
                next_state = "AGUARDANDO_CPF"
            
            elif opt == "2": #FGTS
                self.huggy.send_message(chat_id, "ask_cpf")
                next_state = "AGUARDANDO_CPF"
            
            else:
                self._handoff_human(chat_id)
                next_state = "FINISHED"

        # 2. Validação CPF
        elif current_state == "AGUARDANDO_CPF" or current_state == "CPF_INVALIDO":
            cpf_limpo = clean_digits(message_text)
            
            if validate_cpf(cpf_limpo):
                # CPF VÁLIDO: Salva no contexto e prossegue
                context["cpf"] = cpf_limpo
                self.session.set_context(chat_id, context)

                self.huggy.send_message(chat_id, "cpf_valid_ask_registry")
                next_state = "AGUARDANDO_TEMPO_REGISTRO"
            
            else:
                # CPF INVÁLIDO
                if current_state == "AGUARDANDO_CPF":
                    # Primeira tentativa falha: Pede de novo
                    self.huggy.send_message(chat_id, "cpf_invalid")
                    next_state = "CPF_INVALIDO"
                else:
                    # Segunda tentativa falha (já estava em CPF_INVALIDO): Transbordo
                    self.huggy.send_message(chat_id, "invalid_cpf_fallback_human")
                    self.huggy.start_auto_distribution(chat_id)
                    next_state = "FINISHED"

        # 3. Tempo de Registro
        elif current_state == "AGUARDANDO_TEMPO_REGISTRO":
            opt = message_text.strip()

            if opt == "1":
                # SIMULAR (Temos CPF e temos Requisito)
                cpf_salvo = context.get("cpf", "N/A")
                self.huggy.send_message(chat_id, "simulating", variables={"cpf": cpf_salvo})
                
                # AQUI ENTRARIA A CHAMADA DA API DE SIMULAÇÃO (Fase 6)
                # ... result = api.simular(cpf_salvo) ...

                self.huggy.send_message(chat_id, "simulation_result")
                self.huggy.start_auto_distribution(chat_id) # Entrega o lead pronto
                next_state = "FINISHED"

            elif opt == "2":
                # NÃO ATINGIU REQUISITO
                self.huggy.send_message(chat_id, "requirements_fail")
                tab_id = self.huggy.tabulations.get("LESS_SIX_MONTHS")
                self.huggy.finish_attendance(chat_id, tabulation_id=tab_id)
                next_state = "FINISHED"
            
            else:
                self._handoff_human(chat_id)
                next_state = "FINISHED"

        # 4. Estado Final
        elif current_state == "FINISHED":
            logger.info(f"Chat {chat_id} ignorado (Fluxo finalizado).")
            return

        # 5. Persistência
        if next_state != current_state:
            self.session.set_state(chat_id, next_state)
    
    def _handoff_human(self, chat_id: int):
        """Helper para transferir em caso de erro/imcompreensão"""
        self.huggy.send_message(chat_id, "fallback_human")
        self.huggy.start_auto_distribution(chat_id)