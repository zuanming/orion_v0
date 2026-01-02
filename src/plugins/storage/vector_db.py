"""Vector Database Plugin for storing message embeddings"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("Qdrant or sentence-transformers not installed")

from src.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class VectorDBPlugin(BasePlugin):
    """Store and retrieve message embeddings using Qdrant vector database"""
    
    def __init__(self):
        """Initialize vector DB plugin"""
        self.client: Optional[QdrantClient] = None
        self.embedder: Optional[SentenceTransformer] = None
        self.collection_name: str = "conversations"
        self.vector_size: int = 384  # all-MiniLM-L6-v2 dimension
        self.db_path: str = "data/vector_db"
        self._message_counter = 0
    
    @property
    def name(self) -> str:
        """Plugin name"""
        return "vector_db"
    
    async def initialize(self, config: Dict[str, Any]):
        """
        Initialize vector database and embedding model
        
        Args:
            config: Configuration dict with:
                - path: Path to vector DB
                - collection: Collection name
        """
        if not QDRANT_AVAILABLE:
            logger.error("Qdrant or sentence-transformers not installed")
            return
        
        try:
            self.db_path = config.get('path', 'data/vector_db')
            self.collection_name = config.get('collection', 'conversations')
            
            # Create DB directory
            Path(self.db_path).mkdir(parents=True, exist_ok=True)
            
            # Initialize Qdrant client
            self.client = QdrantClient(path=self.db_path)
            logger.info(f"Initialized Qdrant at {self.db_path}")
            
            # Initialize embedding model
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
            
            # Create collection if it doesn't exist
            try:
                self.client.get_collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created new collection: {self.collection_name}")
        
        except Exception as e:
            logger.error(f"Failed to initialize vector DB: {e}")
            raise
    
    async def process(self, message: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Store message embedding in vector database
        
        Args:
            message: Message text to embed and store
            metadata: Message metadata (timestamp, user_id, message_type)
        
        Returns:
            Dict with storage info or None
        """
        if not self.client or not self.embedder:
            logger.warning("Vector DB not initialized")
            return None
        
        try:
            # Generate embedding
            embedding = self.embedder.encode(message)
            
            # Create point ID (incremental)
            self._message_counter += 1
            point_id = self._message_counter
            
            # Add metadata timestamp if missing
            if 'timestamp' not in metadata:
                metadata['timestamp'] = datetime.now().isoformat()
            
            # Store point with embedding and payload
            point = PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    'message': message[:500],  # Store first 500 chars
                    'timestamp': metadata.get('timestamp'),
                    'user_id': metadata.get('user_id', 'unknown'),
                    'message_type': metadata.get('message_type', 'unknown'),
                    'full_message_hash': hash(message) % (10**9)  # For deduplication
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Stored message embedding: ID={point_id}, len={len(message)}")
            
            return {
                'stored': True,
                'point_id': point_id,
                'embedding_dim': len(embedding)
            }
        
        except Exception as e:
            logger.error(f"Failed to store message embedding: {e}")
            return None
    
    async def retrieve(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search vector database for similar messages
        
        Args:
            query: Search query text
            context: Context dict (may contain search_limit)
        
        Returns:
            Dict with search results
        """
        if not self.client or not self.embedder:
            logger.warning("Vector DB not initialized")
            return None
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(query)
            
            # Search for similar messages
            search_limit = context.get('search_limit', 5)
            
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=search_limit,
                score_threshold=0.3  # Min similarity threshold
            )
            
            # Format results
            results = []
            for scored_point in search_results:
                results.append({
                    'id': scored_point.id,
                    'score': scored_point.score,
                    'message': scored_point.payload.get('message', ''),
                    'timestamp': scored_point.payload.get('timestamp'),
                    'user_id': scored_point.payload.get('user_id'),
                    'message_type': scored_point.payload.get('message_type')
                })
            
            logger.debug(f"Vector search returned {len(results)} results for query")
            
            return {
                'query': query,
                'results': results,
                'count': len(results)
            }
        
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return None
    
    def get_collection_stats(self) -> Optional[Dict[str, Any]]:
        """Get collection statistics"""
        if not self.client:
            return None
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                'collection_name': self.collection_name,
                'points_count': collection_info.points_count,
                'vector_size': self.vector_size,
                'distance': 'cosine'
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return None
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        if self.client:
            try:
                # Get stats before closing
                stats = self.get_collection_stats()
                if stats:
                    logger.info(f"Vector DB shutdown. Points stored: {stats['points_count']}")
                self.client.close()
            except Exception as e:
                logger.warning(f"Error during vector DB shutdown: {e}")
