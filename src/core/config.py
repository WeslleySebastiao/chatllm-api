from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    """Configurações globais da aplicação."""
    
    APP_NAME: str 
    APP_VERSION: str 
    DEBUG: bool = True
    
    OPENAI_API_KEY: str
    MODEL_NAME: str 
    FRONT_URL: str 

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global
settings = Settings()