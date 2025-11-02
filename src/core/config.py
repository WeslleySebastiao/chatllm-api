from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configurações globais da aplicação."""
    
    APP_NAME: str = "ChatLLM API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    MCP_URL: str = "http://localhost:8000/sse"  # endereço do servidor MCP
    
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global
settings = Settings()