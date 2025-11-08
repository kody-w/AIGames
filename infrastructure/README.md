# 🏗️ AI Ambassador Platform - Infrastructure as Code

## Overview

**Ultra-optimized Bicep infrastructure** for deploying the AI Ambassador Platform to Azure with best practices for security, performance, and cost optimization.

## 📁 Directory Structure

```
infrastructure/
├── main.bicep                          # Main Bicep template
├── parameters/
│   ├── dev.parameters.json            # Development environment
│   ├── staging.parameters.json        # Staging environment
│   └── prod.parameters.json           # Production environment
├── scripts/
│   ├── Create-LocalSettings.ps1       # PowerShell script (Windows)
│   └── create-local-settings.sh       # Bash script (Mac/Linux)
├── DEPLOYMENT_GUIDE.md                # Comprehensive deployment guide
└── README.md                          # This file
```

## 🚀 Quick Start

### 1. Deploy Infrastructure

```bash
# Login to Azure
az login

# Create resource group
az group create --name aiambassador-dev-rg --location eastus

# Deploy
az deployment group create \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json \
  --name ai-ambassador-deployment
```

### 2. Generate local.settings.json

**Windows:**
```powershell
.\scripts\Create-LocalSettings.ps1 -ResourceGroupName "aiambassador-dev-rg"
```

**Mac/Linux:**
```bash
./scripts/create-local-settings.sh aiambassador-dev-rg
```

### 3. Deploy Function App

```bash
cd ../Copilot-Agent-365-main
func azure functionapp publish <your-function-app-name>
```

## 📊 Resources Deployed

| Resource | Purpose | SKU |
|----------|---------|-----|
| Azure OpenAI | GPT-4 AI processing | Standard (S0) |
| Storage Account | Agent code & memory | Standard LRS/ZRS |
| Function App | Serverless API | Consumption/Premium |
| Application Insights | Monitoring | Pay-as-you-go |
| Log Analytics | Centralized logging | Pay-as-you-go |
| Key Vault | Secrets management | Standard |

## 💰 Cost Estimates

| Environment | Monthly Cost |
|-------------|--------------|
| **Development** | $35-150 |
| **Staging** | $290-500 |
| **Production** | $470-1,500 |

*Costs vary based on usage and OpenAI token consumption*

## 🔐 Security Features

- ✅ Managed Identity for Function App
- ✅ Secrets stored in Key Vault
- ✅ HTTPS only
- ✅ Minimum TLS 1.2
- ✅ RBAC for all resources
- ✅ No hardcoded secrets
- ✅ Soft delete enabled on Key Vault

## 🎯 Features

### Multi-Environment Support
- **Dev**: Consumption plan, low capacity
- **Staging**: Premium plan, medium capacity
- **Prod**: Premium plan, high capacity, zone redundancy

### Automatic local.settings.json Generation
Scripts automatically extract deployment outputs and create properly formatted local.settings.json files.

### Cost Optimization
- Consumption plan for dev
- Application Insights sampling (10% in prod)
- Configurable retention policies
- Storage lifecycle management ready

### High Availability (Production)
- Zone redundancy for storage
- Premium Functions plan
- Multiple availability zones

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[main.bicep](./main.bicep)** - Infrastructure template with inline documentation

## 🛠️ Customization

### Modify Environment Parameters

Edit `parameters/<env>.parameters.json`:

```json
{
  "parameters": {
    "openAiCapacity": {
      "value": 50  // Increase/decrease capacity
    },
    "functionPricingTier": {
      "value": "Premium"  // or "Consumption"
    }
  }
}
```

### Add Custom Resources

Extend `main.bicep`:

```bicep
resource customResource 'Microsoft.Resource/type@version' = {
  name: 'custom-resource'
  // ... configuration
}
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
- name: Deploy Infrastructure
  run: |
    az deployment group create \
      --resource-group ${{ secrets.RESOURCE_GROUP }} \
      --template-file infrastructure/main.bicep \
      --parameters @infrastructure/parameters/prod.parameters.json
```

### Azure DevOps

```yaml
- task: AzureResourceManagerTemplateDeployment@3
  inputs:
    deploymentScope: 'Resource Group'
    azureResourceManagerConnection: 'Azure-Connection'
    resourceGroupName: '$(resourceGroupName)'
    location: 'East US'
    templateLocation: 'Linked artifact'
    csmFile: 'infrastructure/main.bicep'
    csmParametersFile: 'infrastructure/parameters/prod.parameters.json'
```

## 🧪 Validation

### Validate Template

```bash
az deployment group validate \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json
```

### What-If Analysis

```bash
az deployment group what-if \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json
```

## 🆘 Troubleshooting

### Common Issues

**Issue: "Location not available"**
```bash
# Use eastus, westeurope, or other regions with OpenAI
```

**Issue: "OpenAI quota exceeded"**
```bash
# Request quota increase in Azure Portal
```

**Issue: "Key Vault access denied"**
```bash
# Wait 5 minutes for RBAC propagation
# Or manually grant access
```

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for complete troubleshooting.

## 📊 Monitoring

### View Deployment Status

```bash
az deployment group show \
  --resource-group aiambassador-dev-rg \
  --name ai-ambassador-deployment \
  --query properties.provisioningState
```

### Get Outputs

```bash
az deployment group show \
  --resource-group aiambassador-dev-rg \
  --name ai-ambassador-deployment \
  --query properties.outputs
```

## 🔧 Maintenance

### Update Infrastructure

```bash
# Modify parameters or template
# Re-deploy (idempotent)
az deployment group create \
  --resource-group aiambassador-dev-rg \
  --template-file main.bicep \
  --parameters @parameters/dev.parameters.json \
  --name ai-ambassador-deployment
```

### Delete Resources

```bash
# Delete entire resource group
az group delete --name aiambassador-dev-rg --yes

# Or delete individual resources via portal
```

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-07 | Initial release with multi-environment support |

## 🤝 Contributing

When modifying infrastructure:

1. Test in dev environment first
2. Run `az deployment group validate`
3. Run `az deployment group what-if`
4. Update documentation
5. Update version in parameters files

## 📚 Resources

- [Azure Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/cognitive-services/openai-service/)
- [Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/)
- [Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

## 📧 Support

- **Documentation**: See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Issues**: GitHub repository
- **Azure Support**: https://azure.microsoft.com/support

---

**Infrastructure Version**: 1.0.0
**Bicep Version**: ≥0.15.0
**Azure CLI Version**: ≥2.50.0

✨ **Ready to deploy production-grade AI infrastructure in minutes!**
