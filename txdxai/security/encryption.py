import os
from cryptography.fernet import Fernet
from typing import Optional

def get_encryption_key() -> bytes:
    """
    Get encryption key for agent access keys from environment variable.
    
    CRITICAL: This key MUST be set in production and persist across restarts.
    Without a persistent key, encrypted values become unreadable after restarts.
    
    For production: Store AGENT_KEY_ENCRYPTION_KEY in Azure Key Vault or as
    a persistent environment variable.
    
    For local development: Generate once with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
    and set the result in your .env file.
    """
    key = os.environ.get('AGENT_KEY_ENCRYPTION_KEY')
    
    if not key:
        raise ValueError(
            "AGENT_KEY_ENCRYPTION_KEY environment variable is required. "
            "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    return key


def encrypt_agent_key(plain_key: str) -> str:
    """
    Encrypt agent access key for storage in database.
    
    Args:
        plain_key: The plain text agent access key
        
    Returns:
        Encrypted key as base64 string
    """
    encryption_key = get_encryption_key()
    fernet = Fernet(encryption_key)
    encrypted = fernet.encrypt(plain_key.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_agent_key(encrypted_key: str) -> Optional[str]:
    """
    Decrypt agent access key from database.
    
    Args:
        encrypted_key: The encrypted agent access key
        
    Returns:
        Decrypted plain text key, or None if decryption fails
    """
    try:
        encryption_key = get_encryption_key()
        fernet = Fernet(encryption_key)
        decrypted = fernet.decrypt(encrypted_key.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception:
        return None
