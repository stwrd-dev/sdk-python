"""stwrd — Python SDK for the stwrd identity provider (BFF profile).

Installed as `stwrd-auth`, imported as `stwrd`.
"""

from __future__ import annotations

from .client import ConfigError, Stwrd, connect_to_hook
from .config import StwrdConfig
from .management import ApiResult, ManagementError, ManagementOptions, WriteOptions
from .management_generated import ManagementClient, create_management
from .oidc import IdpUnavailable, OidcError, RefreshUncertain
from .sessions import MemoryStore, SessionStore, StwrdOrganization, StwrdSession, StwrdUser, Tokens
from .webhooks import (
    DuplicateEventError,
    InvalidSignatureError,
    WebhookEvent,
    safe_equal,
    verify_webhook,
    verify_webhook_signature,
)

__all__ = [
    "ApiResult",
    "ManagementClient",
    "ManagementError",
    "ManagementOptions",
    "WriteOptions",
    "create_management",
    "connect_to_hook",
    "ConfigError",
    "DuplicateEventError",
    "IdpUnavailable",
    "InvalidSignatureError",
    "MemoryStore",
    "OidcError",
    "RefreshUncertain",
    "SessionStore",
    "Stwrd",
    "StwrdConfig",
    "StwrdOrganization",
    "StwrdSession",
    "StwrdUser",
    "Tokens",
    "WebhookEvent",
    "safe_equal",
    "verify_webhook",
    "verify_webhook_signature",
]
