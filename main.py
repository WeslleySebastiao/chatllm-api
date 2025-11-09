from fastapi import FastAPI
import logging
import uvicorn
import time
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

app.add_exception_handler(APIError, api_error_handler)
app.include_router(router)

@app.get("/")
def read_root():
    """Rota raiz da API."""
    return {"message": f"Welcome to {settings.APP_NAME}!"}

if __name__ == "__main__":
    print("   http://127.0.0.1:8080   (local)")
    print("   http://<IP_DA_MAQUINA>:8080   (rede local)\n")
    uvicorn.run(app, host="0.0.0.0", port=8080)
    