from dataclasses import dataclass
from typing import Dict, Any
from app.core.domain.enums import BankQueryStatus

@dataclass
class BalanceResul:
    status: BankQueryStatus
    saldo: float
    original_message =  str
    raw_data: Dict[str, Any]