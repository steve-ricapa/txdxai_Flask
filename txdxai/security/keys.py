import secrets
import string
import bcrypt

def generate_access_key(length=40):
    """
    Generate a cryptographically secure random access key.
    
    Args:
        length: Length of the key (default 40 characters)
    
    Returns:
        A random alphanumeric string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_access_key(access_key):
    """
    Hash an access key using bcrypt.
    
    Args:
        access_key: The plain text access key
    
    Returns:
        The bcrypt hashed key as a string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(access_key.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_access_key(access_key, hashed_key):
    """
    Verify an access key against its hash.
    
    Args:
        access_key: The plain text access key to verify
        hashed_key: The stored bcrypt hash
    
    Returns:
        True if the key matches, False otherwise
    """
    return bcrypt.checkpw(access_key.encode('utf-8'), hashed_key.encode('utf-8'))
