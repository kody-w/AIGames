# Webhook Guide - AI Ambassador Platform

Complete guide to using webhooks for real-time event notifications and integrations.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Event Types](#event-types)
4. [Security](#security)
5. [Webhook Registration](#webhook-registration)
6. [Event Delivery](#event-delivery)
7. [Retry Logic](#retry-logic)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

## Overview

Webhooks enable real-time event notifications from the AI Ambassador Platform to your external systems. When events occur (conversations, QR scans, moderation flags, etc.), the platform will send HTTP POST requests to your registered webhook URLs.

### Key Features

- **Real-time notifications**: Receive events as they happen
- **Event filtering**: Subscribe to specific event types
- **Secure delivery**: HMAC-SHA256 signature verification
- **Reliable delivery**: Automatic retry with exponential backoff
- **Delivery logs**: Track all delivery attempts
- **Dead letter queue**: Manual retry for failed deliveries

### Use Cases

- **CRM Integration**: Sync conversation data to Salesforce, HubSpot
- **Analytics**: Send events to analytics platforms (Mixpanel, Segment)
- **Notifications**: Alert teams via Slack, Teams, Discord
- **Automation**: Trigger workflows in Zapier, Make, n8n
- **Data Warehouse**: Stream events to BigQuery, Snowflake
- **Monitoring**: Send alerts to PagerDuty, Opsgenie

## Getting Started

### 1. Create a Webhook Endpoint

Your webhook endpoint must:
- Accept HTTP POST requests
- Use HTTPS (required for production)
- Respond within 30 seconds
- Return 2xx status code for success
- Verify HMAC signature (recommended)

**Example endpoint (Python/Flask):**

```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    # Get request body and signature
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Webhook-Signature')

    # Verify signature
    secret = 'your-webhook-secret'
    expected_sig = verify_signature(payload, signature, secret)

    if not expected_sig:
        return 'Invalid signature', 401

    # Process event
    event = request.json
    print(f"Received event: {event['event_type']}")

    # Your business logic here
    process_event(event)

    return 'OK', 200

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected}"
    return hmac.compare_digest(signature, expected_sig)
```

### 2. Register Your Webhook

**Using the API:**

```bash
curl -X POST http://localhost:7071/api/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "event_types": ["conversation.started", "message.sent", "message.received"],
    "filters": {}
  }'
```

**Response:**

```json
{
  "webhook_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "url": "https://your-app.com/webhook",
  "event_types": ["conversation.started", "message.sent", "message.received"],
  "secret_key": "whsec_a1b2c3d4e5f67890...",
  "status": "active",
  "created_at": "2025-11-07T10:30:00Z"
}
```

**Save the `secret_key`** - you'll need it to verify webhook signatures.

### 3. Test Your Webhook

```bash
curl -X POST http://localhost:7071/api/webhooks/{webhook_id}/test \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "system.info",
    "data": {"test": true, "message": "Test webhook"}
  }'
```

## Event Types

### Ambassador Events

| Event Type | Description | Data |
|------------|-------------|------|
| `ambassador.created` | New ambassador created | `ambassador` object |
| `ambassador.updated` | Ambassador config changed | `changes` object |
| `ambassador.deleted` | Ambassador removed | `ambassador_id` |

### Conversation Events

| Event Type | Description | Data |
|------------|-------------|------|
| `conversation.started` | New conversation began | `user_guid`, `ambassador_id` |
| `conversation.ended` | Conversation finished | `summary` object |
| `conversation.resumed` | User returned | `user_guid`, `ambassador_id` |

### Message Events

| Event Type | Description | Data |
|------------|-------------|------|
| `message.sent` | User sent message | `message` text |
| `message.received` | AI responded | `message` text |
| `message.edited` | Message edited | `old_message`, `new_message` |
| `message.deleted` | Message deleted | `message_id` |

### QR Code Events

| Event Type | Description | Data |
|------------|-------------|------|
| `qr.scanned` | QR code scanned | `ambassador_id`, `location` |
| `qr.generated` | QR code created | `ambassador_id`, `qr_code_url` |

### User Events

| Event Type | Description | Data |
|------------|-------------|------|
| `user.created` | New user registered | `user` object |
| `user.updated` | User profile changed | `user_guid`, `changes` |
| `user.banned` | User banned | `reason` |
| `user.unbanned` | User unbanned | `user_guid` |

### Moderation Events

| Event Type | Description | Data |
|------------|-------------|------|
| `moderation.flagged` | Content flagged | `content`, `reason`, `severity` |
| `moderation.approved` | Flagged content approved | `content_id` |
| `moderation.rejected` | Flagged content rejected | `content_id` |

### Analytics Events

| Event Type | Description | Data |
|------------|-------------|------|
| `analytics.milestone` | Milestone reached | `milestone`, `value` |
| `analytics.report` | Analytics report ready | `report_url` |

### System Events

| Event Type | Description | Data |
|------------|-------------|------|
| `system.error` | System error occurred | `error`, `stack_trace` |
| `system.warning` | Warning condition | `warning`, `details` |
| `system.info` | Information message | `message` |

## Event Schema

All events follow this schema:

```json
{
  "event_id": "uuid",
  "event_type": "conversation.started",
  "timestamp": "2025-11-07T10:30:00Z",
  "data": {
    "...": "event-specific data"
  },
  "user_guid": "user-guid-if-applicable",
  "ambassador_id": "ambassador-id-if-applicable",
  "metadata": {
    "...": "additional metadata"
  }
}
```

## Security

### HMAC Signature Verification

Every webhook delivery includes an `X-Webhook-Signature` header with an HMAC-SHA256 signature:

```
X-Webhook-Signature: sha256=a1b2c3d4e5f67890...
```

**Always verify signatures** to ensure requests are from the AI Ambassador Platform.

### Verification Examples

**Python:**

```python
import hmac
import hashlib

def verify_webhook(request_body, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected}"
    return hmac.compare_digest(signature, expected_sig)
```

**Node.js:**

```javascript
const crypto = require('crypto');

function verifyWebhook(requestBody, signature, secret) {
    const expected = crypto
        .createHmac('sha256', secret)
        .update(requestBody)
        .digest('hex');
    const expectedSig = `sha256=${expected}`;
    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(expectedSig)
    );
}
```

**PHP:**

```php
function verifyWebhook($requestBody, $signature, $secret) {
    $expected = hash_hmac('sha256', $requestBody, $secret);
    $expectedSig = 'sha256=' . $expected;
    return hash_equals($signature, $expectedSig);
}
```

### Headers Sent with Every Webhook

```
Content-Type: application/json
X-Webhook-Signature: sha256=...
X-Webhook-ID: webhook-id
X-Event-Type: conversation.started
X-Event-ID: event-id
X-Delivery-Attempt: 1
User-Agent: AI-Ambassador-Webhooks/1.0
```

## Webhook Registration

### Register New Webhook

```
POST /api/webhooks
```

**Request:**

```json
{
  "url": "https://your-app.com/webhook",
  "event_types": ["conversation.started", "message.sent"],
  "secret_key": "optional-custom-secret",
  "filters": {
    "ambassador_id": "specific-ambassador-id"
  }
}
```

**Response (201 Created):**

```json
{
  "webhook_id": "uuid",
  "url": "https://your-app.com/webhook",
  "event_types": ["conversation.started", "message.sent"],
  "secret_key": "whsec_...",
  "status": "active",
  "filters": {},
  "created_at": "2025-11-07T10:30:00Z"
}
```

### List Webhooks

```
GET /api/webhooks
```

**Response:**

```json
{
  "webhooks": [...],
  "total": 5
}
```

### Get Webhook Details

```
GET /api/webhooks/{webhook_id}
```

### Update Webhook

```
PUT /api/webhooks/{webhook_id}
```

**Request:**

```json
{
  "url": "https://new-url.com/webhook",
  "event_types": ["conversation.started"],
  "status": "inactive"
}
```

### Delete Webhook

```
DELETE /api/webhooks/{webhook_id}
```

## Event Delivery

### Delivery Process

1. Event occurs in the platform
2. Event is published to event system
3. Webhook manager finds matching webhooks
4. HTTP POST request sent to each webhook URL
5. Response validated (2xx = success)
6. Delivery logged

### Delivery Expectations

- **Timeout**: 30 seconds
- **Success**: HTTP 2xx response
- **Failure**: HTTP 4xx, 5xx, timeout, connection error
- **Retry**: Automatic retry on failure

### Event Filtering

Webhooks can filter events by:

```json
{
  "filters": {
    "ambassador_id": "specific-ambassador",
    "user_guid": "specific-user"
  }
}
```

Only events matching **all** filter criteria will be delivered.

## Retry Logic

### Exponential Backoff

Failed deliveries are automatically retried with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 1 minute |
| 3 | 5 minutes |
| 4 | 15 minutes |

After 4 failed attempts, the event is moved to the **dead letter queue**.

### Manual Retry

Retry failed deliveries manually:

```
POST /api/webhooks/{webhook_id}/retry
```

**Request:**

```json
{
  "event": {
    "event_id": "uuid",
    "event_type": "conversation.started",
    "...": "..."
  }
}
```

## Monitoring

### View Delivery Log

```
GET /api/webhooks/{webhook_id}/deliveries?limit=100
```

**Response:**

```json
{
  "webhook_id": "uuid",
  "deliveries": [
    {
      "attempt_id": "uuid",
      "event": {...},
      "attempt_number": 0,
      "status": "success",
      "timestamp": "2025-11-07T10:30:00Z",
      "response_code": 200,
      "duration_ms": 150.5
    }
  ],
  "total": 42
}
```

### Get Statistics

```
GET /api/webhooks/{webhook_id}/stats
```

**Response:**

```json
{
  "webhook_id": "uuid",
  "stats": {
    "total_deliveries": 1000,
    "successful_deliveries": 995,
    "failed_deliveries": 5,
    "success_rate": 99.5,
    "average_duration_ms": 145.2
  }
}
```

### Global Statistics

```
GET /api/webhooks/stats
```

**Response:**

```json
{
  "stats": {
    "total_webhooks": 10,
    "active_webhooks": 8,
    "total_deliveries": 5000,
    "successful_deliveries": 4950,
    "failed_deliveries": 50,
    "success_rate": 99.0,
    "dead_letter_queue_size": 5
  }
}
```

## Troubleshooting

### Webhook Not Receiving Events

1. **Check webhook status**: Ensure `status: "active"`
2. **Verify event types**: Check `event_types` includes the events you expect
3. **Review filters**: Ensure filters match the events
4. **Check delivery log**: Look for failed attempts
5. **Test webhook**: Use the test endpoint

### Signature Verification Fails

1. **Check secret key**: Ensure you're using the correct secret
2. **Use raw request body**: Don't parse JSON before verification
3. **Check encoding**: Use UTF-8 encoding
4. **Timing attack protection**: Use `hmac.compare_digest()` or equivalent

### High Latency

1. **Optimize endpoint**: Process events asynchronously
2. **Return immediately**: Respond with 200 before processing
3. **Check network**: Ensure low latency connection
4. **Scale endpoint**: Use load balancer if needed

### Failed Deliveries

1. **Check endpoint availability**: Ensure endpoint is accessible
2. **Review response codes**: Check what your endpoint is returning
3. **Check timeout**: Ensure processing takes < 30 seconds
4. **Review error logs**: Check delivery log for error messages

### Dead Letter Queue Growing

1. **Fix endpoint issues**: Resolve underlying delivery problems
2. **Manual retry**: Retry failed deliveries after fixing issues
3. **Update webhook URL**: If endpoint moved, update webhook
4. **Disable webhook**: Temporarily disable if endpoint is down

## Best Practices

1. **Verify signatures**: Always verify HMAC signatures
2. **Respond quickly**: Return 200 immediately, process asynchronously
3. **Idempotency**: Handle duplicate events gracefully (same `event_id`)
4. **Error handling**: Log errors but don't crash on malformed events
5. **Rate limiting**: Implement rate limiting on your endpoint
6. **Monitoring**: Set up alerts for failed deliveries
7. **Testing**: Use test endpoint before going live
8. **Documentation**: Document your webhook handler for your team

## Support

For issues or questions:

- **Documentation**: See `WEBHOOK_EXAMPLES.md` for integration examples
- **API Reference**: See function_app.py webhook endpoints
- **Event System**: See utils/event_system.py for event details
- **Webhook Manager**: See utils/webhook_manager.py for delivery logic
