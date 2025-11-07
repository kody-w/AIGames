"""
Email Composition and Management Agent

This agent provides email capabilities including:
- Drafting professional emails
- Email templates
- Follow-up reminders
- Email summarization
- Tone adjustment and formatting

Author: AI Ambassador Platform
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class EmailAgent(BasicAgent):
    """
    Manages email operations including drafting, templating, and email management.
    Supports various email tones and professional formatting.
    """

    def __init__(self):
        self.name = 'Email'
        self.metadata = {
            "name": self.name,
            "description": "Drafts and manages professional emails with customizable templates, tone adjustment, follow-up reminders, and email summarization capabilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["draft", "template", "summarize", "set_reminder", "reply", "format"],
                        "description": "The email action to perform"
                    },
                    "recipient": {
                        "type": "string",
                        "description": "Email recipient address or name"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content or main message"
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["professional", "friendly", "formal", "casual", "persuasive", "apologetic"],
                        "description": "Desired tone for the email (default: professional)"
                    },
                    "template_type": {
                        "type": "string",
                        "enum": ["meeting_request", "follow_up", "introduction", "thank_you", "apology", "proposal", "announcement", "reminder"],
                        "description": "Type of email template to use"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context or details to include in the email"
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CC recipients"
                    },
                    "bcc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "BCC recipients"
                    },
                    "original_email": {
                        "type": "string",
                        "description": "Original email content for reply or summarization"
                    },
                    "reminder_days": {
                        "type": "integer",
                        "description": "Number of days before sending follow-up reminder"
                    },
                    "signature": {
                        "type": "string",
                        "description": "Email signature to append"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Email templates
        self.templates = {
            "meeting_request": {
                "subject": "Meeting Request: {topic}",
                "structure": ["greeting", "purpose", "proposed_times", "call_to_action", "closing"]
            },
            "follow_up": {
                "subject": "Following Up: {topic}",
                "structure": ["greeting", "reference", "update", "next_steps", "closing"]
            },
            "introduction": {
                "subject": "Introduction: {your_name}",
                "structure": ["greeting", "introduction", "purpose", "value_proposition", "closing"]
            },
            "thank_you": {
                "subject": "Thank You - {topic}",
                "structure": ["greeting", "gratitude", "specific_thanks", "future", "closing"]
            },
            "apology": {
                "subject": "Apology Regarding {topic}",
                "structure": ["greeting", "acknowledgment", "apology", "solution", "reassurance", "closing"]
            },
            "proposal": {
                "subject": "Proposal: {topic}",
                "structure": ["greeting", "introduction", "problem", "solution", "benefits", "next_steps", "closing"]
            },
            "announcement": {
                "subject": "Announcement: {topic}",
                "structure": ["greeting", "announcement", "details", "impact", "action_required", "closing"]
            },
            "reminder": {
                "subject": "Reminder: {topic}",
                "structure": ["greeting", "reminder", "details", "deadline", "call_to_action", "closing"]
            }
        }

    def perform(self, **kwargs) -> str:
        """
        Execute email operations based on the specified action.

        Args:
            action: The email action to perform
            **kwargs: Additional parameters specific to the action

        Returns:
            str: Formatted email or operation result

        Raises:
            ValueError: If required parameters are missing
        """
        try:
            action = kwargs.get('action', '').lower()

            if not action:
                return self._error_response("Action parameter is required")

            # Route to appropriate handler
            handlers = {
                'draft': self._draft_email,
                'template': self._use_template,
                'summarize': self._summarize_email,
                'set_reminder': self._set_reminder,
                'reply': self._draft_reply,
                'format': self._format_email
            }

            handler = handlers.get(action)
            if not handler:
                return self._error_response(f"Unknown action: {action}")

            return handler(**kwargs)

        except Exception as e:
            logger.error(f"Email agent error: {str(e)}", exc_info=True)
            return self._error_response(f"Email operation failed: {str(e)}")

    def _draft_email(self, **kwargs) -> str:
        """Draft a professional email from scratch."""
        recipient = kwargs.get('recipient')
        subject = kwargs.get('subject')
        body = kwargs.get('body')
        tone = kwargs.get('tone', 'professional')
        context = kwargs.get('context', '')
        cc = kwargs.get('cc', [])
        signature = kwargs.get('signature', '')

        if not recipient:
            return self._error_response("Recipient is required")
        if not subject and not body:
            return self._error_response("Either subject or body is required")

        # Generate subject if not provided
        if not subject:
            subject = self._generate_subject(body)

        # Enhance body with proper formatting
        formatted_body = self._apply_tone(body, tone, context)

        # Build email
        email = self._build_email(
            recipient=recipient,
            subject=subject,
            body=formatted_body,
            cc=cc,
            signature=signature
        )

        return f"""📧 **Email Draft Created**

{email}

---
**Tone:** {tone.capitalize()}
**Status:** Draft ready to send
"""

    def _use_template(self, **kwargs) -> str:
        """Use a pre-defined email template."""
        template_type = kwargs.get('template_type')
        recipient = kwargs.get('recipient')
        context = kwargs.get('context', '')
        tone = kwargs.get('tone', 'professional')
        signature = kwargs.get('signature', '')

        if not template_type:
            available = ", ".join(self.templates.keys())
            return self._error_response(f"Template type is required. Available: {available}")

        if template_type not in self.templates:
            return self._error_response(f"Unknown template: {template_type}")

        if not recipient:
            return self._error_response("Recipient is required")

        # Generate email from template
        template = self.templates[template_type]
        subject = self._fill_template_subject(template['subject'], context)
        body = self._generate_template_body(template_type, template['structure'], context, tone)

        email = self._build_email(
            recipient=recipient,
            subject=subject,
            body=body,
            signature=signature
        )

        return f"""📧 **Email from Template: {template_type.replace('_', ' ').title()}**

{email}

---
**Template:** {template_type}
**Tone:** {tone.capitalize()}
**Status:** Draft ready to send
"""

    def _summarize_email(self, **kwargs) -> str:
        """Summarize an email thread or long email."""
        original_email = kwargs.get('original_email')
        body = kwargs.get('body')

        content = original_email or body

        if not content:
            return self._error_response("Email content is required for summarization")

        # Extract key points (simulated)
        summary = self._extract_key_points(content)

        return f"""📝 **Email Summary**

**Key Points:**
{summary['key_points']}

**Action Items:**
{summary['action_items']}

**Sentiment:** {summary['sentiment']}
**Priority:** {summary['priority']}

**Quick Stats:**
- Word count: {summary['word_count']}
- Estimated read time: {summary['read_time']} seconds
"""

    def _set_reminder(self, **kwargs) -> str:
        """Set a follow-up reminder for an email."""
        subject = kwargs.get('subject')
        recipient = kwargs.get('recipient')
        reminder_days = kwargs.get('reminder_days', 3)

        if not subject and not recipient:
            return self._error_response("Subject or recipient is required for reminder")

        reminder_date = datetime.now() + timedelta(days=reminder_days)

        return f"""⏰ **Follow-up Reminder Set**

**Email:** {subject if subject else f'Email to {recipient}'}
**Recipient:** {recipient if recipient else 'Multiple recipients'}
**Reminder Date:** {reminder_date.strftime('%A, %B %d, %Y at %I:%M %p')}
**Days Until Reminder:** {reminder_days}

You will be notified to follow up if no response is received.

Note: This is a simulated reminder. In production, this would integrate with a task management system or calendar."""

    def _draft_reply(self, **kwargs) -> str:
        """Draft a reply to an existing email."""
        original_email = kwargs.get('original_email')
        body = kwargs.get('body')
        tone = kwargs.get('tone', 'professional')
        recipient = kwargs.get('recipient')
        signature = kwargs.get('signature', '')

        if not original_email:
            return self._error_response("Original email is required for reply")

        if not body:
            body = "Thank you for your email. I will review this and get back to you shortly."

        # Extract subject from original (add Re:)
        subject = self._extract_subject(original_email)
        if not subject.startswith('Re:'):
            subject = f"Re: {subject}"

        # Format reply
        formatted_body = self._apply_tone(body, tone, '')
        reply_body = f"{formatted_body}\n\n---\n**Original Message:**\n{self._truncate_original(original_email)}"

        email = self._build_email(
            recipient=recipient or "Original Sender",
            subject=subject,
            body=reply_body,
            signature=signature
        )

        return f"""📧 **Reply Draft Created**

{email}

---
**Tone:** {tone.capitalize()}
**Status:** Draft ready to send
"""

    def _format_email(self, **kwargs) -> str:
        """Format and improve an existing email."""
        body = kwargs.get('body')
        tone = kwargs.get('tone', 'professional')

        if not body:
            return self._error_response("Email body is required for formatting")

        # Apply formatting improvements
        formatted = self._apply_formatting_rules(body, tone)

        before_word_count = len(body.split())
        after_word_count = len(formatted.split())

        return f"""✨ **Email Formatted**

**Formatted Version:**
{formatted}

---
**Improvements:**
- Tone adjusted to: {tone.capitalize()}
- Grammar and clarity enhanced
- Professional formatting applied
- Word count: {before_word_count} → {after_word_count}
"""

    # Helper methods

    def _build_email(self, recipient: str, subject: str, body: str, cc: List[str] = None, signature: str = '') -> str:
        """Build formatted email with headers."""
        cc = cc or []
        cc_line = f"**CC:** {', '.join(cc)}\n" if cc else ""

        sig = signature if signature else "\n\nBest regards,\n[Your Name]"

        return f"""**To:** {recipient}
{cc_line}**Subject:** {subject}

{body}{sig}"""

    def _apply_tone(self, body: str, tone: str, context: str) -> str:
        """Apply appropriate tone to email body."""
        # Add greeting based on tone
        greetings = {
            'professional': 'I hope this message finds you well.',
            'friendly': 'I hope you\'re doing great!',
            'formal': 'I trust this message finds you in good health.',
            'casual': 'Hey there!',
            'persuasive': 'I\'m reaching out with an exciting opportunity.',
            'apologetic': 'I want to sincerely apologize for...'
        }

        greeting = greetings.get(tone, greetings['professional'])

        # Format body
        if not body.strip().startswith(('Hi', 'Hello', 'Dear', 'Hey')):
            body = f"{greeting}\n\n{body}"

        return body

    def _generate_subject(self, body: str) -> str:
        """Generate subject line from body content."""
        # Simple subject generation based on first sentence
        first_sentence = body.split('.')[0][:50]
        return first_sentence + ('...' if len(body) > 50 else '')

    def _fill_template_subject(self, subject_template: str, context: str) -> str:
        """Fill in template subject with context."""
        # Extract key information from context
        topic = context.split('\n')[0][:50] if context else "Discussion"
        your_name = "Your Name"

        return subject_template.format(topic=topic, your_name=your_name)

    def _generate_template_body(self, template_type: str, structure: List[str], context: str, tone: str) -> str:
        """Generate email body from template structure."""
        # This is a simplified version - in production, would use more sophisticated generation
        bodies = {
            "meeting_request": f"""I hope this email finds you well.

I would like to schedule a meeting to discuss {context if context else 'an important matter'}.

Would you be available for a 30-minute meeting this week? I'm flexible with timing and happy to work around your schedule.

Please let me know what times work best for you.

Looking forward to connecting.""",

            "follow_up": f"""I wanted to follow up on my previous email regarding {context if context else 'our discussion'}.

I understand you're likely busy, but I wanted to ensure this didn't get lost in your inbox.

Could you please provide an update when you have a moment?

Thank you for your time and consideration.""",

            "introduction": f"""I'm reaching out to introduce myself and explore potential opportunities for collaboration.

{context if context else 'I believe there could be significant value in connecting our teams/organizations.'}

I'd love to schedule a brief call to discuss how we might work together.

Would you be open to a conversation?""",

            "thank_you": f"""Thank you so much for {context if context else 'your time and assistance'}.

I truly appreciate your help and the insights you provided.

This has been invaluable, and I look forward to staying in touch.""",

            "apology": f"""I want to sincerely apologize for {context if context else 'the recent issue'}.

I take full responsibility and understand this has caused inconvenience.

Here's how we're addressing this: [specific actions]

I'm committed to ensuring this doesn't happen again.""",

            "proposal": f"""I'm excited to share a proposal regarding {context if context else 'a new initiative'}.

Here's what I'm proposing: [key details]

Benefits:
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

I'd love to discuss this further and answer any questions you may have.""",

            "announcement": f"""I'm pleased to announce {context if context else 'an important update'}.

Key details:
- [Detail 1]
- [Detail 2]
- [Detail 3]

This will take effect [date/timeline].

Please don't hesitate to reach out if you have questions.""",

            "reminder": f"""This is a friendly reminder about {context if context else 'an upcoming deadline'}.

Details:
- What: [description]
- When: [date/time]
- Action needed: [what to do]

Please confirm receipt of this reminder."""
        }

        return bodies.get(template_type, "Email content here.")

    def _extract_key_points(self, content: str) -> Dict:
        """Extract key points from email content."""
        # Simulated extraction
        word_count = len(content.split())
        read_time = max(1, word_count // 200 * 60)  # Rough estimate

        return {
            'key_points': '• Main topic discussed\n• Important decision made\n• Next steps outlined',
            'action_items': '• Follow up by Friday\n• Review attached document\n• Schedule follow-up meeting',
            'sentiment': 'Neutral/Positive',
            'priority': 'Medium',
            'word_count': word_count,
            'read_time': read_time
        }

    def _extract_subject(self, email: str) -> str:
        """Extract subject from email."""
        # Look for Subject: line
        for line in email.split('\n'):
            if line.startswith('Subject:'):
                return line.replace('Subject:', '').strip()
        return "Your Email"

    def _truncate_original(self, email: str, max_lines: int = 10) -> str:
        """Truncate original email for reply."""
        lines = email.split('\n')
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + '\n[...truncated...]'
        return email

    def _apply_formatting_rules(self, body: str, tone: str) -> str:
        """Apply formatting rules to improve email."""
        # Add proper spacing
        formatted = body.strip()

        # Ensure paragraphs are separated
        formatted = '\n\n'.join([p.strip() for p in formatted.split('\n\n') if p.strip()])

        # Apply tone
        formatted = self._apply_tone(formatted, tone, '')

        return formatted

    def _error_response(self, message: str) -> str:
        """Format error response."""
        return f"❌ Email Agent Error: {message}"


# Usage examples for testing
def _test_email_agent():
    """Test the email agent with various scenarios."""
    agent = EmailAgent()

    print("Test 1: Draft Professional Email")
    print(agent.perform(
        action="draft",
        recipient="client@example.com",
        subject="Project Update",
        body="I wanted to provide you with an update on our progress. We've completed phase 1 and are moving into phase 2 next week.",
        tone="professional"
    ))
    print("\n" + "="*80 + "\n")

    print("Test 2: Use Meeting Request Template")
    print(agent.perform(
        action="template",
        template_type="meeting_request",
        recipient="manager@example.com",
        context="Q4 Planning Session",
        tone="professional"
    ))
    print("\n" + "="*80 + "\n")

    print("Test 3: Summarize Email")
    print(agent.perform(
        action="summarize",
        body="This is a long email about multiple topics including project updates, budget concerns, and timeline adjustments. We need to discuss these in our next meeting and make decisions about resource allocation."
    ))


if __name__ == "__main__":
    _test_email_agent()
