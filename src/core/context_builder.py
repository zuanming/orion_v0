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

        # Markdown formatting instructions for Telegram
        prompt_parts.append("=== FORMATTING INSTRUCTIONS ===")
        prompt_parts.append("You are communicating via Telegram. Use Telegram's markdown format:")
        prompt_parts.append("- Use *single asterisks* for **bold** text")
        prompt_parts.append("- Use _single underscores_ for _italic_ text")
        prompt_parts.append("- Use `backticks` for `inline code`")
        prompt_parts.append("- Use ```code blocks``` for code (no language tag needed)")
        prompt_parts.append("- Use • (bullet) for lists, not - dashes")
        prompt_parts.append("- Do NOT use ## or ### for headers (just use *bold* for emphasis)")
        prompt_parts.append("- Do NOT use **double asterisks** or __double underscores__")
        prompt_parts.append("=== END FORMATTING INSTRUCTIONS ===")
        prompt_parts.append("")

        # CRITICAL: Instructions about user identity
        prompt_parts.append("=== CRITICAL INSTRUCTIONS ===")
        prompt_parts.append("You have access to detailed information about the USER in the 'USER IDENTITY' section below.")
        prompt_parts.append("When the user asks 'Who am I?', 'tell me about myself', or similar, use that information to describe the USER.")
        prompt_parts.append("The identity information contains the user's background, preferences, values, and work style.")
        prompt_parts.append("=== END CRITICAL INSTRUCTIONS ===")
        prompt_parts.append("")
        
        # CRITICAL: Instructions about user identity
        prompt_parts.append("=== CRITICAL INSTRUCTIONS ===")
        prompt_parts.append("You have access to detailed information about the USER in the 'USER IDENTITY' section below.")
        prompt_parts.append("When user asks 'Who am I?', 'tell me about myself', or similar, use that information to describe the USER.")
        prompt_parts.append("The identity information contains the user's background, preferences, values, and work style.")
        prompt_parts.append("=== END CRITICAL INSTRUCTIONS ===")
        prompt_parts.append("")
        
        # Add core identity if available
        if 'core_identity' in context and context['core_identity']:
            prompt_parts.append("## USER IDENTITY & PREFERENCES")
            prompt_parts.append("The following information is about the USER (the person you are assisting), NOT about you (Orion).")
            prompt_parts.append("")
            prompt_parts.append(context['core_identity'])
            prompt_parts.append("")
            prompt_parts.append("IMPORTANT: When user asks 'Who am I?', 'Who am I', or similar questions, use the information above to describe the USER.")
            prompt_parts.append("")
            prompt_parts.append("IMPORTANT: Use this information to understand who the user is, their preferences, work style, and how they prefer to interact.")
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
