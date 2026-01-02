"""Context builder for system prompts"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build system prompts from context"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize context builder
        
        Args:
            config: Configuration with max_tokens, etc.
        """
        self.max_tokens = config.get('max_tokens', 4000)
        self.search_results = config.get('search_results', 5)
    
    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build system prompt from context
        
        Args:
            context: Context dict from plugins with:
                - query: The user query
                - core_identity: User preferences/identity
                - recent_messages: Last N messages
                - vault_results: Relevant vault files
                - vector_results: Semantic search results
        
        Returns:
            System prompt string
        """
        
        prompt_parts = []
        
        # Base system message
        prompt_parts.append("You are Orion, a personal cognitive augmentation assistant.")
        prompt_parts.append("You are helpful, honest, and direct.")
        prompt_parts.append("Current time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        prompt_parts.append("")
        
        # Add core identity if available
        if 'core_identity' in context and context['core_identity']:
            prompt_parts.append("## CORE IDENTITY")
            prompt_parts.append(context['core_identity'])
            prompt_parts.append("")
        
        # Add recent conversation if available
        if 'recent_messages' in context and context['recent_messages']:
            prompt_parts.append("## RECENT CONVERSATION")
            for msg in context['recent_messages'][-5:]:  # Last 5 messages
                role = msg.get('role', 'user').upper()
                content = msg.get('content', '')
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")
        
        # Add vault results if available
        if 'vault_results' in context and context['vault_results']:
            prompt_parts.append("## ACTIVE PROJECTS & NOTES")
            for result in context['vault_results'][:3]:  # Top 3 results
                prompt_parts.append(f"### {result.get('file', 'Unknown')}")
                prompt_parts.append(result.get('content', '')[:500])  # First 500 chars
                prompt_parts.append("")
        
        # Add vector search results if available
        if 'vector_results' in context and context['vector_results']:
            prompt_parts.append("## RELEVANT PAST CONTEXT")
            for result in context['vector_results'][:3]:  # Top 3 results
                prompt_parts.append(f"- {result.get('text', '')[:200]}")
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)
