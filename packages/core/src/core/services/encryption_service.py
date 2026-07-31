from core.domain.entities.exceptions import ConfigurationError
from core.settings import MISSING_SECRET_KEY_MESSAGE, settings
from cryptography.fernet import Fernet


class EncryptionService:
    def __init__(self, key: str | None = None):
        # Allow key injection for testing, default to settings
        resolved = key or settings.secret_key
        if resolved is None:
            raise ConfigurationError("encryption", MISSING_SECRET_KEY_MESSAGE)
        self._fernet = Fernet(resolved.encode())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string."""
        return self._fernet.decrypt(ciphertext.encode()).decode()
