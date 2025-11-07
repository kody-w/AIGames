# AI Ambassador Platform - Deployment Guide

Complete guide for deploying the AI Ambassador Platform to Azure.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
- [Environment Configuration](#environment-configuration)
- [Post-Deployment Steps](#post-deployment-steps)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Azure CLI**: Version 2.50.0 or higher
  ```bash
  # Install Azure CLI
  # macOS
  brew install azure-cli

  # Windows
  winget install Microsoft.AzureCLI

  # Linux
  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
  ```

- **Bicep**: Version 0.20.0 or higher (installed with Azure CLI)
  ```bash
  az bicep install
  az bicep upgrade
  ```

- **Azure Functions Core Tools**: Version 4.x
  ```bash
  # macOS
  brew tap azure/functions
  brew install azure-functions-core-tools@4

  # Windows
  npm install -g azure-functions-core-tools@4
  ```

- **Python**: Version 3.11
  ```bash
  # Check version
  python --version
  ```

- **Git**: For version control
- **jq**: For JSON processing (optional but recommended)

### Azure Requirements

- **Azure Subscription**: Active subscription with sufficient permissions
- **Service Principal**: For CI/CD automation (optional)
- **Required Resource Providers**: Registered in your subscription
  ```bash
  az provider register --namespace Microsoft.Web
  az provider register --namespace Microsoft.Storage
  az provider register --namespace Microsoft.CognitiveServices
  az provider register --namespace Microsoft.KeyVault
  az provider register --namespace Microsoft.Insights
  ```

### Permissions Required

- **Subscription Level**: Contributor or Owner
- **Resource Group Level**: Contributor (minimum)
- **Specific Permissions**:
  - Create and manage Function Apps
  - Create and manage Storage Accounts
  - Create and manage Azure OpenAI resources
  - Create and manage Key Vaults
  - Assign managed identities

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AIGames
```

### 2. Login to Azure

```bash
az login
az account set --subscription <subscription-id>
```

### 3. Configure Environment

Edit the parameter file for your target environment:

```bash
# For dev environment
nano infrastructure/bicep/parameters/dev.bicepparam
```

Update:
- Email addresses for alerts
- Slack webhook (optional)
- Azure OpenAI capacity settings

### 4. Deploy Infrastructure

#### Using Bash (macOS/Linux)

```bash
cd infrastructure
./deploy.sh dev eastus
```

#### Using PowerShell (Windows)

```powershell
cd infrastructure
.\deploy.ps1 -Environment dev -Location eastus
```

### 5. Deploy Application Code

```bash
cd Copilot-Agent-365-main

# Deploy to the created Function App
func azure functionapp publish <function-app-name>
```

### 6. Verify Deployment

```bash
# Test the health endpoint
curl https://<function-app-name>.azurewebsites.net/api/health

# Test the main function
curl -X POST https://<function-app-name>.azurewebsites.net/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

## Deployment Methods

### Method 1: Manual Deployment (Recommended for First Time)

Use the deployment scripts for full control:

```bash
# Validate only (no deployment)
./deploy.sh dev eastus --validate-only

# Full deployment
./deploy.sh dev eastus
```

**Advantages**:
- Full visibility into deployment process
- Interactive confirmations
- Immediate feedback
- Easy troubleshooting

### Method 2: GitHub Actions (Automated CI/CD)

Push to the appropriate branch to trigger deployment:

```bash
# Deploy to dev
git push origin develop

# Deploy to staging
git push origin main

# Deploy to production
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

**Advantages**:
- Fully automated
- Consistent deployments
- Built-in testing
- Audit trail

### Method 3: Azure DevOps Pipelines

Trigger pipeline from Azure DevOps:

1. Go to Azure DevOps project
2. Navigate to Pipelines
3. Select the deployment pipeline
4. Click "Run pipeline"
5. Select environment and branch

### Method 4: Direct Azure CLI

For quick infrastructure-only deployments:

```bash
az deployment sub create \
  --name "manual-deployment-$(date +%s)" \
  --location eastus \
  --template-file infrastructure/bicep/main.bicep \
  --parameters infrastructure/bicep/parameters/dev.bicepparam
```

## Environment Configuration

### Development Environment

**Purpose**: Testing and development

**Configuration**:
- Function App SKU: Y1 (Consumption)
- Storage: Standard_LRS
- OpenAI Capacity: 10 TPM
- Backups: Disabled
- VNet: Disabled

**Estimated Cost**: $5-50/month

**Use Cases**:
- Feature development
- Integration testing
- Demo environments

### Staging Environment

**Purpose**: Pre-production testing and validation

**Configuration**:
- Function App SKU: EP1 (Elastic Premium)
- Storage: Standard_LRS
- OpenAI Capacity: 30 TPM
- Backups: Enabled (14 days)
- VNet: Optional
- Deployment Slots: Enabled

**Estimated Cost**: $200-500/month

**Use Cases**:
- UAT testing
- Performance testing
- Client demos
- Training environments

### Production Environment

**Purpose**: Live production workloads

**Configuration**:
- Function App SKU: EP2 (Elastic Premium)
- Storage: Standard_ZRS (Zone-redundant)
- OpenAI Capacity: 100+ TPM
- Backups: Enabled (30 days)
- VNet: Enabled
- Deployment Slots: Enabled
- Auto-scaling: Enabled
- High Availability: Enabled

**Estimated Cost**: $1,200-5,000/month

**Use Cases**:
- Production traffic
- Mission-critical workloads

## Post-Deployment Steps

### 1. Configure Secrets

Store sensitive values in Key Vault:

```bash
# Example: Add additional secrets
az keyvault secret set \
  --vault-name <keyvault-name> \
  --name "custom-api-key" \
  --value "your-secret-value"
```

### 2. Upload Agent Files

Upload custom agents to Azure File Storage:

```bash
# Get storage connection string
CONN_STRING=$(az storage account show-connection-string \
  --name <storage-account-name> \
  --resource-group <resource-group> \
  --query connectionString -o tsv)

# Upload agents
cd Copilot-Agent-365-main/agents
az storage file upload-batch \
  --destination agents \
  --source . \
  --connection-string "$CONN_STRING"
```

### 3. Configure Ambassador Configurations

Upload ambassador JSON configurations:

```bash
# Upload ambassador configs
az storage file upload \
  --share-name ambassadors \
  --source ambassador-creative-001.json \
  --connection-string "$CONN_STRING"
```

### 4. Configure CORS

If not automatically configured:

```bash
az functionapp cors add \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --allowed-origins "https://ai-ambassadors.app"
```

### 5. Set Up Monitoring Alerts

Verify alert rules are configured:

```bash
az monitor metrics alert list \
  --resource-group <resource-group>
```

### 6. Configure Custom Domains (Production Only)

```bash
# Add custom domain
az functionapp config hostname add \
  --webapp-name <function-app-name> \
  --resource-group <resource-group> \
  --hostname "api.ai-ambassadors.app"

# Enable HTTPS
az functionapp update \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --set httpsOnly=true
```

### 7. Enable Application Insights Live Metrics

```bash
az monitor app-insights component update \
  --app <app-insights-name> \
  --resource-group <resource-group> \
  --query-access Enabled
```

### 8. Test All Endpoints

```bash
# Health check
curl https://<hostname>/api/health

# Main function
curl -X POST https://<hostname>/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Test", "conversation_history": []}'

# Ambassador entry (if implemented)
curl https://<hostname>/api/ambassador_entry?ambassador_id=creative-001
```

## Deployment Strategies

### Blue-Green Deployment

Used for staging and production:

1. Deploy new version to staging slot
2. Run tests on staging slot
3. Swap staging to production
4. Monitor for issues
5. Rollback if needed

```bash
# Deploy to staging slot
func azure functionapp publish <function-app-name> --slot staging

# Swap slots
az functionapp deployment slot swap \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --slot staging
```

### Canary Deployment

Used for production (automated in CD pipeline):

1. Deploy to staging slot (10% traffic)
2. Monitor metrics for 15 minutes
3. Increase to 50% traffic
4. Monitor for 10 minutes
5. Full swap to production

```bash
# Configure traffic routing
az functionapp traffic-routing set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --distribution staging=10
```

### Rolling Deployment

For dev environment:

1. Deploy directly to production slot
2. Monitor health endpoints
3. Rollback if issues detected

## Troubleshooting

### Common Issues

#### 1. Deployment Validation Fails

**Error**: "The template deployment failed because of policy violation"

**Solution**:
- Check Azure Policy restrictions
- Request policy exemption
- Adjust template to comply with policies

#### 2. OpenAI Quota Exceeded

**Error**: "Insufficient quota for GPT-4 deployment"

**Solution**:
```bash
# Check current quota
az cognitiveservices account list-usage \
  --name <openai-account> \
  --resource-group <resource-group>

# Request quota increase
# Submit support ticket through Azure Portal
```

#### 3. Function App Won't Start

**Error**: Function app shows "Service Unavailable"

**Solution**:
```bash
# Check logs
az functionapp log tail \
  --name <function-app-name> \
  --resource-group <resource-group>

# Restart the app
az functionapp restart \
  --name <function-app-name> \
  --resource-group <resource-group>
```

#### 4. Key Vault Access Denied

**Error**: "The user, group or application does not have secrets get permission"

**Solution**:
```bash
# Grant access to Function App managed identity
az keyvault set-policy \
  --name <keyvault-name> \
  --object-id <managed-identity-principal-id> \
  --secret-permissions get list
```

#### 5. Storage Connection Fails

**Error**: "Unable to connect to Azure File Storage"

**Solution**:
- Verify connection string in Key Vault
- Check firewall rules on storage account
- Verify managed identity has Storage Blob Data Contributor role

### Debugging Tips

1. **Enable verbose logging**:
   ```bash
   az functionapp config appsettings set \
     --name <function-app-name> \
     --resource-group <resource-group> \
     --settings "FUNCTIONS_WORKER_RUNTIME_LOG_LEVEL=Debug"
   ```

2. **Check Application Insights**:
   - Go to Azure Portal
   - Navigate to Application Insights
   - View Live Metrics, Failures, and Performance tabs

3. **View resource deployment logs**:
   ```bash
   az deployment sub show \
     --name <deployment-name> \
     --query "properties.error"
   ```

4. **Test locally first**:
   ```bash
   cd Copilot-Agent-365-main
   func start
   ```

### Getting Help

- **Documentation**: Check `/infrastructure/docs/`
- **Logs**: Application Insights in Azure Portal
- **Support**: Create GitHub issue or Azure support ticket

## Next Steps

After successful deployment:

1. Review [INFRASTRUCTURE.md](INFRASTRUCTURE.md) for architecture details
2. Set up [CI/CD pipelines](CICD_SETUP.md)
3. Configure [monitoring and alerts](../infrastructure/docs/MONITORING.md)
4. Review [cost optimization](../infrastructure/scripts/cost-estimation.sh)
5. Set up [disaster recovery plan](TROUBLESHOOTING_DEPLOYMENT.md#disaster-recovery)

## Additional Resources

- [Azure Functions Documentation](https://learn.microsoft.com/azure/azure-functions/)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/cognitive-services/openai/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)
