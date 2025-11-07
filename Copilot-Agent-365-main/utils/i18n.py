"""
Internationalization (i18n) and Localization Module for AI Ambassador Platform

This module provides comprehensive internationalization support including:
- Language detection from browser and user preferences
- Translation loading and caching
- Pluralization rules (ICU message format)
- Number, date/time, and currency formatting
- Right-to-left (RTL) language support
- Cultural adaptations

Performance target: < 10ms for translation lookup
"""

import json
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class I18nManager:
    """
    Main internationalization manager for the AI Ambassador Platform.

    Features:
    - Language detection and fallback
    - Translation caching for performance
    - ICU message format support
    - Cultural formatting
    - RTL support
    """

    # Supported languages configuration
    SUPPORTED_LANGUAGES = {
        'en-US': {
            'name': 'English (US)',
            'native_name': 'English',
            'rtl': False,
            'date_format': 'MM/DD/YYYY',
            'time_format': '12h',
            'currency_symbol': '$',
            'currency_position': 'before',
            'decimal_separator': '.',
            'thousand_separator': ',',
            'first_day_of_week': 0  # Sunday
        },
        'es-ES': {
            'name': 'Spanish (Spain)',
            'native_name': 'Español',
            'rtl': False,
            'date_format': 'DD/MM/YYYY',
            'time_format': '24h',
            'currency_symbol': '€',
            'currency_position': 'after',
            'decimal_separator': ',',
            'thousand_separator': '.',
            'first_day_of_week': 1  # Monday
        },
        'fr-FR': {
            'name': 'French (France)',
            'native_name': 'Français',
            'rtl': False,
            'date_format': 'DD/MM/YYYY',
            'time_format': '24h',
            'currency_symbol': '€',
            'currency_position': 'after',
            'decimal_separator': ',',
            'thousand_separator': ' ',
            'first_day_of_week': 1
        },
        'de-DE': {
            'name': 'German (Germany)',
            'native_name': 'Deutsch',
            'rtl': False,
            'date_format': 'DD.MM.YYYY',
            'time_format': '24h',
            'currency_symbol': '€',
            'currency_position': 'after',
            'decimal_separator': ',',
            'thousand_separator': '.',
            'first_day_of_week': 1
        },
        'zh-CN': {
            'name': 'Chinese (Simplified)',
            'native_name': '简体中文',
            'rtl': False,
            'date_format': 'YYYY/MM/DD',
            'time_format': '24h',
            'currency_symbol': '¥',
            'currency_position': 'before',
            'decimal_separator': '.',
            'thousand_separator': ',',
            'first_day_of_week': 1
        },
        'ja-JP': {
            'name': 'Japanese',
            'native_name': '日本語',
            'rtl': False,
            'date_format': 'YYYY/MM/DD',
            'time_format': '24h',
            'currency_symbol': '¥',
            'currency_position': 'before',
            'decimal_separator': '.',
            'thousand_separator': ',',
            'first_day_of_week': 0
        },
        'ar-SA': {
            'name': 'Arabic (Saudi Arabia)',
            'native_name': 'العربية',
            'rtl': True,
            'date_format': 'DD/MM/YYYY',
            'time_format': '12h',
            'currency_symbol': 'ر.س',
            'currency_position': 'after',
            'decimal_separator': '.',
            'thousand_separator': ',',
            'first_day_of_week': 6  # Saturday
        },
        'pt-BR': {
            'name': 'Portuguese (Brazil)',
            'native_name': 'Português',
            'rtl': False,
            'date_format': 'DD/MM/YYYY',
            'time_format': '24h',
            'currency_symbol': 'R$',
            'currency_position': 'before',
            'decimal_separator': ',',
            'thousand_separator': '.',
            'first_day_of_week': 0
        },
        'hi-IN': {
            'name': 'Hindi (India)',
            'native_name': 'हिन्दी',
            'rtl': False,
            'date_format': 'DD/MM/YYYY',
            'time_format': '12h',
            'currency_symbol': '₹',
            'currency_position': 'before',
            'decimal_separator': '.',
            'thousand_separator': ',',
            'first_day_of_week': 0
        },
        'ru-RU': {
            'name': 'Russian',
            'native_name': 'Русский',
            'rtl': False,
            'date_format': 'DD.MM.YYYY',
            'time_format': '24h',
            'currency_symbol': '₽',
            'currency_position': 'after',
            'decimal_separator': ',',
            'thousand_separator': ' ',
            'first_day_of_week': 1
        }
    }

    # Default fallback language
    DEFAULT_LANGUAGE = 'en-US'

    def __init__(self, locales_path: Optional[str] = None):
        """
        Initialize the I18n Manager.

        Args:
            locales_path: Path to locales directory. If None, uses default path.
        """
        if locales_path is None:
            # Default to locales directory relative to this file
            self.locales_path = Path(__file__).parent.parent / 'locales'
        else:
            self.locales_path = Path(locales_path)

        # Translation cache for performance
        self._translation_cache: Dict[str, Dict[str, Any]] = {}

        # Ensure locales directory exists
        self.locales_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"I18nManager initialized with locales path: {self.locales_path}")

    def detect_language(self,
                       accept_language: Optional[str] = None,
                       user_preference: Optional[str] = None) -> str:
        """
        Detect the appropriate language based on various sources.

        Priority:
        1. User preference (if set)
        2. Browser Accept-Language header
        3. Default language (en-US)

        Args:
            accept_language: Browser Accept-Language header
            user_preference: User's stored language preference

        Returns:
            Language code (e.g., 'en-US')
        """
        # Priority 1: User preference
        if user_preference and user_preference in self.SUPPORTED_LANGUAGES:
            return user_preference

        # Priority 2: Browser Accept-Language
        if accept_language:
            detected = self._parse_accept_language(accept_language)
            if detected:
                return detected

        # Priority 3: Default
        return self.DEFAULT_LANGUAGE

    def _parse_accept_language(self, accept_language: str) -> Optional[str]:
        """
        Parse Accept-Language header and find best match.

        Format: "en-US,en;q=0.9,es;q=0.8"

        Args:
            accept_language: Accept-Language header value

        Returns:
            Best matching supported language code or None
        """
        # Parse language preferences with quality values
        languages = []
        for lang_part in accept_language.split(','):
            parts = lang_part.strip().split(';')
            lang = parts[0].strip()

            # Extract quality value (default 1.0)
            quality = 1.0
            if len(parts) > 1:
                try:
                    q_value = parts[1].strip()
                    if q_value.startswith('q='):
                        quality = float(q_value[2:])
                except:
                    pass

            languages.append((lang, quality))

        # Sort by quality (descending)
        languages.sort(key=lambda x: x[1], reverse=True)

        # Find first match
        for lang, _ in languages:
            # Try exact match
            if lang in self.SUPPORTED_LANGUAGES:
                return lang

            # Try matching base language (e.g., 'en' matches 'en-US')
            base_lang = lang.split('-')[0].lower()
            for supported_lang in self.SUPPORTED_LANGUAGES:
                if supported_lang.lower().startswith(base_lang):
                    return supported_lang

        return None

    def load_translations(self, language_code: str) -> Dict[str, Any]:
        """
        Load translations for a specific language with caching.

        Args:
            language_code: Language code (e.g., 'en-US')

        Returns:
            Dictionary of translations
        """
        # Check cache first
        if language_code in self._translation_cache:
            return self._translation_cache[language_code]

        # Load from file
        translation_file = self.locales_path / language_code / 'messages.json'

        if not translation_file.exists():
            logger.warning(f"Translation file not found for {language_code}, using default")
            # Fallback to default language
            if language_code != self.DEFAULT_LANGUAGE:
                return self.load_translations(self.DEFAULT_LANGUAGE)
            else:
                return {}

        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)

            # Cache translations
            self._translation_cache[language_code] = translations

            return translations
        except Exception as e:
            logger.error(f"Error loading translations for {language_code}: {e}")
            return {}

    def translate(self,
                  key: str,
                  language_code: str,
                  context: Optional[Dict[str, Any]] = None,
                  fallback: Optional[str] = None) -> str:
        """
        Translate a key to the target language with ICU message format support.

        Args:
            key: Translation key (dot notation, e.g., 'ui.buttons.submit')
            language_code: Target language code
            context: Variables for ICU message format interpolation
            fallback: Fallback text if translation not found

        Returns:
            Translated string
        """
        translations = self.load_translations(language_code)

        # Navigate nested keys using dot notation
        value = translations
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                # Key not found, try fallback language
                if language_code != self.DEFAULT_LANGUAGE:
                    return self.translate(key, self.DEFAULT_LANGUAGE, context, fallback)
                else:
                    return fallback or key

        # If value is not a string, return fallback
        if not isinstance(value, str):
            return fallback or key

        # Apply ICU message format if context provided
        if context:
            value = self._apply_icu_format(value, context, language_code)

        return value

    def _apply_icu_format(self,
                          message: str,
                          context: Dict[str, Any],
                          language_code: str) -> str:
        """
        Apply ICU message format to a message.

        Supports:
        - Simple variables: {name}
        - Pluralization: {count, plural, one {# item} other {# items}}
        - Select: {gender, select, male {He} female {She} other {They}}

        Args:
            message: Message template
            context: Variables for interpolation
            language_code: Language for pluralization rules

        Returns:
            Formatted message
        """
        # Simple variable replacement
        result = message
        for key, value in context.items():
            result = result.replace(f'{{{key}}}', str(value))

        # Handle pluralization
        plural_pattern = r'\{(\w+),\s*plural,\s*(.+?)\}'
        for match in re.finditer(plural_pattern, result):
            var_name = match.group(1)
            plural_rules = match.group(2)

            if var_name in context:
                count = context[var_name]
                plural_result = self._apply_plural_rules(count, plural_rules, language_code)
                result = result.replace(match.group(0), plural_result)

        # Handle select
        select_pattern = r'\{(\w+),\s*select,\s*(.+?)\}'
        for match in re.finditer(select_pattern, result):
            var_name = match.group(1)
            select_options = match.group(2)

            if var_name in context:
                value = context[var_name]
                select_result = self._apply_select_rules(value, select_options)
                result = result.replace(match.group(0), select_result)

        return result

    def _apply_plural_rules(self, count: int, rules: str, language_code: str) -> str:
        """
        Apply pluralization rules based on language-specific plural forms.

        Args:
            count: Number for pluralization
            rules: Plural rules string (e.g., "one {# item} other {# items}")
            language_code: Language code for plural rules

        Returns:
            Appropriate plural form
        """
        # Parse rules
        rule_parts = re.findall(r'(\w+)\s*\{([^}]+)\}', rules)
        rule_dict = {key: value for key, value in rule_parts}

        # Determine plural category based on language
        category = self._get_plural_category(count, language_code)

        # Get appropriate form
        if category in rule_dict:
            result = rule_dict[category]
        elif 'other' in rule_dict:
            result = rule_dict['other']
        else:
            result = str(count)

        # Replace # with actual count
        result = result.replace('#', str(count))

        return result

    def _get_plural_category(self, count: int, language_code: str) -> str:
        """
        Determine plural category based on CLDR plural rules.

        Simplified implementation for common languages.

        Args:
            count: Number to categorize
            language_code: Language code

        Returns:
            Plural category: 'zero', 'one', 'two', 'few', 'many', 'other'
        """
        base_lang = language_code.split('-')[0].lower()

        # English, German, Portuguese: one/other
        if base_lang in ['en', 'de', 'pt']:
            return 'one' if count == 1 else 'other'

        # French: zero/one/other
        if base_lang == 'fr':
            if count == 0:
                return 'zero'
            return 'one' if count == 1 else 'other'

        # Russian: complex rules
        if base_lang == 'ru':
            if count % 10 == 1 and count % 100 != 11:
                return 'one'
            elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
                return 'few'
            else:
                return 'other'

        # Arabic: complex rules
        if base_lang == 'ar':
            if count == 0:
                return 'zero'
            elif count == 1:
                return 'one'
            elif count == 2:
                return 'two'
            elif 3 <= count % 100 <= 10:
                return 'few'
            elif 11 <= count % 100 <= 99:
                return 'many'
            else:
                return 'other'

        # Chinese, Japanese: other (no plural forms)
        if base_lang in ['zh', 'ja']:
            return 'other'

        # Hindi: one/other
        if base_lang == 'hi':
            return 'one' if count == 1 else 'other'

        # Spanish: one/other
        if base_lang == 'es':
            return 'one' if count == 1 else 'other'

        # Default: simple one/other
        return 'one' if count == 1 else 'other'

    def _apply_select_rules(self, value: str, options: str) -> str:
        """
        Apply select rules for value matching.

        Args:
            value: Value to match
            options: Select options string (e.g., "male {He} female {She} other {They}")

        Returns:
            Matched option text
        """
        # Parse options
        option_parts = re.findall(r'(\w+)\s*\{([^}]+)\}', options)
        option_dict = {key: value for key, value in option_parts}

        # Get appropriate form
        if value in option_dict:
            return option_dict[value]
        elif 'other' in option_dict:
            return option_dict['other']
        else:
            return str(value)

    def format_number(self,
                     number: float,
                     language_code: str,
                     decimals: int = 2) -> str:
        """
        Format a number according to locale conventions.

        Args:
            number: Number to format
            language_code: Language code
            decimals: Number of decimal places

        Returns:
            Formatted number string
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            language_code = self.DEFAULT_LANGUAGE

        config = self.SUPPORTED_LANGUAGES[language_code]
        decimal_sep = config['decimal_separator']
        thousand_sep = config['thousand_separator']

        # Format with decimals
        formatted = f"{number:,.{decimals}f}"

        # Replace separators
        formatted = formatted.replace(',', '|TEMP|')
        formatted = formatted.replace('.', decimal_sep)
        formatted = formatted.replace('|TEMP|', thousand_sep)

        return formatted

    def format_currency(self,
                       amount: float,
                       language_code: str,
                       currency_code: Optional[str] = None) -> str:
        """
        Format currency according to locale conventions.

        Args:
            amount: Amount to format
            language_code: Language code
            currency_code: Optional override currency code

        Returns:
            Formatted currency string
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            language_code = self.DEFAULT_LANGUAGE

        config = self.SUPPORTED_LANGUAGES[language_code]
        symbol = currency_code or config['currency_symbol']
        position = config['currency_position']

        formatted_number = self.format_number(amount, language_code)

        if position == 'before':
            return f"{symbol}{formatted_number}"
        else:
            return f"{formatted_number} {symbol}"

    def format_date(self,
                   date: datetime,
                   language_code: str,
                   format_type: str = 'medium') -> str:
        """
        Format date according to locale conventions.

        Args:
            date: Date to format
            language_code: Language code
            format_type: 'short', 'medium', 'long', 'full'

        Returns:
            Formatted date string
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            language_code = self.DEFAULT_LANGUAGE

        config = self.SUPPORTED_LANGUAGES[language_code]
        date_format = config['date_format']

        # Format based on pattern
        if format_type == 'short':
            # Just date
            result = date_format
            result = result.replace('YYYY', str(date.year))
            result = result.replace('MM', f'{date.month:02d}')
            result = result.replace('DD', f'{date.day:02d}')
        elif format_type == 'medium':
            # Date with month name
            month_names = self._get_month_names(language_code)
            result = date_format.replace('MM', month_names[date.month - 1])
            result = result.replace('YYYY', str(date.year))
            result = result.replace('DD', str(date.day))
        else:
            # Long/full format
            month_names = self._get_month_names(language_code, short=False)
            day_names = self._get_day_names(language_code, short=False)
            weekday = day_names[date.weekday()]
            month = month_names[date.month - 1]
            result = f"{weekday}, {month} {date.day}, {date.year}"

        return result

    def format_time(self,
                   time: datetime,
                   language_code: str) -> str:
        """
        Format time according to locale conventions (12h or 24h).

        Args:
            time: Time to format
            language_code: Language code

        Returns:
            Formatted time string
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            language_code = self.DEFAULT_LANGUAGE

        config = self.SUPPORTED_LANGUAGES[language_code]
        time_format = config['time_format']

        if time_format == '12h':
            hour = time.hour % 12
            if hour == 0:
                hour = 12
            period = 'AM' if time.hour < 12 else 'PM'
            return f"{hour}:{time.minute:02d} {period}"
        else:
            return f"{time.hour:02d}:{time.minute:02d}"

    def _get_month_names(self, language_code: str, short: bool = True) -> List[str]:
        """Get localized month names."""
        months = {
            'en-US': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'es-ES': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            'fr-FR': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
            'de-DE': ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'],
            'zh-CN': ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
            'ja-JP': ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
            'ar-SA': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
            'pt-BR': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
            'hi-IN': ['जन', 'फर', 'मार', 'अप्र', 'मई', 'जून', 'जुल', 'अग', 'सित', 'अक्ट', 'नव', 'दिस'],
            'ru-RU': ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        }
        return months.get(language_code, months['en-US'])

    def _get_day_names(self, language_code: str, short: bool = True) -> List[str]:
        """Get localized day names."""
        days = {
            'en-US': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'es-ES': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
            'fr-FR': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
            'de-DE': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
            'zh-CN': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            'ja-JP': ['月', '火', '水', '木', '金', '土', '日'],
            'ar-SA': ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'],
            'pt-BR': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
            'hi-IN': ['सोम', 'मंगल', 'बुध', 'गुरु', 'शुक्र', 'शनि', 'रवि'],
            'ru-RU': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        }
        return days.get(language_code, days['en-US'])

    def is_rtl(self, language_code: str) -> bool:
        """
        Check if language uses right-to-left text direction.

        Args:
            language_code: Language code

        Returns:
            True if RTL, False if LTR
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            return False

        return self.SUPPORTED_LANGUAGES[language_code]['rtl']

    def get_language_info(self, language_code: str) -> Dict[str, Any]:
        """
        Get full configuration for a language.

        Args:
            language_code: Language code

        Returns:
            Language configuration dictionary
        """
        return self.SUPPORTED_LANGUAGES.get(language_code, self.SUPPORTED_LANGUAGES[self.DEFAULT_LANGUAGE])

    def get_supported_languages(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all supported languages.

        Returns:
            Dictionary of all supported languages
        """
        return self.SUPPORTED_LANGUAGES

    def clear_cache(self):
        """Clear translation cache."""
        self._translation_cache.clear()
        logger.info("Translation cache cleared")


# Global instance for easy access
_i18n_instance: Optional[I18nManager] = None

def get_i18n_manager(locales_path: Optional[str] = None) -> I18nManager:
    """
    Get or create global I18nManager instance.

    Args:
        locales_path: Optional path to locales directory

    Returns:
        I18nManager instance
    """
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nManager(locales_path)
    return _i18n_instance
