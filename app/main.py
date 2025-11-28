from fastapi import FastAPI
from dotenv import load_dotenv
from app.celery_app import celery_app
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