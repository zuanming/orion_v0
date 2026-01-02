"""Ollama LLM Client for local LLM inference"""

import ollama
import logging
import re
import os
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Source of information used in response"""
    type: str  # 'core', 'conversation', 'vault'
    name: str = ""
    file: str = ""
    days_ago: int = 0


class OllamaClient:
    """
    Local LLM client using Ollama for privacy and cost efficiency
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Ollama client
        
        Args:
            config: Configuration dict with:
                - model: Model name (e.g., 'gemma3:12b')
                - temperature: Response temperature (0.0-1.0)
                - base_url: Ollama API URL
        """
        # Use config if provided, otherwise use environment variables
        if config is None:
            config = {}
        
        self.model = config.get('model') or os.getenv('LLM_MODEL', 'gemma3:12b')
        self.temperature = config.get('temperature', 0.7)
        self.base_url = config.get('base_url') or os.getenv('LLM_API_URL', 'http://127.0.0.1:11434')
        
        # Set Ollama host from environment if provided
        if 'LLM_API_URL' in os.environ:
            ollama.host = self.base_url
        
        logger.info(f"Initialized Ollama client")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  API URL: {self.base_url}")
        logger.info(f"  Temperature: {self.temperature}")

    
    async def generate_response(self, system_prompt: str, 
                               user_message: str) -> Tuple[str, List[Source]]:
        """
        Generate response using Ollama
        
        Args:
            system_prompt: System context and instructions
            user_message: Current user message
        
        Returns:
            (response_text, sources_used)
        """
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                options={
                    'temperature': self.temperature
                }
            )
            
            response_text = response['message']['content']
            
            # Extract sources from system prompt
            sources = self._extract_sources_from_prompt(system_prompt)
            
            logger.debug(f"Generated response: {len(response_text)} chars")
            
            return response_text, sources
        
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def _extract_sources_from_prompt(self, prompt: str) -> List[Source]:
        """
        Extract what sources were included in the prompt
        """
        sources = []
        
        # Check for core identity
        if 'CORE IDENTITY' in prompt or 'core-identity.md' in prompt:
            sources.append(Source(type='core', name='preferences'))
        
        # Check for conversation buffer
        if 'RECENT CONVERSATION' in prompt:
            sources.append(Source(type='conversation', days_ago=0))
        
        # Check for past context
        if 'RELEVANT PAST CONTEXT' in prompt:
            # Simple heuristic: assume recent if in past context
            sources.append(Source(type='conversation', days_ago=7))
        
        # Check for vault files
        if 'ACTIVE PROJECTS' in prompt:
            files = re.findall(r'## ([^\n]+\.md)', prompt)
            for file in files:
                sources.append(Source(type='vault', file=file))
        
        return sources
