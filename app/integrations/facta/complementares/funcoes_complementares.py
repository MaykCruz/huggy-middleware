import httpx
import logging
from typing import Optional, Dict
from app.integrations.facta.auth import FactaAuth

logger = logging.getLogger(__name__)

BANCOS_DICT = {
  "001": "Banco do Brasil",
  "003": "Banco da Amazônia",
  "004": "Banco do Nordeste do Brasil",
  "021": "Banestes",
  "025": "Banco Alfa",
  "033": "Banco Santander",
  "037": "Banco do Estado do Pará",
  "041": "Banco do Estado do Rio Grande do Sul",
  "047": "Banco do Estado de Sergipe",
  "069": "Banco Crefisa",
  "070": "Banco de Brasília",
  "077": "Banco Inter",
  "085": "Cooperativa Central de Crédito Urbano - Cecred",
  "091": "Central Unicred RS",
  "097": "Cooperativa Central de Crédito Noroeste Brasileiro Ltda.",
  "104": "Caixa Econômica Federal",
  "121": "Banco Agibank",
  "133": "Confederação Nacional das Cooperativas Centrais de Crédito",
  "136": "Confederação Nacional das Cooperativas Centrais Unicred Ltda.",
  "208": "Banco BTG Pactual",
  "212": "Banco Original",
  "218": "Banco BS2",
  "237": "Banco Bradesco",
  "246": "Banco ABC Brasil",
  "260": "Nubank",
  "318": "Banco BMG",
  "335": "Banco Digio",
  "336": "Banco C6",
  "341": "Itaú Unibanco",
  "380": "PicPay Bank",
  "389": "Banco Mercantil do Brasil",
  "403": "Cora Sociedade de Crédito Direto",
  "422": "Banco Safra",
  "623": "Banco Pan",
  "707": "Banco Daycoval",
  "745": "Banco Citibank",
  "748": "Banco Sicredi",
  "756": "Bancoob"
}

class FactaDadosCadastrais:
    def __init__(self):
        self.auth = FactaAuth()
        self.base_url = self.auth.base_url
    
    @property
    def _get_headers(self):
        token = self.auth.get_valid_token()
        return {"Authorization": f"Bearer {token}"}
    
    def _formatar_dados_bancarios(self, banco: str, agencia: str, conta: str, tipo: str) -> str:
        """
        Formata os dados brutos para exibição amigável.
        """
        if not banco or not conta:
            return ""
        
        banco_str = str(banco).zfill(3)
        banco_formatado = BANCOS_DICT.get(banco_str, f" Banco {banco_str}")

        agencia_formatada = str(agencia).zfill(4) if agencia else "Sem Agência"

        conta_limpa = str(conta).strip()
        if len(conta_limpa) >= 2 and "-" not in conta_limpa:
            conta_sem_dv = conta_limpa[:-1]
            digito = conta_limpa[-1]
            conta_formatada = f"{conta_sem_dv}-{digito}"
        else:
            conta_formatada = conta_limpa

        tipo_upper = str(tipo).upper()
        tipo_desc = ""
        if tipo_upper == "C":
            tipo_desc = "corrente"
        elif tipo_upper == "P":
            tipo_desc = "poupança"
        
        texto = f"{banco_formatado}\nAgência: {agencia_formatada}\nConta {tipo_desc}: {conta_formatada}"
        return texto
    
    def buscar_conta_bancaria(self, cpf: str) -> Optional[Dict[Dict, str]]:
        """
        Busca dados do cliente na Facta e retorna os dados formatados se existirem.
        """
        url = f"{self.base_url}/proposta/consulta-cliente"
        params = {"cpf": cpf}

        try:
            with httpx.Client(timeout=30.0) as client:
                logger.info(f"🔎 [Facta] Consultando dados cadastrais para CPF {cpf}...")
                response = client.get(url, headers=self._get_headers, params=params)

                if response.status_code != 200:
                    logger.warning(f"⚠️ [Facta] Erro API Consulta: {response.status_code}")
                    return None

                data = response.json()

                if data.get("erro") is True:
                    return None
                
                cliente_lista = data.get("cliente", [])
                if not cliente_lista:
                    return None
                
                dados = cliente_lista[0]

                banco = dados.get("BANCO")
                agencia = dados.get("AGENCIA") 
                conta = dados.get("CONTA")
                tipo = dados.get("TIPO_CONTA", "")

                if not banco or not conta:
                    logger.info(f"ℹ️ [Facta] Cliente encontrado, mas sem dados bancários completos.")
                    return None
                
                texto_completo = self._formatar_dados_bancarios(banco, agencia, conta, tipo)

                return {
                    "raw": dados,
                    "texto_formatado": texto_completo,
                    "banco_nome": BANCOS_DICT.get(str(banco).zfill(3), banco)
                }
        except Exception as e:
            logger.error(f"❌ [Facta] Falha ao buscar dados cadastrais: {e}")
            return None
