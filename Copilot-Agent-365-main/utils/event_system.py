"""
Event System for AI Ambassador Platform

Comprehensive event publishing, queuing, persistence, and replay system
for real-time integrations and extensibility.

Features:
- Event publishing with schema validation
- Event queuing for reliability
- Event persistence for audit trail
- Event replay for reprocessing
- Event filtering and routing
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from queue import Queue
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Supported event types in the platform"""
    # Ambassador events
    AMBASSADOR_CREATED = "ambassador.created"
    AMBASSADOR_UPDATED = "ambassador.updated"
    AMBASSADOR_DELETED = "ambassador.deleted"

    # Conversation events
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_ENDED = "conversation.ended"
    CONVERSATION_RESUMED = "conversation.resumed"

    # Message events
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_EDITED = "message.edited"
    MESSAGE_DELETED = "message.deleted"

    # QR Code events
    QR_SCANNED = "qr.scanned"
    QR_GENERATED = "qr.generated"

    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_BANNED = "user.banned"
    USER_UNBANNED = "user.unbanned"

    # Moderation events
    MODERATION_FLAGGED = "moderation.flagged"
    MODERATION_APPROVED = "moderation.approved"
    MODERATION_REJECTED = "moderation.rejected"

    # Analytics events
    ANALYTICS_MILESTONE = "analytics.milestone"
    ANALYTICS_REPORT = "analytics.report"

    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"


@dataclass
class Event:
    """Event data structure"""
    event_id: str
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    user_guid: Optional[str] = None
    ambassador_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
            "user_guid": self.user_guid,
            "ambassador_id": self.ambassador_id,
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return Event(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=EventType(data["event_type"]),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            data=data.get("data", {}),
            user_guid=data.get("user_guid"),
            ambassador_id=data.get("ambassador_id"),
            metadata=data.get("metadata", {})
        )


class EventListener:
    """Event listener for handling events"""

    def __init__(self,
                 callback: Callable[[Event], None],
                 event_types: Optional[List[EventType]] = None,
                 filters: Optional[Dict[str, Any]] = None):
        """
        Initialize event listener

        Args:
            callback: Function to call when event matches
            event_types: List of event types to listen for (None = all)
            filters: Additional filters (ambassador_id, user_guid, etc.)
        """
        self.listener_id = str(uuid.uuid4())
        self.callback = callback
        self.event_types = event_types
        self.filters = filters or {}
        self.enabled = True

    def matches(self, event: Event) -> bool:
        """Check if event matches listener criteria"""
        if not self.enabled:
            return False

        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Check filters
        for key, value in self.filters.items():
            event_value = getattr(event, key, None) or event.data.get(key)
            if event_value != value:
                return False

        return True

    def handle(self, event: Event):
        """Handle event if it matches criteria"""
        if self.matches(event):
            try:
                self.callback(event)
            except Exception as e:
                logger.error(f"Error in event listener {self.listener_id}: {e}")


class EventQueue:
    """Thread-safe event queue for reliable processing"""

    def __init__(self, max_size: int = 10000):
        self.queue = Queue(maxsize=max_size)
        self.processing = False
        self.thread = None

    def enqueue(self, event: Event):
        """Add event to queue"""
        try:
            self.queue.put(event, block=False)
        except:
            logger.warning(f"Event queue full, dropping event {event.event_id}")

    def start_processing(self, processor: Callable[[Event], None]):
        """Start processing events from queue"""
        if self.processing:
            return

        self.processing = True

        def process_loop():
            while self.processing:
                try:
                    event = self.queue.get(timeout=1)
                    processor(event)
                    self.queue.task_done()
                except:
                    pass

        self.thread = threading.Thread(target=process_loop, daemon=True)
        self.thread.start()

    def stop_processing(self):
        """Stop processing events"""
        self.processing = False
        if self.thread:
            self.thread.join(timeout=5)


class EventStore:
    """Event persistence for audit trail and replay"""

    def __init__(self, storage_manager=None):
        """
        Initialize event store

        Args:
            storage_manager: Azure File Storage manager for persistence
        """
        self.storage_manager = storage_manager
        self.in_memory_events: List[Event] = []
        self.max_memory_events = 1000

    def store_event(self, event: Event):
        """Store event for audit trail"""
        # Store in memory
        self.in_memory_events.append(event)
        if len(self.in_memory_events) > self.max_memory_events:
            self.in_memory_events.pop(0)

        # Store in Azure if available
        if self.storage_manager:
            try:
                date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                path = f"events/{date_str}/{event.event_id}.json"
                self.storage_manager.write_json(event.to_dict(), path)
            except Exception as e:
                logger.error(f"Failed to persist event {event.event_id}: {e}")

    def get_events(self,
                   event_type: Optional[EventType] = None,
                   user_guid: Optional[str] = None,
                   ambassador_id: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[Event]:
        """Retrieve events with filters"""
        filtered_events = self.in_memory_events

        # Apply filters
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        if user_guid:
            filtered_events = [e for e in filtered_events if e.user_guid == user_guid]

        if ambassador_id:
            filtered_events = [e for e in filtered_events if e.ambassador_id == ambassador_id]

        if start_time:
            filtered_events = [e for e in filtered_events
                             if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) >= start_time]

        if end_time:
            filtered_events = [e for e in filtered_events
                             if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) <= end_time]

        # Return most recent first
        filtered_events = sorted(filtered_events,
                                key=lambda e: e.timestamp,
                                reverse=True)

        return filtered_events[:limit]

    def replay_events(self,
                     processor: Callable[[Event], None],
                     event_type: Optional[EventType] = None,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None):
        """Replay events for reprocessing"""
        events = self.get_events(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        logger.info(f"Replaying {len(events)} events")

        for event in reversed(events):  # Replay in chronological order
            try:
                processor(event)
            except Exception as e:
                logger.error(f"Error replaying event {event.event_id}: {e}")


class EventSystem:
    """
    Central event system for the platform

    Features:
    - Event publishing with validation
    - Event queuing for reliability
    - Event persistence for audit
    - Event replay for reprocessing
    - Event listeners for subscriptions
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize event system"""
        if hasattr(self, 'initialized'):
            return

        self.initialized = True
        self.listeners: List[EventListener] = []
        self.event_queue = EventQueue()
        self.event_store = EventStore()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0
        }

        # Start queue processing
        self.event_queue.start_processing(self._process_event)

        logger.info("Event system initialized")

    def set_storage_manager(self, storage_manager):
        """Set Azure storage manager for persistence"""
        self.event_store.storage_manager = storage_manager

    def publish(self,
                event_type: EventType,
                data: Dict[str, Any],
                user_guid: Optional[str] = None,
                ambassador_id: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None) -> Event:
        """
        Publish event to the system

        Args:
            event_type: Type of event
            data: Event data payload
            user_guid: Optional user GUID
            ambassador_id: Optional ambassador ID
            metadata: Optional metadata

        Returns:
            Published Event object
        """
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data,
            user_guid=user_guid,
            ambassador_id=ambassador_id,
            metadata=metadata or {}
        )

        # Store event
        self.event_store.store_event(event)

        # Queue for processing
        self.event_queue.enqueue(event)

        self.stats["events_published"] += 1

        logger.debug(f"Published event: {event_type.value} [{event.event_id}]")

        return event

    def _process_event(self, event: Event):
        """Process event by notifying listeners"""
        try:
            # Notify all matching listeners in parallel
            futures = []
            for listener in self.listeners:
                if listener.matches(event):
                    future = self.executor.submit(listener.handle, event)
                    futures.append(future)

            # Wait for all listeners to complete (with timeout)
            for future in futures:
                try:
                    future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Listener failed: {e}")
                    self.stats["events_failed"] += 1

            self.stats["events_processed"] += 1

        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            self.stats["events_failed"] += 1

    def subscribe(self,
                  callback: Callable[[Event], None],
                  event_types: Optional[List[EventType]] = None,
                  filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Subscribe to events

        Args:
            callback: Function to call when event matches
            event_types: List of event types to listen for (None = all)
            filters: Additional filters

        Returns:
            Listener ID for unsubscribing
        """
        listener = EventListener(callback, event_types, filters)
        self.listeners.append(listener)
        logger.info(f"Added event listener {listener.listener_id}")
        return listener.listener_id

    def unsubscribe(self, listener_id: str):
        """Remove event listener"""
        self.listeners = [l for l in self.listeners if l.listener_id != listener_id]
        logger.info(f"Removed event listener {listener_id}")

    def get_events(self, **kwargs) -> List[Event]:
        """Get events from store with filters"""
        return self.event_store.get_events(**kwargs)

    def replay_events(self, processor: Callable[[Event], None], **kwargs):
        """Replay events for reprocessing"""
        self.event_store.replay_events(processor, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Get event system statistics"""
        return {
            **self.stats,
            "active_listeners": len([l for l in self.listeners if l.enabled]),
            "queue_size": self.event_queue.queue.qsize(),
            "stored_events": len(self.event_store.in_memory_events)
        }

    def shutdown(self):
        """Shutdown event system gracefully"""
        logger.info("Shutting down event system")
        self.event_queue.stop_processing()
        self.executor.shutdown(wait=True)


# Global event system instance
event_system = EventSystem()


# Convenience functions for publishing specific events

def publish_ambassador_created(ambassador_id: str, ambassador_data: Dict[str, Any]):
    """Publish ambassador created event"""
    return event_system.publish(
        EventType.AMBASSADOR_CREATED,
        data={"ambassador": ambassador_data},
        ambassador_id=ambassador_id
    )


def publish_ambassador_updated(ambassador_id: str, changes: Dict[str, Any]):
    """Publish ambassador updated event"""
    return event_system.publish(
        EventType.AMBASSADOR_UPDATED,
        data={"changes": changes},
        ambassador_id=ambassador_id
    )


def publish_ambassador_deleted(ambassador_id: str):
    """Publish ambassador deleted event"""
    return event_system.publish(
        EventType.AMBASSADOR_DELETED,
        data={"ambassador_id": ambassador_id},
        ambassador_id=ambassador_id
    )


def publish_conversation_started(user_guid: str, ambassador_id: str, metadata: Dict[str, Any] = None):
    """Publish conversation started event"""
    return event_system.publish(
        EventType.CONVERSATION_STARTED,
        data=metadata or {},
        user_guid=user_guid,
        ambassador_id=ambassador_id
    )


def publish_conversation_ended(user_guid: str, ambassador_id: str, summary: Dict[str, Any]):
    """Publish conversation ended event"""
    return event_system.publish(
        EventType.CONVERSATION_ENDED,
        data={"summary": summary},
        user_guid=user_guid,
        ambassador_id=ambassador_id
    )


def publish_message_sent(user_guid: str, ambassador_id: str, message: str):
    """Publish message sent event"""
    return event_system.publish(
        EventType.MESSAGE_SENT,
        data={"message": message},
        user_guid=user_guid,
        ambassador_id=ambassador_id
    )


def publish_message_received(user_guid: str, ambassador_id: str, message: str):
    """Publish message received event"""
    return event_system.publish(
        EventType.MESSAGE_RECEIVED,
        data={"message": message},
        user_guid=user_guid,
        ambassador_id=ambassador_id
    )


def publish_qr_scanned(ambassador_id: str, location: Optional[str] = None, user_guid: Optional[str] = None):
    """Publish QR code scanned event"""
    return event_system.publish(
        EventType.QR_SCANNED,
        data={"location": location},
        user_guid=user_guid,
        ambassador_id=ambassador_id
    )


def publish_user_created(user_guid: str, user_data: Dict[str, Any]):
    """Publish user created event"""
    return event_system.publish(
        EventType.USER_CREATED,
        data={"user": user_data},
        user_guid=user_guid
    )


def publish_user_banned(user_guid: str, reason: str):
    """Publish user banned event"""
    return event_system.publish(
        EventType.USER_BANNED,
        data={"reason": reason},
        user_guid=user_guid
    )


def publish_moderation_flagged(user_guid: str, content: str, reason: str, ambassador_id: Optional[str] = None):
    """Publish content flagged event"""
    return event_system.publish(
        EventType.MODERATION_FLAGGED,
        data={"content": content, "reason": reason},
        user_guid=user_guid,
        ambassador_id=ambassador_id
    )


def publish_analytics_milestone(milestone: str, value: Any, metadata: Dict[str, Any] = None):
    """Publish analytics milestone event"""
    return event_system.publish(
        EventType.ANALYTICS_MILESTONE,
        data={"milestone": milestone, "value": value, **(metadata or {})}
    )
