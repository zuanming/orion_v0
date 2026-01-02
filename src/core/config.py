"""Configuration loader for Orion"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Config:
    """Load and manage Orion configuration"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize config from YAML file
        
        Args:
            config_path: Path to config.yaml (relative to orion root)
        """
        # Try multiple path strategies to find config
        paths_to_try = []
        
        # 1. If absolute path provided, use it
        if Path(config_path).is_absolute():
            paths_to_try.append(Path(config_path))
        else:
            # 2. Try relative to this file's location (orion/src/core/ -> orion/)
            orion_root = Path(__file__).parent.parent.parent
            paths_to_try.append(orion_root / config_path)
            
            # 3. Try from working directory
            paths_to_try.append(Path(config_path))
            
            # 4. Try orion subdirectory from working directory
            paths_to_try.append(Path("orion") / config_path)
        
        # Find the first path that exists
        self.path = None
        for path in paths_to_try:
            if path.exists():
                self.path = path
                break
        
        if self.path is None:
            raise FileNotFoundError(
                f"Config file not found. Tried:\n" + 
                "\n".join(f"  - {p}" for p in paths_to_try)
            )
        
        self.data = {}
        self.load()
    
    def load(self):
        """Load configuration from file"""
        if not self.path.exists():
            raise FileNotFoundError(f"Config file not found: {self.path}")
        
        with open(self.path, 'r') as f:
            self.data = yaml.safe_load(f)
        
        logger.info(f"Configuration loaded from {self.path}")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation path
        
        Example:
            config.get('llm.model')  # Returns 'llama3.1'
            config.get('llm.missing', 'default_value')
        """
        keys = path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access"""
        return self.data[key]
