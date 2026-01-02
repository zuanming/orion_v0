"""Vector Search Plugin for semantic search through conversation history"""

import logging
from typing import Dict, Any, Optional

from src.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class VectorSearchPlugin(BasePlugin):
    """Semantic search through past messages using vector DB"""
    
    def __init__(self):
        """Initialize vector search plugin"""
        self.vector_db_plugin = None
        self.search_limit: int = 5
    
    @property
    def name(self) -> str:
        """Plugin name"""
        return "vector_search"
    
    async def initialize(self, config: Dict[str, Any]):
        """
        Initialize vector search
        
        Args:
            config: Configuration dict with:
                - vector_db_plugin: Reference to VectorDBPlugin instance
                - search_limit: Max results to return (default 5)
        """
        try:
            self.vector_db_plugin = config.get('vector_db_plugin')
            self.search_limit = config.get('search_limit', 5)
            
            if not self.vector_db_plugin:
                logger.warning("Vector DB plugin not provided to VectorSearchPlugin")
            
            logger.info(f"Initialized vector search (limit={self.search_limit})")
        
        except Exception as e:
            logger.error(f"Failed to initialize vector search: {e}")
            raise
    
    async def process(self, message: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        VectorSearch is read-only, doesn't process messages
        
        Args:
            message: Message text (ignored)
            metadata: Message metadata (ignored)
        
        Returns:
            None (not a storage plugin)
        """
        return None
    
    async def retrieve(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search for semantically similar past messages
        
        Args:
            query: Search query text
            context: Context dict (may contain search_limit override)
        
        Returns:
            Dict with search results
        """
        try:
            if not self.vector_db_plugin:
                logger.warning("Vector DB plugin not available")
                return None
            
            # Use context override or default
            search_limit = context.get('search_limit', self.search_limit)
            
            # Call vector DB plugin's retrieve
            search_context = {'search_limit': search_limit}
            db_results = await self.vector_db_plugin.retrieve(query, search_context)
            
            if not db_results or 'results' not in db_results:
                logger.debug("No vector search results found")
                return None
            
            # Format results
            formatted_results = []
            for result in db_results['results']:
                formatted_results.append({
                    'message': result['message'],
                    'similarity': result['score'],
                    'timestamp': result['timestamp'],
                    'type': result['message_type']
                })
            
            logger.debug(f"Vector search found {len(formatted_results)} similar messages")
            
            return {
                'type': 'vector_search_results',
                'query': query,
                'results': formatted_results,
                'count': len(formatted_results)
            }
        
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return None
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        try:
            logger.info("Vector search plugin shutdown")
        except Exception as e:
            logger.warning(f"Error during vector search shutdown: {e}")
