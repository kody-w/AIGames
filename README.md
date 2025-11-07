# AIBAST Infrastructure - Bicep Deployment

This repository contains Azure Bicep templates for deploying the complete AIBAST (AI-Based Agent System Tools) infrastructure on Azure.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Deployment](#detailed-deployment)
- [Configuration](#configuration)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)

## 🎯 Overview

The AIBAST infrastructure consists of:

- **Azure Functions** - Agent platform runtime (RAPP)
- **Azure File Storage** - Agent code and memory storage
- **Azure Container Registry** - Agent container images
- **Azure Kubernetes Service (AKS)** - Agent deployment platform
- **Azure OpenAI** - AI capabilities
- **Application Insights** - Monitoring and observability
- **Key Vault** - Secrets management

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Subscription                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Resource Group (aibast-{env}-rg)          │ │
│  │                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │  Function   │  │   Storage   │  │   OpenAI    │   │ │
│  │  │     App     │◄─┤   Account   │  │   Service   │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  │         │                                               │ │
│  │         │          ┌─────────────┐  ┌─────────────┐   │ │
│  │         │          │     ACR     │  │     AKS     │   │ │
│  │         │          │  Registry   │◄─┤   Cluster   │   │ │
│  │         │          └─────────────┘  └─────────────┘   │ │
│  │         │                                  │            │ │
│  │         │          ┌─────────────┐        │            │ │
│  │         └─────────►│  Key Vault  │◄───────┘            │ │
│  │                    └─────────────┘                      │ │
│  │                           │                             │ │
│  │                    ┌─────────────┐                     │ │
│  │                    │ App Insights│                     │ │
│  │                    └─────────────┘                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Prerequisites

### Required Tools

1. **Azure CLI** (v2.50.0 or later)
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Or on Windows with winget
   winget install -e --id Microsoft.AzureCLI
   ```

2. **Azure Bicep** (installed automatically with Azure CLI)
   ```bash
   # Verify Bicep installation
   az bicep version
   
   # Upgrade to latest version
   az bicep upgrade
   ```

3. **kubectl** (for AKS management)
   ```bash
   # Install kubectl
   az aks install-cli
   ```

4. **jq** (for JSON processing)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install jq
   
   # macOS
   brew install jq
   ```

### Azure Subscription

- Active Azure subscription with Contributor or Owner role
- Sufficient quota for:
  - 1 Function App (Premium or Consumption plan)
  - 1 Storage Account (Standard)
  - 1 Container Registry (Standard or Premium)
  - 1 AKS cluster (3-20 nodes depending on environment)
  - 1 OpenAI account
  - 1 Key Vault

### Azure Resource Providers

Ensure the following resource providers are registered:

```bash
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.Insights
```

## 🚀 Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd aibast-infrastructure

# Login to Azure
az login

# Set your subscription (optional)
az account set --subscription "<your-subscription-id>"
```

### 2. Update Parameters

Edit the parameters file for your environment:

```bash
# For development
nano parameters/dev.parameters.json

# Update these values:
# - adminEmail: Your email for alerts
# - location: Your preferred Azure region
```

### 3. Deploy

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Deploy to development environment
./deploy.sh dev eastus

# Or manually with Azure CLI
az deployment sub create \
  --name aibast-dev-deployment \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json
```

### 4. Configure AKS Access

```bash
# Get AKS credentials (from deployment output)
az aks get-credentials \
  --resource-group aibast-dev-rg \
  --name aibast-dev-aks-<uniqueid>

# Verify cluster access
kubectl get nodes
```

## 📝 Detailed Deployment

### Module Structure

```
.
├── main.bicep                      # Main orchestration template
├── modules/
│   ├── storage.bicep               # Storage Account & File Share
│   ├── acr.bicep                   # Container Registry
│   ├── openai.bicep                # Azure OpenAI Service
│   ├── monitoring.bicep            # Application Insights & Alerts
│   ├── function-app.bicep          # Azure Function App
│   ├── aks.bicep                   # AKS Cluster
│   └── keyvault.bicep              # Key Vault & Secrets
├── parameters/
│   ├── dev.parameters.json         # Development parameters
│   ├── staging.parameters.json     # Staging parameters
│   └── prod.parameters.json        # Production parameters
├── deploy.sh                       # Deployment automation script
└── README.md                       # This file
```

### Deployment Steps (Manual)

#### Step 1: Validate Template

```bash
az deployment sub validate \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json
```

#### Step 2: What-If Analysis

```bash
az deployment sub what-if \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json
```

#### Step 3: Deploy

```bash
az deployment sub create \
  --name aibast-deployment-$(date +%Y%m%d-%H%M%S) \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json \
  --output json > deployment-output.json
```

#### Step 4: Extract Outputs

```bash
# Get Function App URL
jq -r '.properties.outputs.functionAppUrl.value' deployment-output.json

# Get AKS cluster name
jq -r '.properties.outputs.aksClusterName.value' deployment-output.json

# Get all outputs
jq '.properties.outputs' deployment-output.json
```

## ⚙️ Configuration

### Environment-Specific Parameters

#### Development (`dev.parameters.json`)

```json
{
  "environment": "dev",
  "aksNodeCount": 1,
  "aksNodeVmSize": "Standard_D2s_v3",
  "deployOpenAI": true
}
```

- **Cost**: ~$200-500/month
- **Use Case**: Testing, development, proof-of-concept
- **Features**: Single node AKS, Consumption Function plan

#### Staging (`staging.parameters.json`)

```json
{
  "environment": "staging",
  "aksNodeCount": 2,
  "aksNodeVmSize": "Standard_D4s_v3",
  "deployOpenAI": true
}
```

- **Cost**: ~$500-1,200/month
- **Use Case**: Pre-production testing, QA
- **Features**: Multi-node AKS, Standard storage

#### Production (`prod.parameters.json`)

```json
{
  "environment": "prod",
  "aksNodeCount": 3,
  "aksNodeVmSize": "Standard_D4s_v3",
  "deployOpenAI": true
}
```

- **Cost**: ~$1,200-3,600/month
- **Use Case**: Production workloads
- **Features**: HA AKS with auto-scaling, Premium Function plan, GRS storage, zone redundancy

### Customization Options

#### Modify SKUs

Edit `main.bicep` or individual module files:

```bicep
// In modules/storage.bicep
var storageSku = environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'

// In modules/function-app.bicep
var hostingPlanSku = environment == 'prod' ? 'EP1' : 'Y1'
```

#### Add Custom Tags

Edit `main.bicep`:

```bicep
var tags = {
  Environment: environment
  Project: 'AIBAST'
  ManagedBy: 'Bicep'
  CostCenter: 'AI-Innovation'
  Owner: 'YourTeam'
}
```

## 🔧 Post-Deployment

### 1. Configure Function App

```bash
# Get Function App name
FUNCTION_APP=$(jq -r '.properties.outputs.functionAppName.value' deployment-output.json)

# Deploy function code (using Azure Functions Core Tools)
cd /path/to/function-app-code
func azure functionapp publish $FUNCTION_APP
```

### 2. Initialize Storage Structure

```bash
# Get storage connection string from Key Vault
RESOURCE_GROUP=$(jq -r '.properties.outputs.resourceGroupName.value' deployment-output.json)
KV_NAME=$(jq -r '.properties.outputs.keyVaultName.value' deployment-output.json)

STORAGE_CONN=$(az keyvault secret show \
  --vault-name $KV_NAME \
  --name storage-connection-string \
  --query value -o tsv)

# Create directory structure (using Azure CLI or Storage Explorer)
az storage directory create \
  --share-name <file-share-name> \
  --name agents \
  --connection-string "$STORAGE_CONN"

az storage directory create \
  --share-name <file-share-name> \
  --name multi_agents \
  --connection-string "$STORAGE_CONN"

az storage directory create \
  --share-name <file-share-name> \
  --name agent_catalogue \
  --connection-string "$STORAGE_CONN"

az storage directory create \
  --share-name <file-share-name> \
  --name shared_memories \
  --connection-string "$STORAGE_CONN"
```

### 3. Configure AKS with Kubernetes Resources

```bash
# Get AKS credentials
AKS_NAME=$(jq -r '.properties.outputs.aksClusterName.value' deployment-output.json)
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME

# Create namespace
kubectl create namespace aibast-agents

# Create secrets from Key Vault
kubectl create secret generic azure-secrets \
  --from-literal=openai-api-key=$(az keyvault secret show --vault-name $KV_NAME --name azure-openai-api-key --query value -o tsv) \
  --namespace aibast-agents

# Apply Kubernetes manifests
kubectl apply -f kubernetes/
```

### 4. Verify Deployment

```bash
# Test Function App endpoint
FUNCTION_URL=$(jq -r '.properties.outputs.functionAppUrl.value' deployment-output.json)
curl "$FUNCTION_URL/api/health"

# Check AKS nodes
kubectl get nodes

# Check Application Insights
APP_INSIGHTS=$(jq -r '.properties.outputs.appInsightsName.value' deployment-output.json)
az monitor app-insights component show \
  --app $APP_INSIGHTS \
  --resource-group $RESOURCE_GROUP
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Deployment Fails with Quota Errors

**Problem**: "Quota exceeded for Standard_D4s_v3"

**Solution**:
```bash
# Check current quota
az vm list-usage --location eastus --output table

# Request quota increase
az support tickets create \
  --ticket-name "AKS-Quota-Increase" \
  --problem-classification "/providers/Microsoft.Support/services/quota/problemClassifications/cores-or-quota-increase"
```

#### 2. OpenAI Deployment Fails

**Problem**: "Azure OpenAI is not available in this region"

**Solution**:
- Check OpenAI availability: https://learn.microsoft.com/azure/ai-services/openai/concepts/models
- Use supported regions: eastus, westeurope, southcentralus
- Update `location` parameter in deployment

#### 3. Function App Cannot Access Storage

**Problem**: "Failed to connect to storage account"

**Solution**:
```bash
# Verify storage connection string in Function App settings
az functionapp config appsettings list \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='AzureWebJobsStorage'].value"

# Restart Function App
az functionapp restart \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP
```

#### 4. AKS Nodes Not Ready

**Problem**: kubectl shows nodes in "NotReady" state

**Solution**:
```bash
# Check node status
kubectl describe nodes

# Check system pods
kubectl get pods -n kube-system

# Check AKS diagnostics
az aks show \
  --name $AKS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "provisioningState"
```

### Debug Commands

```bash
# View deployment logs
az deployment sub show \
  --name <deployment-name> \
  --query properties.error

# Check resource group status
az group show --name $RESOURCE_GROUP --query properties.provisioningState

# View Activity Log
az monitor activity-log list \
  --resource-group $RESOURCE_GROUP \
  --max-events 50

# Function App logs
az functionapp log tail \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP
```

## 💰 Cost Estimation

### Monthly Cost Breakdown by Environment

#### Development Environment
| Service | SKU | Estimated Cost |
|---------|-----|----------------|
| Function App | Consumption Y1 | $0-50 |
| Storage Account | Standard LRS | $20-40 |
| Container Registry | Standard | $25 |
| AKS | 1x Standard_D2s_v3 | $70-100 |
| Azure OpenAI | Pay-per-use | $50-200 |
| Key Vault | Standard | $5 |
| Application Insights | Pay-per-GB | $10-30 |
| **Total** | | **~$200-500/month** |

#### Staging Environment
| Service | SKU | Estimated Cost |
|---------|-----|----------------|
| Function App | Consumption Y1 | $0-100 |
| Storage Account | Standard LRS | $30-60 |
| Container Registry | Standard | $25 |
| AKS | 2x Standard_D4s_v3 | $280-400 |
| Azure OpenAI | Pay-per-use | $100-400 |
| Key Vault | Standard | $5 |
| Application Insights | Pay-per-GB | $20-50 |
| **Total** | | **~$500-1,200/month** |

#### Production Environment
| Service | SKU | Estimated Cost |
|---------|-----|----------------|
| Function App | Premium EP1 | $150-300 |
| Storage Account | Standard GRS | $50-100 |
| Container Registry | Premium | $50 |
| AKS | 3x Standard_D4s_v3 (scales to 20) | $420-2,800 |
| Azure OpenAI | Pay-per-use | $200-1,000 |
| Key Vault | Standard | $5 |
| Application Insights | Pay-per-GB | $50-150 |
| **Total** | | **~$1,200-3,600/month** |

### Cost Optimization Tips

1. **Use Spot Instances for AKS** (non-production)
   ```bicep
   // In modules/aks.bicep
   scaleSetPriority: 'Spot'
   scaleSetEvictionPolicy: 'Delete'
   spotMaxPrice: -1 // Pay up to regular price
   ```

2. **Enable Auto-shutdown for Dev/Test**
   ```bash
   # Stop AKS cluster during off-hours
   az aks stop --name $AKS_NAME --resource-group $RESOURCE_GROUP
   
   # Start when needed
   az aks start --name $AKS_NAME --resource-group $RESOURCE_GROUP
   ```

3. **Use Azure Reservations** (production)
   - 1-year or 3-year reserved instances for VMs
   - Can save up to 72% on compute costs

4. **Monitor and Set Budgets**
   ```bash
   # Create a budget alert
   az consumption budget create \
     --budget-name aibast-monthly-budget \
     --amount 2000 \
     --resource-group $RESOURCE_GROUP \
     --time-grain Monthly
   ```

## 🔐 Security Best Practices

### 1. Enable Private Endpoints (Production)

```bicep
// In modules/storage.bicep
networkAcls: {
  bypass: 'AzureServices'
  defaultAction: 'Deny'
  virtualNetworkRules: [
    {
      id: subnetId
      action: 'Allow'
    }
  ]
}
```

### 2. Use Managed Identities

All resources already use managed identities. Verify:

```bash
# Check Function App identity
az functionapp identity show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP

# Check AKS identity
az aks show \
  --name $AKS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query identity
```

### 3. Enable Microsoft Defender

```bash
# Enable Defender for Cloud
az security pricing create \
  --name VirtualMachines \
  --tier Standard

# Enable Defender for Containers
az security pricing create \
  --name Containers \
  --tier Standard
```

### 4. Rotate Secrets Regularly

```bash
# Rotate storage key
az storage account keys renew \
  --account-name $STORAGE_NAME \
  --key primary

# Update Key Vault secret
az keyvault secret set \
  --vault-name $KV_NAME \
  --name storage-connection-string \
  --value "new-connection-string"
```

## 📚 Additional Resources

- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [AKS Best Practices](https://learn.microsoft.com/azure/aks/best-practices)
- [Azure Functions Best Practices](https://learn.microsoft.com/azure/azure-functions/functions-best-practices)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Your License Here]

## 📧 Support

For issues or questions:
- Create an issue in the repository
- Contact: admin@example.com
