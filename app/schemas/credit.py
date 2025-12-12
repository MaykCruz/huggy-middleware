from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AnalysisStatus(str, Enum):
    """
    Herdar de 'str' ajuda na serialização JSON automática
    """
    APROVADO = "APROVADO"
    SEM_AUTORIZACAO = "SEM_AUTORIZACAO"
    MUDANCAS_CADASTRAIS = "MUDANCAS_CADASTRAIS"
    SEM_SALDO = "SEM_SALDO"
    ANIVERSARIANTE = "ANIVERSARIANTE"
    SALDO_NAO_ENCONTRADO = "SALDO_NAO_ENCONTRADO"
    SEM_ADESAO = "SEM_ADESAO"
    LIMITE_EXCEDIDO_CONSULTAS_FGTS = "LIMITE_EXCEDIDO_CONSULTAS_FGTS"
    RETORNO_DESCONHECIDO = "RETORNO_DESCONHECIDO"

class CreditOffer(BaseModel):
    """
    Substitui o dataclass.
    Representa o resultado padronizado de uma simulação de crédito.
    """
    status: AnalysisStatus
    message_key: str = Field(..., description="Chave da mensagem no messages.json")

    variables: Dict[str, str] = Field(default_factory=dict)
    is_internal: bool = False

    raw_details: Dict[str, Any] = Field(default_factory=dict)

    banco_origem: Optional[str] = None
    valor_liquido: Optional[float] = 0.0
