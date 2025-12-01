from enum import Enum

class BankQueryStatus(Enum):
    # --- SUCESSO ---
    SUCCESS = "SUCCESS"               # Deu certo, saldo retornado
    
    # --- PENDÊNCIAS DO CLIENTE (Ação Necessária) ---
    NEEDS_AUTHORIZATION = "NEEDS_AUTH" # Cliente precisa autorizar no app FGTS
    NEEDS_ADESAO = "NEEDS_ADESAO"      # Cliente precisa aderir ao Saque-Aniversário
    
    # --- BLOQUEIOS TEMPORÁRIOS (Aguardar) ---
    DATA_MISMATCH = "DATA_MISMATCH"    # Mudança cadastral recente (bloqueio temporário)
    BIRTHDAY_WINDOW = "BIRTHDAY_WINDOW" # Janela de aniversário (bloqueio de 90 dias ou mês vigente)
    THROTTLED = "THROTTLED"            # API pediu para esperar (volte em X segundos)
    
    # --- BLOQUEIOS DEFINITIVOS (Falha) ---
    NO_BALANCE = "NO_BALANCE"          # Sem saldo suficiente ou conta zerada
    BALANCE_NOT_FOUND = "NOT_FOUND"    # Conta não localizada na Caixa
    
    # --- ERROS TÉCNICOS ---
    SYSTEM_ERROR = "SYSTEM_ERROR"      # Erro genérico ou não mapeado