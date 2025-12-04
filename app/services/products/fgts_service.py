import logging
from typing import Dict, Any, List
from app.integrations.facta.fgts.service import FactaFGTSService

logger = logging.getLogger(__name__)

class FGTSService:
    """
    Service Global de FGTS.
    Responsável por consultar múltiplos parceiros (Facta, etc.) e agregar/comparar os resultados.
    """
    def __init__(self):
        self.facta_service = FactaFGTSService()

    def consultar_melhor_oportunidade(self, cpf: str) -> Dict[str, Any]:
        """
        Executa a lógica de prioridade (Waterfall).
        Atualmente: Chama Facta.
        Futuramente: Se Facta falhar ou não for vantajoso, chama Próximo.
        """
        logger.info(f"🌐 [Global FGTS] Buscando oportunidade para CPF: {cpf}")

        resultado = self.facta_service.simular_antecipacao(cpf)

        resultado["banco_origem"] = "FACTA"

        if resultado.get("aprovado"):
            logger.info("✅ [Global FGTS] Proposta encontrada na FACTA.")
            return resultado

        logger.warning(f"❌ [Global FGTS] Nenhuma proposta aprovada. Retornando resultado FACTA.")
        return resultado