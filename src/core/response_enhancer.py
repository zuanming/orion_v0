"""Response enhancement with uncertainty markers, source citations, and error handling"""

import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Source of information used in response"""
    type: str  # 'core', 'conversation', 'vault'
    name: str = ""
    file: str = ""
    days_ago: int = 0


class ResponseEnhancer:
    """
    Enhance responses with uncertainty markers and source citations
    """
    
    def enhance_response(self, response: str, sources: List[Source], 
                        query: str = "") -> str:
        """
        Enhance response with:
        1. Uncertainty marker (if sources are weak/old)
        2. Source citations (what was used)
        
        Args:
            response: Raw LLM response
            sources: Sources used in generation
            query: Original user query
        
        Returns:
            Enhanced response
        """
        
        enhanced = response
        
        # Add uncertainty marker if needed
        uncertainty = self._get_uncertainty_marker(sources)
        if uncertainty and not self._already_has_uncertainty(response):
            # Add at end of first sentence
            sentences = response.split('. ')
            if len(sentences) > 0:
                sentences[0] += f" {uncertainty}"
                enhanced = '. '.join(sentences)
        
        # Add source citations
        enhanced += self._format_sources(sources)
        
        return enhanced
    
    def _get_uncertainty_marker(self, sources: List[Source]) -> str:
        """
        Determine uncertainty marker based on sources
        """
        
        if not sources:
            return "(not certain - please confirm)"
        
        # Core identity = high confidence
        if any(s.type == 'core' for s in sources):
            return ""
        
        # Only old conversations = uncertainty
        conversation_sources = [s for s in sources if s.type == 'conversation']
        if conversation_sources and all(s.days_ago > 30 for s in conversation_sources):
            return "(from a while ago - still current?)"
        
        # Mixed recent sources = moderate confidence
        if any(s.days_ago > 7 for s in conversation_sources):
            return "(based on what we discussed)"
        
        return ""
    
    def _already_has_uncertainty(self, response: str) -> bool:
        """Check if response already expresses uncertainty"""
        uncertainty_markers = [
            'i think', 'probably', 'maybe', 'not sure', 
            'might be', 'could be', 'seems like',
            'if i recall', 'i believe'
        ]
        response_lower = response.lower()
        return any(marker in response_lower for marker in uncertainty_markers)
    
    def _format_sources(self, sources: List[Source]) -> str:
        """
        Format sources for Telegram display
        """
        if not sources:
            return ""
        
        output = "\n\n📚 Sources:"
        
        # Group by type
        core_sources = [s for s in sources if s.type == 'core']
        vault_sources = [s for s in sources if s.type == 'vault']
        convo_sources = [s for s in sources if s.type == 'conversation']
        
        # Add core
        if core_sources:
            output += "\n• Your preferences"
        
        # Add vault (max 2)
        for src in vault_sources[:2]:
            output += f"\n• vault/{src.file}"
        
        # Add conversations
        if convo_sources:
            most_recent = min(s.days_ago for s in convo_sources)
            if most_recent == 0:
                output += "\n• Earlier in this conversation"
            else:
                output += f"\n• Conversation ({most_recent} days ago)"
        
        return output


class ConflictDetector:
    """
    Detect when new information conflicts with old
    """
    
    def detect_conflict(self, new_info: str, existing_info: List[str]) -> Optional[str]:
        """
        Check if new information conflicts with existing
        
        Returns:
            Conflict message if detected, None otherwise
        """
        
        for old_info in existing_info:
            if self._same_topic(new_info, old_info):
                if self._contradicts(new_info, old_info):
                    return f"(you mentioned '{old_info}' before - using latest)"
        
        return None
    
    def _same_topic(self, info1: str, info2: str) -> bool:
        """
        Check if two pieces of information are about the same thing
        Simple keyword overlap for MVP
        """
        words1 = set(info1.lower().split())
        words2 = set(info2.lower().split())
        
        # Remove common words
        common = {'i', 'the', 'a', 'an', 'is', 'am', 'are', 'was', 'were'}
        words1 -= common
        words2 -= common
        
        # Significant overlap = same topic
        overlap = words1 & words2
        return len(overlap) >= 2
    
    def _contradicts(self, info1: str, info2: str) -> bool:
        """
        Simple contradiction detection
        """
        # Preference indicators
        pref_words = ['prefer', 'like', 'better', 'favorite', 'choose']
        
        has_pref1 = any(w in info1.lower() for w in pref_words)
        has_pref2 = any(w in info2.lower() for w in pref_words)
        
        # Both express preferences = potential conflict
        if has_pref1 and has_pref2:
            return True
        
        # Negation patterns
        if ('not' in info1.lower() or 'no' in info1.lower()) != \
           ('not' in info2.lower() or 'no' in info2.lower()):
            return True
        
        return False


class ErrorAcknowledger:
    """
    Detect and acknowledge user corrections
    """
    
    correction_phrases = [
        'no', 'nope', 'wrong', 'incorrect', 'actually', 
        'not quite', "that's not right", "that's wrong"
    ]
    
    def is_correction(self, message: str) -> bool:
        """
        Detect if user is correcting the assistant
        """
        message_lower = message.lower().strip()
        
        # Check if message starts with correction phrase
        for phrase in self.correction_phrases:
            if message_lower.startswith(phrase):
                return True
        
        # Check if correction phrase is prominent
        words = message_lower.split()
        if len(words) <= 5:  # Short message
            return any(phrase in message_lower for phrase in self.correction_phrases)
        
        return False
    
    def get_acknowledgment(self) -> str:
        """Return acknowledgment prefix"""
        return "Got it, I'll update that. "
