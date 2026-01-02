"""Plugin manager for Orion"""

import logging
from typing import Dict, Any, List
from src.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """Manage plugin lifecycle and execution"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.config_map: Dict[str, Dict[str, Any]] = {}
    
    async def register(self, plugin: BasePlugin, config: Dict[str, Any]):
        """
        Register and initialize a plugin
        
        Args:
            plugin: Plugin instance
            config: Plugin configuration
        """
        plugin_name = plugin.name
        
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} already registered, replacing")
        
        self.plugins[plugin_name] = plugin
        self.config_map[plugin_name] = config
        
        await plugin.initialize(config)
        logger.info(f"Registered plugin: {plugin_name}")
    
    async def process_message(self, message: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run message through all storage plugins
        
        Args:
            message: Message text
            metadata: Message metadata
        
        Returns:
            List of processing results from plugins
        """
        results = []
        
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
            
            try:
                result = await plugin.process(message, metadata)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error processing message in {plugin.name}: {e}")
        
        return results
    
    async def build_context(self, query: str, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run retrieval plugins to build context
        
        Args:
            query: User query
            base_context: Base context to augment
        
        Returns:
            Augmented context dict
        """
        context = base_context.copy()
        
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
            
            try:
                retrieved = await plugin.retrieve(query, context)
                if retrieved:
                    # Merge retrieved data into context
                    for key, value in retrieved.items():
                        if key not in context:
                            context[key] = value
                        elif isinstance(context[key], list) and isinstance(value, list):
                            context[key].extend(value)
                        elif isinstance(context[key], dict) and isinstance(value, dict):
                            context[key].update(value)
            except Exception as e:
                logger.error(f"Error retrieving context from {plugin.name}: {e}")
        
        return context
    
    async def shutdown_all(self):
        """Shutdown all plugins"""
        for plugin in self.plugins.values():
            try:
                await plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {plugin.name}: {e}")
        
        logger.info("All plugins shut down")
