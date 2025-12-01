import httpx
import logging
from typing import Dict, Any, List
from app.integrations.facta.auth import FactaAuth
from app.integrations.facta.translator import FactaTranslator
from app.integrations.facta.schemas import BalanceResult
from app.core.domain.enums import BankQueryStatus

logger = logging.getLogger(__name__)

class FactaFGTSAdapter:
    def __init__(self):
        self.auth = FactaAuth()
        self.base_url = self.auth.base_url

    @property
    def headers(self) -> Dict[str, str]:
        """
        Propriedade dinâmica que garante um token válido a cada chamada.
        """
        token = self.auth.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_balance(self, cpf: str) -> Dict[str, Any]:
        """
        Consulta o saldo do FGTS na Caixa (via Facta).
        Endpoint: GET /fgts/saldo
        """
        url = f"{self.base_url}/fgts/saldo"
        params = {"cpf": cpf, "banco": "facta"}

        try:
            with httpx.Client(timeout=30.0) as client:
                logger.info(f"💰 [Facta] Consultando saldo para CPF {cpf}...")
                response = client.get(url, headers=self.headers, params=params)

                if response.status_code == 403 and 'cloudflare' in response.text.lower():
                    logger.critical(f"🛡️ [Facta] Bloqueio de WAF/Cloudflare detectado!")
                    return {"erro": True, "mensagem": "Bloqueio de Segurança (Cloudflare)"}
                
                return response.json()
        
        except httpx.ReadTimeout:
            logger.error("❌ [Facta] Timeout na consulta de saldo.")
            return {"erro": True, "mensagem": "Timeout na consulta de saldo"}
        except Exception as e:
            logger.error(f"❌ [Facta] Erro técnico saldo: {e}")
            return {"erro": True, "mensagem": str(e)}

    def calculate_simulation(self, cpf: str, tabela: int, taxa: float, parcelas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executa o cálculo de valores líquidos.
        Endpoint: POST /fgts/calculo
        """
        url = f"{self.base_url}/fgts/calculo"

        try:
            cpf_clean = cpf.replace(".", "").replace("-", "")

            body = {
                "cpf": cpf_clean,
                "taxa": taxa,
                "tabela": tabela,
                "parcelas": parcelas
            }

            with httpx.Client(timeout=30.0) as client:
                logger.debug(f"🧮 [Facta] Simulando Tabela {tabela}...")
                response = client.post(url, headers=self.headers, json=body)

                if response.status_code == 403 and 'cloudflare' in response.text.lower():
                     return {"erro": True, "mensagem": "Bloqueio de Segurança (Cloudflare)"}

                return response.json()
        
        except Exception as e:
            logger.error(f"❌ [Facta] Erro técnico simulação: {e}")
            return {"erro": True, "mensagem": str(e)}