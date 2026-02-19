import jwt
from jwt import PyJWKClient
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from src.core.config import settings

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/", "/docs", "/openapi.json", "/redoc"}

# PyJWKClient já faz cache interno das chaves automaticamente
_jwks_client: PyJWKClient | None = None

def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(url)
        logger.info("JWKSClient inicializado.")
    return _jwks_client


def _cors_error_response(status_code: int, message: str, origin: str | None) -> JSONResponse:
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(status_code=status_code, content={"error": message}, headers=headers)


async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    origin = request.headers.get("origin")
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return _cors_error_response(401, "Token de autenticação ausente.", origin)

    token = auth_header.split(" ")[1]

    try:
        client = _get_jwks_client()
        # Busca automaticamente a chave correta baseado no "kid" do token
        signing_key = client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={"verify_aud": False}
        )
        request.state.user = payload

    except jwt.ExpiredSignatureError:
        return _cors_error_response(401, "Token expirado. Faça login novamente.", origin)
    except jwt.InvalidTokenError as e:
        logger.warning(f"[AUTH] Token inválido: {type(e).__name__}: {e}")
        return _cors_error_response(401, "Token inválido.", origin)
    except Exception as e:
        logger.error(f"[AUTH] Erro inesperado: {e}")
        return _cors_error_response(500, "Erro interno na autenticação.", origin)

    return await call_next(request)