# CI/CD and Infrastructure as Code

Complete production-ready CI/CD system for the AI Ambassador Platform.

## Overview

This repository includes comprehensive Infrastructure as Code (Bicep), automated testing, and zero-downtime deployment pipelines.

## Quick Links

- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Infrastructure Architecture](./INFRASTRUCTURE.md)
- [CI/CD Setup](./CICD_SETUP.md)
- [Troubleshooting](./TROUBLESHOOTING_DEPLOYMENT.md)

## Repository Structure

```
AIGames/
├── infrastructure/
│   ├── bicep/
│   │   ├── main.bicep                 # Main orchestrator
│   │   └── modules/                   # Bicep modules
│   │       ├── function-app.bicep     # Azure Functions
│   │       ├── storage.bicep          # Storage Account
│   │       ├── openai.bicep           # Azure OpenAI
│   │       ├── app-insights.bicep     # Monitoring
│   │       ├── key-vault.bicep        # Secrets
│   │       ├── redis.bicep            # Redis Cache
│   │       ├── static-web-app.bicep   # Static Web App
│   │       └── cdn.bicep              # CDN
│   ├── parameters/
│   │   ├── dev.bicepparam             # Dev environment
│   │   ├── staging.bicepparam         # Staging environment
│   │   └── prod.bicepparam            # Production environment
│   └── app-settings.template.json     # Function App settings
├── .github/workflows/
│   ├── ci.yml                         # Continuous Integration
│   ├── cd-dev.yml                     # Deploy to Dev
│   ├── cd-staging.yml                 # Deploy to Staging
│   ├── cd-prod.yml                    # Deploy to Production
│   └── destroy.yml                    # Destroy Environment
├── scripts/
│   ├── deploy.sh                      # Bash deployment script
│   ├── deploy.ps1                     # PowerShell deployment script
│   ├── rollback.sh                    # Rollback script
│   ├── cost-estimation.sh             # Cost estimation
│   └── feature-flags.py               # Feature flag management
└── tests/
    └── smoke/
        ├── test_health.py             # Health check tests
        └── test_integration.py        # Integration tests
```

## Features

### Infrastructure as Code
- **Bicep templates** for all Azure resources
- **Modular architecture** for reusability
- **Environment-specific parameters**
- **Idempotent deployments**

### CI/CD Pipeline
- **Continuous Integration** on every push
- **Automated testing** (unit, integration, e2e)
- **Code quality gates** (linting, security scanning)
- **Automated deployments** per environment
- **Blue-green deployment** for production
- **Automatic rollback** on failure

### Monitoring & Alerts
- **Application Insights** integration
- **Cost management** and budget alerts
- **Performance monitoring**
- **Error rate alerts**
- **Certificate expiration alerts**

### Security
- **Managed Identity** for all Azure resources
- **Key Vault** for secrets management
- **RBAC authorization**
- **No secrets in code**
- **Security scanning** in CI pipeline

## Quick Start

### 1. Prerequisites

```bash
# Install required tools
az --version              # Azure CLI
func --version            # Azure Functions Core Tools
python --version          # Python 3.11
```

### 2. Configure GitHub Secrets

Required secrets:
- `AZURE_CREDENTIALS` - Service principal JSON
- `AZURE_OPENAI_API_KEY` - OpenAI API key

Optional secrets:
- `SLACK_WEBHOOK` - Slack notifications

### 3. Deploy

**Development:**
```bash
git checkout -b feature/my-feature develop
git push origin feature/my-feature
# Merge to develop → Auto-deploys to dev
```

**Staging:**
```bash
git checkout main
git merge develop
git push origin main
# Auto-deploys to staging (requires approval)
```

**Production:**
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
# Create GitHub Release → Auto-deploys to prod (requires 2 approvals)
```

## Deployment Strategies

### Development
- **Trigger:** Push to `develop` branch
- **Strategy:** Direct deployment
- **Approval:** None
- **Rollback:** Manual

### Staging
- **Trigger:** Push to `main` branch
- **Strategy:** Direct deployment with tests
- **Approval:** 1 reviewer
- **Rollback:** Manual

### Production
- **Trigger:** GitHub Release
- **Strategy:** Blue-green deployment
- **Approval:** 2 reviewers
- **Rollback:** Automatic on failure

## Cost Estimates

| Environment | Monthly Cost | Auto-scaling | Retention |
|-------------|--------------|--------------|-----------|
| Development | $100-200 | No | 7 days |
| Staging | $500-800 | Yes (1-5) | 30 days |
| Production | $1,200-3,000 | Yes (2-10) | 90 days |

## Environments

### Development
- **Purpose:** Testing and development
- **Plan:** Consumption (Y1)
- **Storage:** Standard LRS
- **Features:** Basic monitoring, 7-day logs
- **Auto-deploy:** Push to develop

### Staging
- **Purpose:** Pre-production testing
- **Plan:** Elastic Premium EP1
- **Storage:** Standard LRS
- **Features:** Redis, CDN, 30-day logs, performance testing
- **Auto-deploy:** Push to main (requires approval)

### Production
- **Purpose:** Live production workloads
- **Plan:** Elastic Premium EP1 (auto-scaling)
- **Storage:** Standard GRS (geo-redundant)
- **Features:** Redis Premium, CDN, 90-day logs, blue-green deployment
- **Auto-deploy:** Release creation (requires 2 approvals)

## Monitoring

### Application Insights
- Real-time metrics
- Distributed tracing
- Custom events
- Performance counters

### Alerts Configured
- Error rate > 5%
- Response time > 2s
- Budget exceeded (80%, 90%, 100%)
- Certificate expiration (30 days)

### Cost Management
```bash
# Estimate costs
./scripts/cost-estimation.sh <environment>

# View actual costs
az costmanagement query --type ActualCost --timeframe MonthToDate
```

## Testing

### Unit Tests
```bash
pytest tests/unit -v
```

### Integration Tests
```bash
pytest tests/integration -v
```

### Smoke Tests
```bash
export FUNCTION_URL=https://<function-app>.azurewebsites.net
pytest tests/smoke -v
```

### Performance Tests
Included in staging deployment workflow.

## Rollback

### Automatic Rollback
Production deployments automatically rollback if:
- Health check fails
- Error rate > 10 errors/minute
- Response time > 2 seconds

### Manual Rollback
```bash
./scripts/rollback.sh <environment>
```

## Feature Flags

Control feature rollout per environment:

```python
from scripts.feature_flags import is_feature_enabled

if is_feature_enabled('voice_responses', user_id):
    # Enable voice responses
    pass
```

Configure in `scripts/feature-flags.py`.

## Security Best Practices

1. All secrets in Key Vault
2. Managed Identity for authentication
3. RBAC for authorization
4. HTTPS only (TLS 1.2+)
5. Regular security scanning
6. No secrets in code
7. Rotate keys every 90 days

## Troubleshooting

Common issues and solutions in [TROUBLESHOOTING_DEPLOYMENT.md](./TROUBLESHOOTING_DEPLOYMENT.md).

Quick diagnostics:
```bash
# Check resource group
az group show --name aiambassador-<env>-rg

# Check function app
az functionapp show --name <function-app> --resource-group <rg>

# View logs
az functionapp log tail --name <function-app> --resource-group <rg>

# Test health
curl https://<function-app>.azurewebsites.net/api/health
```

## Contributing

1. Create feature branch from `develop`
2. Make changes
3. Run tests locally
4. Create PR to `develop`
5. Merge after CI passes
6. Deploy to staging via `main` branch
7. Create release for production

## Support

- **Issues:** GitHub Issues
- **Documentation:** `/docs` folder
- **Slack:** #ai-ambassador-platform

## License

See LICENSE file.

## Additional Resources

- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Azure OpenAI Documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)

---

**Built with:** Azure Functions, Azure OpenAI, Bicep, GitHub Actions, Python 3.11
