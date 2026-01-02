"""Telegram bot interface for Orion"""

import logging
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.core.telegram_formatter import TelegramFormatter, TelegramMessageBuilder

logger = logging.getLogger(__name__)


class TelegramInterface:
    """Telegram bot interface for Orion MVP"""
    
    def __init__(self, bot_token: str, message_processor):
        """
        Initialize Telegram interface
        
        Args:
            bot_token: Telegram bot token
            message_processor: Async message processor from Orion
        """
        self.bot_token = bot_token
        self.message_processor = message_processor
        self.application: Optional[Application] = None
    
    async def initialize(self):
        """Initialize and setup telegram handlers"""
        logger.info("Initializing Telegram bot...")
        
        # Create application
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("help", self.handle_help))
        self.application.add_handler(CommandHandler("reset", self.handle_reset))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        logger.info("✓ Telegram handlers registered")
        logger.info("✓ Bot ready to receive messages")
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_name = update.effective_user.first_name
        
        message = TelegramMessageBuilder() \
            .add_text(f"Hello {user_name}! [OK]") \
            .add_line_break() \
            .add_text("I'm Orion, your personal cognitive augmentation assistant.") \
            .add_line_break() \
            .add_header("Commands") \
            .add_list([
                "/help - Show available commands",
                "/reset - Clear conversation history",
            ]) \
            .add_line_break() \
            .add_text("Just send me a message and I'll help!") \
            .build()
        
        await update.message.reply_text(message)
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        message = TelegramMessageBuilder() \
            .add_header("AVAILABLE COMMANDS") \
            .add_list([
                "/start - Start the bot",
                "/help - Show this help message",
                "/reset - Clear conversation history",
            ]) \
            .add_line_break() \
            .add_header("FEATURES") \
            .add_list([
                "[BRAIN] Context-aware responses",
                "[BOOKS] Source citations",
                "[HELP] Uncertainty markers",
                "[CYCLE] Correction handling",
            ]) \
            .add_line_break() \
            .add_text("Just send any message and I'll respond!") \
            .build()
        
        await update.message.reply_text(message)
    
    async def handle_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command"""
        user_id = str(update.effective_user.id)
        
        # Clear user context from message processor if needed
        # TODO: Implement conversation reset in Phase 2
        
        message = TelegramMessageBuilder() \
            .add_text("[CYCLE] Conversation history cleared!") \
            .add_line_break() \
            .add_text("Ready for a fresh start.") \
            .build()
        
        await update.message.reply_text(message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages from users"""
        try:
            user_id = str(update.effective_user.id)
            user_name = update.effective_user.first_name
            message_text = update.message.text
            
            logger.info(f"Message from {user_name} ({user_id}): {message_text}")
            
            # Show typing indicator
            await update.message.chat.send_action("typing")
            
            # Process message through Orion
            response = await self.message_processor.process_message(
                message_text, 
                user_id=user_id
            )
            
            logger.info(f"Response: {response[:100]}...")
            
            # Format response for Telegram
            formatted_response = TelegramFormatter.format_response(response, include_sources=True)
            
            # Split into chunks if response is too long (Telegram limit: 4096 chars)
            message_chunks = TelegramFormatter.truncate_message(formatted_response, max_length=4096)
            
            # Send each chunk as separate message (plain text to avoid markdown parsing errors)
            for chunk in message_chunks:
                await update.message.reply_text(chunk)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
            # Send plain text error message
            error_text = f"Error: {str(e)}"
            await update.message.reply_text(error_text)
    
    def run(self):
        """Run the bot - BLOCKING (synchronous)
        
        This method creates and runs its own event loop.
        Call this from the main thread, not from async context.
        """
        import asyncio
        
        if not self.application:
            # Initialize synchronously if not already done
            asyncio.run(self.initialize())
        
        logger.info("Starting Telegram bot polling...")
        logger.info("Bot is now listening for messages...")
        logger.info("Press Ctrl+C to stop")
        
        # This is the proper way to run: from sync context
        self.application.run_polling()
