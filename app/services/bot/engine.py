import logging
from app.services.bot.memory.session import SessionManager
from app.integrations.huggy.service import HuggyService
from app.utils.validators import validate_cpf, clean_digits

logger = logging.getLogger(__name__)

class BotEngine:
    """
    Máquina de Estados que decide o fluxo da conversa.
    """
    def __init__(self):
        self.session = SessionManager()
        self.huggy = HuggyService()

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
                
                sim_response = self.proposal_service.simulate_fgts(cpf_salvo)

                if sim_response.message_key:
                    self.huggy.send_message(chat_id, sim_response.message_key, variables=sim_response.message_args)
                
                if sim_response.internal_log:
                    self.huggy.send_message(chat_id, "dynamic_text", variables={"content": f"🔒 Sistema: {sim_response.internal_log}"}, force_internal=True)

                action = sim_response.action_status
                
                if action == "COMPLETED":
                    # Sucesso: Distribui para humano fechar
                    self.huggy.start_auto_distribution(chat_id)
                    next_state = "FINISHED"

                elif action == "PENDING_AUTH":
                    # Pausa o fluxo aqui. O cliente vai ler "Autorize no app" e responder depois.
                    next_state = "WAITING_AUTHORIZATION" 

                elif action == "PENDING_ADESAO":
                    # Encerra (Regra de negócio: não esperamos adesão na linha)
                    self.huggy.start_auto_distribution(chat_id)
                    next_state = "FINISHED"

                else: # FAILED (Sem saldo, bloqueio, etc)
                    tab_id = self.huggy.tabulations.get("REQUIREMENTS_FAIL")
                    self.huggy.finish_attendance(chat_id, tabulation_id=tab_id)
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