# src/core/mcp_client.py
import requests
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

def check_mcp_connection():
    """Tenta se conectar ao servidor MCP e retorna (ok, mensagem)."""
    try:
        response = requests.get(f"{settings.MCP_URL}/health", timeout=3)
        if response.status_code == 200:
            logger.info("Conexão com MCP OK.")
            return True, "MCP online"
        else:
            logger.warning(f"⚠️ MCP respondeu com status {response.status_code}")
            return False, f"MCP respondeu com status {response.status_code}"
    except Exception as e:
        logger.error(f"Erro ao conectar ao MCP: {e}")
        return False, str(e)