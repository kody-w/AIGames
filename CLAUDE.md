# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the **AI Ambassador Platform** - a consumer-friendly AI experience system that bridges physical and digital worlds through QR codes. The platform is built on top of the AIBAST (AI-Based Agent System Tools) infrastructure and the Copilot Agent 365 framework.

**Core Concept**: Transform technical "agents" into culturally-adaptable "AI Ambassadors" that users discover by scanning QR codes in physical locations - creating a Pokemon GO-style experience for AI interactions.

## Project Structure

```
AIGames/
├── Copilot-Agent-365-main/     # Core agent framework (AIBAST)
│   ├── function_app.py         # Azure Function entry point
│   ├── agents/                 # Agent implementations
│   ├── utils/                  # Azure storage utilities
│   └── docs/                   # Framework documentation
├── AI_Ambassador_Implementation_Spec.md  # Full platform specification
├── AI_Ambassador_Integration_Map.md      # Integration architecture
├── README.md                   # Infrastructure deployment guide
└── *.html files                # Web interface prototypes
```

## Key Technologies

- **Backend**: Azure Functions (Python 3.11)
- **AI**: Azure OpenAI (GPT-4)
- **Storage**: Azure File Storage (agent code + memory)
- **Infrastructure**: Azure (AKS, ACR, Storage, Key Vault)
- **Deployment**: Azure Bicep templates

## Development Commands

### Working with Copilot-Agent-365

**Start local development:**
```bash
cd Copilot-Agent-365-main
./run.sh              # Mac/Linux
.\run.ps1             # Windows
```

**Test the API locally:**
```bash
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

**Python environment:**
- Python 3.11 required (Azure Functions v4 compatibility)
- Virtual environment: `.venv/`
- Install dependencies: `pip install -r requirements.txt`

### Infrastructure Deployment

**Deploy Azure infrastructure:**
```bash
# Quick deployment with Bicep
./deploy.sh dev eastus

# Or manual deployment
az deployment sub create \
  --name aibast-dev-deployment \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json
```

**Post-deployment setup:**
```bash
# Get AKS credentials
az aks get-credentials --resource-group aibast-dev-rg --name aibast-dev-aks-<uniqueid>

# Verify cluster
kubectl get nodes
```

## Architecture

### High-Level System Flow

```
Physical QR Code → User Scans → Web Interface → Azure Function → Agent System
                                                      ↓
                                              Azure OpenAI + Memory
                                                      ↓
                                              Ambassador Response
```

### Core Components

**1. Ambassador System (AI_Ambassador_Implementation_Spec.md)**
- **Ambassador Configuration**: JSON-based definitions with visual theming, capabilities, and world settings
- **QR Code Integration**: Physical-to-digital bridge with URL pattern `https://ai-ambassadors.app/enter/{ambassador_id}`
- **Seeded Demos**: Reproducible experiences using synthetic memory for showcases and sales
- **User Sessions**: GUID-based user tracking with persistent memory contexts

**2. Agent Framework (Copilot-Agent-365-main/)**
- **function_app.py**: Main Azure Function that orchestrates all agent interactions
  - Entry point: `businessinsightbot_function` HTTP trigger
  - Dynamic agent loading from local folder + Azure File Storage
  - Default GUID: `c0p110t0-aaaa-bbbb-cccc-123456789abc`
  - Dual response format: formatted markdown + voice (split by `|||VOICE|||`)

- **Agent System**: All agents inherit from `BasicAgent`
  - Built-in agents: `ContextMemoryAgent`, `ManageMemoryAgent`, `GitHubAgentLibraryManager`
  - Custom agents loaded from `agents/` folder or Azure File Storage
  - Function calling via OpenAI function definitions

- **Memory System**: Dual-layer architecture
  - **Shared memory**: Accessible to all users (`shared_memories/` path)
  - **User-specific memory**: Per-GUID isolation (`user_{guid}/` paths)
  - Storage: Azure File Share via `AzureFileStorageManager`
  - Context switching: Send GUID in request to load user-specific context
  - Memory trimming: Last 20 messages retained to prevent overflow

### Request Flow

1. **QR Code Scan** → Ambassador entry endpoint
2. **Load ambassador config** from Azure File Storage
3. **Initialize session** (demo with seed or real user with new GUID)
4. **Create Assistant** instance with user GUID
5. **Load memory context** (shared + user-specific)
6. **Call Azure OpenAI** with agent function definitions
7. **Execute agents** if functions called
8. **Return formatted response** + voice response

### Ambassador Data Model Key Fields

```json
{
  "ambassador": {
    "id": "unique-id",
    "name": "DisplayName",
    "avatar": {"type": "emoji", "value": "🎨"},
    "world": {"type": "creative_studio", "environment": {...}},
    "agent_mapping": {
      "base_agent": "BasicAgent",
      "custom_agent": "CustomAgent"
    },
    "demo_configuration": {
      "seeded_run": true,
      "parameters": {"user_guid": "demo-001"},
      "synthetic_memory": {"memories": [...]}
    }
  }
}
```

## Creating Custom Agents

**Basic Agent Template:**
```python
from agents.basic_agent import BasicAgent

class MyCustomAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyCustom'
        self.metadata = {
            "name": self.name,
            "description": "What this agent does",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        input_data = kwargs.get('input', '')
        # Your logic here
        return f"Processed: {input_data}"
```

**Agent Storage:**
- Local: Place in `Copilot-Agent-365-main/agents/` folder
- Azure: Upload to Azure File Storage `agents/` or `multi_agents/` shares
- Auto-loaded on function startup

## Ambassador Integration

### Adding Ambassador Entry Point (function_app.py)

The platform requires adding an `ambassador_entry` function to handle QR code scans:

```python
@app.route(route="ambassador_entry", auth_level=func.AuthLevel.ANONYMOUS)
def ambassador_entry(req: func.HttpRequest) -> func.HttpResponse:
    """Entry point for QR code scans - loads ambassador and initializes session"""
    # 1. Extract ambassador_id from route
    # 2. Load ambassador config from Azure File Storage
    # 3. Check if demo (seeded_run) or real user
    # 4. Initialize memory context (synthetic for demo, empty for real)
    # 5. Return ambassador config + session info
```

### Seeded Demo Implementation

For reproducible demos, use the `ManageMemoryAgent` with seeded memory:

```python
def initialize_seeded_memory(user_guid, memory_seed, config):
    """Initialize memory with synthetic data for demo"""
    storage_manager = AzureFileStorageManager()
    storage_manager.set_memory_context(user_guid)

    # Load synthetic memory from config
    synthetic_memory = config['demo_configuration']['synthetic_memory']

    # Write to memory storage
    memory_data = {}
    for memory in synthetic_memory['memories']:
        memory_data[memory['id']] = memory

    storage_manager.write_json(memory_data)
```

## Configuration

### Environment Variables (local.settings.json)

Required for local development:
```json
{
  "AZURE_OPENAI_API_KEY": "your-key",
  "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
  "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
  "AZURE_OPENAI_API_VERSION": "2025-01-01-preview",
  "AzureWebJobsStorage": "connection-string",
  "AZURE_FILES_SHARE_NAME": "your-share-name",
  "ASSISTANT_NAME": "AI Ambassador",
  "CHARACTERISTIC_DESCRIPTION": "Your AI companion"
}
```

**IMPORTANT**: Never commit `local.settings.json` - it contains secrets.

### Bicep Deployment Parameters

Environment-specific parameters in `parameters/{env}.parameters.json`:

- **dev**: 1 AKS node, Standard_D2s_v3, ~$200-500/month
- **staging**: 2 AKS nodes, Standard_D4s_v3, ~$500-1,200/month
- **prod**: 3+ AKS nodes, Standard_D4s_v3, auto-scaling, ~$1,200-3,600/month

## Important Notes

### Python Version
- **Use Python 3.11** - Required for Azure Functions v4
- **Do NOT use Python 3.13+** - Causes compatibility issues

### Memory System
- Default GUID used when no user GUID provided (backward compatibility)
- Context automatically switches based on user GUID in request
- Agent files from Azure Storage loaded into `/tmp/agents` and `/tmp/multi_agents` at runtime

### Response Format
- Must include `|||VOICE|||` delimiter to split formatted/voice responses
- Format: `markdown_response|||VOICE|||voice_response`

### Security
- Function keys should be rotated regularly
- Never expose Function Keys in client code
- Use Managed Identity for Azure resource authentication
- Monitor API usage to avoid unexpected costs

### CORS Handling
- All responses include CORS headers via `build_cors_response()`
- OPTIONS preflight requests supported
- Safe handling of None origin values

### Error Handling
- Retry logic (max 3 attempts) for OpenAI API calls
- Agent loading failures logged but don't crash the app
- Graceful degradation when memory initialization fails
- All message content sanitized via `ensure_string_content()` to prevent None errors

## Key Design Patterns

**String Safety:**
- All potentially None values have default values
- Function arguments stringified via `ensure_string_function_args()`
- Content sanitization prevents undefined errors

**Agent Loading:**
- Dynamic loading from both local folder and Azure File Storage
- Inspection-based discovery of BasicAgent subclasses
- Error isolation - one agent failure doesn't crash system

**Memory Context:**
- GUID-based user isolation
- Shared + user-specific dual-layer architecture
- Automatic context switching based on request GUID
- Seeded memory support for reproducible demos

## QR Code Integration

### URL Pattern
```
https://ai-ambassadors.app/enter/{ambassador_id}?source={location}
```

### Physical Placement Ideas
- Retail stores: Product assistance (500-2K scans/day)
- Museums: Educational guides (200-1K scans/day)
- Conferences: Demo assistants (100-500 scans/event)
- Restaurants: Menu helpers (50-200 scans/day)

### QR Code Design Requirements
- High contrast (black on white)
- Minimum size: 2" x 2"
- Error correction: Level H (high)
- Include ambassador avatar/emoji
- Clear call-to-action

## Testing

**Test locally:**
```bash
# PowerShell (Windows)
Invoke-RestMethod -Uri "http://localhost:7071/api/businessinsightbot_function" `
  -Method Post `
  -Body '{"user_input": "Hello", "conversation_history": []}' `
  -ContentType "application/json"

# Curl (Mac/Linux)
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

**Test with specific user GUID:**
```bash
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "YOUR_GUID_HERE", "conversation_history": []}'
```

## Deployment Modes

### Standalone Mode
- Direct REST API access via Azure Functions
- No additional dependencies
- Cost: ~$5/month + OpenAI usage

### Power Platform Mode (Optional)
- Microsoft Teams integration
- Microsoft 365 Copilot deployment
- User context from Office 365
- Cost: ~$25-40/user/month + OpenAI usage

See `Copilot-Agent-365-main/README.md` for Power Platform setup instructions.

## Common Operations

**View Azure Function logs:**
```bash
az functionapp log tail --name <function-app-name> --resource-group <resource-group>
```

**Update Function App settings:**
```bash
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings "KEY=value"
```

**Deploy code to Azure:**
```bash
cd Copilot-Agent-365-main
func azure functionapp publish <function-app-name>
```

## Documentation References

- **AI Ambassador Spec**: `AI_Ambassador_Implementation_Spec.md`
- **Integration Map**: `AI_Ambassador_Integration_Map.md`
- **Infrastructure Guide**: `README.md`
- **Framework Docs**: `Copilot-Agent-365-main/CLAUDE.md`
- **Copilot-365 README**: `Copilot-Agent-365-main/README.md`
