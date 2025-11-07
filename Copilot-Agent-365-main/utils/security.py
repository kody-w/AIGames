"""
Security module for AI Ambassador Platform
Provides rate limiting, input validation, request signature validation,
suspicious activity detection, and security logging.
"""

import hashlib
import hmac
import json
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class SecurityEventType(Enum):
    """Types of security events"""
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    INPUT_VALIDATION_FAILED = "input_validation_failed"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    AUTHENTICATION_FAILED = "authentication_failed"
    INVALID_SIGNATURE = "invalid_signature"
    BANNED_IP = "banned_ip"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    OVERSIZED_REQUEST = "oversized_request"
    INVALID_ORIGIN = "invalid_origin"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    timestamp: datetime
    ip_address: Optional[str] = None
    user_guid: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_guid": self.user_guid,
            "details": self.details,
            "severity": self.severity
        }


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    max_request_size_bytes: int = 1048576  # 1MB
    max_input_length: int = 10000
    max_conversation_history_length: int = 100
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    banned_keywords: List[str] = field(default_factory=lambda: [
        "<?php", "<?=", "<script>", "javascript:", "onerror=",
        "onload=", "eval(", "exec(", "system(", "passthru(",
        "shell_exec(", "base64_decode(", "../../../", "..\\..\\",
    ])
    sql_injection_patterns: List[str] = field(default_factory=lambda: [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(--\s*$)",
        r"(;\s*drop\b)",
        r"('\s*or\s*'1'\s*=\s*'1)",
        r"('\s*or\s*1\s*=\s*1)",
    ])
    xss_patterns: List[str] = field(default_factory=lambda: [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"<iframe[^>]*>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
    ])
    token_rotation_days: int = 90
    signature_header: str = "X-Request-Signature"
    signature_timestamp_header: str = "X-Request-Timestamp"
    signature_max_age_seconds: int = 300


class RateLimiter:
    """Rate limiter with per-IP and per-GUID tracking"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.ip_requests: Dict[str, List[float]] = defaultdict(list)
        self.guid_requests: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}
        self.blocked_guids: Dict[str, float] = {}

    def _clean_old_requests(self, requests: List[float], window_seconds: int) -> List[float]:
        current_time = time.time()
        cutoff = current_time - window_seconds
        return [req_time for req_time in requests if req_time > cutoff]

    def _check_limit(self, identifier: str, requests_dict: Dict[str, List[float]],
                     limit: int, window_seconds: int) -> Tuple[bool, int]:
        current_time = time.time()
        requests_dict[identifier] = self._clean_old_requests(
            requests_dict[identifier], window_seconds
        )
        request_count = len(requests_dict[identifier])
        if request_count >= limit:
            return False, request_count
        requests_dict[identifier].append(current_time)
        return True, request_count + 1

    def check_ip_rate_limit(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        if ip_address in self.blocked_ips:
            if time.time() < self.blocked_ips[ip_address]:
                return False, "IP temporarily blocked due to rate limit violations"
            else:
                del self.blocked_ips[ip_address]
        
        allowed, count = self._check_limit(
            ip_address, self.ip_requests,
            self.config.requests_per_minute, 60
        )
        if not allowed:
            self.blocked_ips[ip_address] = time.time() + 300
            return False, f"Rate limit exceeded: {count} requests in last minute (limit: {self.config.requests_per_minute})"
        
        allowed, count = self._check_limit(
            ip_address, self.ip_requests,
            self.config.requests_per_hour, 3600
        )
        if not allowed:
            return False, f"Rate limit exceeded: {count} requests in last hour (limit: {self.config.requests_per_hour})"
        
        return True, None

    def check_guid_rate_limit(self, user_guid: str) -> Tuple[bool, Optional[str]]:
        if user_guid in self.blocked_guids:
            if time.time() < self.blocked_guids[user_guid]:
                return False, "User temporarily blocked due to rate limit violations"
            else:
                del self.blocked_guids[user_guid]
        
        allowed, count = self._check_limit(
            user_guid, self.guid_requests,
            self.config.requests_per_hour, 3600
        )
        if not allowed:
            self.blocked_guids[user_guid] = time.time() + 3600
            return False, f"Rate limit exceeded: {count} requests in last hour (limit: {self.config.requests_per_hour})"
        
        return True, None

    def get_remaining_requests(self, identifier: str, is_guid: bool = False) -> Dict[str, int]:
        requests_dict = self.guid_requests if is_guid else self.ip_requests
        requests_dict[identifier] = self._clean_old_requests(requests_dict[identifier], 3600)
        minute_requests = len([r for r in requests_dict[identifier] if r > time.time() - 60])
        hour_requests = len(requests_dict[identifier])
        return {
            "minute_remaining": max(0, self.config.requests_per_minute - minute_requests),
            "hour_remaining": max(0, self.config.requests_per_hour - hour_requests),
            "minute_limit": self.config.requests_per_minute,
            "hour_limit": self.config.requests_per_hour
        }


class InputValidator:
    """Input validation and sanitization"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in config.sql_injection_patterns]
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in config.xss_patterns]

    def validate_input_length(self, user_input: str) -> Tuple[bool, Optional[str]]:
        if len(user_input) > self.config.max_input_length:
            return False, f"Input exceeds maximum length of {self.config.max_input_length} characters"
        return True, None

    def validate_guid_format(self, guid: str) -> Tuple[bool, Optional[str]]:
        guid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not guid_pattern.match(guid):
            return False, "Invalid GUID format"
        return True, None

    def check_sql_injection(self, text: str) -> Tuple[bool, Optional[str]]:
        for pattern in self.sql_patterns:
            if pattern.search(text):
                return False, f"Potential SQL injection detected: {pattern.pattern}"
        return True, None

    def check_xss_attack(self, text: str) -> Tuple[bool, Optional[str]]:
        for pattern in self.xss_patterns:
            if pattern.search(text):
                return False, f"Potential XSS attack detected: {pattern.pattern}"
        return True, None

    def check_banned_keywords(self, text: str) -> Tuple[bool, Optional[str]]:
        text_lower = text.lower()
        for keyword in self.config.banned_keywords:
            if keyword.lower() in text_lower:
                return False, f"Banned keyword detected: {keyword}"
        return True, None

    def validate_conversation_history(self, history: List[Dict]) -> Tuple[bool, Optional[str]]:
        if not isinstance(history, list):
            return False, "Conversation history must be a list"
        if len(history) > self.config.max_conversation_history_length:
            return False, f"Conversation history exceeds maximum length of {self.config.max_conversation_history_length}"
        for i, message in enumerate(history):
            if not isinstance(message, dict):
                return False, f"Message {i} is not a dictionary"
            if 'role' not in message or 'content' not in message:
                return False, f"Message {i} missing required fields (role, content)"
            if message['role'] not in ['user', 'assistant', 'system', 'function']:
                return False, f"Message {i} has invalid role: {message['role']}"
        return True, None

    def validate_request_body(self, body: Dict) -> Tuple[bool, Optional[str]]:
        if 'user_input' not in body:
            return False, "Missing required field: user_input"
        user_input = body.get('user_input', '')
        if not isinstance(user_input, str):
            user_input = str(user_input)
        valid, error = self.validate_input_length(user_input)
        if not valid:
            return False, error
        valid, error = self.check_sql_injection(user_input)
        if not valid:
            return False, error
        valid, error = self.check_xss_attack(user_input)
        if not valid:
            return False, error
        valid, error = self.check_banned_keywords(user_input)
        if not valid:
            return False, error
        if 'conversation_history' in body:
            valid, error = self.validate_conversation_history(body['conversation_history'])
            if not valid:
                return False, error
        if 'user_guid' in body and body['user_guid']:
            valid, error = self.validate_guid_format(body['user_guid'])
            if not valid:
                return False, error
        return True, None


class SecurityLogger:
    """Logs security events"""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.logger = logging.getLogger('security')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_event(self, event: SecurityEvent):
        event_dict = event.to_dict()
        if event.severity == "critical":
            self.logger.critical(json.dumps(event_dict))
        elif event.severity == "high":
            self.logger.error(json.dumps(event_dict))
        elif event.severity == "medium":
            self.logger.warning(json.dumps(event_dict))
        else:
            self.logger.info(json.dumps(event_dict))
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(event_dict) + '\n')
            except Exception as e:
                self.logger.error(f"Failed to write security log to file: {str(e)}")


class SuspiciousActivityDetector:
    """Detects suspicious activity patterns"""

    def __init__(self):
        self.failed_auth_attempts: Dict[str, List[float]] = defaultdict(list)
        self.suspicious_patterns: Dict[str, List[float]] = defaultdict(list)

    def record_failed_auth(self, identifier: str) -> bool:
        current_time = time.time()
        self.failed_auth_attempts[identifier] = [
            t for t in self.failed_auth_attempts[identifier]
            if t > current_time - 3600
        ]
        self.failed_auth_attempts[identifier].append(current_time)
        return len(self.failed_auth_attempts[identifier]) >= 5

    def record_suspicious_pattern(self, identifier: str, pattern: str) -> int:
        current_time = time.time()
        key = f"{identifier}:{pattern}"
        self.suspicious_patterns[key] = [
            t for t in self.suspicious_patterns[key]
            if t > current_time - 3600
        ]
        self.suspicious_patterns[key].append(current_time)
        return len(self.suspicious_patterns[key])

    def is_suspicious(self, identifier: str) -> bool:
        current_time = time.time()
        recent_failures = [
            t for t in self.failed_auth_attempts.get(identifier, [])
            if t > current_time - 3600
        ]
        if len(recent_failures) >= 3:
            return True
        for key, times in self.suspicious_patterns.items():
            if key.startswith(identifier):
                recent = [t for t in times if t > current_time - 3600]
                if len(recent) >= 5:
                    return True
        return False


class SecurityManager:
    """Main security manager"""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        self.input_validator = InputValidator(self.config)
        self.activity_detector = SuspiciousActivityDetector()
        self.logger = SecurityLogger()

    def validate_request(self, request_data: Dict, ip_address: str,
                        headers: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str], List[SecurityEvent]]:
        events = []
        headers = headers or {}
        user_guid = request_data.get('user_guid')

        if self.config.ip_blacklist:
            if ip_address in self.config.ip_blacklist:
                event = SecurityEvent(
                    event_type=SecurityEventType.BANNED_IP,
                    timestamp=datetime.now(),
                    ip_address=ip_address,
                    user_guid=user_guid,
                    details={"reason": "IP in blacklist"},
                    severity="high"
                )
                events.append(event)
                self.logger.log_event(event)
                return False, "Access denied", events

        if self.config.ip_whitelist:
            if ip_address not in self.config.ip_whitelist:
                event = SecurityEvent(
                    event_type=SecurityEventType.BANNED_IP,
                    timestamp=datetime.now(),
                    ip_address=ip_address,
                    user_guid=user_guid,
                    details={"reason": "IP not in whitelist"},
                    severity="high"
                )
                events.append(event)
                self.logger.log_event(event)
                return False, "Access denied", events

        allowed, error_msg = self.rate_limiter.check_ip_rate_limit(ip_address)
        if not allowed:
            event = SecurityEvent(
                event_type=SecurityEventType.RATE_LIMIT_VIOLATION,
                timestamp=datetime.now(),
                ip_address=ip_address,
                user_guid=user_guid,
                details={"limit_type": "ip", "message": error_msg},
                severity="medium"
            )
            events.append(event)
            self.logger.log_event(event)
            return False, error_msg, events

        if user_guid:
            allowed, error_msg = self.rate_limiter.check_guid_rate_limit(user_guid)
            if not allowed:
                event = SecurityEvent(
                    event_type=SecurityEventType.RATE_LIMIT_VIOLATION,
                    timestamp=datetime.now(),
                    ip_address=ip_address,
                    user_guid=user_guid,
                    details={"limit_type": "guid", "message": error_msg},
                    severity="medium"
                )
                events.append(event)
                self.logger.log_event(event)
                return False, error_msg, events

        valid, error_msg = self.input_validator.validate_request_body(request_data)
        if not valid:
            event = SecurityEvent(
                event_type=SecurityEventType.INPUT_VALIDATION_FAILED,
                timestamp=datetime.now(),
                ip_address=ip_address,
                user_guid=user_guid,
                details={"validation_error": error_msg},
                severity="medium"
            )
            events.append(event)
            self.logger.log_event(event)
            return False, error_msg, events

        if self.activity_detector.is_suspicious(ip_address):
            event = SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_PATTERN,
                timestamp=datetime.now(),
                ip_address=ip_address,
                user_guid=user_guid,
                details={"reason": "Suspicious activity detected"},
                severity="high"
            )
            events.append(event)
            self.logger.log_event(event)
            return False, "Suspicious activity detected", events

        return True, None, events

    def get_security_headers(self) -> Dict[str, str]:
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }


_security_manager = None


def get_security_manager(config: Optional[SecurityConfig] = None) -> SecurityManager:
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(config)
    return _security_manager
