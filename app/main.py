import os
import redis
from fastapi import FastAPI
from dotenv import load_dotenv
from app.infrastructure.celery import celery_app
from app.routers import webhooks
from app.core.logger import setup_logging

load_dotenv()

setup_logging()

app = FastAPI(title="Huggy Middleware")

app.include_router(webhooks.router)

@app.get("/")
async def root():
    return {"message": "Huggy Middleware is running 🚀"}

@app.get("/health/celery")
async def check_celery():
    """Endpoint para verificar conectividade com o Redis/Celery"""
    try:
        inspection = celery_app.control.inspect()
        active = inspection.active()
        return {"status": "ok", "workers_active": active}
    except Exception as e:
        return {"status": "error", "details": str(e)}

@app.post("/admin/refresh-messages")
async def refresh_messages():
    """
    Limpa o cache de mensagens no Redis.
    Isso força o bot a baixar a versão mais recente do Gist na próxima interação.
    """
    try:
        redis_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

        r = redis.from_url(redis_url, decode_responses=True)

        r.delete("bot:content:messages")

        return {
            "status": "success",
            "message": "Cache limpo! 🧹 A próxima mensagem será carregada do Gist."
        }
    except Exception as e:
        return {"status": "error", "details": str(e)}