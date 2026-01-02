"""Convert bot responses to Telegram markdown formatting"""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TelegramFormatter:
    """
    Format responses for Telegram using Telegram Bot API markdown
    
    Telegram supports:
    - *bold* (surround with *)
    - _italic_ (surround with _)
    - __underline__ (surround with __)
    - ~strikethrough~ (surround with ~)
    - `inline code` (surround with `)
    - ```code block``` (surround with ```)
    - [inline URL](http://www.example.com)
    - [inline mention of a user](tg://user?id=123456789)
    - ![[inline fixed-height image](http://www.example.com/image.png)]
    """
    
    @staticmethod
    def format_response(response: str, include_sources: bool = True) -> str:
        """
        Format response for Telegram
        
        Args:
            response: Raw response text (may include sources)
            include_sources: Whether to format sources section
        
        Returns:
            Telegram-formatted response
        """
        
        # Split response and sources if present
        if include_sources and "📚 Sources:" in response:
            parts = response.split("📚 Sources:")
            main_response = parts[0].strip()
            sources = "📚 Sources:" + parts[1]
            
            # Format main response and sources separately
            formatted_main = TelegramFormatter._format_main_response(main_response)
            formatted_sources = TelegramFormatter._format_sources(sources)
            
            return f"{formatted_main}\n\n{formatted_sources}"
        else:
            return TelegramFormatter._format_main_response(response)
    
    @staticmethod
    def _format_main_response(text: str) -> str:
        """Format the main response text"""
        
        text = text.strip()
        
        # FIRST: Convert markdown **bold** to Telegram *bold*
        # This handles ResponseEnhancer output
        text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
        
        # Format uncertainty markers with italics
        text = re.sub(
            r'\(not certain - please confirm\)',
            r'_not certain - please confirm_',
            text
        )
        text = re.sub(
            r'\(from a while ago - still current\?\)',
            r'_from a while ago - still current?_',
            text
        )
        text = re.sub(
            r'\(based on what we discussed\)',
            r'_based on what we discussed_',
            text
        )
        
        # Format section headers with bold
        text = re.sub(
            r'^## (.+)$',
            r'*\1*',
            text,
            flags=re.MULTILINE
        )
        
        # Format bullet lists with • emoji (preserve or add)
        text = re.sub(
            r'^- ',
            r'• ',
            text,
            flags=re.MULTILINE
        )
        
        return text
    
    @staticmethod
    def _format_sources(sources_text: str) -> str:
        """Format sources section"""
        
        lines = sources_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith('📚'):
                # Bold the header
                formatted_lines.append(f"*{line.strip()}*")
            elif line.strip().startswith('•'):
                # Keep bullet format but make file paths code
                source = line.strip()
                # Format vault/file paths as code
                source = re.sub(
                    r'vault/([^ ]+)',
                    r'`vault/\1`',
                    source
                )
                formatted_lines.append(source)
            elif line.strip().startswith('('):
                # Format metadata in italics
                formatted_lines.append(f"_{line.strip()}_")
            elif line.strip():
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def format_error(error_message: str) -> str:
        """Format error messages for Telegram"""
        return f"⚠️ *Error:* _{error_message}_"
    
    @staticmethod
    def format_status(status: str, is_success: bool = True) -> str:
        """Format status messages"""
        emoji = "✅" if is_success else "❌"
        return f"{emoji} {status}"
    
    @staticmethod
    def format_list(items: list, title: str = "") -> str:
        """Format a list for Telegram"""
        formatted = ""
        if title:
            formatted += f"*{title}*\n"
        
        for item in items:
            formatted += f"• {item}\n"
        
        return formatted.strip()
    
    @staticmethod
    def format_key_value(data: Dict[str, Any], title: str = "") -> str:
        """Format key-value pairs for Telegram"""
        formatted = ""
        if title:
            formatted += f"*{title}*\n"
        
        for key, value in data.items():
            # Format key in bold
            key_formatted = key.replace('_', ' ').title()
            formatted += f"*{key_formatted}:* {value}\n"
        
        return formatted.strip()
    
    @staticmethod
    def escape_special_chars(text: str) -> str:
        """Escape Telegram special characters if needed"""
        # Most characters don't need escaping in Telegram markdown v2
        # But these can cause issues:
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        # Only escape if we're not already in formatting
        # This is a simple version - for production, use telegram's escape functions
        return text
    
    @staticmethod
    def format_code_block(code: str, language: str = "") -> str:
        """Format code block for Telegram"""
        if language:
            return f"```{language}\n{code}\n```"
        else:
            return f"```\n{code}\n```"
    
    @staticmethod
    def format_context_info(context: Dict[str, Any]) -> str:
        """Format context information for debugging/display"""
        formatted = "*Context Information:*\n"
        
        if 'core_identity' in context:
            formatted += f"\n*Identity:*\n{context['core_identity']}\n"
        
        if 'recent_messages' in context and context['recent_messages']:
            formatted += f"\n*Recent Messages ({len(context['recent_messages'])} total):*\n"
            for msg in context['recent_messages'][-3:]:  # Last 3
                role = "You" if msg.get('role') == 'user' else "Assistant"
                content = msg.get('content', '')[:100]
                formatted += f"_{role}:_ {content}...\n"
        
        if 'vault_results' in context and context['vault_results']:
            formatted += f"\n*Vault Files ({len(context['vault_results'])} total):*\n"
            for result in context['vault_results'][:3]:  # Top 3
                formatted += f"• `{result.get('file', 'unknown')}`\n"
        
        return formatted
    
    @staticmethod
    def truncate_message(text: str, max_length: int = 4096) -> list:
        """
        Telegram has a 4096 character limit per message
        Split long messages into multiple messages
        
        Args:
            text: Text to potentially split
            max_length: Max characters per message (Telegram limit is 4096)
        
        Returns:
            List of message chunks
        """
        # First, validate and fix markdown entities
        text = TelegramFormatter._validate_markdown(text)
        
        if len(text) <= max_length:
            return [text]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        messages = []
        current_message = ""
        
        for para in paragraphs:
            # If single paragraph is too long, split it
            if len(para) > max_length:
                # Save current message if it has content
                if current_message:
                    messages.append(current_message.strip())
                    current_message = ""
                
                # Split long paragraph by sentences
                sentences = para.split('. ')
                for sentence in sentences:
                    if len(current_message) + len(sentence) > max_length:
                        messages.append(current_message.strip())
                        current_message = sentence + ". "
                    else:
                        current_message += sentence + ". "
            else:
                # Try to add paragraph to current message
                if len(current_message) + len(para) + 4 > max_length:  # +4 for \n\n
                    if current_message:
                        messages.append(current_message.strip())
                    current_message = para
                else:
                    if current_message:
                        current_message += "\n\n"
                    current_message += para
        
        # Add final message
        if current_message:
            messages.append(current_message.strip())
        
        return messages
    
    @staticmethod
    def _validate_markdown(text: str) -> str:
        """
        Validate and fix Telegram markdown entities
        Remove problematic markdown to send as plain text instead
        """
        # Instead of trying to fix broken markdown, strip it entirely
        # This is safer and avoids entity parsing errors
        
        # Remove **bold**
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        
        # Remove __underline__
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # Remove ~strikethrough~
        text = re.sub(r'~(.+?)~', r'\1', text)
        
        # Note: Keep simple *bold* and _italic_ for Telegram
        # They're more stable, but clean up if unmatched
        
        # Clean up any trailing/leading markdown characters
        text = text.strip()
        text = re.sub(r'[\*_`~]+\s*$', '', text)
        text = re.sub(r'^\s*[\*_`~]+', '', text)
        
        return text


class TelegramMessageBuilder:
    """Build complex Telegram messages"""
    
    def __init__(self):
        self.sections = []
    
    def add_header(self, title: str) -> 'TelegramMessageBuilder':
        """Add a bold header"""
        self.sections.append(f"*{title}*")
        return self
    
    def add_text(self, text: str) -> 'TelegramMessageBuilder':
        """Add plain text"""
        self.sections.append(text)
        return self
    
    def add_italic(self, text: str) -> 'TelegramMessageBuilder':
        """Add italicized text"""
        self.sections.append(f"_{text}_")
        return self
    
    def add_code(self, code: str, language: str = "") -> 'TelegramMessageBuilder':
        """Add code block"""
        if language:
            self.sections.append(f"```{language}\n{code}\n```")
        else:
            self.sections.append(f"```\n{code}\n```")
        return self
    
    def add_list(self, items: list) -> 'TelegramMessageBuilder':
        """Add bulleted list"""
        for item in items:
            self.sections.append(f"• {item}")
        return self
    
    def add_link(self, text: str, url: str) -> 'TelegramMessageBuilder':
        """Add clickable link"""
        self.sections.append(f"[{text}]({url})")
        return self
    
    def add_line_break(self) -> 'TelegramMessageBuilder':
        """Add blank line separator"""
        self.sections.append("")
        return self
    
    def build(self) -> str:
        """Build final message"""
        # Join sections, removing empty strings except those used as separators
        result = "\n".join(self.sections)
        # Clean up multiple blank lines
        result = re.sub(r'\n\n\n+', '\n\n', result)
        return result.strip()
    
    def build_chunks(self, max_length: int = 4096) -> list:
        """Build and split into Telegram message chunks"""
        message = self.build()
        return TelegramFormatter.truncate_message(message, max_length)

