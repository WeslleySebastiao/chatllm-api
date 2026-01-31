from src.core.config import settings
from fastapi import FastAPI
import logging
import uvicorn
import time
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.logging import setup_logging
from src.core.exceptions import APIError, api_error_handler
from src.api.reviews.read_routes import router_reviews_read
from src.api.routes import router
from src.api.DashboardViews.routes import router_view
from src.api.reviews.execution_routes import router_review

from src.mcp.loader import load_all_tools
import os

# Configura logs
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Server Initializer')
    logger.info('Loading tools')
    load_all_tools()
    logger.info('Tool loaded')
    yield
    logger.info('Shutdown Complete')

app = FastAPI(
    # Seus parâmetros antigos:
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan  
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONT_URL, ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(APIError, api_error_handler)
app.include_router(router)
app.include_router(router_view)
app.include_router(router_review)
app.include_router(router_reviews_read)
@app.get("/")
def health():
    """Verifica se a API está viva"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
    