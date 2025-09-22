# app/utils/auth.py
# Verify Supabase JWTs using JWKS (async). Caches JWKS for performance.

import os
import time
from typing import Dict, Any
import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError

SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")
SUPABASE_ISSUER = os.getenv("SUPABASE_ISSUER")

if not SUPABASE_JWKS_URL or not SUPABASE_ISSUER:
    # don't crash on import; raise when used
    pass

# simple in-memory cache
_jwks_cache = {"keys": None, "fetched_at": 0, "ttl": 3600}


async def _fetch_jwks() -> Dict[str, Any]:
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < _jwks_cache["ttl"]:
        return _jwks_cache["keys"]
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(SUPABASE_JWKS_URL)
        r.raise_for_status()
        jwks = r.json()
    _jwks_cache["keys"] = jwks
    _jwks_cache["fetched_at"] = now
    return jwks


async def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Verify Supabase JWT and return decoded claims.
    Raises jose.exceptions.JWTError on failure.
    """
    if not SUPABASE_JWKS_URL or not SUPABASE_ISSUER:
        raise JWTError("SUPABASE_JWKS_URL or SUPABASE_ISSUER not configured in environment")

    jwks = await _fetch_jwks()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise JWTError("Missing KID in token header")

    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        raise JWTError("No matching JWK found")

    public_key = jwk.construct(key)
    pem = public_key.to_pem().decode()

    # decode and validate issuer. Not verifying audience by default.
    try:
        claims = jwt.decode(
            token,
            pem,
            algorithms=[key.get("alg", "RS256")],
            issuer=SUPABASE_ISSUER,
            options={"verify_aud": False},
        )
    except Exception as exc:
        raise JWTError(f"Token verification failed: {exc}")

    return claims
