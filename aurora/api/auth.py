# AGENCY OS — Authentication & Authorization Middleware
# JWT, API Key, OAuth2 support for the API server

"""
AGENCY OS — Authentication Middleware
JWT tokens, API keys, and OAuth2 support.
"""
from __future__ import annotations
import os, hashlib, secrets, uuid, time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from functools import wraps

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# ─── Configuration ───

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
API_KEY_PREFIX = "ao_"


# ─── Models ───

class AuthUser:
    """Authenticated user context."""
    def __init__(self, user_id: str, email: str, name: str,
                 org_id: Optional[str] = None, roles: Dict = None):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.org_id = org_id
        self.roles = roles or {}

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if not self.org_id:
            return False
        from aurora.enterprise.core import Role, Permission
        role = self.roles.get(self.org_id)
        if not role:
            return False
        try:
            perm = Permission(permission)
            return perm in Role.permissions(role)
        except ValueError:
            return False

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "org_id": self.org_id,
            "roles": {k: v.value for k, v in self.roles.items()}
        }


# ─── JWT Token Management ───

class TokenManager:
    """JWT token creation and validation."""

    @staticmethod
    def create_token(user_id: str, email: str, org_id: Optional[str] = None,
                     roles: Dict = None, expiry_hours: int = None) -> str:
        """Create a JWT token."""
        try:
            import jwt
        except ImportError:
            # Fallback: use simple signed token
            return TokenManager._create_simple_token(user_id, email, org_id)

        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "email": email,
            "org_id": org_id,
            "roles": {k: v.value if hasattr(v, 'value') else str(v) for k, v in (roles or {}).items()},
            "iat": now,
            "exp": now + timedelta(hours=expiry_hours or JWT_EXPIRY_HOURS),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """Decode and validate a JWT token."""
        try:
            import jwt
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except Exception:
            return None

    @staticmethod
    def _create_simple_token(user_id: str, email: str, org_id: Optional[str]) -> str:
        """Fallback simple token (not JWT, for when PyJWT not installed)."""
        payload = f"{user_id}:{email}:{org_id}:{time.time()}"
        signature = hashlib.sha256(f"{payload}:{JWT_SECRET}".encode()).hexdigest()
        return f"{payload}:{signature}"


# ─── API Key Management ───

class APIKeyManager:
    """API key creation and validation."""

    def __init__(self):
        self._keys: Dict[str, Dict] = {}  # key -> {user_id, name, created, last_used}

    def create_key(self, user_id: str, name: str = "default") -> str:
        """Create a new API key."""
        key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
        self._keys[key] = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "is_active": True
        }
        return key

    def validate_key(self, key: str) -> Optional[str]:
        """Validate an API key and return user_id."""
        key_data = self._keys.get(key)
        if not key_data or not key_data.get("is_active"):
            return None
        key_data["last_used"] = datetime.now().isoformat()
        return key_data["user_id"]

    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        if key in self._keys:
            self._keys[key]["is_active"] = False
            return True
        return False

    def list_keys(self, user_id: str) -> List[Dict]:
        """List all API keys for a user."""
        return [{"key": k[:12] + "...", **v} for k, v in self._keys.items()
                if v["user_id"] == user_id]


# ─── Auth Dependencies ───

security = HTTPBearer(auto_error=False)
api_key_manager = APIKeyManager()
token_manager = TokenManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> AuthUser:
    """
    FastAPI dependency to get the current authenticated user.
    
    Supports:
    - Bearer JWT tokens
    - API keys in Authorization header
    - API keys in X-API-Key header
    """
    user = None

    # Try Bearer token
    if credentials and credentials.credentials:
        token = credentials.credentials

        # Check if it's an API key
        if token.startswith(API_KEY_PREFIX):
            user_id = api_key_manager.validate_key(token)
            if user_id:
                # Would load user from enterprise_core
                user = AuthUser(user_id=user_id, email="", name="")
        else:
            # Try JWT
            payload = token_manager.decode_token(token)
            if payload:
                user = AuthUser(
                    user_id=payload["sub"],
                    email=payload.get("email", ""),
                    name=payload.get("name", ""),
                    org_id=payload.get("org_id"),
                    roles=payload.get("roles", {})
                )

    # Try X-API-Key header
    if not user and request:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            user_id = api_key_manager.validate_key(api_key)
            if user_id:
                user = AuthUser(user_id=user_id, email="", name="")

    if not user:
        raise HTTPException(401, "Authentication required")

    return user


def require_permission(permission: str):
    """Decorator/dependency factory to require a specific permission."""
    async def checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if not user.has_permission(permission):
            raise HTTPException(403, f"Permission required: {permission}")
        return user
    return checker


# ─── Rate Limiting ───

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60, burst: int = 100):
        self.rpm = requests_per_minute
        self.burst = burst
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if request is within rate limit."""
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []

        # Clean old entries
        self._requests[key] = [t for t in self._requests[key] if now - t < 60]

        if len(self._requests[key]) >= self.rpm:
            return False

        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        if key not in self._requests:
            return self.rpm
        recent = [t for t in self._requests[key] if now - t < 60]
        return max(0, self.rpm - len(recent))


rate_limiter = RateLimiter()


async def rate_limit_check(request: Request):
    """FastAPI dependency for rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(429, "Rate limit exceeded. Try again later.")