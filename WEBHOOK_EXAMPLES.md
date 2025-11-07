# Webhook Integration Examples

Real-world examples for integrating AI Ambassador Platform webhooks with popular services and platforms.

## Table of Contents

1. [Python Webhook Receiver](#python-webhook-receiver)
2. [Node.js Webhook Receiver](#nodejs-webhook-receiver)
3. [Slack Integration](#slack-integration)
4. [Zapier Integration](#zapier-integration)
5. [Make (Integromat) Integration](#make-integration)
6. [Salesforce Integration](#salesforce-integration)
7. [Discord Integration](#discord-integration)
8. [Google Sheets Integration](#google-sheets-integration)

## Python Webhook Receiver

### Flask Example

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

WEBHOOK_SECRET = 'your-webhook-secret-here'

def verify_signature(payload, signature, secret):
    """Verify HMAC-SHA256 signature"""
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected}"
    return hmac.compare_digest(signature, expected_sig)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    # Get raw request body
    payload = request.data.decode('utf-8')

    # Get signature from header
    signature = request.headers.get('X-Webhook-Signature')

    if not signature:
        logging.warning('No signature provided')
        return jsonify({'error': 'No signature'}), 401

    # Verify signature
    if not verify_signature(payload, signature, WEBHOOK_SECRET):
        logging.warning('Invalid signature')
        return jsonify({'error': 'Invalid signature'}), 401

    # Parse event
    event = json.loads(payload)

    logging.info(f"Received event: {event['event_type']} [{event['event_id']}]")

    # Route to appropriate handler
    handlers = {
        'conversation.started': handle_conversation_started,
        'message.sent': handle_message_sent,
        'message.received': handle_message_received,
        'qr.scanned': handle_qr_scanned,
        'user.banned': handle_user_banned,
        'moderation.flagged': handle_moderation_flagged,
        'analytics.milestone': handle_analytics_milestone
    }

    handler = handlers.get(event['event_type'])
    if handler:
        try:
            handler(event)
        except Exception as e:
            logging.error(f"Error handling event: {e}")
            # Still return 200 to prevent retries for processing errors
            return jsonify({'status': 'error', 'message': str(e)}), 200
    else:
        logging.warning(f"No handler for event type: {event['event_type']}")

    return jsonify({'status': 'success'}), 200

def handle_conversation_started(event):
    """Handle conversation started event"""
    user_guid = event.get('user_guid')
    ambassador_id = event.get('ambassador_id')

    logging.info(f"New conversation: User {user_guid} with Ambassador {ambassador_id}")

    # Your business logic
    # - Create CRM lead
    # - Send welcome email
    # - Log to analytics

def handle_message_sent(event):
    """Handle user message event"""
    message = event['data'].get('message')
    user_guid = event.get('user_guid')

    logging.info(f"User {user_guid} sent: {message}")

    # Your business logic
    # - Save to database
    # - Analyze sentiment
    # - Trigger workflows

def handle_message_received(event):
    """Handle AI response event"""
    message = event['data'].get('message')
    ambassador_id = event.get('ambassador_id')

    logging.info(f"Ambassador {ambassador_id} responded: {message}")

    # Your business logic
    # - Save to database
    # - Update conversation state

def handle_qr_scanned(event):
    """Handle QR code scan event"""
    ambassador_id = event.get('ambassador_id')
    location = event['data'].get('location')

    logging.info(f"QR scanned: Ambassador {ambassador_id} at {location}")

    # Your business logic
    # - Track foot traffic
    # - Send location-based offers
    # - Update analytics

def handle_user_banned(event):
    """Handle user banned event"""
    user_guid = event.get('user_guid')
    reason = event['data'].get('reason')

    logging.warning(f"User {user_guid} banned: {reason}")

    # Your business logic
    # - Notify admin
    # - Update user record
    # - Blacklist in other systems

def handle_moderation_flagged(event):
    """Handle content flagged event"""
    content = event['data'].get('content')
    reason = event['data'].get('reason')
    user_guid = event.get('user_guid')

    logging.warning(f"Content flagged from {user_guid}: {reason}")

    # Your business logic
    # - Alert moderation team
    # - Create review task
    # - Notify user

def handle_analytics_milestone(event):
    """Handle analytics milestone event"""
    milestone = event['data'].get('milestone')
    value = event['data'].get('value')

    logging.info(f"Milestone reached: {milestone} = {value}")

    # Your business logic
    # - Send celebration message
    # - Update dashboards
    # - Notify stakeholders

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### FastAPI Example

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

WEBHOOK_SECRET = 'your-webhook-secret-here'

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    expected_sig = f"sha256={expected}"
    return hmac.compare_digest(signature, expected_sig)

@app.post("/webhook")
async def webhook_handler(request: Request):
    # Get raw body
    payload = await request.body()

    # Get signature
    signature = request.headers.get('x-webhook-signature')

    if not signature or not verify_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    event = await request.json()

    logging.info(f"Received: {event['event_type']}")

    # Process event asynchronously
    # await process_event(event)

    return {"status": "success"}
```

## Node.js Webhook Receiver

### Express.js Example

```javascript
const express = require('express');
const crypto = require('crypto');
const bodyParser = require('body-parser');

const app = express();
const WEBHOOK_SECRET = 'your-webhook-secret-here';

// Use raw body parser for signature verification
app.use(bodyParser.json({
    verify: (req, res, buf) => {
        req.rawBody = buf.toString('utf8');
    }
}));

function verifySignature(payload, signature, secret) {
    const expected = crypto
        .createHmac('sha256', secret)
        .update(payload)
        .digest('hex');
    const expectedSig = `sha256=${expected}`;

    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(expectedSig)
    );
}

app.post('/webhook', (req, res) => {
    const signature = req.headers['x-webhook-signature'];

    if (!signature) {
        return res.status(401).json({ error: 'No signature' });
    }

    // Verify signature
    if (!verifySignature(req.rawBody, signature, WEBHOOK_SECRET)) {
        return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = req.body;
    console.log(`Received event: ${event.event_type}`);

    // Route to handlers
    switch (event.event_type) {
        case 'conversation.started':
            handleConversationStarted(event);
            break;
        case 'message.sent':
            handleMessageSent(event);
            break;
        case 'qr.scanned':
            handleQRScanned(event);
            break;
        default:
            console.log(`No handler for ${event.event_type}`);
    }

    res.json({ status: 'success' });
});

function handleConversationStarted(event) {
    console.log(`New conversation: ${event.user_guid}`);
    // Your business logic
}

function handleMessageSent(event) {
    console.log(`Message: ${event.data.message}`);
    // Your business logic
}

function handleQRScanned(event) {
    console.log(`QR scanned: ${event.ambassador_id}`);
    // Your business logic
}

app.listen(3000, () => {
    console.log('Webhook server running on port 3000');
});
```

## Slack Integration

Send webhook events to Slack channels:

```python
import requests
import json

SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

def send_to_slack(event):
    """Send event notification to Slack"""

    # Format message based on event type
    if event['event_type'] == 'conversation.started':
        message = {
            "text": "New Conversation Started",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎉 New Conversation Started"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*User:*\n{event['user_guid']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Ambassador:*\n{event['ambassador_id']}"
                        }
                    ]
                }
            ]
        }

    elif event['event_type'] == 'moderation.flagged':
        message = {
            "text": "Content Flagged for Review",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ Content Flagged"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Reason:* {event['data']['reason']}\n*Content:* {event['data']['content'][:100]}..."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Review"
                            },
                            "url": f"https://your-app.com/moderation/{event['event_id']}"
                        }
                    ]
                }
            ]
        }

    elif event['event_type'] == 'analytics.milestone':
        message = {
            "text": "Milestone Reached!",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎯 Milestone Reached!"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{event['data']['milestone']}*: {event['data']['value']}"
                    }
                }
            ]
        }

    else:
        # Default message format
        message = {
            "text": f"Event: {event['event_type']}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Event:* {event['event_type']}\n*Data:* ```{json.dumps(event['data'], indent=2)}```"
                    }
                }
            ]
        }

    # Send to Slack
    response = requests.post(SLACK_WEBHOOK_URL, json=message)
    return response.status_code == 200
```

## Zapier Integration

### Setup Instructions

1. Create a **Catch Hook** webhook in Zapier
2. Copy the webhook URL
3. Register the webhook in AI Ambassador Platform
4. Send test event to populate Zapier fields
5. Build your Zap workflow

### Example Zap Workflow

```
Trigger: Webhook - Catch Hook
  ↓
Filter: Only continue if event_type = "conversation.started"
  ↓
Action: Google Sheets - Create Spreadsheet Row
  - Sheet: Conversations
  - User GUID: {{user_guid}}
  - Ambassador: {{ambassador_id}}
  - Timestamp: {{timestamp}}
  ↓
Action: Send Email (Gmail)
  - To: sales@company.com
  - Subject: New conversation started
  - Body: User {{user_guid}} started conversation with {{ambassador_id}}
```

### Zapier Code Step (JavaScript)

```javascript
// Extract and transform webhook data
const event = inputData;

const formattedData = {
    eventType: event.event_type,
    userId: event.user_guid,
    ambassadorId: event.ambassador_id,
    timestamp: new Date(event.timestamp).toLocaleString(),
    data: JSON.stringify(event.data)
};

output = formattedData;
```

## Make Integration

### Setup Instructions

1. Create new scenario in Make
2. Add **Webhooks** module → **Custom webhook**
3. Create new webhook and copy URL
4. Register webhook in AI Ambassador Platform
5. Send test event to determine data structure
6. Add modules to process events

### Example Make Scenario

```
Webhook Trigger
  ↓
Router (by event_type)
  ├─ conversation.started → Salesforce: Create Lead
  ├─ message.sent → Airtable: Create Record
  ├─ qr.scanned → Google Analytics: Send Event
  └─ moderation.flagged → Slack: Send Message
```

### Make Filters

```javascript
// Filter: Only process QR scans from specific location
event.event_type === "qr.scanned" &&
event.data.location === "Store-123"

// Filter: Only high-severity moderation flags
event.event_type === "moderation.flagged" &&
event.data.severity === "high"
```

## Salesforce Integration

Sync conversation data to Salesforce:

```python
from simple_salesforce import Salesforce
import logging

# Initialize Salesforce
sf = Salesforce(
    username='your-username',
    password='your-password',
    security_token='your-token'
)

def handle_conversation_started(event):
    """Create Salesforce lead from conversation"""

    user_guid = event.get('user_guid')
    ambassador_id = event.get('ambassador_id')

    # Create lead
    lead_data = {
        'FirstName': 'AI',
        'LastName': f'User-{user_guid[:8]}',
        'Company': 'Unknown',
        'LeadSource': 'AI Ambassador',
        'Description': f'Conversation with {ambassador_id}',
        'Status': 'New',
        # Custom fields
        'User_GUID__c': user_guid,
        'Ambassador_ID__c': ambassador_id,
        'Conversation_Started__c': event['timestamp']
    }

    try:
        result = sf.Lead.create(lead_data)
        logging.info(f"Created Salesforce lead: {result['id']}")
    except Exception as e:
        logging.error(f"Error creating Salesforce lead: {e}")

def handle_message_sent(event):
    """Log message as Salesforce task"""

    user_guid = event.get('user_guid')
    message = event['data'].get('message')

    # Find lead by user GUID
    leads = sf.query(f"SELECT Id FROM Lead WHERE User_GUID__c = '{user_guid}'")

    if leads['totalSize'] > 0:
        lead_id = leads['records'][0]['Id']

        # Create task
        task_data = {
            'WhoId': lead_id,
            'Subject': 'User Message',
            'Description': message,
            'Status': 'Completed',
            'ActivityDate': event['timestamp']
        }

        try:
            sf.Task.create(task_data)
            logging.info(f"Created task for lead {lead_id}")
        except Exception as e:
            logging.error(f"Error creating task: {e}")
```

## Discord Integration

Send webhook events to Discord:

```python
import requests

DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/YOUR/WEBHOOK/URL'

def send_to_discord(event):
    """Send event to Discord channel"""

    # Format embed based on event type
    if event['event_type'] == 'conversation.started':
        embed = {
            "title": "🎉 New Conversation",
            "description": f"User started conversation with {event['ambassador_id']}",
            "color": 5814783,  # Blue
            "fields": [
                {
                    "name": "User GUID",
                    "value": event['user_guid'],
                    "inline": True
                },
                {
                    "name": "Ambassador",
                    "value": event['ambassador_id'],
                    "inline": True
                }
            ],
            "timestamp": event['timestamp']
        }

    elif event['event_type'] == 'moderation.flagged':
        embed = {
            "title": "⚠️ Content Flagged",
            "description": event['data']['reason'],
            "color": 15158332,  # Red
            "fields": [
                {
                    "name": "Content",
                    "value": event['data']['content'][:1024]
                }
            ],
            "timestamp": event['timestamp']
        }

    else:
        embed = {
            "title": f"Event: {event['event_type']}",
            "description": f"```json\n{json.dumps(event['data'], indent=2)}```",
            "color": 3447003,  # Gray
            "timestamp": event['timestamp']
        }

    payload = {
        "embeds": [embed]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    return response.status_code == 204
```

## Google Sheets Integration

Log events to Google Sheets:

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup Google Sheets API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open spreadsheet
sheet = client.open('AI Ambassador Events').sheet1

def log_to_sheets(event):
    """Log event to Google Sheets"""

    row = [
        event['event_id'],
        event['event_type'],
        event['timestamp'],
        event.get('user_guid', ''),
        event.get('ambassador_id', ''),
        json.dumps(event['data'])
    ]

    sheet.append_row(row)
    logging.info(f"Logged event {event['event_id']} to Google Sheets")
```

## Testing Your Integration

### Test with curl

```bash
# Simulate webhook delivery
curl -X POST https://your-app.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=test" \
  -H "X-Event-Type: conversation.started" \
  -d '{
    "event_id": "test-123",
    "event_type": "conversation.started",
    "timestamp": "2025-11-07T10:30:00Z",
    "data": {},
    "user_guid": "test-user",
    "ambassador_id": "test-ambassador"
  }'
```

### Test with AI Ambassador Platform

```bash
# Use the test endpoint
curl -X POST http://localhost:7071/api/webhooks/{webhook_id}/test \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "conversation.started",
    "data": {"test": true}
  }'
```

## Performance Tips

1. **Respond quickly**: Return 200 immediately, process asynchronously
2. **Queue processing**: Use task queue (Celery, Bull, etc.)
3. **Batch operations**: Group database writes
4. **Cache lookups**: Cache frequently accessed data
5. **Monitor performance**: Track webhook processing time
6. **Scale horizontally**: Add more webhook workers as needed

## Error Handling

```python
@app.route('/webhook', methods=['POST'])
def webhook_handler():
    try:
        # Verify signature
        # Parse event
        # Process event

        return jsonify({'status': 'success'}), 200

    except SignatureError:
        # Invalid signature - return 401
        return jsonify({'error': 'Invalid signature'}), 401

    except ValidationError as e:
        # Malformed event - return 400 (no retry)
        return jsonify({'error': str(e)}), 400

    except ProcessingError as e:
        # Processing error - return 200 (prevent retry)
        logging.error(f"Processing error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 200

    except Exception as e:
        # Unexpected error - return 500 (will retry)
        logging.exception("Unexpected error")
        return jsonify({'error': 'Internal error'}), 500
```
