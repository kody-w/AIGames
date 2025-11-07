# AI Ambassador Platform - Infrastructure Architecture

## Overview

The AI Ambassador Platform uses Azure services with Infrastructure as Code (Bicep).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Azure Cloud                         │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐   ┌───────────┐ │
│  │    CDN       │───>│  Static Web  │   │   Redis   │ │
│  │              │    │     App      │   │   Cache   │ │
│  └──────────────┘    └──────────────┘   └───────────┘ │
│                             │                  │        │
│                             v                  v        │
│                      ┌──────────────────────────┐      │
│                      │   Azure Functions        │      │
│                      │   (Python 3.11)          │      │
│                      └──────────┬───────────────┘      │
│                                 │                       │
│                 ┌───────────────┼───────────────┐      │
│                 │               │               │      │
│                 v               v               v      │
│          ┌────────────┐  ┌──────────┐  ┌─────────┐   │
│          │   Azure    │  │  Storage │  │   Key   │   │
│          │   OpenAI   │  │ Account  │  │  Vault  │   │
│          └────────────┘  └──────────┘  └─────────┘   │
│                                                        │
│          ┌────────────────────────────────┐           │
│          │    Application Insights        │           │
│          │    + Log Analytics             │           │
│          └────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

## Components

### Azure Functions
- Runtime: Python 3.11
- Plans:
  - Dev: Consumption (Y1)
  - Staging/Prod: Elastic Premium (EP1)
- Auto-scaling: 1-10 instances (prod)
- Managed Identity enabled

### Storage Account
- Dev: Standard LRS
- Prod: Standard GRS
- File shares: agents, multi-agents, shared-memories, backups
- Soft delete enabled (7 days)

### Azure OpenAI
- Models: GPT-4, GPT-3.5-turbo
- Capacity:
  - Dev: 20 TPM
  - Staging: 50 TPM
  - Prod: 100 TPM

### Application Insights
- Real-time monitoring
- Retention:
  - Dev: 7 days
  - Staging: 30 days
  - Prod: 90 days

### Key Vault
- Secret management
- RBAC authorization
- Soft delete + purge protection
- 90-day retention

### Redis Cache (Optional)
- Staging/Prod only
- Response caching
- Session storage

### Static Web App
- PWA hosting
- Free tier (dev)
- Standard tier (staging/prod)

### CDN (Optional)
- Static asset caching
- Global distribution
- Standard Microsoft tier

## Networking

### VNet Integration (Prod)
- Private endpoints for storage
- Service endpoints for Key Vault
- Outbound only for Function App

### CORS Configuration
- Allowed origins:
  - https://ai-ambassadors.app
  - https://portal.azure.com
  - http://localhost:3000
  - http://localhost:5000

## Security

### Managed Identity
- System-assigned identity for Function App
- RBAC roles:
  - Storage Blob Data Contributor
  - Storage File Data Privileged Contributor
  - Cognitive Services OpenAI User
  - Key Vault Secrets User

### Secrets Management
- All secrets in Key Vault
- No connection strings in code
- Key rotation every 90 days

### Network Security
- HTTPS only
- TLS 1.2 minimum
- Firewall rules for storage
- IP restrictions (optional)

## Monitoring

### Alerts
- Error rate > 5%
- Response time > 2s
- Budget exceeded
- Certificate expiration

### Metrics
- Request count
- Response time
- Error rate
- Token usage
- Cost

## Cost Breakdown

### Development: $100-200/month
- Functions: $5-10
- Storage: $2-5
- OpenAI: $50-80
- App Insights: $10-15
- Static Web App: $0

### Staging: $500-800/month
- Functions: $200-300
- Storage: $10-15
- OpenAI: $150-250
- App Insights: $30-50
- Redis: $15-20
- CDN: $10-20
- Static Web App: $9

### Production: $1,200-3,000/month
- Functions: $600-900
- Storage: $40-60
- OpenAI: $800-1,200
- App Insights: $200-300
- Redis: $300-350
- CDN: $40-60
- Static Web App: $9
- Backup: $10-20

## Disaster Recovery

### Backup Strategy
- Automated daily backups
- 90-day retention (prod)
- Geo-redundant storage
- Point-in-time restore

### High Availability
- Multi-instance deployment
- Auto-scaling
- Health checks
- Blue-green deployment

## Scalability

### Auto-scaling Rules
- CPU > 70% → Scale out
- CPU < 30% → Scale in
- Max instances: 10 (prod), 5 (staging), 1 (dev)
- Cool down: 5 minutes

### Performance Targets
- Response time: < 500ms (P95)
- Throughput: > 100 req/sec
- Availability: 99.9%
- Error rate: < 1%

See DEPLOYMENT_GUIDE.md for deployment instructions.
