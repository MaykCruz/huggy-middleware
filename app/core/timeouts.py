from typing import List, TypedDict, Literal

class TimeoutStep(TypedDict):
    delay_seconds: int
    action: Literal["WARN", "KILL"]
    message_key: str
    tabulation_key: str | None

TIMEOUT_POLICES = {
    "MENU_APRESENTACAO": 
        {
            "delay": 600, # 10 minutos
            "action": "TRANSITION",
            "new_state": "MENU_TIMEOUT_1",
            "message_key": "timeout_1_menu"
        },
    "MENU_TIMEOUT_1":
        {
            "delay": 1800, # 30 minutos
            "action": "TRANSITION",
            "new_state": "MENU_TIMEOUT_2",
            "message_key": "timeout_2_menu"
        },
    "MENU_TIMEOUT_2":
        {
            "delay_seconds": 18000, # 5 horas
            "action": "KILL",
            "message_key": "timeout_finalizar",
            "tabulation_key": "SEM_RETORNO_DO_CLIENTE"
        },
    "FGTS_AGUARDANDO_CPF": 
        {
            "delay": 300, # 5 minutos
            "action": "TRANSITION",
            "new_state": "CPF_TIMEOUT",
            "message_key": "timeout_1_cpf"
        },
    "CLT_AGUARDANDO_CPF": 
        {
            "delay": 300, # 5 minutos
            "action": "TRANSITION",
            "new_state": "CPF_TIMEOUT",
            "message_key": "timeout_1_cpf"
        },
    "CPF_TIMEOUT":
        {
            "delay": 18000, # 5 horas
            "action": "KILL",
            "message_key": "timeout_finalizar",
            "tabulation_key": "SEM_RETORNO_DO_CLIENTE"
        }
    
}