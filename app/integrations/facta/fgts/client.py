import httpx
import logging
from app.integrations.facta.auth import FactaAuth
from app.utils.formatters import parse_valor_monetario
from app.integrations.facta.fgts.funcoes_auxiliares import (
    interpretar_retorno, 
    organizar_parcelas,
    selecionar_melhor_tabela
)

logger = logging.getLogger(__name__)

class FactaFGTSAdapter:
    def __init__(self):
        self.auth = FactaAuth()
        self.base_url = self.auth.base_url

    @property
    def _get_headers(self):
        token = self.auth.get_valid_token()
        return {"Authorization": f"Bearer {token}","Content-Type": "application/json"}
    
    def consultar_saldo(self, cpf: str) -> dict:
        url = f"{self.base_url}/fgts/saldo"
        params = {"cpf": cpf, "banco": "facta"}

        try:
            with httpx.Client(timeout=30.0) as client:
                logger.info(f"💰 [Facta] Consultando saldo para CPF {cpf}...")
                response = client.get(url, headers=self._get_headers, params=params)
                data = response.json()

                status = interpretar_retorno(data)
        
                return {
                    "status": status,
                    "dados": data.get("retorno", {}),
                    "msg_original": data.get("mensagem", "")
                }
        except Exception as e:
            logger.error(f"Erro Saldo: {e}")
            return {"status": "ERRO_TECNICO", "msg_original": str(e)}

    def simular_calculo(self, cpf: str, dados_saldo: dict) -> dict:
        parcelas = organizar_parcelas(dados_saldo)

        saldo_bruto = parse_valor_monetario(dados_saldo.get("saldo_total", 0))

        info_tabela = selecionar_melhor_tabela(saldo_bruto)

        logger.info(f"🧮 [Facta] Simulando tabela '{info_tabela['nome']}' (Cód {info_tabela['codigo']}) para saldo {saldo_bruto}")

        url = f"{self.base_url}/fgts/calculo"

        body = {
            "cpf": cpf.replace(".", "").replace("-", ""),
            "taxa": info_tabela["taxa"],
            "tabela": info_tabela["codigo"],
            "parcelas": parcelas
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=self._get_headers, json=body)
                data = resp.json()
                
                # Verifica se aprovou
                if data.get("permitido", "").upper() == "SIM":
                    return {
                        "status": "APROVADO",
                        "valor_liquido": parse_valor_monetario(data.get("valor_liquido")),
                        "raw": data
                    }
                else:
                    return {
                        "status": "REPROVADO", 
                        "msg_original": data.get("mensagem")
                    }
        except Exception as e:
            return {"status": "ERRO_TECNICO", "msg_original": str(e)}