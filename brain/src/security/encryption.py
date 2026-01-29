import os
from typing import Optional

from cryptography.fernet import Fernet

from core.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data using Fernet."""

    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            key: Base64-encoded Fernet key. If None, uses from settings or generates new.
        """
        if key:
            self.key = key
        elif settings.ENCRYPTION_KEY:
            self.key = settings.ENCRYPTION_KEY
        else:
            # Generate a new key if none provided (for development)
            self.key = Fernet.generate_key().decode()

        self.fernet = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            str: Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        encrypted = self.fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            str: Decrypted plaintext

        Raises:
            ValueError: If decryption fails
        """
        if not encrypted_text:
            return ""
        try:
            decrypted = self.fernet.decrypt(encrypted_text.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def is_encrypted(self, text: str) -> bool:
        """
        Check if text appears to be encrypted (basic heuristic).

        Args:
            text: Text to check

        Returns:
            bool: True if text appears encrypted
        """
        if not text:
            return False
        try:
            self.fernet.decrypt(text.encode())
            return True
        except:
            return False


# Global encryption service instance
encryption_service = EncryptionService()