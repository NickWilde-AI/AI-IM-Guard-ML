from __future__ import annotations

from dataclasses import dataclass


ROLE_PERMISSIONS = {
    "admin": {"read", "write", "audit", "config"},
    "writer": {"write"},
    "reader": {"read", "config"},
    "auditor": {"read", "audit"},
}


@dataclass(frozen=True)
class AuthConfig:
    token_roles: dict[str, str]

    @property
    def enabled(self) -> bool:
        return bool(self.token_roles)

    def role_for_token(self, token: str) -> str | None:
        return self.token_roles.get(token)

    def allows(self, role: str | None, permission: str) -> bool:
        if role is None:
            return not self.enabled
        return permission in ROLE_PERMISSIONS.get(role, set())


def parse_auth_config(single_token: str = "", token_spec: str = "") -> AuthConfig:
    token_roles: dict[str, str] = {}
    if single_token:
        token_roles[single_token] = "admin"
    for item in token_spec.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            token, role = item.split(":", 1)
        else:
            token, role = item, "admin"
        token = token.strip()
        role = role.strip() or "admin"
        if token:
            token_roles[token] = role
    return AuthConfig(token_roles)
