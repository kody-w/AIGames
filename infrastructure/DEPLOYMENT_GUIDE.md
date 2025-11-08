# 🚀 AI Ambassador Platform - Infrastructure Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Deployment Steps](#detailed-deployment-steps)
5. [Environment Configurations](#environment-configurations)
6. [Cost Optimization](#cost-optimization)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Post-Deployment](#post-deployment)

---

## Overview

This infrastructure deployment provisions **all Azure resources** needed for the AI Ambassador Platform:

### Resources Deployed

| Resource | Purpose | Pricing Tier |
|----------|---------|--------------|
| **Azure OpenAI** | GPT-4 AI processing | Standard (S0) |
| **Storage Account** | Agent code & memory storage | Standard LRS/ZRS |
| **Function App** | Serverless API hosting | Consumption/Premium |
| **Application Insights** | Monitoring & analytics | Pay-as-you-go |
| **Log Analytics** | Centralized logging | Pay-as-you-go |
| **Key Vault** | Secrets management | Standard |
| **App Service Plan** | Function App compute | Consumption/Premium |

### Architecture Diagram

```
┌─────────────────┐
│   QR Code Scan  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        Azure Function App               │
│  ┌───────────────────────────────────┐ │
│  │  Emotional Intelligence           │ │
│  │  Episodic Memory Synthesis        │ │
│  │  Multi-Agent Swarm Collaboration  │ │
│  └───────────────────────────────────┘ │
└─────────┬──────────────────────┬────────┘
          │                      │
          ▼                      ▼
┌──────────────────┐    ┌─────────────────┐
│  Azure OpenAI    │    │ Azure Storage   │
│  (GPT-4)         │    │ (File Share)    │
└──────────────────┘    └─────────────────┘
          │                      │
          └──────────┬───────────┘
                     ▼
          ┌──────────────────────┐
          │  Application Insights │
          │  (Monitoring)         │
          └──────────────────────┘
```

---

## Prerequisites

### Required Tools

1. **Azure CLI** (v2.50.0+)
   ```bash
   # Install
   # Windows
   winget install Microsoft.AzureCLI

   # macOS
   brew install azure-cli

   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

   # Verify
   az --version
   ```

2. **Bicep CLI** (included with Azure CLI v2.20.0+)
   ```bash
   # Verify
   az bicep version

   # Upgrade if needed
   az bicep upgrade
   ```

3. **Azure Subscription**
   - Active Azure subscription
   - Sufficient permissions (Contributor or Owner role)
   - Azure OpenAI access enabled

4. **jq** (for JSON parsing in bash scripts)
   ```bash
   # macOS
   brew install jq

   # Ubuntu/Debian
   sudo apt-get install jq

   # Windows (via Chocolatey)
   choco install jq
   ```

### Azure OpenAI Access

**Important**: Azure OpenAI requires approved access. Apply here:
- https://aka.ms/oai/access

This typically takes 1-2 business days for approval.

---

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Create Resource Group

```bash
# Development
az group create \
  --name aiambassador-dev-rg \
  --location eastus

# Production
az group create \
  --name aiambassador-prod-rg \
  --location eastus
```

### 3. Deploy Infrastructure

```bash
# Navigate to infrastructure directory
cd infrastructure

# Deploy to Development
az deployment group create \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json \
  --name ai-ambassador-deployment

# Deploy to Production
az deployment group create \
  --resource-group aiambassador-prod-rg \
  --template-file main.bicep \
  --parameters @parameters/prod.parameters.json \
  --name ai-ambassador-deployment
```

### 4. Generate local.settings.json

**Windows (PowerShell):**
```powershell
cd scripts
.\Create-LocalSettings.ps1 -ResourceGroupName "aiambassador-dev-rg"
```

**Mac/Linux (Bash):**
```bash
cd scripts
./create-local-settings.sh aiambassador-dev-rg
```

### 5. Deploy Function App Code

```bash
cd ../Copilot-Agent-365-main

# Deploy
func azure functionapp publish <your-function-app-name>
```

---

## Detailed Deployment Steps

### Step 1: Validate Bicep Template

Before deploying, validate the template syntax:

```bash
az deployment group validate \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json
```

**Expected Output:**
```json
{
  "properties": {
    "provisioningState": "Succeeded",
    "validatedResources": [...]
  }
}
```

### Step 2: What-If Analysis

Preview what will be created (without actually deploying):

```bash
az deployment group what-if \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json
```

This shows:
- Resources that will be created (green `+`)
- Resources that will be modified (orange `~`)
- Resources that will be deleted (red `-`)

### Step 3: Deploy with Monitoring

Deploy and watch progress:

```bash
az deployment group create \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json \
  --name ai-ambassador-deployment \
  --verbose
```

**Deployment time:** 5-10 minutes

### Step 4: Verify Deployment

```bash
# Check deployment status
az deployment group show \
  --resource-group aiambassador-dev-rg \
  --name ai-ambassador-deployment \
  --query properties.provisioningState

# List deployed resources
az resource list \
  --resource-group aiambassador-dev-rg \
  --output table
```

### Step 5: Retrieve Deployment Outputs

```bash
# Get all outputs
az deployment group show \
  --resource-group aiambassador-dev-rg \
  --name ai-ambassador-deployment \
  --query properties.outputs

# Get specific output
az deployment group show \
  --resource-group aiambassador-dev-rg \
  --name ai-ambassador-deployment \
  --query properties.outputs.functionAppUrl.value \
  --output tsv
```

---

## Environment Configurations

### Development Environment

**File:** `parameters/dev.parameters.json`

**Configuration:**
- Function App: **Consumption** plan
- OpenAI Capacity: **10K tokens/min**
- Storage: **Standard LRS**
- Zone Redundancy: **Disabled**
- Log Retention: **30 days**

**Estimated Monthly Cost:** $50-150

**Use Cases:**
- Local development
- Feature testing
- Proof of concepts

### Staging Environment

**File:** `parameters/staging.parameters.json`

**Configuration:**
- Function App: **Premium EP1** plan
- OpenAI Capacity: **50K tokens/min**
- Storage: **Standard LRS**
- Zone Redundancy: **Disabled**
- Log Retention: **60 days**

**Estimated Monthly Cost:** $200-500

**Use Cases:**
- Pre-production testing
- UAT testing
- Performance testing

### Production Environment

**File:** `parameters/prod.parameters.json`

**Configuration:**
- Function App: **Premium EP1** plan
- OpenAI Capacity: **100K tokens/min**
- Storage: **Standard ZRS** (zone-redundant)
- Zone Redundancy: **Enabled**
- Log Retention: **90 days**
- Application Insights Sampling: **10%**

**Estimated Monthly Cost:** $500-1,500

**Use Cases:**
- Production workloads
- Customer-facing applications
- High availability required

---

## Cost Optimization

### Development Best Practices

1. **Use Consumption Plan**
   - Pay only for executions
   - Auto-scales to zero when idle
   - Perfect for low-traffic dev/test

2. **Reduce OpenAI Capacity**
   - Start with 10K tokens/min
   - Scale up as needed
   - Monitor usage with Application Insights

3. **Shorter Retention**
   - 30 days for dev environments
   - Reduces Log Analytics costs

4. **Auto-Shutdown**
   - Use Azure DevTest Labs for scheduled shutdown
   - Stop non-prod environments after hours

### Production Cost Optimization

1. **Application Insights Sampling**
   ```bicep
   SamplingPercentage: 10  // Sample 10% of telemetry
   ```
   Reduces costs by 90% while maintaining statistical significance

2. **Reserved Instances**
   - Purchase 1-year reservations for Production
   - Save up to 40% on Function App costs

3. **Storage Lifecycle Policies**
   ```bash
   # Move old data to cool/archive tiers
   az storage account management-policy create \
     --account-name <storage-account> \
     --policy @lifecycle-policy.json
   ```

4. **Monitor and Alert on Costs**
   ```bash
   # Set up budget alerts
   az consumption budget create \
     --amount 1000 \
     --budget-name monthly-budget \
     --resource-group aiambassador-prod-rg \
     --time-grain Monthly
   ```

### Cost Breakdown Estimate

| Environment | OpenAI | Function App | Storage | Monitoring | **Total/Month** |
|-------------|--------|--------------|---------|------------|-----------------|
| **Dev** | $20 | $0 (Consumption) | $5 | $10 | **$35-150** |
| **Staging** | $100 | $150 (Premium) | $10 | $30 | **$290-500** |
| **Prod** | $200 | $200 (Premium) | $20 | $50 | **$470-1,500** |

*Note: Actual costs depend on usage patterns and OpenAI token consumption*

---

## Security Best Practices

### 1. Managed Identity Setup

The Bicep template automatically configures Managed Identity. Verify:

```bash
# Check Function App identity
az functionapp identity show \
  --name <function-app-name> \
  --resource-group aiambassador-prod-rg
```

### 2. Key Vault Access

Function App has automatic access via RBAC. No keys in app settings!

```bash
# Verify role assignment
az role assignment list \
  --scope /subscriptions/<sub-id>/resourceGroups/aiambassador-prod-rg/providers/Microsoft.KeyVault/vaults/<vault-name> \
  --query "[?principalType=='ServicePrincipal']"
```

### 3. Network Security

For production, enable:

**Private Endpoints:**
```bash
# Add private endpoint for Storage
az network private-endpoint create \
  --name storage-private-endpoint \
  --resource-group aiambassador-prod-rg \
  --vnet-name <your-vnet> \
  --subnet <your-subnet> \
  --private-connection-resource-id <storage-account-id> \
  --connection-name storage-connection \
  --group-id file
```

**IP Restrictions:**
```bash
# Restrict Function App to specific IPs
az functionapp config access-restriction add \
  --name <function-app-name> \
  --resource-group aiambassador-prod-rg \
  --rule-name allow-office \
  --action Allow \
  --ip-address 203.0.113.0/24 \
  --priority 100
```

### 4. Enable Monitoring & Alerts

```bash
# Create alert for failed executions
az monitor metrics alert create \
  --name function-failures \
  --resource-group aiambassador-prod-rg \
  --scopes <function-app-id> \
  --condition "count FunctionExecutionCount < 1" \
  --description "Alert when no function executions" \
  --evaluation-frequency 5m \
  --window-size 15m
```

### 5. Secrets Rotation

**OpenAI Keys:**
```bash
# Rotate OpenAI key
az cognitiveservices account keys regenerate \
  --name <openai-account-name> \
  --resource-group aiambassador-prod-rg \
  --key-name key1

# Update Key Vault
az keyvault secret set \
  --vault-name <keyvault-name> \
  --name OpenAI-ApiKey \
  --value "<new-key>"
```

**Storage Keys:**
```bash
# Rotate storage key
az storage account keys renew \
  --account-name <storage-account-name> \
  --key primary

# Update Key Vault
az keyvault secret set \
  --vault-name <keyvault-name> \
  --name Storage-ConnectionString \
  --value "<new-connection-string>"
```

---

## Troubleshooting

### Issue: Deployment Fails with "Location Not Available"

**Error:**
```
The subscription is not registered for the resource type 'accounts' in the location 'westus'.
```

**Solution:**
```bash
# Check available locations for Azure OpenAI
az account list-locations \
  --query "[?metadata.regionType=='Physical'].name" \
  --output table

# Use eastus, westeurope, or other available regions
```

### Issue: OpenAI Deployment Fails

**Error:**
```
The subscription does not have QuotaId/Feature required by SKU 'S0' from kind 'OpenAI' in the location.
```

**Solution:**
1. Ensure Azure OpenAI access is approved
2. Check quota in Azure Portal
3. Request quota increase if needed

### Issue: Function App Won't Start

**Check logs:**
```bash
# Stream live logs
az webapp log tail \
  --name <function-app-name> \
  --resource-group aiambassador-prod-rg

# Download logs
az webapp log download \
  --name <function-app-name> \
  --resource-group aiambassador-prod-rg \
  --log-file logs.zip
```

**Common fixes:**
1. Verify Python 3.11 is configured
2. Check Application Settings are correct
3. Ensure dependencies are in requirements.txt

### Issue: Key Vault Access Denied

**Error:**
```
The user, group or application 'appid=...' does not have secrets get permission
```

**Solution:**
```bash
# Grant Function App access
az keyvault set-policy \
  --name <keyvault-name> \
  --object-id <function-app-principal-id> \
  --secret-permissions get list
```

### Issue: High Costs

**Diagnose:**
```bash
# View cost analysis
az consumption usage list \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --query "[?contains(instanceId, 'aiambassador')]"
```

**Common causes:**
1. OpenAI token usage too high → Implement caching
2. Function App over-scaled → Adjust scale limits
3. Log Analytics retention too long → Reduce to 30 days

---

## Post-Deployment

### 1. Test Function App

```bash
# Get Function App URL
FUNCTION_URL=$(az deployment group show \
  --resource-group aiambassador-dev-rg \
  --name ai-ambassador-deployment \
  --query properties.outputs.functionAppUrl.value \
  --output tsv)

# Test endpoint
curl -X POST "$FUNCTION_URL/api/businessinsightbot_function" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello!", "conversation_history": []}'
```

### 2. Upload Agent Files

```bash
# Get storage account name
STORAGE_ACCOUNT=$(az deployment group show \
  --resource-group aiambassador-dev-rg \
  --name ai-ambassador-deployment \
  --query properties.outputs.storageAccountName.value \
  --output tsv)

# Upload agent files
az storage file upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination aiambassador-files-dev \
  --source ../Copilot-Agent-365-main/agents
```

### 3. Configure Monitoring Dashboard

Create custom dashboard in Azure Portal:
1. Navigate to Application Insights
2. Create dashboard with:
   - Function execution count
   - Average duration
   - Failure rate
   - OpenAI token usage

### 4. Set Up CI/CD

**GitHub Actions Example:**

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy Function App
        run: |
          func azure functionapp publish ${{ secrets.FUNCTION_APP_NAME }}
```

---

## Summary

### Deployment Checklist

- [ ] Azure OpenAI access approved
- [ ] Azure CLI & Bicep installed
- [ ] Resource group created
- [ ] Bicep template validated
- [ ] Infrastructure deployed successfully
- [ ] local.settings.json generated
- [ ] Function app code deployed
- [ ] Agent files uploaded to storage
- [ ] Endpoints tested
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Documentation reviewed

### Key Outputs

After deployment, you'll have:

1. **Function App URL** - API endpoint
2. **Storage Account** - For agents & memory
3. **OpenAI Endpoint** - GPT-4 access
4. **Application Insights** - Monitoring
5. **Key Vault** - Secrets management

### Support

- **Documentation**: See CLAUDE.md in project root
- **Issues**: GitHub repository
- **Azure Support**: https://azure.microsoft.com/support

---

**Deployment Guide Version**: 1.0.0
**Last Updated**: November 7, 2025
**Maintained By**: AI Ambassador Platform Team
