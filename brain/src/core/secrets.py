import os
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Centralized secrets manager for secure access to sensitive configuration.
    Implements Fail-Fast principle by validating secrets at initialization.
    """

    def __init__(self):
        self._openai_api_key = None
        logger.info("Initializing SecretsManager...")
        self._load_secrets()
        logger.info("SecretsManager initialized successfully.")

    def _load_secrets(self):
        """
        Load secrets from environment variables with validation.
        Raises ValueError if required secrets are missing.
        """
        self._openai_api_key = os.getenv('OPENAI_API_KEY')
        if self._openai_api_key is None:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it before running the application."
            )
        logger.info("OPENAI_API_KEY loaded successfully.")

    def get_openai_api_key(self):
        """
        Get the OpenAI API key.
        Returns:
            str: The OpenAI API key
        """
        return self._openai_api_key

# Global instance for application-wide use
secrets_manager = None

def get_secrets_manager():
    global secrets_manager
    if secrets_manager is None:
        secrets_manager = SecretsManager()
    return secrets_manager