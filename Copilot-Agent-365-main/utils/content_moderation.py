"""
Content Moderation Utility for AI Ambassador Platform

This module provides comprehensive content moderation capabilities including:
- Profanity filtering
- PII detection
- Spam detection
- Toxicity detection
- Prompt injection detection
- Adult content detection
- Violence detection
- Malicious URL detection
- Azure OpenAI Content Safety integration

Performance target: < 50ms for real-time checks
"""

import re
import json
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import os

try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available - using rule-based moderation only")


class ModerationResult:
    """Result of content moderation check"""

    def __init__(self):
        self.flagged = False
        self.severity = "none"  # none, low, medium, high, critical
        self.categories = {}  # category -> score
        self.action = "allow"  # allow, warn, filter, block, report
        self.reasons = []
        self.filtered_content = None
        self.latency_ms = 0
        self.method = "rule-based"  # rule-based, azure-ai, hybrid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "flagged": self.flagged,
            "severity": self.severity,
            "categories": self.categories,
            "action": self.action,
            "reasons": self.reasons,
            "filtered_content": self.filtered_content,
            "latency_ms": self.latency_ms,
            "method": self.method,
            "timestamp": datetime.utcnow().isoformat()
        }


class ContentModerator:
    """Main content moderation engine"""

    # Comprehensive profanity list (sample - should be expanded)
    PROFANITY_PATTERNS = [
        r'\b(fuck|shit|damn|hell|ass|bitch|bastard|crap|piss)\w*\b',
        r'\b(cock|dick|pussy|cunt|whore|slut|fag|nigger|retard)\w*\b',
        r'\b(motherfucker|asshole|bullshit|goddamn|sonofabitch)\w*\b',
        # Obfuscated versions
        r'\bf+u+c+k+\w*\b',
        r'\bs+h+i+t+\w*\b',
        r'\b\w*\*+\w*\b',  # asterisk obfuscation
    ]

    # PII patterns
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'address': r'\b\d{1,5}\s+[\w\s]+(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|trail|trl|drive|dr|court|ct|parkway|pkwy|circle|cir|boulevard|blvd)\b',
    }

    # Spam patterns
    SPAM_PATTERNS = [
        r'(?i)\b(buy now|click here|limited time|act now|free money|make money fast)\b',
        r'(?i)\b(viagra|cialis|pharmacy|pills|medication)\b',
        r'(?i)\b(casino|lottery|gambling|prize|winner)\b',
        r'(?i)\b(mlm|multi-level|pyramid scheme)\b',
        r'(?i)\b(crypto|bitcoin|investment opportunity)\b',
    ]

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r'(?i)ignore (previous|all|above) (instructions|prompts|commands)',
        r'(?i)system:?\s*(prompt|instructions|role)',
        r'(?i)(you are now|act as|pretend to be|roleplay as)',
        r'(?i)(bypass|override|disable) (safety|moderation|filter)',
        r'(?i)jailbreak',
        r'(?i)sudo mode',
        r'(?i)developer mode',
        r'(?i)\[INST\]|\[/INST\]',  # Llama-style injection
    ]

    # Toxicity patterns
    TOXICITY_PATTERNS = {
        'hate_speech': [
            r'(?i)\b(hate|despise|loathe)\s+(all\s+)?(blacks|whites|jews|muslims|christians|gays|women|men)\b',
            r'(?i)\b(kill|hurt|attack|destroy)\s+(all\s+)?(blacks|whites|jews|muslims|christians|gays|women|men)\b',
            r'(?i)\b(racial|ethnic)\s+slur\b',
        ],
        'harassment': [
            r'(?i)\b(kill yourself|kys|die|neck yourself)\b',
            r'(?i)\b(worthless|pathetic|loser|idiot|moron|stupid)\s+(person|human|user)\b',
            r'(?i)\byou (should|ought to|need to) (die|kill yourself)\b',
        ],
        'threat': [
            r'(?i)\b(i will|i\'ll|gonna)\s+(kill|hurt|harm|attack|murder)\b',
            r'(?i)\b(watch out|be careful|you\'re dead)\b',
            r'(?i)\b(bomb|explosive|weapon|gun|knife)\s+(threat|attack)\b',
        ],
    }

    # Adult content patterns
    ADULT_CONTENT_PATTERNS = [
        r'(?i)\b(porn|pornography|xxx|nsfw|nude|naked)\b',
        r'(?i)\b(sex|sexual|erotic|orgasm|masturbat)\w*\b',
        r'(?i)\b(penis|vagina|breast|nipple)\w*\b',
        r'(?i)\bonlyfans\b',
    ]

    # Violence patterns
    VIOLENCE_PATTERNS = [
        r'(?i)\b(murder|kill|stab|shoot|torture|mutilate)\w*\b',
        r'(?i)\b(blood|gore|violent|brutal|savage)\w*\b',
        r'(?i)\b(suicide|self-harm|cutting)\w*\b',
        r'(?i)\b(terrorist|terrorism|bomb|explosive)\w*\b',
    ]

    # Malicious URL patterns
    MALICIOUS_URL_PATTERNS = [
        r'(?i)bit\.ly/[a-z0-9]+',  # URL shorteners (can hide malicious links)
        r'(?i)tinyurl\.com',
        r'(?i)goo\.gl',
        r'(?i)\.exe\b',  # Executable files
        r'(?i)\.scr\b',
        r'(?i)\.bat\b',
        r'(?i)phishing',
        r'(?i)malware',
    ]

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the content moderator

        Args:
            config_path: Path to moderation_config.json
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.violation_tracker = defaultdict(list)  # user_guid -> [violations]
        self.banned_users = set()  # Permanent bans
        self.temp_banned_users = {}  # user_guid -> ban_expiry_timestamp

        # Initialize Azure OpenAI client if available
        self.azure_client = None
        if OPENAI_AVAILABLE and self.config.get('azure_moderation', {}).get('enabled', False):
            try:
                self.azure_client = AzureOpenAI(
                    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                    api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
                    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize Azure OpenAI client: {e}")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load moderation configuration"""
        default_config = {
            'enabled': True,
            'max_violations_per_hour': 10,
            'temp_ban_duration_hours': 24,
            'severity_thresholds': {
                'low': 0.3,
                'medium': 0.5,
                'high': 0.7,
                'critical': 0.9
            },
            'actions': {
                'low': 'warn',
                'medium': 'filter',
                'high': 'block',
                'critical': 'ban'
            },
            'azure_moderation': {
                'enabled': True,
                'thresholds': {
                    'hate': 0.5,
                    'self_harm': 0.5,
                    'sexual': 0.5,
                    'violence': 0.5
                }
            },
            'whitelist_words': [],
            'blacklist_words': [],
            'allowed_domains': [],
            'blocked_domains': [],
            'enable_pii_detection': True,
            'enable_spam_detection': True,
            'enable_prompt_injection_detection': True,
            'multi_language_support': True,
            'languages': ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko']
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.error(f"Failed to load config from {config_path}: {e}")

        return default_config

    def check_content(self, content: str, user_guid: Optional[str] = None,
                     context: Optional[str] = None) -> ModerationResult:
        """
        Main content moderation check

        Args:
            content: Content to check
            user_guid: User identifier for tracking violations
            context: Optional context (e.g., 'user_input', 'ai_output')

        Returns:
            ModerationResult object
        """
        start_time = time.time()
        result = ModerationResult()

        # Check if user is banned
        if user_guid:
            if self._is_user_banned(user_guid):
                result.flagged = True
                result.severity = "critical"
                result.action = "block"
                result.reasons.append("User is banned")
                result.latency_ms = int((time.time() - start_time) * 1000)
                return result

        # Rule-based checks
        rule_based_result = self._rule_based_check(content)
        result.categories.update(rule_based_result.categories)
        result.reasons.extend(rule_based_result.reasons)

        # Azure OpenAI moderation check (if enabled)
        if self.azure_client and self.config['azure_moderation']['enabled']:
            try:
                azure_result = self._azure_moderation_check(content)
                result.categories.update(azure_result.categories)
                result.reasons.extend(azure_result.reasons)
                result.method = "hybrid"
            except Exception as e:
                self.logger.error(f"Azure moderation check failed: {e}")
                result.method = "rule-based"
        else:
            result.method = "rule-based"

        # Calculate overall severity
        result.severity = self._calculate_severity(result.categories)
        result.flagged = result.severity != "none"

        # Determine action
        result.action = self._determine_action(result.severity)

        # Apply filtering if needed
        if result.action == "filter":
            result.filtered_content = self._filter_content(content)

        # Track violations
        if result.flagged and user_guid:
            self._track_violation(user_guid, result)

        result.latency_ms = int((time.time() - start_time) * 1000)
        return result

    def _rule_based_check(self, content: str) -> ModerationResult:
        """Perform rule-based content checking"""
        result = ModerationResult()

        # Profanity check
        profanity_score = self._check_profanity(content)
        if profanity_score > 0:
            result.categories['profanity'] = profanity_score
            result.reasons.append(f"Profanity detected (score: {profanity_score:.2f})")

        # PII check
        if self.config.get('enable_pii_detection', True):
            pii_types = self._check_pii(content)
            if pii_types:
                result.categories['pii'] = 1.0
                result.reasons.append(f"PII detected: {', '.join(pii_types)}")

        # Spam check
        if self.config.get('enable_spam_detection', True):
            spam_score = self._check_spam(content)
            if spam_score > 0:
                result.categories['spam'] = spam_score
                result.reasons.append(f"Spam patterns detected (score: {spam_score:.2f})")

        # Prompt injection check
        if self.config.get('enable_prompt_injection_detection', True):
            injection_score = self._check_prompt_injection(content)
            if injection_score > 0:
                result.categories['prompt_injection'] = injection_score
                result.reasons.append(f"Prompt injection attempt detected (score: {injection_score:.2f})")

        # Toxicity check
        toxicity_results = self._check_toxicity(content)
        for category, score in toxicity_results.items():
            if score > 0:
                result.categories[category] = score
                result.reasons.append(f"{category} detected (score: {score:.2f})")

        # Adult content check
        adult_score = self._check_adult_content(content)
        if adult_score > 0:
            result.categories['adult_content'] = adult_score
            result.reasons.append(f"Adult content detected (score: {adult_score:.2f})")

        # Violence check
        violence_score = self._check_violence(content)
        if violence_score > 0:
            result.categories['violence'] = violence_score
            result.reasons.append(f"Violent content detected (score: {violence_score:.2f})")

        # Malicious URL check
        malicious_url_score = self._check_malicious_urls(content)
        if malicious_url_score > 0:
            result.categories['malicious_urls'] = malicious_url_score
            result.reasons.append(f"Malicious URLs detected (score: {malicious_url_score:.2f})")

        return result

    def _check_profanity(self, content: str) -> float:
        """Check for profanity"""
        content_lower = content.lower()
        matches = 0

        for pattern in self.PROFANITY_PATTERNS:
            matches += len(re.findall(pattern, content_lower))

        # Check blacklist
        for word in self.config.get('blacklist_words', []):
            if word.lower() in content_lower:
                matches += 1

        # Normalize score (cap at 1.0)
        return min(matches * 0.3, 1.0)

    def _check_pii(self, content: str) -> List[str]:
        """Check for personally identifiable information"""
        found_pii = []

        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                found_pii.append(pii_type)

        return found_pii

    def _check_spam(self, content: str) -> float:
        """Check for spam patterns"""
        matches = 0

        for pattern in self.SPAM_PATTERNS:
            matches += len(re.findall(pattern, content))

        # Check for repetition
        words = content.split()
        if len(words) > 5:
            unique_words = set(words)
            repetition_ratio = 1 - (len(unique_words) / len(words))
            if repetition_ratio > 0.7:  # More than 70% repetition
                matches += 2

        # Normalize score
        return min(matches * 0.25, 1.0)

    def _check_prompt_injection(self, content: str) -> float:
        """Check for prompt injection attempts"""
        matches = 0

        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, content):
                matches += 1

        # Normalize score
        return min(matches * 0.5, 1.0)

    def _check_toxicity(self, content: str) -> Dict[str, float]:
        """Check for toxic content"""
        results = {}

        for category, patterns in self.TOXICITY_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                matches += len(re.findall(pattern, content))

            if matches > 0:
                results[category] = min(matches * 0.4, 1.0)

        return results

    def _check_adult_content(self, content: str) -> float:
        """Check for adult content"""
        matches = 0

        for pattern in self.ADULT_CONTENT_PATTERNS:
            matches += len(re.findall(pattern, content))

        return min(matches * 0.3, 1.0)

    def _check_violence(self, content: str) -> float:
        """Check for violent content"""
        matches = 0

        for pattern in self.VIOLENCE_PATTERNS:
            matches += len(re.findall(pattern, content))

        return min(matches * 0.3, 1.0)

    def _check_malicious_urls(self, content: str) -> float:
        """Check for malicious URLs"""
        matches = 0

        for pattern in self.MALICIOUS_URL_PATTERNS:
            matches += len(re.findall(pattern, content))

        # Check blocked domains
        for domain in self.config.get('blocked_domains', []):
            if domain in content.lower():
                matches += 1

        return min(matches * 0.5, 1.0)

    def _azure_moderation_check(self, content: str) -> ModerationResult:
        """Check content using Azure OpenAI Content Safety API"""
        result = ModerationResult()

        try:
            response = self.azure_client.moderations.create(input=content)

            if response.results:
                mod_result = response.results[0]
                thresholds = self.config['azure_moderation']['thresholds']

                # Check each category
                categories = mod_result.categories
                scores = mod_result.category_scores

                if scores.hate > thresholds['hate']:
                    result.categories['hate'] = scores.hate
                    result.reasons.append(f"Hate speech detected (Azure AI: {scores.hate:.2f})")

                if scores.self_harm > thresholds['self_harm']:
                    result.categories['self_harm'] = scores.self_harm
                    result.reasons.append(f"Self-harm content detected (Azure AI: {scores.self_harm:.2f})")

                if scores.sexual > thresholds['sexual']:
                    result.categories['sexual'] = scores.sexual
                    result.reasons.append(f"Sexual content detected (Azure AI: {scores.sexual:.2f})")

                if scores.violence > thresholds['violence']:
                    result.categories['violence'] = scores.violence
                    result.reasons.append(f"Violent content detected (Azure AI: {scores.violence:.2f})")

        except Exception as e:
            self.logger.error(f"Azure moderation API error: {e}")

        return result

    def _calculate_severity(self, categories: Dict[str, float]) -> str:
        """Calculate overall severity based on category scores"""
        if not categories:
            return "none"

        max_score = max(categories.values())
        thresholds = self.config['severity_thresholds']

        if max_score >= thresholds['critical']:
            return "critical"
        elif max_score >= thresholds['high']:
            return "high"
        elif max_score >= thresholds['medium']:
            return "medium"
        elif max_score >= thresholds['low']:
            return "low"
        else:
            return "none"

    def _determine_action(self, severity: str) -> str:
        """Determine moderation action based on severity"""
        actions = self.config['actions']
        return actions.get(severity, 'allow')

    def _filter_content(self, content: str) -> str:
        """Filter/redact inappropriate content"""
        filtered = content

        # Replace profanity with asterisks
        for pattern in self.PROFANITY_PATTERNS:
            filtered = re.sub(pattern, lambda m: '*' * len(m.group()), filtered, flags=re.IGNORECASE)

        # Redact PII
        for pii_type, pattern in self.PII_PATTERNS.items():
            if pii_type == 'email':
                filtered = re.sub(pattern, '[EMAIL_REDACTED]', filtered)
            elif pii_type == 'phone':
                filtered = re.sub(pattern, '[PHONE_REDACTED]', filtered)
            elif pii_type == 'ssn':
                filtered = re.sub(pattern, '[SSN_REDACTED]', filtered)
            elif pii_type == 'credit_card':
                filtered = re.sub(pattern, '[CARD_REDACTED]', filtered)

        return filtered

    def _track_violation(self, user_guid: str, result: ModerationResult):
        """Track user violations for rate limiting and banning"""
        violation = {
            'timestamp': datetime.utcnow(),
            'severity': result.severity,
            'categories': result.categories,
            'reasons': result.reasons
        }

        self.violation_tracker[user_guid].append(violation)

        # Clean old violations (older than 1 hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.violation_tracker[user_guid] = [
            v for v in self.violation_tracker[user_guid]
            if v['timestamp'] > cutoff
        ]

        # Check if temporary ban needed
        recent_violations = len(self.violation_tracker[user_guid])
        max_violations = self.config.get('max_violations_per_hour', 10)

        if recent_violations >= max_violations:
            self._temp_ban_user(user_guid)

        # Check if permanent ban needed (critical severity)
        if result.severity == "critical":
            self._ban_user(user_guid)

    def _is_user_banned(self, user_guid: str) -> bool:
        """Check if user is banned (permanent or temporary)"""
        # Check permanent ban
        if user_guid in self.banned_users:
            return True

        # Check temporary ban
        if user_guid in self.temp_banned_users:
            if datetime.utcnow().timestamp() < self.temp_banned_users[user_guid]:
                return True
            else:
                # Ban expired
                del self.temp_banned_users[user_guid]
                return False

        return False

    def _ban_user(self, user_guid: str):
        """Permanently ban a user"""
        self.banned_users.add(user_guid)
        self.logger.warning(f"User {user_guid} has been permanently banned")

    def _temp_ban_user(self, user_guid: str):
        """Temporarily ban a user"""
        duration_hours = self.config.get('temp_ban_duration_hours', 24)
        expiry = datetime.utcnow() + timedelta(hours=duration_hours)
        self.temp_banned_users[user_guid] = expiry.timestamp()
        self.logger.warning(f"User {user_guid} has been temporarily banned until {expiry}")

    def unban_user(self, user_guid: str):
        """Unban a user (for moderation dashboard)"""
        if user_guid in self.banned_users:
            self.banned_users.remove(user_guid)
        if user_guid in self.temp_banned_users:
            del self.temp_banned_users[user_guid]
        self.logger.info(f"User {user_guid} has been unbanned")

    def get_user_violations(self, user_guid: str) -> List[Dict]:
        """Get violation history for a user"""
        violations = self.violation_tracker.get(user_guid, [])
        return [
            {
                'timestamp': v['timestamp'].isoformat(),
                'severity': v['severity'],
                'categories': v['categories'],
                'reasons': v['reasons']
            }
            for v in violations
        ]

    def whitelist_content(self, content: str):
        """Add content to whitelist (for false positives)"""
        words = content.lower().split()
        self.config['whitelist_words'].extend(words)
        self.logger.info(f"Added to whitelist: {content}")

    def blacklist_content(self, content: str):
        """Add content to blacklist"""
        words = content.lower().split()
        self.config['blacklist_words'].extend(words)
        self.logger.info(f"Added to blacklist: {content}")


# Singleton instance
_moderator_instance = None

def get_moderator(config_path: Optional[str] = None) -> ContentModerator:
    """Get or create the global moderator instance"""
    global _moderator_instance
    if _moderator_instance is None:
        _moderator_instance = ContentModerator(config_path)
    return _moderator_instance
