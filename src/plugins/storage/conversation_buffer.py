"""Conversation Buffer Plugin for maintaining recent message history"""

import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from collections import deque

from src.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class ConversationBufferPlugin(BasePlugin):
    """
    Maintain a buffer of recent messages for context awareness
    Stores last N messages in memory and persists to disk
    """
    
    def __init__(self):
        """Initialize conversation buffer"""
        self.messages: deque = deque(maxlen=20)  # Keep last 20 messages
        self.buffer_file: Optional[Path] = None
        self.max_size: int = 20
    
    @property
    def name(self) -> str:
        """Plugin name"""
        return "conversation_buffer"
    
    async def initialize(self, config: Dict[str, Any]):
        """
        Initialize conversation buffer
        
        Args:
            config: Configuration dict with:
                - size: Max messages to keep (default 20)
                - path: Path to persist buffer (optional)
        """
        try:
            self.max_size = config.get('size', 20)
            self.messages = deque(maxlen=self.max_size)
            
            # Optional: specify storage path for persistence
            storage_path = config.get('path', 'data/buffer')
            if storage_path:
                self.buffer_file = Path(storage_path) / 'conversation_buffer.json'
                self.buffer_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Load existing buffer if available
                if self.buffer_file.exists():
                    await self._load_buffer()
            
            logger.info(f"Initialized conversation buffer (max_size={self.max_size})")
        
        except Exception as e:
            logger.error(f"Failed to initialize conversation buffer: {e}")
            raise
    
    async def process(self, message: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add message to buffer
        
        Args:
            message: Message text
            metadata: Message metadata (timestamp, user_id, message_type)
        
        Returns:
            Dict with buffer info or None
        """
        try:
            # Ensure timestamp
            if 'timestamp' not in metadata:
                metadata['timestamp'] = datetime.now().isoformat()
            
            # Create message entry
            message_entry = {
                'message': message,
                'timestamp': metadata['timestamp'],
                'user_id': metadata.get('user_id', 'unknown'),
                'message_type': metadata.get('message_type', 'unknown')
            }
            
            # Add to buffer
            self.messages.append(message_entry)
            
            logger.debug(f"Added to buffer. Current size: {len(self.messages)}/{self.max_size}")
            
            # Persist if configured
            if self.buffer_file:
                await self._save_buffer()
            
            return {
                'buffered': True,
                'buffer_size': len(self.messages),
                'max_size': self.max_size
            }
        
        except Exception as e:
            logger.error(f"Failed to add message to buffer: {e}")
            return None
    
    async def retrieve(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve recent messages from buffer
        
        Args:
            query: Not used for buffer retrieval
            context: Context dict (may contain 'count' for how many messages)
        
        Returns:
            Dict with recent messages
        """
        try:
            count = context.get('count', 5)
            
            # Get most recent N messages
            recent = list(self.messages)[-count:] if self.messages else []
            
            # Convert to format expected by ContextBuilder
            recent_messages = []
            for msg in recent:
                recent_messages.append({
                    'role': 'user' if msg.get('message_type') == 'user' else 'assistant',
                    'content': msg.get('message', ''),
                    'timestamp': msg.get('timestamp')
                })
            
            logger.debug(f"Retrieved {len(recent_messages)} recent messages from buffer")
            
            return {
                'recent_messages': recent_messages,
                'total_buffered': len(self.messages)
            }
        
        except Exception as e:
            logger.error(f"Failed to retrieve from buffer: {e}")
            return None
    
    async def _save_buffer(self):
        """Persist buffer to disk"""
        if not self.buffer_file:
            return
        
        try:
            buffer_data = {
                'messages': list(self.messages),
                'count': len(self.messages),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.buffer_file, 'w') as f:
                json.dump(buffer_data, f, indent=2)
            
            logger.debug(f"Saved buffer to {self.buffer_file}")
        
        except Exception as e:
            logger.error(f"Failed to save buffer: {e}")
    
    async def _load_buffer(self):
        """Load buffer from disk"""
        if not self.buffer_file or not self.buffer_file.exists():
            return
        
        try:
            with open(self.buffer_file, 'r') as f:
                buffer_data = json.load(f)
            
            messages = buffer_data.get('messages', [])
            
            # Add messages back to buffer
            for msg in messages[-self.max_size:]:  # Only keep max_size
                self.messages.append(msg)
            
            logger.info(f"Loaded {len(self.messages)} messages from buffer file")
        
        except Exception as e:
            logger.error(f"Failed to load buffer: {e}")
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        return {
            'current_size': len(self.messages),
            'max_size': self.max_size,
            'utilization': f"{len(self.messages) / self.max_size * 100:.1f}%",
            'persisted': self.buffer_file is not None
        }
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        try:
            # Save buffer one last time
            if self.buffer_file:
                await self._save_buffer()
            
            stats = self.get_buffer_stats()
            logger.info(f"Buffer shutdown. Stats: {stats}")
        
        except Exception as e:
            logger.warning(f"Error during buffer shutdown: {e}")
