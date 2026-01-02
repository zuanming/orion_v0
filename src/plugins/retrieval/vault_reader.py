"""Vault Reader Plugin for reading project notes and files"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class VaultReaderPlugin(BasePlugin):
    """Read and retrieve project notes from the user's vault"""
    
    def __init__(self):
        """Initialize vault reader"""
        self.vault_path: Optional[Path] = None
        self.projects_path: Optional[Path] = None
        self.file_cache: Dict[str, str] = {}
    
    @property
    def name(self) -> str:
        """Plugin name"""
        return "vault_reader"
    
    async def initialize(self, config: Dict[str, Any]):
        """
        Initialize vault reader
        
        Args:
            config: Configuration dict with:
                - path: Path to vault directory
        """
        try:
            vault_path = config.get('path', 'vault')
            self.vault_path = Path(vault_path)
            self.projects_path = self.vault_path / 'projects'
            
            # Create vault directory structure if it doesn't exist
            if not self.vault_path.exists():
                logger.info(f"Creating vault directory: {self.vault_path}")
                self.vault_path.mkdir(parents=True, exist_ok=True)
            
            if not self.projects_path.exists():
                logger.info(f"Creating projects directory: {self.projects_path}")
                self.projects_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Initialized vault reader at {self.vault_path}")
        
        except Exception as e:
            logger.error(f"Failed to initialize vault reader: {e}")
            raise
    
    async def process(self, message: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        VaultReader is read-only, doesn't process messages
        
        Args:
            message: Message text (ignored)
            metadata: Message metadata (ignored)
        
        Returns:
            None (not a storage plugin)
        """
        return None
    
    async def retrieve(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search vault for relevant project files
        
        Args:
            query: Search query text
            context: Context dict (may contain search_limit)
        
        Returns:
            Dict with matching vault files
        """
        try:
            if not self.projects_path.exists():
                logger.debug("Projects path doesn't exist")
                return None
            
            # Search for matching files
            matching_files = await self._search_vault(query)
            
            if not matching_files:
                logger.debug(f"No vault files match query: {query}")
                return None
            
            # Format for context builder
            vault_results = []
            for file_info in matching_files:
                vault_results.append({
                    'file': file_info['file'],
                    'content': file_info['excerpt'],
                    'path': file_info['path']
                })
            
            logger.debug(f"Found {len(vault_results)} vault files matching query")
            
            return {
                'vault_results': vault_results
            }
        
        except Exception as e:
            logger.error(f"Vault search failed: {e}")
            return None
    
    async def _search_vault(self, query: str) -> List[Dict[str, Any]]:
        """
        Search vault files for query terms
        
        Args:
            query: Search query
        
        Returns:
            List of matching files with excerpts
        """
        try:
            matching = []
            query_lower = query.lower()
            
            # Get all markdown files
            if not self.projects_path.exists():
                return matching
            
            md_files = list(self.projects_path.glob('*.md'))
            
            for file_path in md_files[:10]:  # Limit to first 10 files
                try:
                    content = file_path.read_text()
                    
                    # Simple keyword matching
                    if query_lower in content.lower():
                        # Get excerpt (first 200 chars or next sentence)
                        lines = content.split('\n')
                        excerpt = '\n'.join(lines[:5])  # First 5 lines
                        
                        matching.append({
                            'file': file_path.name,
                            'path': f"vault/projects/{file_path.name}",
                            'excerpt': excerpt[:300],
                            'relevance': content.lower().count(query_lower)
                        })
                
                except Exception as e:
                    logger.warning(f"Error reading vault file {file_path}: {e}")
                    continue
            
            # Sort by relevance (highest first)
            matching.sort(key=lambda x: x['relevance'], reverse=True)
            
            return matching[:5]  # Return top 5 results
        
        except Exception as e:
            logger.error(f"Error searching vault: {e}")
            return []
    
    async def get_vault_structure(self) -> Dict[str, Any]:
        """Get overview of vault structure"""
        try:
            if not self.vault_path.exists():
                return {'status': 'vault_not_found'}
            
            # Count files
            all_files = list(self.vault_path.glob('**/*.md'))
            project_files = list(self.projects_path.glob('*.md')) if self.projects_path.exists() else []
            
            return {
                'total_files': len(all_files),
                'project_files': len(project_files),
                'vault_path': str(self.vault_path),
                'projects': [f.name for f in project_files[:10]]
            }
        
        except Exception as e:
            logger.error(f"Failed to get vault structure: {e}")
            return {}
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        try:
            vault_info = await self.get_vault_structure()
            logger.info(f"Vault reader shutdown. Vault info: {vault_info}")
        except Exception as e:
            logger.warning(f"Error during vault reader shutdown: {e}")
