"""
Webhook Manager for AI Ambassador Platform

Comprehensive webhook delivery system with:
- Registration and management
- HMAC signature authentication
- Retry with exponential backoff
- Dead letter queue
- Delivery logging
- Performance monitoring
"""

import uuid
import json
import hmac
import hashlib
import logging
import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import time
from concurrent.futures import ThreadPoolExecutor

from .event_system import Event, EventType, event_system

logger = logging.getLogger(__name__)


class WebhookStatus(str, Enum):
    """Webhook status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"


class DeliveryStatus(str, Enum):
    """Delivery attempt status"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RETRYING = "retrying"


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 4
    initial_delay: int = 0  # seconds
    backoff_multiplier: float = 5.0
    max_delay: int = 900  # 15 minutes

    def get_delay(self, attempt: int) -> int:
        """Calculate delay for attempt"""
        if attempt == 0:
            return self.initial_delay

        delay = self.initial_delay + (self.backoff_multiplier ** (attempt - 1) * 60)
        return min(int(delay), self.max_delay)


@dataclass
class Webhook:
    """Webhook configuration"""
    webhook_id: str
    url: str
    event_types: List[str]
    secret_key: str
    status: WebhookStatus = WebhookStatus.ACTIVE
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "webhook_id": self.webhook_id,
            "url": self.url,
            "event_types": self.event_types,
            "secret_key": self.secret_key,
            "status": self.status.value if isinstance(self.status, WebhookStatus) else self.status,
            "retry_config": {
                "max_attempts": self.retry_config.max_attempts,
                "initial_delay": self.retry_config.initial_delay,
                "backoff_multiplier": self.retry_config.backoff_multiplier,
                "max_delay": self.retry_config.max_delay
            },
            "filters": self.filters,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Webhook':
        """Create from dictionary"""
        retry_config_data = data.get("retry_config", {})
        retry_config = RetryConfig(
            max_attempts=retry_config_data.get("max_attempts", 4),
            initial_delay=retry_config_data.get("initial_delay", 0),
            backoff_multiplier=retry_config_data.get("backoff_multiplier", 5.0),
            max_delay=retry_config_data.get("max_delay", 900)
        )

        return Webhook(
            webhook_id=data["webhook_id"],
            url=data["url"],
            event_types=data["event_types"],
            secret_key=data["secret_key"],
            status=WebhookStatus(data.get("status", "active")),
            retry_config=retry_config,
            filters=data.get("filters", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            metadata=data.get("metadata", {})
        )


@dataclass
class DeliveryAttempt:
    """Webhook delivery attempt"""
    attempt_id: str
    webhook_id: str
    event: Event
    attempt_number: int
    status: DeliveryStatus
    timestamp: str
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "attempt_id": self.attempt_id,
            "webhook_id": self.webhook_id,
            "event": self.event.to_dict(),
            "attempt_number": self.attempt_number,
            "status": self.status.value if isinstance(self.status, DeliveryStatus) else self.status,
            "timestamp": self.timestamp,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms
        }


class WebhookValidator:
    """Webhook validation utilities"""

    @staticmethod
    async def validate_url(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
        """
        Validate webhook URL

        Args:
            url: URL to validate
            timeout: Request timeout in seconds

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check HTTPS
        if not url.startswith("https://"):
            return False, "URL must use HTTPS"

        # Check reachability
        try:
            async with aiohttp.ClientSession() as session:
                async with session.options(url, timeout=timeout, ssl=True) as response:
                    if response.status >= 500:
                        return False, f"Server error: {response.status}"
                    return True, None
        except aiohttp.ClientSSLError as e:
            return False, f"SSL certificate error: {str(e)}"
        except aiohttp.ClientError as e:
            return False, f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature

        Args:
            payload: Request body as string
            secret: Webhook secret key

        Returns:
            Signature in format "sha256=<hex>"
        """
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Verify HMAC-SHA256 signature

        Args:
            payload: Request body as string
            signature: Signature from header
            secret: Webhook secret key

        Returns:
            True if signature is valid
        """
        expected = WebhookValidator.generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected)


class WebhookDeliveryService:
    """Service for delivering webhooks"""

    def __init__(self, timeout: int = 30):
        """
        Initialize delivery service

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.delivery_history: List[DeliveryAttempt] = []
        self.max_history = 1000

    async def deliver(self, webhook: Webhook, event: Event, attempt_number: int = 0) -> DeliveryAttempt:
        """
        Deliver event to webhook

        Args:
            webhook: Webhook configuration
            event: Event to deliver
            attempt_number: Retry attempt number

        Returns:
            DeliveryAttempt with results
        """
        attempt_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Prepare payload
        payload = json.dumps(event.to_dict(), separators=(',', ':'))

        # Generate signature
        signature = WebhookValidator.generate_signature(payload, webhook.secret_key)

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-ID": webhook.webhook_id,
            "X-Event-Type": event.event_type.value if isinstance(event.event_type, EventType) else event.event_type,
            "X-Event-ID": event.event_id,
            "X-Delivery-Attempt": str(attempt_number + 1),
            "User-Agent": "AI-Ambassador-Webhooks/1.0"
        }

        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    data=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ssl=True
                ) as response:
                    duration_ms = (time.time() - start_time) * 1000
                    response_body = await response.text()

                    if 200 <= response.status < 300:
                        attempt = DeliveryAttempt(
                            attempt_id=attempt_id,
                            webhook_id=webhook.webhook_id,
                            event=event,
                            attempt_number=attempt_number,
                            status=DeliveryStatus.SUCCESS,
                            timestamp=timestamp,
                            response_code=response.status,
                            response_body=response_body[:1000],  # Limit size
                            duration_ms=duration_ms
                        )
                    else:
                        attempt = DeliveryAttempt(
                            attempt_id=attempt_id,
                            webhook_id=webhook.webhook_id,
                            event=event,
                            attempt_number=attempt_number,
                            status=DeliveryStatus.FAILED,
                            timestamp=timestamp,
                            response_code=response.status,
                            response_body=response_body[:1000],
                            error_message=f"HTTP {response.status}",
                            duration_ms=duration_ms
                        )

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            attempt = DeliveryAttempt(
                attempt_id=attempt_id,
                webhook_id=webhook.webhook_id,
                event=event,
                attempt_number=attempt_number,
                status=DeliveryStatus.FAILED,
                timestamp=timestamp,
                error_message="Request timeout",
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            attempt = DeliveryAttempt(
                attempt_id=attempt_id,
                webhook_id=webhook.webhook_id,
                event=event,
                attempt_number=attempt_number,
                status=DeliveryStatus.FAILED,
                timestamp=timestamp,
                error_message=str(e),
                duration_ms=duration_ms
            )

        # Store in history
        self._add_to_history(attempt)

        return attempt

    def _add_to_history(self, attempt: DeliveryAttempt):
        """Add delivery attempt to history"""
        self.delivery_history.append(attempt)
        if len(self.delivery_history) > self.max_history:
            self.delivery_history.pop(0)

    def get_delivery_history(self, webhook_id: Optional[str] = None, limit: int = 100) -> List[DeliveryAttempt]:
        """Get delivery history"""
        history = self.delivery_history

        if webhook_id:
            history = [a for a in history if a.webhook_id == webhook_id]

        return sorted(history, key=lambda a: a.timestamp, reverse=True)[:limit]

    def get_stats(self, webhook_id: Optional[str] = None) -> Dict[str, Any]:
        """Get delivery statistics"""
        history = self.delivery_history
        if webhook_id:
            history = [a for a in history if a.webhook_id == webhook_id]

        if not history:
            return {
                "total_deliveries": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0
            }

        successful = [a for a in history if a.status == DeliveryStatus.SUCCESS]
        failed = [a for a in history if a.status == DeliveryStatus.FAILED]

        durations = [a.duration_ms for a in history if a.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_deliveries": len(history),
            "successful_deliveries": len(successful),
            "failed_deliveries": len(failed),
            "success_rate": len(successful) / len(history) * 100 if history else 0,
            "average_duration_ms": avg_duration
        }


class WebhookManager:
    """
    Central webhook management system

    Features:
    - Webhook registration and management
    - Event delivery with retry
    - Dead letter queue
    - Delivery logging
    - Statistics and monitoring
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize webhook manager"""
        if hasattr(self, 'initialized'):
            return

        self.initialized = True
        self.webhooks: Dict[str, Webhook] = {}
        self.delivery_service = WebhookDeliveryService()
        self.dead_letter_queue: List[Tuple[Webhook, Event, int]] = []
        self.storage_manager = None
        self.event_listener_id = None

        # Subscribe to all events
        self._subscribe_to_events()

        logger.info("Webhook manager initialized")

    def set_storage_manager(self, storage_manager):
        """Set Azure storage manager for persistence"""
        self.storage_manager = storage_manager
        self._load_webhooks()

    def _subscribe_to_events(self):
        """Subscribe to event system"""
        self.event_listener_id = event_system.subscribe(
            callback=self._handle_event,
            event_types=None  # Listen to all events
        )

    def _handle_event(self, event: Event):
        """Handle incoming event"""
        # Find matching webhooks
        matching_webhooks = self._find_matching_webhooks(event)

        # Deliver to each webhook (async)
        for webhook in matching_webhooks:
            asyncio.run(self._deliver_with_retry(webhook, event))

    def _find_matching_webhooks(self, event: Event) -> List[Webhook]:
        """Find webhooks that match event"""
        matching = []

        event_type_value = event.event_type.value if isinstance(event.event_type, EventType) else event.event_type

        for webhook in self.webhooks.values():
            # Check status
            if webhook.status != WebhookStatus.ACTIVE:
                continue

            # Check event type
            if event_type_value not in webhook.event_types:
                continue

            # Check filters
            if webhook.filters:
                match = True
                for key, value in webhook.filters.items():
                    event_value = getattr(event, key, None) or event.data.get(key)
                    if event_value != value:
                        match = False
                        break
                if not match:
                    continue

            matching.append(webhook)

        return matching

    async def _deliver_with_retry(self, webhook: Webhook, event: Event):
        """Deliver event with retry logic"""
        attempt_number = 0
        max_attempts = webhook.retry_config.max_attempts

        while attempt_number < max_attempts:
            # Deliver
            attempt = await self.delivery_service.deliver(webhook, event, attempt_number)

            # Save attempt if storage available
            if self.storage_manager:
                try:
                    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    path = f"webhooks/deliveries/{date_str}/{attempt.attempt_id}.json"
                    self.storage_manager.write_json(attempt.to_dict(), path)
                except Exception as e:
                    logger.error(f"Failed to save delivery attempt: {e}")

            # Check if successful
            if attempt.status == DeliveryStatus.SUCCESS:
                logger.info(f"Webhook delivered successfully: {webhook.webhook_id} -> {event.event_id}")
                return

            # Calculate retry delay
            attempt_number += 1
            if attempt_number < max_attempts:
                delay = webhook.retry_config.get_delay(attempt_number)
                logger.warning(f"Webhook delivery failed, retrying in {delay}s: {webhook.webhook_id}")
                await asyncio.sleep(delay)

        # All retries exhausted - add to dead letter queue
        logger.error(f"Webhook delivery failed after {max_attempts} attempts: {webhook.webhook_id}")
        self.dead_letter_queue.append((webhook, event, max_attempts))

        # Save to dead letter queue storage
        if self.storage_manager:
            try:
                dlq_entry = {
                    "webhook_id": webhook.webhook_id,
                    "event": event.to_dict(),
                    "attempts": max_attempts,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                dlq_id = str(uuid.uuid4())
                path = f"webhooks/failed/{dlq_id}.json"
                self.storage_manager.write_json(dlq_entry, path)
            except Exception as e:
                logger.error(f"Failed to save to dead letter queue: {e}")

    def register_webhook(self,
                        url: str,
                        event_types: List[str],
                        secret_key: Optional[str] = None,
                        filters: Optional[Dict[str, Any]] = None,
                        retry_config: Optional[RetryConfig] = None) -> Webhook:
        """
        Register new webhook

        Args:
            url: Webhook URL
            event_types: List of event types to subscribe to
            secret_key: Secret key for HMAC signature (generated if not provided)
            filters: Event filters
            retry_config: Retry configuration

        Returns:
            Created Webhook object
        """
        webhook = Webhook(
            webhook_id=str(uuid.uuid4()),
            url=url,
            event_types=event_types,
            secret_key=secret_key or self._generate_secret(),
            retry_config=retry_config or RetryConfig(),
            filters=filters or {}
        )

        self.webhooks[webhook.webhook_id] = webhook

        # Save to storage
        self._save_webhooks()

        logger.info(f"Registered webhook: {webhook.webhook_id} -> {url}")

        return webhook

    def update_webhook(self, webhook_id: str, updates: Dict[str, Any]) -> Optional[Webhook]:
        """Update webhook configuration"""
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return None

        # Apply updates
        if "url" in updates:
            webhook.url = updates["url"]
        if "event_types" in updates:
            webhook.event_types = updates["event_types"]
        if "status" in updates:
            webhook.status = WebhookStatus(updates["status"])
        if "filters" in updates:
            webhook.filters = updates["filters"]

        webhook.updated_at = datetime.now(timezone.utc).isoformat()

        # Save to storage
        self._save_webhooks()

        logger.info(f"Updated webhook: {webhook_id}")

        return webhook

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self._save_webhooks()
            logger.info(f"Deleted webhook: {webhook_id}")
            return True
        return False

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID"""
        return self.webhooks.get(webhook_id)

    def list_webhooks(self) -> List[Webhook]:
        """List all webhooks"""
        return list(self.webhooks.values())

    async def test_webhook(self, webhook_id: str, event_type: str, test_data: Optional[Dict[str, Any]] = None) -> DeliveryAttempt:
        """Send test event to webhook"""
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")

        # Create test event
        test_event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType(event_type),
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=test_data or {"test": True}
        )

        # Deliver
        return await self.delivery_service.deliver(webhook, test_event, 0)

    async def retry_failed_delivery(self, webhook_id: str, event: Event) -> DeliveryAttempt:
        """Manually retry failed delivery"""
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")

        return await self.delivery_service.deliver(webhook, event, 0)

    def get_delivery_history(self, webhook_id: Optional[str] = None, limit: int = 100) -> List[DeliveryAttempt]:
        """Get delivery history"""
        return self.delivery_service.get_delivery_history(webhook_id, limit)

    def get_stats(self, webhook_id: Optional[str] = None) -> Dict[str, Any]:
        """Get webhook statistics"""
        delivery_stats = self.delivery_service.get_stats(webhook_id)

        return {
            **delivery_stats,
            "total_webhooks": len(self.webhooks),
            "active_webhooks": len([w for w in self.webhooks.values() if w.status == WebhookStatus.ACTIVE]),
            "dead_letter_queue_size": len(self.dead_letter_queue)
        }

    def _generate_secret(self) -> str:
        """Generate webhook secret key"""
        return f"whsec_{uuid.uuid4().hex}"

    def _save_webhooks(self):
        """Save webhooks to storage"""
        if not self.storage_manager:
            return

        try:
            webhooks_data = {
                webhook_id: webhook.to_dict()
                for webhook_id, webhook in self.webhooks.items()
            }
            self.storage_manager.write_json(webhooks_data, "webhooks/registrations.json")
        except Exception as e:
            logger.error(f"Failed to save webhooks: {e}")

    def _load_webhooks(self):
        """Load webhooks from storage"""
        if not self.storage_manager:
            return

        try:
            webhooks_data = self.storage_manager.read_json("webhooks/registrations.json")
            if webhooks_data:
                self.webhooks = {
                    webhook_id: Webhook.from_dict(data)
                    for webhook_id, data in webhooks_data.items()
                }
                logger.info(f"Loaded {len(self.webhooks)} webhooks from storage")
        except Exception as e:
            logger.error(f"Failed to load webhooks: {e}")


# Global webhook manager instance
webhook_manager = WebhookManager()
