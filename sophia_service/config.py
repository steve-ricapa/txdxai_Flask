import os
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SophiaConfig:
    """Configuration for SOPHIA service"""
    
    BACKEND_URL: str = os.getenv('BACKEND_URL', 'http://localhost:5000/api')
    
    AZURE_OPENAI_ENDPOINT: str = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    AZURE_OPENAI_KEY: str = os.getenv('AZURE_OPENAI_KEY', '')
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o')
    
    AZURE_SEARCH_ENDPOINT: str = os.getenv('AZURE_SEARCH_ENDPOINT', '')
    AZURE_SEARCH_KEY: str = os.getenv('AZURE_SEARCH_KEY', '')
    
    SOPHIA_PORT: int = int(os.getenv('SOPHIA_PORT', '8000'))
    SOPHIA_HOST: str = os.getenv('SOPHIA_HOST', '0.0.0.0')
    
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')
    
    CACHE_TTL_SECONDS: int = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    
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
    
    @classmethod
    def is_azure_configured(cls) -> bool:
        """Check if Azure AI is configured"""
        return bool(cls.AZURE_OPENAI_ENDPOINT and cls.AZURE_OPENAI_KEY)
    
    @classmethod
    def get_info(cls) -> Dict:
        """Get configuration info (without sensitive data)"""
        return {
            'debug': cls.DEBUG,
            'backend_url': cls.BACKEND_URL,
            'azure_configured': cls.is_azure_configured(),
            'cache_ttl': cls.CACHE_TTL_SECONDS,
            'has_search': bool(cls.AZURE_SEARCH_ENDPOINT)
        }


class ConfigCache:
    """Cache for agent configurations"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, datetime] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, company_id: int) -> Optional[Dict]:
        """Get cached config for company"""
        key = f"company-{company_id}"
        
        if key not in self._cache:
            return None
        
        if key in self._timestamps:
            age = datetime.utcnow() - self._timestamps[key]
            if age > self.ttl:
                logger.info(f"Cache expired for company {company_id}")
                self.invalidate(company_id)
                return None
        
        return self._cache.get(key)
    
    def set(self, company_id: int, config: Dict):
        """Set cached config for company"""
        key = f"company-{company_id}"
        self._cache[key] = config
        self._timestamps[key] = datetime.utcnow()
        logger.info(f"Cached config for company {company_id}")
    
    def invalidate(self, company_id: int):
        """Invalidate cache for company"""
        key = f"company-{company_id}"
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
        logger.info(f"Invalidated cache for company {company_id}")
    
    def invalidate_all(self):
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("Invalidated all cache")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'total_entries': len(self._cache),
            'ttl_seconds': self.ttl.total_seconds(),
            'companies': list(self._cache.keys())
        }


config = SophiaConfig()
config_cache = ConfigCache(ttl_seconds=config.CACHE_TTL_SECONDS)
