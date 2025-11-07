# Agent Library Deployment Guide

This guide covers deploying and using the complete AI Ambassador Agent Library.

## Quick Start

### 1. Install Dependencies

```bash
cd Copilot-Agent-365-main
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `agent_library_config.json` and add your API keys:

```json
{
  "agents": {
    "Calendar": {
      "api_keys": {
        "google_credentials_path": "/path/to/credentials.json",
        "microsoft_client_id": "your_id",
        "microsoft_client_secret": "your_secret"
      }
    },
    "Email": {
      "api_keys": {
        "sendgrid_api_key": "your_key"
      }
    }
    // ... configure other agents
  }
}
```

Or use environment variables:

```bash
export SENDGRID_API_KEY="your_key"
export TWILIO_ACCOUNT_SID="your_sid"
export AZURE_TRANSLATOR_KEY="your_key"
# ... etc
```

### 3. Test Agents

Run the test suite:

```bash
python tests/agents/test_agent_library.py
```

### 4. Start the Function App

```bash
./run.sh  # Mac/Linux
.\run.ps1 # Windows
```

### 5. Access Agent Marketplace

Open `agent-marketplace.html` in your browser to browse and test agents interactively.

## Agent Configuration

### Per-Agent Configuration

Each agent can be configured individually in `agent_library_config.json`:

```json
{
  "AgentName": {
    "enabled": true,
    "version": "1.0.0",
    "api_keys": {
      // Agent-specific API keys
    },
    "rate_limits": {
      "calls_per_minute": 60,
      "calls_per_hour": 1000
    },
    "default_parameters": {
      // Agent-specific defaults
    }
  }
}
```

### Global Settings

Configure global behavior:

```json
{
  "global_settings": {
    "error_retry_attempts": 3,
    "error_retry_delay_ms": 1000,
    "enable_agent_logging": true,
    "enable_performance_monitoring": true,
    "cache_enabled": true,
    "cache_ttl_seconds": 3600
  }
}
```

## Ambassador Integration

### Using Agents in Ambassadors

Example ambassador configuration using multiple agents:

```json
{
  "ambassador": {
    "id": "my-assistant",
    "name": "My Assistant",
    "agent_mapping": {
      "enabled_agents": [
        "Calendar",
        "Email",
        "TaskManagement",
        "Notification"
      ]
    }
  }
}
```

See `example_configs/` for complete examples:
- `personal_assistant.json` - Uses Calendar, Email, TaskManagement, Notification, Document
- `research_assistant.json` - Uses WebResearch, Document, KnowledgeBase, DataAnalysis, Translation
- `marketing_assistant.json` - Uses Email, ImageGeneration, SentimentAnalysis, DataAnalysis, Notification

## API Requirements by Agent

### Calendar Agent
- **Google Calendar API**
  - OAuth 2.0 credentials
  - Scopes: `calendar.events`, `calendar.readonly`
  - Setup: https://developers.google.com/calendar/api/quickstart

- **Microsoft Graph API**
  - Client ID and Secret
  - Permissions: `Calendars.ReadWrite`
  - Setup: https://docs.microsoft.com/graph/auth-register-app-v2

### Email Agent
- **SendGrid**
  - API Key with Mail Send permissions
  - Sender verification required
  - Setup: https://sendgrid.com/docs/api-reference/

- **Microsoft Graph**
  - Mail.Send permission
  - Setup: https://docs.microsoft.com/graph/api/user-sendmail

### Web Research Agent
- **SerpAPI**
  - API key from https://serpapi.com
  - Rate limits by plan tier

- **Bing Search API**
  - Subscription key from Azure
  - Setup: https://docs.microsoft.com/azure/cognitive-services/bing-web-search/

### Translation Agent
- **Azure Translator**
  - Subscription key and region
  - Setup: https://docs.microsoft.com/azure/cognitive-services/translator/

### Sentiment Analysis Agent
- **Azure Text Analytics**
  - Subscription key and endpoint
  - Setup: https://docs.microsoft.com/azure/cognitive-services/text-analytics/

### Image Generation Agent
- **OpenAI DALL-E**
  - API key from https://platform.openai.com

- **Stability AI**
  - API key from https://stability.ai

### Notification Agent
- **Twilio (SMS)**
  - Account SID, Auth Token, Phone Number
  - Setup: https://www.twilio.com/docs/sms

- **SendGrid (Email)**
  - API Key (same as Email Agent)

- **Push Services**
  - FCM (Firebase Cloud Messaging) or APNs
  - Setup varies by platform

### Agents Without External APIs

These agents work out-of-the-box:
- DataAnalysis
- Document
- TaskManagement
- KnowledgeBase
- Recommendation

## Testing

### Unit Tests

```bash
# Run all tests
python tests/agents/test_agent_library.py

# Run specific test class
python -m unittest tests.agents.test_agent_library.TestCalendarAgent

# Run with verbose output
python tests/agents/test_agent_library.py -v
```

### Integration Tests

Test with actual API calls (requires API keys):

```bash
# Set test environment
export TEST_WITH_REAL_APIS=true

# Run integration tests
python tests/agents/test_integration.py
```

### Interactive Testing

Use the Agent Marketplace for interactive testing:

1. Open `agent-marketplace.html`
2. Select an agent
3. Click "Try It"
4. Enter parameters as JSON
5. Execute function

## Monitoring

### Agent Registry

Use the Agent Registry to monitor agent health:

```python
from utils.agent_registry import AgentRegistry

registry = AgentRegistry()
registry.register_all_agents()

# Check health of all agents
health = registry.health_check_all()

# Get usage statistics
stats = registry.get_all_stats()

# Export registry
registry.export_registry('agent_registry_export.json')
```

### Performance Monitoring

Enable performance monitoring in `agent_library_config.json`:

```json
{
  "monitoring": {
    "enable_health_checks": true,
    "health_check_interval_minutes": 5,
    "alert_on_error_rate_threshold": 0.1,
    "alert_on_response_time_threshold_ms": 5000
  }
}
```

### Cost Tracking

Monitor API usage costs:

```json
{
  "cost_tracking": {
    "enabled": true,
    "cost_per_agent_call": {
      "Calendar": 0.001,
      "Email": 0.002,
      "WebResearch": 0.01,
      "ImageGeneration": 0.02
    }
  }
}
```

## Troubleshooting

### Agent Not Loading

1. Check agent file is in `agents/` directory
2. Verify agent class inherits from `BasicAgent`
3. Check for syntax errors in agent file
4. Review function app logs

### API Authentication Errors

1. Verify API keys are correct
2. Check API key permissions/scopes
3. Ensure API service is active
4. Review rate limits

### Rate Limiting

1. Check `agent_library_config.json` rate limits
2. Implement exponential backoff
3. Monitor API quota usage
4. Consider upgrading API tier

### Performance Issues

1. Enable caching in global settings
2. Optimize payload sizes
3. Use batch operations when available
4. Monitor execution times

## Production Deployment

### Pre-Deployment Checklist

- [ ] All API keys configured
- [ ] Tests passing
- [ ] Rate limits configured
- [ ] Error handling tested
- [ ] Monitoring enabled
- [ ] Cost tracking enabled
- [ ] Documentation reviewed

### Deployment Steps

1. **Configure Production Environment**
   ```bash
   cp agent_library_config.json agent_library_config.prod.json
   # Edit with production API keys
   ```

2. **Deploy to Azure Functions**
   ```bash
   func azure functionapp publish <function-app-name>
   ```

3. **Configure Environment Variables**
   ```bash
   az functionapp config appsettings set \
     --name <function-app-name> \
     --resource-group <resource-group> \
     --settings @production-settings.json
   ```

4. **Verify Deployment**
   ```bash
   curl -X POST https://<function-app>.azurewebsites.net/api/businessinsightbot_function \
     -H "Content-Type: application/json" \
     -d '{"user_input": "test", "conversation_history": []}'
   ```

5. **Monitor Health**
   - Check Application Insights
   - Review agent health dashboard
   - Monitor error rates

### Scaling Considerations

- **Function App Plan**: Consider Premium or Dedicated plan for high traffic
- **Rate Limiting**: Implement per-user rate limits
- **Caching**: Use Redis for distributed caching
- **Load Balancing**: Deploy to multiple regions
- **Database**: Use Azure Cosmos DB for agent state

## Security Best Practices

1. **Never commit API keys**
   - Use environment variables
   - Use Azure Key Vault in production

2. **Input Validation**
   - All agents validate inputs
   - Sanitize user-provided data

3. **Rate Limiting**
   - Implement per-user quotas
   - Monitor for abuse

4. **Logging**
   - Log all agent calls
   - Do not log sensitive data
   - Use Application Insights

5. **API Key Rotation**
   - Rotate keys regularly
   - Have backup keys ready
   - Monitor for compromised keys

## Support and Documentation

- **Agent Library Reference**: See `AGENT_LIBRARY.md`
- **Framework Documentation**: See `CLAUDE.md`
- **Infrastructure Guide**: See `README.md` (parent directory)
- **Integration Map**: See `AI_Ambassador_Integration_Map.md`

## Version History

- **v1.0.0** (2025-11-07): Initial release with 12 production-ready agents

## Next Steps

1. Configure API keys for desired agents
2. Test agents with your use cases
3. Create custom ambassador configurations
4. Deploy to production
5. Monitor and optimize

For questions or issues, consult the documentation or contact support.
