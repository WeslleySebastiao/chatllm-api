from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configurações globais da aplicação."""
    
    APP_NAME: str 
    APP_VERSION: str 
    DEBUG: bool = True
    
    MCP_URL: str  # endereço do servidor MCP
    
    OPENAI_API_KEY: str
    MODEL_NAME: str 

    FRONT_URL: str 

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global
settings = Settings()