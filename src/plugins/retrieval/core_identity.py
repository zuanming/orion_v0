"""Core Identity Plugin for reading user preferences and context"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from src.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class CoreIdentityPlugin(BasePlugin):
    """Read and retrieve user identity/preferences from vault"""
    
    def __init__(self):
        """Initialize core identity plugin"""
        self.identity_file: Optional[Path] = None
        self.core_identity: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        """Plugin name"""
        return "core_identity"
    
    async def initialize(self, config: Dict[str, Any]):
        """
        Initialize core identity reader
        
        Args:
            config: Configuration dict with:
                - path: Path to vault directory
                - core_identity_file: Filename of core identity (default: _SYSTEM/core-identity.md)
        """
        try:
            vault_path = config.get('path', 'vault')
            identity_filename = config.get('core_identity_file', '_SYSTEM/core-identity.md')
            
            self.identity_file = Path(vault_path) / identity_filename
            
            # Create _SYSTEM directory if it doesn't exist
            if not self.identity_file.parent.exists():
                logger.info(f"Creating system directory: {self.identity_file.parent}")
                self.identity_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to load existing identity
            if self.identity_file.exists():
                await self._load_identity()
                logger.info(f"Loaded core identity from {self.identity_file}")
            else:
                logger.warning(f"Core identity file not found: {self.identity_file}")
                logger.info(f"Create your identity file at: {self.identity_file}")
                logger.info("See vault/_SYSTEM/core-identity.md.example for template")
                self.core_identity = {
                    'name': 'User',
                    'status': 'identity_file_not_found'
                }
        
        except Exception as e:
            logger.error(f"Failed to initialize core identity: {e}")
            raise
    
    async def process(self, message: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        CoreIdentity is read-only, doesn't process messages
        
        Args:
            message: Message text (ignored)
            metadata: Message metadata (ignored)
        
        Returns:
            None (not a storage plugin)
        """
        return None
    
    async def retrieve(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve user identity/preferences
        
        Args:
            query: Search query (not used)
            context: Context dict (not used)
        
        Returns:
            Dict with user identity information
        """
        try:
            # Reload identity to get latest changes
            if self.identity_file and self.identity_file.exists():
                await self._load_identity()
            
            # Format identity for context builder
            identity_text = self._format_identity_for_context()
            
            return {
                'core_identity': identity_text,
                'identity_source': str(self.identity_file)
            }
        
        except Exception as e:
            logger.error(f"Failed to retrieve identity: {e}")
            return None
    
    async def _load_identity(self):
        """Load and parse core identity file"""
        try:
            if not self.identity_file.exists():
                logger.warning(f"Identity file not found: {self.identity_file}")
                return
            
            # Read with UTF-8 encoding to handle special characters
            content = self.identity_file.read_text(encoding='utf-8')
            
            # Parse markdown format
            self.core_identity = self._parse_identity_markdown(content)
            
            logger.debug(f"Loaded identity with keys: {list(self.core_identity.keys())}")
        
        except Exception as e:
            logger.error(f"Failed to load identity file: {e}")
            self.core_identity = {}
    
    def _parse_identity_markdown(self, content: str) -> Dict[str, Any]:
        """
        Parse markdown identity file
        
        Expected format:
        # My Profile
        
        ## Name
        John Doe
        
        ## Location
        San Francisco
        
        ## Style
        Casual and friendly
        
        ## Interests
        - Programming
        - Writing
        - Coffee
        
        ## Preferences
        - I prefer async/await style
        - I like detailed explanations
        """
        identity = {}
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Check for section header
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    identity[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line[3:].strip().lower().replace(' ', '_')
                current_content = []
            
            elif current_section:
                current_content.append(line)
        
        # Save final section
        if current_section:
            identity[current_section] = '\n'.join(current_content).strip()
        
        return identity
    
    def _format_identity_for_context(self) -> str:
        """Format identity dictionary as readable text for LLM context"""
        if not self.core_identity:
            return "No user identity information available."
        
        # For the main markdown file, return the full structured content
        # This preserves sections, subsections, and lists
        identity_file = Path(self.identity_file)
        if identity_file.exists():
            try:
                content = identity_file.read_text(encoding='utf-8')
                return content.strip()
            except Exception:
                pass
        
        # Fallback to simple format
        lines = []
        for key, value in self.core_identity.items():
            key_title = key.replace('_', ' ').title()
            lines.append(f"**{key_title}**: {value}")
        
        return "\n".join(lines)
    
    def get_identity_summary(self) -> str:
        """Get human-readable identity summary"""
        lines = ["**Core Identity:**"]
        
        for key, value in self.core_identity.items():
            if value and not value.startswith('identity_'):
                # Truncate long values
                if len(value) > 100:
                    value = value[:100] + "..."
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        return "\n".join(lines)
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        try:
            logger.info(f"Core identity plugin shutdown. Loaded {len(self.core_identity)} fields")
        except Exception as e:
            logger.warning(f"Error during core identity shutdown: {e}")
