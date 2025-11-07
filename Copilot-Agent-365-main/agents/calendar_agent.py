"""
Calendar Management Agent

This agent provides calendar management capabilities including:
- Scheduling meetings
- Checking availability
- Sending calendar invites
- Rescheduling and canceling meetings
- Support for Google Calendar and Outlook

Author: AI Ambassador Platform
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class CalendarAgent(BasicAgent):
    """
    Manages calendar operations including meeting scheduling, availability checks,
    and calendar invitations across multiple calendar platforms.
    """

    def __init__(self):
        self.name = 'Calendar'
        self.metadata = {
            "name": self.name,
            "description": "Manages calendar operations including scheduling meetings, checking availability, sending invites, and managing appointments. Supports Google Calendar and Outlook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["schedule_meeting", "check_availability", "send_invite", "reschedule", "cancel", "list_events"],
                        "description": "The calendar action to perform"
                    },
                    "title": {
                        "type": "string",
                        "description": "Meeting or event title"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or natural language"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS) or natural language"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses"
                    },
                    "description": {
                        "type": "string",
                        "description": "Meeting description or agenda"
                    },
                    "location": {
                        "type": "string",
                        "description": "Meeting location (physical address or video conference link)"
                    },
                    "event_id": {
                        "type": "string",
                        "description": "Event ID for reschedule or cancel operations"
                    },
                    "calendar_type": {
                        "type": "string",
                        "enum": ["google", "outlook"],
                        "description": "Calendar platform type (default: google)"
                    },
                    "date_range_start": {
                        "type": "string",
                        "description": "Start date for availability check or event listing"
                    },
                    "date_range_end": {
                        "type": "string",
                        "description": "End date for availability check or event listing"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        """
        Execute calendar operations based on the specified action.

        Args:
            action: The calendar action to perform
            **kwargs: Additional parameters specific to the action

        Returns:
            str: Result message describing the operation outcome

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        try:
            action = kwargs.get('action', '').lower()

            if not action:
                return self._error_response("Action parameter is required")

            # Route to appropriate handler
            handlers = {
                'schedule_meeting': self._schedule_meeting,
                'check_availability': self._check_availability,
                'send_invite': self._send_invite,
                'reschedule': self._reschedule_meeting,
                'cancel': self._cancel_meeting,
                'list_events': self._list_events
            }

            handler = handlers.get(action)
            if not handler:
                return self._error_response(f"Unknown action: {action}")

            return handler(**kwargs)

        except Exception as e:
            logger.error(f"Calendar agent error: {str(e)}", exc_info=True)
            return self._error_response(f"Calendar operation failed: {str(e)}")

    def _schedule_meeting(self, **kwargs) -> str:
        """Schedule a new meeting."""
        title = kwargs.get('title')
        start_time = kwargs.get('start_time')
        end_time = kwargs.get('end_time')
        attendees = kwargs.get('attendees', [])
        description = kwargs.get('description', '')
        location = kwargs.get('location', '')
        calendar_type = kwargs.get('calendar_type', 'google')

        # Validate required fields
        if not title:
            return self._error_response("Meeting title is required")
        if not start_time:
            return self._error_response("Start time is required")
        if not end_time:
            return self._error_response("End time is required")

        # Parse times
        try:
            start_dt = self._parse_time(start_time)
            end_dt = self._parse_time(end_time)
        except ValueError as e:
            return self._error_response(f"Invalid time format: {str(e)}")

        # Validate time range
        if start_dt >= end_dt:
            return self._error_response("Start time must be before end time")

        # Generate event ID
        event_id = self._generate_event_id()

        # Format response
        attendee_list = ", ".join(attendees) if attendees else "No attendees"

        result = {
            "status": "success",
            "action": "schedule_meeting",
            "event_id": event_id,
            "details": {
                "title": title,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "duration_minutes": int((end_dt - start_dt).total_seconds() / 60),
                "attendees": attendees,
                "description": description,
                "location": location,
                "calendar_type": calendar_type
            }
        }

        return f"""✅ Meeting scheduled successfully!

**{title}**
📅 Date: {start_dt.strftime('%A, %B %d, %Y')}
🕐 Time: {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}
⏱️ Duration: {result['details']['duration_minutes']} minutes
👥 Attendees: {attendee_list}
📍 Location: {location if location else 'Not specified'}
📝 Description: {description if description else 'No description'}

Event ID: {event_id}
Calendar: {calendar_type.capitalize()}

Note: This is a simulated scheduling. In production, this would integrate with {calendar_type.capitalize()} Calendar API to create the actual event."""

    def _check_availability(self, **kwargs) -> str:
        """Check availability for a time period."""
        date_range_start = kwargs.get('date_range_start', kwargs.get('start_time'))
        date_range_end = kwargs.get('date_range_end', kwargs.get('end_time'))
        attendees = kwargs.get('attendees', [])

        if not date_range_start or not date_range_end:
            return self._error_response("Date range (start and end) is required")

        try:
            start_dt = self._parse_time(date_range_start)
            end_dt = self._parse_time(date_range_end)
        except ValueError as e:
            return self._error_response(f"Invalid date format: {str(e)}")

        # Simulate availability check
        # In production, this would query the actual calendar API
        available_slots = self._generate_available_slots(start_dt, end_dt)

        if not attendees:
            return f"""📅 Availability Check

**Time Range:** {start_dt.strftime('%B %d, %Y')} - {end_dt.strftime('%B %d, %Y')}

**Available Time Slots:**
{self._format_time_slots(available_slots)}

Note: This is a simulated availability check. In production, this would query actual calendar data."""
        else:
            return f"""📅 Group Availability Check

**Time Range:** {start_dt.strftime('%B %d, %Y')} - {end_dt.strftime('%B %d, %Y')}
**Attendees:** {', '.join(attendees)}

**Common Available Slots:**
{self._format_time_slots(available_slots)}

Note: This is a simulated availability check. In production, this would query all attendees' calendars to find common free time."""

    def _send_invite(self, **kwargs) -> str:
        """Send calendar invitation to attendees."""
        event_id = kwargs.get('event_id')
        attendees = kwargs.get('attendees', [])
        title = kwargs.get('title')

        if not attendees:
            return self._error_response("Attendee list is required")

        if not title and not event_id:
            return self._error_response("Either event_id or meeting title is required")

        attendee_count = len(attendees)
        attendee_list = ", ".join(attendees)

        return f"""📧 Calendar Invitations Sent

**Recipients:** {attendee_list} ({attendee_count} attendee{'s' if attendee_count != 1 else ''})
**Meeting:** {title if title else f'Event {event_id}'}

✅ Invitations have been sent successfully.

Attendees will receive:
- Email notification with meeting details
- Calendar event (.ics file)
- Option to accept/decline/tentative

Note: This is a simulated invitation. In production, this would send actual calendar invites via the calendar API."""

    def _reschedule_meeting(self, **kwargs) -> str:
        """Reschedule an existing meeting."""
        event_id = kwargs.get('event_id')
        new_start = kwargs.get('start_time')
        new_end = kwargs.get('end_time')

        if not event_id:
            return self._error_response("Event ID is required for rescheduling")

        if not new_start or not new_end:
            return self._error_response("New start and end times are required")

        try:
            start_dt = self._parse_time(new_start)
            end_dt = self._parse_time(new_end)
        except ValueError as e:
            return self._error_response(f"Invalid time format: {str(e)}")

        return f"""🔄 Meeting Rescheduled

**Event ID:** {event_id}
**New Date:** {start_dt.strftime('%A, %B %d, %Y')}
**New Time:** {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}

✅ Meeting has been rescheduled successfully.
📧 Update notifications sent to all attendees.

Note: This is a simulated reschedule. In production, this would update the actual calendar event and notify attendees."""

    def _cancel_meeting(self, **kwargs) -> str:
        """Cancel an existing meeting."""
        event_id = kwargs.get('event_id')
        title = kwargs.get('title')

        if not event_id and not title:
            return self._error_response("Event ID or meeting title is required for cancellation")

        identifier = event_id if event_id else title

        return f"""❌ Meeting Cancelled

**Meeting:** {identifier}

✅ Meeting has been cancelled successfully.
📧 Cancellation notifications sent to all attendees.

The calendar event has been removed from all participants' calendars.

Note: This is a simulated cancellation. In production, this would delete the actual calendar event and notify attendees."""

    def _list_events(self, **kwargs) -> str:
        """List calendar events for a date range."""
        date_range_start = kwargs.get('date_range_start')
        date_range_end = kwargs.get('date_range_end')
        calendar_type = kwargs.get('calendar_type', 'google')

        # Default to next 7 days if no range specified
        if not date_range_start:
            start_dt = datetime.now()
        else:
            try:
                start_dt = self._parse_time(date_range_start)
            except ValueError as e:
                return self._error_response(f"Invalid start date: {str(e)}")

        if not date_range_end:
            end_dt = start_dt + timedelta(days=7)
        else:
            try:
                end_dt = self._parse_time(date_range_end)
            except ValueError as e:
                return self._error_response(f"Invalid end date: {str(e)}")

        # Generate sample events
        events = self._generate_sample_events(start_dt, end_dt)

        events_list = "\n".join([
            f"• **{e['title']}** - {e['start'].strftime('%m/%d %I:%M %p')} ({e['duration']} min)"
            for e in events
        ])

        return f"""📅 Calendar Events

**Period:** {start_dt.strftime('%B %d, %Y')} - {end_dt.strftime('%B %d, %Y')}
**Calendar:** {calendar_type.capitalize()}

{events_list if events else 'No events scheduled for this period.'}

Note: This is a simulated event list. In production, this would retrieve actual calendar events from the API."""

    # Helper methods

    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime object."""
        # Try ISO format first
        try:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except:
            pass

        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except:
                continue

        # If all parsing fails, raise error
        raise ValueError(f"Unable to parse time: {time_str}. Use ISO format (YYYY-MM-DDTHH:MM:SS) or natural date formats.")

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import uuid
        return f"cal_{uuid.uuid4().hex[:12]}"

    def _generate_available_slots(self, start_dt: datetime, end_dt: datetime) -> List[Dict[str, datetime]]:
        """Generate sample available time slots."""
        slots = []
        current = start_dt.replace(hour=9, minute=0, second=0, microsecond=0)

        days_diff = (end_dt - start_dt).days
        for day in range(min(days_diff + 1, 5)):  # Limit to 5 days
            day_date = current + timedelta(days=day)
            # Skip weekends
            if day_date.weekday() < 5:  # Monday = 0, Friday = 4
                # Morning slot
                slots.append({
                    'start': day_date.replace(hour=9, minute=0),
                    'end': day_date.replace(hour=10, minute=0)
                })
                # Afternoon slot
                slots.append({
                    'start': day_date.replace(hour=14, minute=0),
                    'end': day_date.replace(hour=15, minute=0)
                })

        return slots

    def _format_time_slots(self, slots: List[Dict[str, datetime]]) -> str:
        """Format time slots for display."""
        if not slots:
            return "No available slots found."

        formatted = []
        for slot in slots[:10]:  # Show max 10 slots
            start = slot['start']
            end = slot['end']
            formatted.append(
                f"• {start.strftime('%A, %B %d')} - {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}"
            )

        if len(slots) > 10:
            formatted.append(f"... and {len(slots) - 10} more slots")

        return "\n".join(formatted)

    def _generate_sample_events(self, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Generate sample events for demonstration."""
        events = []
        sample_events = [
            ("Team Standup", 30, 9),
            ("Project Review", 60, 14),
            ("Client Meeting", 45, 11),
            ("Sprint Planning", 90, 13)
        ]

        current = start_dt
        event_idx = 0

        while current <= end_dt and len(events) < 5:
            if current.weekday() < 5:  # Weekday
                event_name, duration, hour = sample_events[event_idx % len(sample_events)]
                event_time = current.replace(hour=hour, minute=0, second=0)

                if event_time >= start_dt and event_time <= end_dt:
                    events.append({
                        'title': event_name,
                        'start': event_time,
                        'duration': duration
                    })
                    event_idx += 1

            current += timedelta(days=1)

        return events

    def _error_response(self, message: str) -> str:
        """Format error response."""
        return f"❌ Calendar Agent Error: {message}"


# Usage examples for testing
def _test_calendar_agent():
    """Test the calendar agent with various scenarios."""
    agent = CalendarAgent()

    print("Test 1: Schedule Meeting")
    print(agent.perform(
        action="schedule_meeting",
        title="Product Demo",
        start_time="2025-11-10T14:00:00",
        end_time="2025-11-10T15:00:00",
        attendees=["john@example.com", "jane@example.com"],
        location="Conference Room A",
        description="Q4 product demonstration"
    ))
    print("\n" + "="*80 + "\n")

    print("Test 2: Check Availability")
    print(agent.perform(
        action="check_availability",
        date_range_start="2025-11-10",
        date_range_end="2025-11-15",
        attendees=["team@example.com"]
    ))
    print("\n" + "="*80 + "\n")

    print("Test 3: Send Invite")
    print(agent.perform(
        action="send_invite",
        event_id="cal_abc123",
        attendees=["newperson@example.com"],
        title="Product Demo"
    ))


if __name__ == "__main__":
    _test_calendar_agent()
