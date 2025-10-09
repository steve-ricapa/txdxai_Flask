import os
from cryptography.fernet import Fernet
from typing import Optional

def get_encryption_key() -> bytes:
    """
    Get or generate encryption key for agent access keys.
    In production, this should come from environment variable or Azure Key Vault.
    """
    key = os.environ.get('AGENT_KEY_ENCRYPTION_KEY')
    
    if not key:
        key = Fernet.generate_key().decode('utf-8')
        os.environ['AGENT_KEY_ENCRYPTION_KEY'] = key
    
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
