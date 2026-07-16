"""Clerk session-token verification.

The frontend attaches a Clerk session JWT as `Authorization: Bearer <token>`.
We verify it against Clerk's JWKS (public keys) fetched from the issuer, and use
the `sub` claim as the user id.

For local development you can set `DISABLE_AUTH=true`, which bypasses verification
and treats every request as a single fixed dev user. Never do this in production.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient

from .config import Settings, get_settings

DEV_USER_ID = "dev-user"

_bearer = HTTPBearer(auto_error=False)

# Cache one JWKS client per issuer so we don't refetch keys on every request.
_jwks_clients: dict[str, PyJWKClient] = {}


def _jwks_client(issuer: str) -> PyJWKClient:
    if issuer not in _jwks_clients:
        jwks_url = issuer.rstrip("/") + "/.well-known/jwks.json"
        _jwks_clients[issuer] = PyJWKClient(jwks_url)
    return _jwks_clients[issuer]


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    """FastAPI dependency that returns the authenticated Clerk user id."""

    if settings.disable_auth:
        return DEV_USER_ID

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    if not settings.clerk_jwt_issuer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_JWT_ISSUER is not configured on the server",
        )

    token = credentials.credentials
    try:
        signing_key = _jwks_client(settings.clerk_jwt_issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_jwt_issuer,
            options={"verify_aud": False},  # Clerk session tokens have no fixed audience
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return user_id
