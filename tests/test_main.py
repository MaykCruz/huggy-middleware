from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_admin_refresh_success(mock_redis):
    """Deve funcionar com o token correto"""
    response = client.post(
        "/admin/refresh-messages",
        headers={"x-admin-token": "TEST_SECRET_TOKEN"} # Igual ao conftest.py
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    # Verifica se chamou o redis.delete
    mock_redis.delete.assert_called_with("bot:content:messages")

def test_admin_refresh_unauthorized_no_token():
    """Deve falhar (401/422) se não enviar o header"""
    response = client.post("/admin/refresh-messages")
    # FastAPI pode retornar 422 (Validation Error) quando falta header obrigatório
    assert response.status_code in [401, 422] 

def test_admin_refresh_unauthorized_wrong_token():
    """Deve falhar (401) se o token estiver errado"""
    response = client.post(
        "/admin/refresh-messages",
        headers={"x-admin-token": "SENHA_ERRADA"}
    )
    assert response.status_code == 401
    assert "inválido" in response.json()["detail"]