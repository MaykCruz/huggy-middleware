import re
from typing import Dict, Any, Tuple
from app.core.domain.enums import BankQueryStatus

class FactaTranslator:
    @staticmethod
    def interpret_balance_response(response_data: Dict[str, Any]) -> Tuple[BankQueryStatus, str, float]:
        
        # 1. Erro Técnico HTTP injetado pelo Adapter
        if response_data.get("erro_http"):
             return BankQueryStatus.SYSTEM_ERROR, response_data.get("mensagem", "Erro HTTP"), 0.0

        # 2. Happy Path (Sucesso)
        if not response_data.get("erro"):
            retorno = response_data.get("retorno", {})
            try:
                saldo_raw = str(retorno.get("saldo_total", "0"))
                saldo_limpo = saldo_raw.replace("R$", "").strip().replace(",", ".")
                saldo = float(saldo_limpo)
            except:
                saldo = 0.0
            return BankQueryStatus.SUCCESS, "Saldo retornado com sucesso", saldo

        # 3. Análise de Erros (Híbrida: Código + Texto)
        code = response_data.get("codigo") # Pode ser None
        msg = response_data.get("mensagem", "").lower() # Normaliza para minusculo
        
        # --- A. DETECÇÃO DE INFRA (THROTTLING) ---
        if re.search(r"volte em \d+ segundos", msg):
            return BankQueryStatus.THROTTLED, msg, 0.0

        # --- B. DETECÇÃO POR CÓDIGO (Prioridade Alta) ---
        if code == 7: return BankQueryStatus.NEEDS_AUTHORIZATION, msg, 0.0
        if code == 9: return BankQueryStatus.NEEDS_ADESAO, msg, 0.0
        if code == 35: return BankQueryStatus.DATA_MISMATCH, msg, 0.0
        if code in [5, 10]: return BankQueryStatus.BIRTHDAY_WINDOW, msg, 0.0
        
        # --- C. DETECÇÃO POR TEXTO (Fallback Robusto) ---
        # Resolve o caso do JSON sem código ou códigos variados
        
        # Caso: Saldo não encontrado (Erro na Caixa ou conta inexistente)
        # Cobre código 102 e o JSON sem código "Saldo não encontrado..."
        if code == 102 or "saldo não encontrado" in msg:
            return BankQueryStatus.BALANCE_NOT_FOUND, msg, 0.0

        # Caso: Sem saldo (Conta existe, mas está zerada/bloqueada)
        # Cobre códigos 101, 104 e textos variados
        if code in [101, 104] or "não possui saldo" in msg or "saldo fgts" in msg:
            return BankQueryStatus.NO_BALANCE, msg, 0.0
            
        # Caso: Autorização (Fallback de texto para garantir)
        if "autorização" in msg:
            return BankQueryStatus.NEEDS_AUTHORIZATION, msg, 0.0

        # Fallback Final
        return BankQueryStatus.SYSTEM_ERROR, f"Erro não mapeado: {msg}", 0.0