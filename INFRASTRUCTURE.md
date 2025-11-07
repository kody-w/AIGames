# AI Ambassador Platform - Infrastructure Overview

Comprehensive documentation of the platform's infrastructure architecture, components, and design decisions.

## Architecture Overview

The AI Ambassador Platform is built on Azure using a serverless, event-driven architecture optimized for scalability, cost-efficiency, and developer productivity.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS (443)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Azure Front Door (Optional)                    │
│                   - CDN, WAF, Load Balancing                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Azure Function App                             │
│                   - Python 3.11 Runtime                          │
│                   - HTTP Triggered Functions                     │
│                   - Managed Identity                             │
│                   - Deployment Slots (Staging/Prod)              │
└─────┬──────────┬──────────┬──────────┬────────────┬────────────┘
      │          │          │          │            │
      │          │          │          │            │
┌─────▼──────┐ ┌▼──────┐ ┌─▼─────┐ ┌─▼────────┐ ┌─▼──────────┐
│  Storage   │ │ OpenAI│ │KeyVault│ │App Insights│ │VNet (Opt)│
│  Account   │ │Service│ │        │ │            │ │          │
│            │ │       │ │        │ │            │ │          │
│- File Shares│ │- GPT-4│ │- Secrets│ │- Telemetry │ │- Isolation│
│- Blobs     │ │- Embed│ │- Keys  │ │- Logs      │ │- Security│
│- Queues    │ │       │ │        │ │- Metrics   │ │          │
└────────────┘ └───────┘ └────────┘ └────────────┘ └───────────┘
```

## Core Components

### 1. Azure Function App

**Purpose**: Serverless compute platform for running the AI Ambassador logic

**Configuration**:
- **Runtime**: Python 3.11
- **Version**: Azure Functions v4
- **Hosting Plan**:
  - Dev: Y1 (Consumption)
  - Staging: EP1 (Elastic Premium)
  - Prod: EP2 (Elastic Premium)
- **Operating System**: Linux
- **Scaling**:
  - Dev: Up to 10 instances
  - Staging: Up to 100 instances
  - Prod: Up to 200 instances

**Key Features**:
- Managed identity for secure access to Azure resources
- Deployment slots for blue-green deployments
- Auto-scaling based on CPU/memory metrics
- CORS configuration for web access
- Health check endpoint
- Application Insights integration

**Endpoints**:
- `/api/businessinsightbot_function` - Main agent interaction
- `/api/ambassador_entry` - QR code entry point
- `/api/health` - Health check

### 2. Azure Storage Account

**Purpose**: Persistent storage for agent code, memory, and backups

**Configuration**:
- **SKU**:
  - Dev/Staging: Standard_LRS (Locally Redundant)
  - Prod: Standard_ZRS (Zone Redundant)
- **Replication**: Automatic based on SKU
- **Encryption**: Microsoft-managed keys
- **Network Access**: Allow Azure services
- **HTTPS Only**: Enforced

**Storage Components**:

#### File Shares
- `ambassadors/` - Ambassador configuration JSON files
- `agents/` - Custom agent Python files
- `multi-agents/` - Multi-agent orchestration files
- `memories/` - User conversation memory
- `backups/` - System backups (if enabled)

**Quotas**:
- Dev: 100-200 GB total
- Staging: 500-1000 GB total
- Prod: 2000-5000 GB total

#### Blob Containers
- `deployments/` - Deployment packages
- `logs/` - Historical logs (cool tier)

**Lifecycle Policies**:
- Logs move to cool tier after 30 days
- Logs move to archive tier after 90 days
- Old backups deleted after retention period

### 3. Azure OpenAI Service

**Purpose**: AI capabilities for natural language processing

**Configuration**:
- **SKU**: S0 (Standard)
- **Deployments**:
  - `gpt-4`: Primary model for agent interactions
  - `gpt-4-turbo`: High-throughput model (prod only)
  - `text-embedding-ada-002`: Embeddings for RAG (optional)

**Capacity (TPM - Tokens Per Minute)**:
- Dev: 10 TPM (GPT-4)
- Staging: 30 TPM (GPT-4)
- Prod: 100+ TPM (GPT-4), 80 TPM (GPT-4 Turbo)

**Cost Optimization**:
- Token usage monitoring
- Caching frequent responses
- Model selection based on complexity
- Rate limiting implementation

### 4. Azure Key Vault

**Purpose**: Secure secret management

**Configuration**:
- **SKU**: Standard
- **Soft Delete**: Enabled
- **Purge Protection**: Enabled (prod only)
- **RBAC**: Disabled (using access policies)
- **Network Access**: Allow Azure services

**Stored Secrets**:
- `storage-connection-string` - Storage account connection
- `openai-api-key` - OpenAI API key
- `app-insights-connection-string` - Application Insights
- Custom secrets (API keys, credentials)

**Access Policy**:
- Function App managed identity: Get, List secrets
- Deployment service principal: Get, List, Set secrets

### 5. Application Insights

**Purpose**: Application performance monitoring and diagnostics

**Configuration**:
- **Type**: Web application
- **Sampling**:
  - Dev: 50%
  - Staging: 75%
  - Prod: 100%
- **Retention**:
  - Dev: 30 days
  - Staging: 60 days
  - Prod: 90 days
- **Daily Cap**:
  - Dev: 1 GB
  - Staging: 5 GB
  - Prod: 10 GB

**Monitored Metrics**:
- Request rate and response times
- Dependency calls (OpenAI, Storage)
- Exception tracking
- Custom events and metrics
- User sessions and page views

### 6. Log Analytics Workspace

**Purpose**: Centralized logging and analytics

**Configuration**:
- **SKU**: Pay-as-you-go
- **Retention**: Same as Application Insights
- **Ingestion**: All Azure resource logs

**Log Categories**:
- Function execution logs
- HTTP request logs
- Dependency calls
- Key Vault access logs
- OpenAI API calls

### 7. Virtual Network (Optional - Prod)

**Purpose**: Network isolation and security

**Configuration**:
- **Address Space**: 10.0.0.0/16
- **Subnets**:
  - `function-subnet` (10.0.1.0/24) - Function App VNet integration
  - `private-endpoint-subnet` (10.0.2.0/24) - Private endpoints

**Network Security Group**:
- Allow HTTPS (443) inbound
- Allow Azure Load Balancer
- Deny all other inbound traffic

**Service Endpoints**:
- Microsoft.Storage
- Microsoft.KeyVault
- Microsoft.CognitiveServices

## Resource Naming Convention

All resources follow a consistent naming pattern:

```
aibast-{environment}-{resource-type}-{unique-id}
```

**Examples**:
- `aibast-dev-func-abc123de` - Function App (dev)
- `aibast-prod-kv-xyz789fg` - Key Vault (prod)
- `aibastprodstorabc123` - Storage Account (no hyphens)

**Environment Codes**:
- `dev` - Development
- `staging` - Staging/UAT
- `prod` - Production

## Scaling Strategy

### Horizontal Scaling (Function App)

**Auto-scale Rules**:

1. **CPU-based Scaling**:
   - Scale out: CPU > 70% for 5 minutes → Add 2 instances
   - Scale in: CPU < 30% for 10 minutes → Remove 1 instance

2. **Memory-based Scaling**:
   - Scale out: Memory > 75% for 5 minutes → Add 2 instances

**Limits**:
- Dev: 1-10 instances
- Staging: 2-100 instances
- Prod: 3-200 instances

### Vertical Scaling

Change Function App SKU based on workload:

```bash
# Upgrade to higher tier
az functionapp plan update \
  --name <plan-name> \
  --resource-group <rg> \
  --sku EP3
```

**When to Scale Up**:
- Consistently high CPU/memory usage
- Response time degradation
- Frequent cold starts (move to Premium)

### Storage Scaling

Storage automatically scales based on usage:
- No manual intervention required
- Pay only for what you use
- Monitor usage with Azure Monitor

### OpenAI Scaling

Request quota increases:

```bash
# Check current usage
az cognitiveservices account list-usage \
  --name <openai-account> \
  --resource-group <rg>

# Submit quota increase request through Azure Portal
```

## High Availability

### Function App HA

**Features**:
- Multiple instances across availability zones (EP2+)
- Health check probes
- Automatic instance replacement on failure
- 99.95% SLA (Premium plan)

### Storage HA

**Redundancy Options**:
- LRS: 3 copies within single datacenter
- ZRS: 3 copies across availability zones (prod)
- GRS: Geo-redundant (optional for critical data)

### OpenAI HA

**Resilience**:
- Built-in retry logic (3 attempts)
- Fallback to different deployment
- Circuit breaker pattern
- Request queuing during outages

## Disaster Recovery

### Backup Strategy

**Automated Backups**:
- Storage: Soft delete (7-90 days)
- Key Vault: Soft delete with purge protection
- Function App: Deployment slots maintain previous version

**Manual Backups**:
- Pre-deployment snapshots
- Configuration exports
- Code repository (Git)

### Recovery Procedures

**RTO (Recovery Time Objective)**:
- Dev: 4 hours
- Staging: 2 hours
- Prod: 1 hour

**RPO (Recovery Point Objective)**:
- Dev: 24 hours
- Staging: 4 hours
- Prod: 1 hour

**Recovery Steps**:

1. **Infrastructure Recovery**:
   ```bash
   # Redeploy from backup
   az deployment sub create \
     --name "dr-recovery-$(date +%s)" \
     --location <secondary-region> \
     --template-file infrastructure/bicep/main.bicep \
     --parameters <backup-parameters>
   ```

2. **Data Recovery**:
   ```bash
   # Restore storage data
   az storage blob restore \
     --account-name <storage> \
     --source-container backups \
     --destination-container memories \
     --pattern "*"
   ```

3. **Application Recovery**:
   ```bash
   # Deploy application code
   func azure functionapp publish <function-app-name>
   ```

## Security Architecture

### Identity and Access Management

**Managed Identity**:
- System-assigned identity for Function App
- Access to Key Vault, Storage, OpenAI
- No credentials in code or configuration

**RBAC Roles**:
- Function App → Storage: Storage Blob Data Contributor
- Function App → Key Vault: Key Vault Secrets User
- Function App → OpenAI: Cognitive Services User

### Network Security

**Inbound**:
- HTTPS only (TLS 1.2+)
- CORS restrictions
- WAF (if using Front Door)

**Outbound**:
- Service endpoints (prod)
- Private endpoints (optional)
- VNet integration (prod)

### Data Protection

**Encryption**:
- At rest: Azure Storage encryption (AES-256)
- In transit: TLS 1.2+
- Key management: Azure-managed keys

**Access Control**:
- Shared access signatures (time-limited)
- Key rotation policy
- Audit logging

## Monitoring and Alerting

### Metrics Monitored

1. **Performance**:
   - Response time (p50, p95, p99)
   - Throughput (requests/sec)
   - Error rate (%)

2. **Resource Utilization**:
   - CPU percentage
   - Memory usage
   - Storage capacity

3. **Business Metrics**:
   - Active users
   - Ambassador interactions
   - OpenAI token usage

### Alert Rules

**Critical Alerts** (PagerDuty):
- Error rate > 5%
- Response time > 5 seconds
- Function App down
- OpenAI quota exhausted

**Warning Alerts** (Email/Slack):
- Error rate > 2%
- Response time > 2 seconds
- High CPU/memory (>80%)
- Storage capacity > 80%

## Cost Management

### Cost Breakdown

**Dev Environment** (~$5-50/month):
- Function App (Y1): $0
- Storage: $1-5
- OpenAI: $3-20
- Monitoring: $1-10

**Staging Environment** (~$200-500/month):
- Function App (EP1): $169
- Storage: $10-30
- OpenAI: $30-150
- Monitoring: $10-50

**Production Environment** (~$1,200-5,000/month):
- Function App (EP2): $338
- Storage: $50-200
- OpenAI: $500-4,000
- Monitoring: $50-200
- VNet: $7

### Cost Optimization

1. **Function App**:
   - Use Consumption plan for low-traffic environments
   - Enable auto-scaling to prevent over-provisioning
   - Review instance count regularly

2. **Storage**:
   - Implement lifecycle policies
   - Use appropriate access tiers
   - Delete unused data

3. **OpenAI**:
   - Cache frequent responses
   - Optimize prompts to reduce tokens
   - Use appropriate model (GPT-3.5 vs GPT-4)
   - Implement rate limiting

4. **Monitoring**:
   - Adjust sampling rates
   - Set data retention policies
   - Configure daily caps

### Cost Monitoring

```bash
# View current costs
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "[?contains(instanceName, 'aibast')]"

# Set budget alerts
az consumption budget create \
  --amount 1000 \
  --category Cost \
  --time-grain Monthly \
  --name aibast-prod-budget
```

## Compliance and Governance

### Azure Policy

**Enforced Policies**:
- Require HTTPS for storage
- Require encryption at rest
- Require managed identities
- Restrict allowed VM sizes
- Require tags (Environment, Project, CostCenter)

### Tagging Strategy

All resources tagged with:
- `Environment`: dev, staging, prod
- `Project`: AI-Ambassador-Platform
- `ManagedBy`: Bicep
- `CostCenter`: Department code
- `Owner`: Team or individual

### Audit Logging

**Enabled Logs**:
- Resource creation/deletion
- Configuration changes
- Access attempts
- Security events

**Retention**: 90 days (prod), 30 days (dev/staging)

## Future Enhancements

1. **Multi-region Deployment**:
   - Active-active setup
   - Traffic Manager
   - Geo-replication

2. **Enhanced Security**:
   - Private endpoints for all services
   - DDoS protection
   - Advanced threat protection

3. **Performance Optimization**:
   - Redis cache layer
   - CDN for static assets
   - Database for structured data

4. **Advanced Monitoring**:
   - Custom dashboards
   - ML-based anomaly detection
   - Predictive scaling

## References

- [Azure Architecture Center](https://learn.microsoft.com/azure/architecture/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
- [Azure Functions Best Practices](https://learn.microsoft.com/azure/azure-functions/functions-best-practices)
