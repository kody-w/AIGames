#!/usr/bin/env python3
"""
Example Webhook Receiver for AI Ambassador Platform

This is a sample webhook endpoint that receives and processes events
from the AI Ambassador Platform. Use this as a starting point for
your integration.

Features:
- HMAC signature verification
- Event routing by type
- Error handling
- Logging

Usage:
    python webhook-receiver-example.py

Then register this webhook:
    curl -X POST http://localhost:7071/api/webhooks \
      -H "Content-Type: application/json" \
      -d '{
        "url": "http://localhost:5000/webhook",
        "event_types": ["conversation.started", "message.sent", "qr.scanned"]
      }'
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = 'your-webhook-secret-here'  # Replace with your actual secret


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify HMAC-SHA256 signature

    Args:
        payload: Raw request body
        signature: Signature from X-Webhook-Signature header
        secret: Webhook secret key

    Returns:
        True if signature is valid
    """
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected}"

    return hmac.compare_digest(signature, expected_sig)


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Main webhook endpoint

    Receives POST requests from AI Ambassador Platform
    """
    try:
        # Get raw request body
        payload = request.data.decode('utf-8')

        # Get signature from header
        signature = request.headers.get('X-Webhook-Signature')
        event_type = request.headers.get('X-Event-Type')
        event_id = request.headers.get('X-Event-ID')

        logger.info(f"Received webhook: {event_type} [{event_id}]")

        # Verify signature
        if not signature:
            logger.warning('No signature provided')
            return jsonify({'error': 'No signature'}), 401

        if not verify_signature(payload, signature, WEBHOOK_SECRET):
            logger.warning('Invalid signature')
            return jsonify({'error': 'Invalid signature'}), 401

        # Parse event
        event = json.loads(payload)

        # Route to appropriate handler
        handlers = {
            'ambassador.created': handle_ambassador_created,
            'ambassador.updated': handle_ambassador_updated,
            'ambassador.deleted': handle_ambassador_deleted,
            'conversation.started': handle_conversation_started,
            'conversation.ended': handle_conversation_ended,
            'message.sent': handle_message_sent,
            'message.received': handle_message_received,
            'qr.scanned': handle_qr_scanned,
            'qr.generated': handle_qr_generated,
            'user.created': handle_user_created,
            'user.banned': handle_user_banned,
            'moderation.flagged': handle_moderation_flagged,
            'analytics.milestone': handle_analytics_milestone,
            'system.error': handle_system_error
        }

        handler = handlers.get(event['event_type'])

        if handler:
            # Process event
            result = handler(event)
            logger.info(f"Event processed successfully: {event_id}")
            return jsonify({'status': 'success', 'result': result}), 200
        else:
            logger.warning(f"No handler for event type: {event['event_type']}")
            return jsonify({'status': 'success', 'message': 'No handler'}), 200

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return jsonify({'error': 'Invalid JSON'}), 400

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        # Return 200 to prevent retries for processing errors
        return jsonify({'status': 'error', 'message': str(e)}), 200


# =============================================================================
# Event Handlers
# =============================================================================

def handle_ambassador_created(event):
    """Handle ambassador created event"""
    ambassador = event['data'].get('ambassador', {})
    ambassador_id = event.get('ambassador_id')

    logger.info(f"New ambassador created: {ambassador_id}")

    # Your business logic here
    # Examples:
    # - Send notification to admin
    # - Create ambassador profile in CRM
    # - Initialize analytics tracking

    return {'ambassador_id': ambassador_id}


def handle_ambassador_updated(event):
    """Handle ambassador updated event"""
    changes = event['data'].get('changes', {})
    ambassador_id = event.get('ambassador_id')

    logger.info(f"Ambassador updated: {ambassador_id}")

    # Your business logic here
    # Examples:
    # - Update ambassador profile
    # - Notify subscribers
    # - Log change history

    return {'updated': True}


def handle_ambassador_deleted(event):
    """Handle ambassador deleted event"""
    ambassador_id = event.get('ambassador_id')

    logger.info(f"Ambassador deleted: {ambassador_id}")

    # Your business logic here
    # Examples:
    # - Archive ambassador data
    # - Notify users
    # - Clean up resources

    return {'deleted': True}


def handle_conversation_started(event):
    """Handle conversation started event"""
    user_guid = event.get('user_guid')
    ambassador_id = event.get('ambassador_id')

    logger.info(f"Conversation started: User {user_guid} with {ambassador_id}")

    # Your business logic here
    # Examples:
    # - Create CRM lead
    # - Send welcome email
    # - Initialize user session
    # - Track in analytics

    return {
        'user_guid': user_guid,
        'ambassador_id': ambassador_id,
        'action': 'lead_created'
    }


def handle_conversation_ended(event):
    """Handle conversation ended event"""
    user_guid = event.get('user_guid')
    summary = event['data'].get('summary', {})

    logger.info(f"Conversation ended: User {user_guid}")

    # Your business logic here
    # Examples:
    # - Save conversation transcript
    # - Update CRM
    # - Send follow-up email
    # - Calculate satisfaction score

    return {'conversation_saved': True}


def handle_message_sent(event):
    """Handle user message sent event"""
    message = event['data'].get('message')
    user_guid = event.get('user_guid')
    ambassador_id = event.get('ambassador_id')

    logger.info(f"Message from {user_guid}: {message[:50]}...")

    # Your business logic here
    # Examples:
    # - Save to database
    # - Analyze sentiment
    # - Detect keywords
    # - Trigger workflows

    return {'message_logged': True}


def handle_message_received(event):
    """Handle AI response event"""
    message = event['data'].get('message')
    ambassador_id = event.get('ambassador_id')

    logger.info(f"AI response from {ambassador_id}: {message[:50]}...")

    # Your business logic here
    # Examples:
    # - Save to database
    # - Update conversation state
    # - Track response quality

    return {'response_logged': True}


def handle_qr_scanned(event):
    """Handle QR code scanned event"""
    ambassador_id = event.get('ambassador_id')
    location = event['data'].get('location')
    user_guid = event.get('user_guid')

    logger.info(f"QR scanned: {ambassador_id} at {location} by {user_guid}")

    # Your business logic here
    # Examples:
    # - Track foot traffic
    # - Send location-based offer
    # - Update analytics
    # - Trigger welcome message

    return {
        'location': location,
        'ambassador_id': ambassador_id,
        'tracked': True
    }


def handle_qr_generated(event):
    """Handle QR code generated event"""
    ambassador_id = event.get('ambassador_id')
    qr_url = event['data'].get('qr_code_url')

    logger.info(f"QR generated for {ambassador_id}: {qr_url}")

    # Your business logic here
    # Examples:
    # - Save QR code to database
    # - Email to stakeholder
    # - Generate printable materials

    return {'qr_saved': True}


def handle_user_created(event):
    """Handle user created event"""
    user_guid = event.get('user_guid')
    user_data = event['data'].get('user', {})

    logger.info(f"New user created: {user_guid}")

    # Your business logic here
    # Examples:
    # - Create user profile
    # - Send welcome email
    # - Initialize preferences
    # - Add to mailing list

    return {'user_created': True}


def handle_user_banned(event):
    """Handle user banned event"""
    user_guid = event.get('user_guid')
    reason = event['data'].get('reason')

    logger.warning(f"User banned: {user_guid} - {reason}")

    # Your business logic here
    # Examples:
    # - Notify admin team
    # - Update user record
    # - Blacklist in other systems
    # - Generate report

    return {'user_banned': True}


def handle_moderation_flagged(event):
    """Handle content flagged event"""
    content = event['data'].get('content')
    reason = event['data'].get('reason')
    severity = event['data'].get('severity', 'medium')
    user_guid = event.get('user_guid')

    logger.warning(f"Content flagged: {reason} (severity: {severity})")

    # Your business logic here
    # Examples:
    # - Alert moderation team
    # - Create review task
    # - Notify user
    # - Update user trust score

    return {
        'flagged': True,
        'severity': severity,
        'review_required': severity in ['high', 'critical']
    }


def handle_analytics_milestone(event):
    """Handle analytics milestone event"""
    milestone = event['data'].get('milestone')
    value = event['data'].get('value')

    logger.info(f"Milestone reached: {milestone} = {value}")

    # Your business logic here
    # Examples:
    # - Send celebration message
    # - Update dashboards
    # - Notify stakeholders
    # - Generate report

    return {
        'milestone': milestone,
        'value': value,
        'celebrated': True
    }


def handle_system_error(event):
    """Handle system error event"""
    error = event['data'].get('error')
    details = event['data'].get('details', {})

    logger.error(f"System error: {error}")

    # Your business logic here
    # Examples:
    # - Alert on-call engineer
    # - Create incident ticket
    # - Log to monitoring system
    # - Trigger auto-remediation

    return {'error_logged': True}


# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'webhook-receiver'
    }), 200


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    logger.info("Starting webhook receiver...")
    logger.info("Endpoint: http://localhost:5000/webhook")
    logger.info("Remember to update WEBHOOK_SECRET with your actual secret!")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
