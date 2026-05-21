"""Encrypt connector tokens at rest."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    secret = (
        os.environ.get("CONNECTOR_TOKEN_KEY")
        or os.environ.get("SUPABASE_JWT_SECRET")
        or os.environ.get("API_JWT_SECRET")
    )
    if not secret:
        raise RuntimeError("CONNECTOR_TOKEN_KEY or JWT secret required for token encryption")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_token(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_token(cipher: str) -> str:
    return _fernet().decrypt(cipher.encode("utf-8")).decode("utf-8")
