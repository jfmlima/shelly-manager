from core.domain.entities.exceptions import ConfigurationError
from core.settings import (
    INVALID_SECRET_KEY_MESSAGE,
    MISSING_SECRET_KEY_MESSAGE,
    settings,
)
from cryptography.fernet import Fernet


class EncryptionService:
    def __init__(self, key: str | None = None):
        # Allow key injection for testing, default to settings
        resolved = settings.secret_key if key is None else key
        if not resolved:
            raise ConfigurationError("encryption", MISSING_SECRET_KEY_MESSAGE)
        try:
            self._fernet = Fernet(resolved.encode())
        except Exception as e:
            raise ConfigurationError(
                "encryption", f"{INVALID_SECRET_KEY_MESSAGE} {e}"
            ) from e

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string."""
        return self._fernet.decrypt(ciphertext.encode()).decode()
