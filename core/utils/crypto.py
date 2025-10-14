import os
from cryptography.fernet import Fernet
from django.conf import settings

# Clave única en settings.SECRET_KEY (o .env)
def get_cipher():
    key = getattr(settings, "FERNET_KEY", None)
    if not key:
        key = Fernet.generate_key()
        print("⚠️ FERNET_KEY no encontrada. Generada temporalmente:", key.decode())
    return Fernet(key)

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
