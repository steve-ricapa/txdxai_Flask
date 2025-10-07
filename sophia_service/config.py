import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class SophiaConfig:
    """Configuration for SOPHIA service"""
    
    BACKEND_URL: str = os.getenv('BACKEND_URL', 'http://localhost:5000/api')
    
    AZURE_OPENAI_ENDPOINT: str = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    AZURE_OPENAI_KEY: str = os.getenv('AZURE_OPENAI_KEY', '')
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
    
    AZURE_SEARCH_ENDPOINT: str = os.getenv('AZURE_SEARCH_ENDPOINT', '')
    AZURE_SEARCH_KEY: str = os.getenv('AZURE_SEARCH_KEY', '')
    
    SOPHIA_PORT: int = int(os.getenv('SOPHIA_PORT', '5001'))
    SOPHIA_HOST: str = os.getenv('SOPHIA_HOST', '0.0.0.0')
    
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = []
        
        if not cls.AZURE_OPENAI_ENDPOINT:
            required.append('AZURE_OPENAI_ENDPOINT')
        if not cls.AZURE_OPENAI_KEY:
            required.append('AZURE_OPENAI_KEY')
            
        if required:
            print(f"⚠️  Missing required config: {', '.join(required)}")
            print("SOPHIA will run in limited mode without Azure AI capabilities")
            return False
        
        return True

config = SophiaConfig()
