# Quick Start: Ambassador Entry Endpoint

## Setup in 5 Minutes

### 1. Upload Ambassador Configuration

Upload an ambassador configuration to Azure File Storage:

**Path:** `ambassador_catalogue/creative-001.json`

**Content:** Use the example from `/Users/kodyw/AIGames/ambassador-creative-001.json`

### 2. Start Local Testing

```bash
cd Copilot-Agent-365-main
./run.sh  # Mac/Linux
```

### 3. Test the Endpoint

```bash
curl http://localhost:7071/api/ambassador_entry/creative-001?source=test
```

### 4. Expected Response

```json
{
  "ambassador": {
    "id": "creative-001",
    "name": "CreativeBot",
    "display_name": "Creative Companion",
    "avatar": {"type": "emoji", "value": "🎨"},
    "world": {...},
    "capabilities": [...]
  },
  "session": {
    "user_guid": "demo-creative-001",
    "is_demo": true,
    "session_id": "...",
    "agent_endpoint": "/api/businessinsightbot_function"
  },
  "analytics": {
    "scan_id": "...",
    "timestamp": "...",
    "source": "test"
  }
}
```

## Usage Flow

### Step 1: User Scans QR Code

QR Code URL:
```
https://your-app.azurewebsites.net/api/ambassador_entry/creative-001?source=gallery
```

### Step 2: Frontend Calls Ambassador Entry

```javascript
const response = await fetch(
  '/api/ambassador_entry/creative-001?source=gallery'
);
const data = await response.json();
```

### Step 3: Extract Session Info

```javascript
const userGuid = data.session.user_guid;
const isDemo = data.session.is_demo;
const ambassador = data.ambassador;
```

### Step 4: Display Ambassador World

```javascript
// Show avatar
console.log(ambassador.avatar.value); // 🎨

// Load world
console.log(ambassador.world.name); // "The Imagination Lab"
console.log(ambassador.world.description);
```

### Step 5: Start Chat

```javascript
const chatResponse = await fetch('/api/businessinsightbot_function', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_input: "Hello!",
    conversation_history: [],
    user_guid: userGuid
  })
});
```

## Common Issues

### Ambassador Not Found (404)

**Problem:** Ambassador configuration not in Azure File Storage.

**Solution:**
1. Check file exists: `ambassador_catalogue/creative-001.json`
2. Verify file name matches ambassador_id
3. Validate JSON structure

### Invalid JSON (500)

**Problem:** Ambassador configuration has syntax errors.

**Solution:**
1. Validate JSON: `cat config.json | python -m json.tool`
2. Check required fields are present
3. Fix syntax errors

### CORS Errors

**Problem:** Browser blocking cross-origin requests.

**Solution:**
- Endpoint already has CORS headers
- Clear browser cache
- Check origin is allowed

## Quick Commands

```bash
# Validate ambassador config
python3 -c "import json; print(json.load(open('ambassador-creative-001.json')))"

# Test endpoint
curl -i http://localhost:7071/api/ambassador_entry/creative-001

# Test with source tracking
curl http://localhost:7071/api/ambassador_entry/creative-001?source=gallery_main

# Pretty print response
curl http://localhost:7071/api/ambassador_entry/creative-001 | python3 -m json.tool
```

## What's Next?

1. Create more ambassador configurations
2. Generate QR codes
3. Build frontend interface
4. Deploy to Azure
5. Test with real users

## Full Documentation

See `/Users/kodyw/AIGames/Copilot-Agent-365-main/AMBASSADOR_ENDPOINT.md` for complete API documentation.
