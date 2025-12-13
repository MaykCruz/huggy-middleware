import pytest
from app.services.products.fgts_service import FGTSService
from app.schemas.credit import AnalysisStatus

# 👇 CORREÇÃO: Mockamos a classe FactaFGTSService, não o Adapter
@pytest.fixture
def mock_facta_service(mocker):
    # O patch deve ser onde a classe é IMPORTADA/USADA
    return mocker.patch("app.services.products.fgts_service.FactaFGTSService")

def test_service_catch_all_generic_error(mock_facta_service):
    """Testa se o Service captura erros desconhecidos sem crashar"""
    mock_instance = mock_facta_service.return_value
    
    # Simula o retorno do método simular_antecipacao
    mock_instance.simular_antecipacao.return_value = {
        "aprovado": False,
        "motivo": "ERRO_ALIENIGENA", 
        "msg_tecnica": "Falha na matrix", # Seu código usa msg_tecnica ou str(motivo)
        "detalhes": {}
    }

    service = FGTSService()
    oferta = service.consultar_melhor_oportunidade("12345678900")

    assert oferta is not None
    assert oferta.status == AnalysisStatus.RETORNO_DESCONHECIDO
    assert oferta.is_internal is True
    assert oferta.variables["erro"] == "Falha na matrix"

def test_service_limite_excedido(mock_facta_service):
    """Testa o status específico de Limite Excedido"""
    mock_instance = mock_facta_service.return_value
    
    # 👇 Simulando o retorno exato que o FactaFGTSService entregaria
    mock_instance.simular_antecipacao.return_value = {
        "aprovado": False,
        "motivo": "LIMITE_EXCEDIDO_CONSULTAS_FGTS",
        "msg_tecnica": "Limite atingido",
        "detalhes": {}
    }

    service = FGTSService()
    oferta = service.consultar_melhor_oportunidade("12345678900")

    # 👇 Verificando com as constantes do seu código
    assert oferta.status == AnalysisStatus.LIMITE_EXCEDIDO_CONSULTAS_FGTS
    assert oferta.message_key == "limite_excedido_fgts"