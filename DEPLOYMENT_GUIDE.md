# AI Ambassador Platform - Deployment Guide

Complete guide for deploying the AI Ambassador Platform to Azure.

## Quick Start

### Prerequisites
- Azure CLI (v2.50+)
- Azure Functions Core Tools (v4.x)
- Python 3.11
- Git

### Deploy Development Environment

```bash
cd scripts
./deploy.sh dev eastus
```

### Deploy via GitHub Actions

1. Push to `develop` branch → Deploys to Dev
2. Merge to `main` → Deploys to Staging (requires approval)
3. Create Release → Deploys to Production (requires 2 approvals)

## Environments

### Development ($100-200/month)
- Consumption plan
- 7-day retention
- Auto-deploy on push to develop

### Staging ($500-800/month)
- Premium EP1 plan
- 30-day retention
- Redis + CDN enabled
- Auto-deploy on push to main

### Production ($1,200-3,000/month)
- Premium EP1 (auto-scaling 2-10 instances)
- 90-day retention
- GRS storage
- Blue-green deployment

## Manual Deployment

### Bash
```bash
./scripts/deploy.sh <environment> <location>
```

### PowerShell
```powershell
.\scripts\deploy.ps1 -Environment <env> -Location <location>
```

## Rollback

```bash
./scripts/rollback.sh <environment>
```

## Cost Estimation

```bash
./scripts/cost-estimation.sh <environment>
```

## Verification

```bash
# Health check
curl https://<function-app>.azurewebsites.net/api/health

# API test
curl -X POST https://<function-app>.azurewebsites.net/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

See full documentation in repository docs folder.
