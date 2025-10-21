# core/utils/crypto.py
import logging
from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)

def get_cipher():
    key = getattr(settings, "FERNET_KEY", None)
    if not key:
        # no mostramos datos sensibles, solo log
        logger.error("FERNET_KEY no configurada en settings")
        raise RuntimeError("FERNET_KEY no configurada")
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_field(value: str) -> str:
    if not value:
        return None
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def decrypt_field(token: str) -> str:
    if not token:
        return None
    cipher = get_cipher()
    return cipher.decrypt(token.encode()).decode()
