from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    """Configurações globais da aplicação."""
    
    APP_NAME: str 
    APP_VERSION: str="0.6.0"
    DEBUG: bool = True
    SUPABASE_JWT_SECRET: str
    OPENAI_API_KEY: str
    MODEL_NAME: str 
    FRONT_URL: str
    API_KEY: str
    SUPABASE_DB_USER : str
    SUPABASE_DB_PASSWORD : str
    SUPABASE_DB_HOST : str
    SUPABASE_DB_PORT : int
    SUPABASE_DB_NAME : str
    SUPABASE_URL: str
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global
settings = Settings()