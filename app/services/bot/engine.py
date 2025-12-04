import logging
from app.services.bot.memory.session import SessionManager
from app.integrations.huggy.service import HuggyService
from app.services.products.fgts_service import FGTSService 
from app.utils.validators import validate_cpf, clean_digits
from app.utils.formatters import formatar_moeda

logger = logging.getLogger(__name__)

class BotEngine:
    """
    Máquina de Estados que decide o fluxo da conversa.
    """
    def __init__(self):
        self.session = SessionManager()
        self.huggy = HuggyService()
        self.fgts_service = FGTSService()

    def process(self, chat_id: int, message_text: str):
        current_state = self.session.get_state(chat_id)
        context = self.session.get_context(chat_id)

        logger.info(f"🤖 [Engine] Chat: {chat_id} | Estado: {current_state} | Input: '{message_text}'")

        next_state = current_state

        # --- MÁQUINA DE ESTADOS ---

        # 0. Início
        if current_state == "START":
            self.huggy.send_message(chat_id, "menu_bem_vindo")
            next_state = "MENU_APRESENTACAO"

        # 1. Menu Inicial
        elif current_state == "MENU_APRESENTACAO":
            opt = message_text.strip()

            if opt == "1": # CLT
                self.huggy.send_message(chat_id, "pedir_cpf")
                next_state = "CLT_AGUARDANDO_CPF"
            
            elif opt == "2": # FGTS
                self.huggy.send_message(chat_id, "pedir_cpf")
                next_state = "FGTS_AGUARDANDO_CPF"
            
            else:
                self._handoff_human(chat_id)
                next_state = "FINISHED"

        # ---------------------------------------------------------
        # FLUXO 1: CLT (CPF -> Tempo Registro -> Fim)
        # ---------------------------------------------------------
        elif current_state == "CLT_AGUARDANDO_CPF" or current_state == "CLT_CPF_INVALIDO":
            cpf_limpo = clean_digits(message_text)
            
            if validate_cpf(cpf_limpo):
                # CPF VÁLIDO
                context["cpf"] = cpf_limpo
                self.session.set_context(chat_id, context)

                self.huggy.send_message(chat_id, "cpf_valid_ask_registry")
                next_state = "CLT_AGUARDANDO_TEMPO_REGISTRO"
            
            else:
                # CPF INVÁLIDO
                if current_state == "CLT_AGUARDANDO_CPF":
                    self.huggy.send_message(chat_id, "cpf_invalido")
                    next_state = "CLT_CPF_INVALIDO"
                else:
                    self.huggy.send_message(chat_id, "invalid_cpf_fallback_human")
                    self.huggy.start_auto_distribution(chat_id)
                    next_state = "FINISHED"

        # (Adicione aqui a lógica de CLT_AGUARDANDO_TEMPO_REGISTRO se tiver)
        elif current_state == "CLT_AGUARDANDO_TEMPO_REGISTRO":
            opt = message_text.strip()

            if opt == "1": # Possui o mínimo de 6 meses.
                self.huggy.send_message(chat_id, "iniciando_simulacao") # Retorno genérico pois ainda não temos o service do clt
                next_state = "FINISHED"
            
            elif opt == "2": # Não possui o mínimo de 6 meses.
                self.huggy.send_message(chat_id, "requirements_fail")
                self.huggy.finish_attendance(chat_id, tabulation_id=self.huggy.tabulations.get("MENOS_SEIS_MESES"))
                next_state = "FINISHED"

        # ---------------------------------------------------------
        # FLUXO 2: FGTS (CPF -> Simulação Imediata)
        # ---------------------------------------------------------
        elif current_state == "FGTS_AGUARDANDO_CPF" or current_state == "FGTS_CPF_INVALIDO":
            cpf_limpo = clean_digits(message_text)
            
            if validate_cpf(cpf_limpo):
                # 1. CPF VÁLIDO: Salva contexto
                context["cpf"] = cpf_limpo
                self.session.set_context(chat_id, context)

                # 2. FEEDBACK E SIMULAÇÃO IMEDIATA
                # Não mudamos para um estado intermediário, executamos já.
                self.huggy.send_message(chat_id, "iniciando_simulacao", variables={"cpf": cpf_limpo})
                
                # Chama o Service Global
                resultado = self.fgts_service.consultar_melhor_oportunidade(cpf_limpo)

                # 3. TRATAMENTO DO RESULTADO
                if resultado.get("aprovado"):
                    # SUCESSO
                    raw_val = resultado["detalhes"]["valor_liquido"]
                    val_liquido = formatar_moeda(raw_val)

                    banco = resultado.get("banco_origem", "Parceiro")

                    self.huggy.send_message(
                        chat_id, 
                        "proposal_success", 
                        variables={"valor": f"{val_liquido}", "banco": banco}
                    )
                    self.huggy.start_auto_distribution(chat_id)
                    next_state = "FINISHED"
                
                else:
                    # ERRO / REPROVAÇÃO
                    motivo = resultado.get("motivo")
                    logger.info(f"⛔ Recusa FGTS para {cpf_limpo}: {motivo}")

                    if motivo == "SEM_AUT":
                        self.huggy.send_message(chat_id, "facta_error_auth")
                        next_state = "WAITING_AUTHORIZATION"
                    
                    elif motivo == "SEM_SALDO":
                        self.huggy.send_message(chat_id, "facta_error_balance")
                        # Finaliza com tabulação específica
                        if self.huggy.tabulations.get("SEM_SALDO"):
                            self.huggy.finish_attendance(chat_id, tabulation_id=self.huggy.tabulations.get("SEM_SALDO"))
                        next_state = "FINISHED"

                    elif motivo == "SALDO_INSUFICIENTE_PARA_OPERACAO":
                        self.huggy.send_message(chat_id, "facta_error_balance")
                        # Finaliza com tabulação específica
                        if self.huggy.tabulations.get("SEM_SALDO"):
                            self.huggy.finish_attendance(chat_id, tabulation_id=self.huggy.tabulations.get("SEM_SALDO"))
                        next_state = "FINISHED"

                    else:
                        # Erro Genérico
                        self.huggy.send_message(chat_id, "generic_error", force_internal=True)
                        self.huggy.start_auto_distribution(chat_id)
                        next_state = "FINISHED"
            
            else:
                # CPF INVÁLIDO (Lógica de retry)
                if current_state == "FGTS_AGUARDANDO_CPF":
                    self.huggy.send_message(chat_id, "cpf_invalid")
                    next_state = "FGTS_CPF_INVALIDO"
                else:
                    self.huggy.send_message(chat_id, "invalid_cpf_fallback_human")
                    self.huggy.start_auto_distribution(chat_id)
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