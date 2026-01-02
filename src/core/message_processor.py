"""Main message processing pipeline with enhancements"""

import logging
from datetime import datetime
from typing import Dict, Any

from src.core.plugin_manager import PluginManager
from src.core.context_builder import ContextBuilder
from src.core.response_enhancer import (
    ResponseEnhancer, 
    ConflictDetector, 
    ErrorAcknowledger
)

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Core message processing pipeline with enhancements:
    - Automatic storage to vector DB
    - Context retrieval from multiple sources
    - Response generation with Ollama
    - Response enhancement (uncertainty, sources, error handling)
    """
    
    def __init__(self, plugin_manager: PluginManager, 
                 context_builder: ContextBuilder,
                 llm_client):
        """
        Initialize message processor
        
        Args:
            plugin_manager: Plugin manager for storage/retrieval
            context_builder: Context builder for prompts
            llm_client: LLM client (Ollama)
        """
        self.plugins = plugin_manager
        self.context_builder = context_builder
        self.llm = llm_client
        
        # Enhancement tools
        self.enhancer = ResponseEnhancer()
        self.conflict_detector = ConflictDetector()
        self.error_acknowledger = ErrorAcknowledger()
    
    async def process_message(self, message: str, user_id: str = None) -> str:
        """
        Process incoming message and generate enhanced response
        
        Args:
            message: User message
            user_id: User identifier
        
        Returns:
            Enhanced response with sources and uncertainty markers
        """
        logger.info(f"Processing message: {message[:50]}...")
        
        # Check if this is a correction
        correction_prefix = ""
        if self.error_acknowledger.is_correction(message):
            correction_prefix = self.error_acknowledger.get_acknowledgment()
            logger.info("Detected user correction")
        
        # Prepare metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'message_type': 'user'
        }
        
        # Run processing plugins (store message, extract info)
        await self.plugins.process_message(message, metadata)
        
        # Build context from retrieval plugins
        base_context = {'query': message}
        context = await self.plugins.build_context(message, base_context)
        
        # Build system prompt
        system_prompt = self.context_builder.build_system_prompt(context)
        
        # Generate response with sources
        try:
            response_text, sources = await self.llm.generate_response(
                system_prompt=system_prompt,
                user_message=message
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I encountered an error processing your message. Please try again."
        
        # Enhance response with uncertainty + sources
        enhanced_response = self.enhancer.enhance_response(
            response=response_text,
            sources=sources,
            query=message
        )
        
        # Add correction prefix if needed
        if correction_prefix:
            enhanced_response = correction_prefix + enhanced_response
        
        # Store assistant response
        response_metadata = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'message_type': 'assistant'
        }
        await self.plugins.process_message(enhanced_response, response_metadata)
        
        logger.info(f"Generated enhanced response: {enhanced_response[:50]}...")
        
        return enhanced_response
