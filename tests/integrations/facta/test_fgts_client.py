import pytest
from app.integrations.facta.fgts.client import FactaFGTSAdapter

@pytest.fixture
def mock_auth(mocker):
    # Mock da Auth para não tentar conectar de verdade
    mock = mocker.patch("app.integrations.facta.fgts.client.FactaAuth")
    mock.return_value.get_valid_token.return_value = "TOKEN_FAKE"
    return mock

def test_interpretar_retorno_sucesso():
    adapter = FactaFGTSAdapter()
    resp = {"erro": False, "codigo": 0, "mensagem": "Sucesso"}
    assert adapter._interpretar_retorno(resp) == "SUCESSO"

def test_interpretar_retorno_sem_saldo():
    adapter = FactaFGTSAdapter()
    resp = {"erro": True, "codigo": 100, "mensagem": "Cliente não possui saldo FGTS"}
    assert adapter._interpretar_retorno(resp) == "SEM_SALDO"

def test_interpretar_retorno_limite_excedido():
    adapter = FactaFGTSAdapter()
    # 👇 CORREÇÃO: A frase exata que seu código espera
    resp = {"erro": True, "mensagem": "Erro: limite mensal de consultas fgts excedido"}
    
    assert adapter._interpretar_retorno(resp) == "LIMITE_EXCEDIDO_CONSULTAS_FGTS"

def test_interpretar_retorno_desconhecido():
    adapter = FactaFGTSAdapter()
    resp = {"erro": True, "codigo": 999, "mensagem": "Erro maluco do sistema"}
    assert adapter._interpretar_retorno(resp) == "RETORNO_DESCONHECIDO"