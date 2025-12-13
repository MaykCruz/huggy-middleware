import pytest
import os
from unittest.mock import MagicMock

# 1. Configura variáveis de ambiente FAKES para o teste
@pytest.fixture(scope="session", autouse=True)
def mock_env():
    os.environ["ADMIN_API_TOKEN"] = "TEST_SECRET_TOKEN"
    os.environ["FACTA_USER"] = "test_user"
    os.environ["FACTA_PASSWORD"] = "test_pass"
    os.environ["FACTA_PROXY_URL"] = "http://user:pass@127.0.0.1:8080"
    os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

# 2. Mock do Redis (Para não precisar subir um container)
@pytest.fixture
def mock_redis(mocker):
    redis_mock = MagicMock()
    # Simula o from_url retornando nosso mock
    mocker.patch("redis.from_url", return_value=redis_mock)
    return redis_mock

# 3. Mock do TokenManager (Para não travar no Lock distribuído)
@pytest.fixture
def mock_token_manager(mocker):
    manager = MagicMock()
    manager.get_token.return_value = None # Simula cache vazio por padrão
    manager.acquire_lock.return_value = True # Sempre consegue o lock
    
    mocker.patch("app.integrations.facta.auth.TokenManager", return_value=manager)
    mocker.patch("app.infrastructure.token_manager.TokenManager", return_value=manager)
    return manager