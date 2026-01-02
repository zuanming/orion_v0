"""
Orion - Personal Cognitive Augmentation Assistant
Main entry point

Status: Phase 1 Complete (Core Infrastructure)
Next: Phase 2 (Storage & Retrieval Plugins)
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from src.core.config import Config
from src.core.plugin_manager import PluginManager
from src.core.context_builder import ContextBuilder
from src.core.message_processor import MessageProcessor
from src.llm.ollama_client import OllamaClient

from src.plugins.storage.vector_db import VectorDBPlugin
from src.plugins.storage.conversation_buffer import ConversationBufferPlugin
from src.plugins.retrieval.core_identity import CoreIdentityPlugin
from src.plugins.retrieval.vector_search import VectorSearchPlugin
from src.plugins.retrieval.vault_reader import VaultReaderPlugin

from src.interfaces.telegram_bot import TelegramInterface

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_orion():
    """Initialize Orion MVP with all components"""
    
    load_dotenv()
    
    # Load config
    config = Config('config.yaml')
    logger.info(f"✓ Configuration loaded (v{config.get('app.version')})")
    
    # Initialize plugin manager
    plugin_manager = PluginManager()
    logger.info("✓ Plugin manager initialized")
    
    # Register Phase 2 storage plugins
    await plugin_manager.register(VectorDBPlugin(), config['storage']['vector_db'])
    logger.info("✓ VectorDBPlugin registered")
    
    await plugin_manager.register(ConversationBufferPlugin(), config['storage']['buffer'])
    logger.info("✓ ConversationBufferPlugin registered")
    
    # Register Phase 2 retrieval plugins
    await plugin_manager.register(CoreIdentityPlugin(), config['storage']['vault'])
    logger.info("✓ CoreIdentityPlugin registered")
    
    await plugin_manager.register(VaultReaderPlugin(), config['storage']['vault'])
    logger.info("✓ VaultReaderPlugin registered")
    
    # VectorSearchPlugin needs reference to VectorDBPlugin
    vector_search_config = {
        'vector_db_plugin': plugin_manager.plugins.get('vector_db'),
        'search_limit': config['context'].get('search_results', 5)
    }
    await plugin_manager.register(VectorSearchPlugin(), vector_search_config)
    logger.info("✓ VectorSearchPlugin registered")
    
    logger.info(f"✓ Registered {len(plugin_manager.plugins)} plugins")
    
    # Initialize context builder
    context_builder = ContextBuilder(config['context'])
    logger.info("✓ Context builder initialized")
    
    # Initialize Ollama client
    llm_config = config['llm']
    llm_client = OllamaClient(llm_config)
    logger.info("✓ LLM client initialized")
    
    # Initialize message processor
    processor = MessageProcessor(plugin_manager, context_builder, llm_client)
    logger.info("✓ Message processor initialized")
    
    # Initialize Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
    telegram = TelegramInterface(telegram_token, processor)
    await telegram.initialize()
    logger.info("✓ Telegram interface initialized")
    
    return telegram, processor, plugin_manager


async def test_basic_flow():
    """Test basic message processing (for development)"""
    telegram, processor, plugin_manager = await initialize_orion()
    
    logger.info("\n" + "="*60)
    logger.info("ORION MVP - BASIC FLOW TEST")
    logger.info("="*60)
    
    # Test message
    test_message = "Hello Orion! What can you do?"
    logger.info(f"\nTest message: {test_message}")
    
    try:
        response = await processor.process_message(test_message, user_id="test_user")
        logger.info(f"\nResponse:\n{response}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
    
    await plugin_manager.shutdown_all()


def main():
    """Main entry point"""
    logger.info("Starting Orion MVP...")
    logger.info("="*60)
    
    try:
        # Run the Telegram bot
        asyncio.run(initialize_for_bot())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


async def initialize_for_bot():
    """Initialize Orion and start bot"""
    telegram, processor, plugin_manager = await initialize_orion()
    
    logger.info("\n" + "="*60)
    logger.info("ORION MVP - TELEGRAM BOT RUNNING")
    logger.info("="*60)
    logger.info("Bot is ready to receive messages from Telegram!")
    
    # NOTE: We initialize but don't run from async context
    # The run() method will handle its own event loop
    # Return these for the sync wrapper to use
    return telegram, processor, plugin_manager


# Synchronous wrapper to call the bot
def run_bot_sync():
    """Run bot from synchronous context"""
    telegram, processor, plugin_manager = asyncio.run(initialize_for_bot())
    
    try:
        # This will block until Ctrl+C
        telegram.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        # Cleanup
        asyncio.run(plugin_manager.shutdown_all())


if __name__ == "__main__":
    run_bot_sync()
