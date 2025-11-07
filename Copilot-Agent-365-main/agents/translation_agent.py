"""
Translation Agent for AI Ambassador Platform

This agent provides real-time translation services with cultural context awareness.
Supports all platform languages and integrates with Azure OpenAI for
context-aware translation.

Features:
- Real-time message translation
- Language detection
- Cultural context adaptation
- Ambassador response localization
- Conversation tone preservation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.basic_agent import BasicAgent
from utils.i18n import get_i18n_manager
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)


class TranslationAgent(BasicAgent):
    """
    Agent for handling translation and localization services.

    Provides:
    - Message translation between supported languages
    - Automatic language detection
    - Cultural context awareness
    - Tone and formality preservation
    - Multi-language conversation support
    """

    def __init__(self):
        self.name = 'Translation'

        self.metadata = {
            "name": self.name,
            "description": "Translates messages between languages with cultural context awareness. Detects source language automatically and provides culturally appropriate translations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to translate"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "Target language code (e.g., 'es-ES', 'fr-FR', 'ja-JP'). Supported: en-US, es-ES, fr-FR, de-DE, zh-CN, ja-JP, ar-SA, pt-BR, hi-IN, ru-RU"
                    },
                    "source_language": {
                        "type": "string",
                        "description": "Optional source language code. If not provided, will auto-detect."
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context for translation (e.g., 'formal', 'informal', 'technical', 'marketing')"
                    },
                    "preserve_tone": {
                        "type": "boolean",
                        "description": "Whether to preserve the original tone and formality. Default: true"
                    }
                },
                "required": ["text", "target_language"]
            }
        }

        super().__init__(self.name, self.metadata)

        # Initialize i18n manager
        self.i18n = get_i18n_manager()

        # Language names for better communication
        self.language_names = {
            'en-US': 'English (US)',
            'es-ES': 'Spanish',
            'fr-FR': 'French',
            'de-DE': 'German',
            'zh-CN': 'Chinese (Simplified)',
            'ja-JP': 'Japanese',
            'ar-SA': 'Arabic',
            'pt-BR': 'Portuguese (Brazil)',
            'hi-IN': 'Hindi',
            'ru-RU': 'Russian'
        }

    def perform(self, **kwargs) -> str:
        """
        Perform translation with cultural context.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Optional source language code
            context: Optional context ('formal', 'informal', etc.)
            preserve_tone: Whether to preserve tone (default: True)

        Returns:
            Formatted translation result with metadata
        """
        try:
            text = kwargs.get('text', '')
            target_lang = kwargs.get('target_language', 'en-US')
            source_lang = kwargs.get('source_language')
            context = kwargs.get('context', 'general')
            preserve_tone = kwargs.get('preserve_tone', True)

            if not text:
                return "Error: No text provided for translation."

            # Validate target language
            if target_lang not in self.i18n.SUPPORTED_LANGUAGES:
                supported = ', '.join(self.language_names.values())
                return f"Error: Unsupported target language '{target_lang}'. Supported languages: {supported}"

            # Auto-detect source language if not provided
            if not source_lang:
                source_lang = self._detect_language(text)

            # Check if translation is needed
            if source_lang == target_lang:
                return f"Text is already in {self.language_names.get(target_lang, target_lang)}. No translation needed.\n\nOriginal text: {text}"

            # Perform translation
            # Note: In a production environment, this would call Azure OpenAI or Azure Translator
            # For now, we'll use a placeholder that would integrate with the translation service
            translated_text = self._translate_text(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
                preserve_tone=preserve_tone
            )

            # Get language info for RTL detection
            target_info = self.i18n.get_language_info(target_lang)
            is_rtl = target_info['rtl']

            # Format response
            result = {
                'translated_text': translated_text,
                'source_language': self.language_names.get(source_lang, source_lang),
                'target_language': self.language_names.get(target_lang, target_lang),
                'is_rtl': is_rtl,
                'context': context,
                'original_text': text
            }

            return self._format_translation_result(result)

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"Translation failed: {str(e)}"

    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the given text.

        In production, this would use Azure Cognitive Services Language Detection.
        For now, we'll use simple heuristics.

        Args:
            text: Text to analyze

        Returns:
            Detected language code
        """
        # Simple heuristic-based detection
        # In production, use Azure Cognitive Services

        # Check for Arabic script
        if any('\u0600' <= char <= '\u06FF' for char in text):
            return 'ar-SA'

        # Check for Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh-CN'

        # Check for Japanese characters (Hiragana, Katakana, Kanji)
        if any(('\u3040' <= char <= '\u309f') or
               ('\u30a0' <= char <= '\u30ff') or
               ('\u4e00' <= char <= '\u9faf') for char in text):
            return 'ja-JP'

        # Check for Devanagari script (Hindi)
        if any('\u0900' <= char <= '\u097F' for char in text):
            return 'hi-IN'

        # Check for Cyrillic script (Russian)
        if any('\u0400' <= char <= '\u04FF' for char in text):
            return 'ru-RU'

        # Common words detection
        common_words = {
            'es-ES': ['el', 'la', 'de', 'que', 'es', 'en', 'y', 'a', 'los', 'por'],
            'fr-FR': ['le', 'de', 'un', 'et', 'à', 'les', 'des', 'en', 'du', 'une'],
            'de-DE': ['der', 'die', 'das', 'und', 'in', 'den', 'von', 'zu', 'mit', 'ist'],
            'pt-BR': ['o', 'a', 'de', 'que', 'e', 'do', 'da', 'em', 'um', 'para']
        }

        text_lower = text.lower()
        for lang, words in common_words.items():
            if any(f' {word} ' in f' {text_lower} ' for word in words):
                return lang

        # Default to English
        return 'en-US'

    def _translate_text(self,
                       text: str,
                       source_lang: str,
                       target_lang: str,
                       context: str,
                       preserve_tone: bool) -> str:
        """
        Translate text using Azure OpenAI or Azure Translator.

        In production, this would make an API call to Azure services.
        For now, we'll return a placeholder that indicates the translation system.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Translation context
            preserve_tone: Whether to preserve tone

        Returns:
            Translated text
        """
        # Placeholder for actual translation service integration
        # In production, this would call:
        # 1. Azure Translator API for direct translation
        # 2. Azure OpenAI for context-aware, culturally-adapted translation

        # For demonstration, we'll return a formatted message
        # In real implementation, replace this with actual API call

        translation_prompt = f"""Translate the following text from {source_lang} to {target_lang}.

Context: {context}
Preserve tone: {preserve_tone}

Text: {text}

Provide a culturally appropriate translation that maintains the original meaning and tone."""

        # This would be replaced with actual Azure OpenAI call
        # For now, return a placeholder indicating translation would happen
        return f"[TRANSLATED TO {target_lang}]: {text}"

    def _format_translation_result(self, result: Dict[str, Any]) -> str:
        """
        Format translation result for display.

        Args:
            result: Translation result dictionary

        Returns:
            Formatted result string
        """
        output = []

        output.append("=" * 60)
        output.append("TRANSLATION RESULT")
        output.append("=" * 60)
        output.append("")

        output.append(f"Source Language: {result['source_language']}")
        output.append(f"Target Language: {result['target_language']}")
        output.append(f"Context: {result['context']}")
        output.append(f"Right-to-Left: {'Yes' if result['is_rtl'] else 'No'}")
        output.append("")

        output.append("Original Text:")
        output.append("-" * 60)
        output.append(result['original_text'])
        output.append("")

        output.append("Translated Text:")
        output.append("-" * 60)
        output.append(result['translated_text'])
        output.append("")

        if result['is_rtl']:
            output.append("Note: Target language uses right-to-left text direction.")
            output.append("")

        output.append("=" * 60)

        return "\n".join(output)

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages.

        Returns:
            List of language info dictionaries
        """
        languages = []
        for code, name in self.language_names.items():
            info = self.i18n.get_language_info(code)
            languages.append({
                'code': code,
                'name': name,
                'native_name': info['native_name'],
                'rtl': info['rtl']
            })
        return languages

    def translate_ambassador_response(self,
                                     response: str,
                                     user_language: str,
                                     ambassador_personality: Optional[Dict] = None) -> str:
        """
        Translate ambassador response with personality preservation.

        Args:
            response: Ambassador's original response
            user_language: User's preferred language
            ambassador_personality: Optional personality context

        Returns:
            Translated response maintaining ambassador's personality
        """
        # Detect response language
        source_lang = self._detect_language(response)

        if source_lang == user_language:
            return response

        # Determine context based on personality
        context = 'friendly'
        if ambassador_personality:
            tone = ambassador_personality.get('tone', 'friendly')
            context = tone

        # Translate with personality preservation
        return self._translate_text(
            text=response,
            source_lang=source_lang,
            target_lang=user_language,
            context=context,
            preserve_tone=True
        )


# Export agent for dynamic loading
def get_agent():
    """Factory function for agent loading."""
    return TranslationAgent()
