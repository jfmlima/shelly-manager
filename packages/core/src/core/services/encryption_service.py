from core.settings import settings
from cryptography.fernet import Fernet


class EncryptionService:
    def __init__(self, key: str | None = None):
        # Allow key injection for testing, default to settings
        key_bytes = (key or settings.secret_key).encode()
        self._fernet = Fernet(key_bytes)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string."""
        return self._fernet.decrypt(ciphertext.encode()).decode()
