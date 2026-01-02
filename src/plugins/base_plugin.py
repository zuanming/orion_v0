"""Base plugin interface for Orion"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all Orion plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier"""
        pass
    
    @property
    def enabled(self) -> bool:
        """Whether plugin is enabled"""
        return True
    
    async def initialize(self, config: Dict[str, Any]):
        """
        Initialize plugin with configuration
        
        Args:
            config: Plugin-specific configuration dict
        """
        logger.info(f"Initializing plugin: {self.name}")
    
    async def process(self, message: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming message (storage plugins)
        
        Args:
            message: Message text
            metadata: Message metadata (timestamp, user_id, role, etc.)
        
        Returns:
            Processing result or None
        """
        return None
    
    async def retrieve(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve relevant information for context (retrieval plugins)
        
        Args:
            query: User query or search term
            context: Current context (previous messages, metadata, etc.)
        
        Returns:
            Retrieved information or None
        """
        return None
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        logger.info(f"Shutting down plugin: {self.name}")
