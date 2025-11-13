from fastapi import FastAPI
import logging
import uvicorn
import time
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.services.mcp import MCPClient
from src.core.logging import setup_logging
from src.core.exceptions import APIError, api_error_handler
from src.api.routes import router 

# Configura logs
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando conexão SSE global com o MCP...")
    app.state.mcp_sse_client = MCPClient("http://localhost:8000")
    yield
    print("Fechando conexão SSE global...")

app = FastAPI(
    # Seus parâmetros antigos:
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan  
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(APIError, api_error_handler)
app.include_router(router)

@app.get("/")
def read_root():
    """Rota raiz da API."""
    return {"message": f"Welcome to {settings.APP_NAME}!"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
    