/*
  AI Ambassador Platform - Ultra-Optimized Infrastructure

  This Bicep template provisions all Azure resources needed for the AI Ambassador Platform
  with best practices for security, performance, and cost optimization.

  Resources Provisioned:
  - Azure OpenAI Service (GPT-4)
  - Azure Storage Account (File Share for agents/memory)
  - Azure Function App (Python 3.11)
  - Application Insights (Monitoring)
  - App Service Plan (Consumption or Premium)
  - Key Vault (Secrets Management)
  - Log Analytics Workspace

  Author: AI Ambassador Platform Team
  Version: 1.0.0
*/

// ============================================================================
// PARAMETERS
// ============================================================================

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Project name - used for resource naming')
@minLength(3)
@maxLength(10)
param projectName string = 'aiambassador'

@description('Unique suffix for globally unique resources (leave empty for auto-generation)')
param uniqueSuffix string = ''

@description('Function App pricing tier')
@allowed([
  'Consumption'  // Best for dev, low traffic
  'Premium'      // Best for prod, high traffic
])
param functionPricingTier string = 'Consumption'

@description('Azure OpenAI model deployment name')
param openAiModelName string = 'gpt-4'

@description('Azure OpenAI model version')
param openAiModelVersion string = '0125-Preview'

@description('Azure OpenAI deployment capacity (in thousands of tokens per minute)')
@minValue(1)
@maxValue(1000)
param openAiCapacity int = 20

@description('Enable zone redundancy for production')
param enableZoneRedundancy bool = false

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'AI-Ambassador-Platform'
  ManagedBy: 'Bicep'
}

// ============================================================================
// VARIABLES
// ============================================================================

var namingPrefix = '${projectName}-${environment}'
var suffix = !empty(uniqueSuffix) ? uniqueSuffix : uniqueString(resourceGroup().id)

// Resource names
var storageAccountName = '${projectName}${environment}${suffix}'
var functionAppName = '${namingPrefix}-func-${suffix}'
var appServicePlanName = '${namingPrefix}-asp'
var openAiAccountName = '${namingPrefix}-openai-${suffix}'
var keyVaultName = '${namingPrefix}-kv-${suffix}'
var appInsightsName = '${namingPrefix}-ai'
var logAnalyticsName = '${namingPrefix}-logs'

// Configuration
var fileShareName = '${projectName}-files-${environment}'
var openAiDeploymentName = '${openAiModelName}-deployment'
var openAiApiVersion = '2024-02-15-preview'

// App Service Plan SKU configuration
var appServicePlanSku = functionPricingTier == 'Premium' ? {
  name: 'EP1'  // Elastic Premium 1
  tier: 'ElasticPremium'
  size: 'EP1'
  family: 'EP'
  capacity: 1
} : {
  name: 'Y1'  // Consumption
  tier: 'Dynamic'
  size: 'Y1'
  family: 'Y'
  capacity: 0
}

// Storage redundancy
var storageSkuName = environment == 'prod' && enableZoneRedundancy ? 'Standard_ZRS' : 'Standard_LRS'

// ============================================================================
// RESOURCES
// ============================================================================

// ----------------------------------------------------------------------------
// Log Analytics Workspace (for Application Insights)
// ----------------------------------------------------------------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: environment == 'prod' ? 90 : 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// ----------------------------------------------------------------------------
// Application Insights
// ----------------------------------------------------------------------------

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: environment == 'prod' ? 90 : 30
    SamplingPercentage: environment == 'prod' ? 10 : 100  // Sample 10% in prod to reduce costs
    DisableIpMasking: false
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ----------------------------------------------------------------------------
// Storage Account (for File Share and Function App storage)
// ----------------------------------------------------------------------------

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: storageSkuName
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        file: {
          enabled: true
          keyType: 'Account'
        }
        blob: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Storage'
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'  // Restrict in prod with private endpoints
    }
  }
}

// File Services
resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    shareDeleteRetentionPolicy: {
      enabled: true
      days: environment == 'prod' ? 14 : 7
    }
  }
}

// File Share for agents and memory
resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: fileShareName
  properties: {
    accessTier: 'TransactionOptimized'
    shareQuota: 5120  // 5TB quota
    enabledProtocols: 'SMB'
  }
}

// ----------------------------------------------------------------------------
// Azure OpenAI Service
// ----------------------------------------------------------------------------

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiAccountName
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// GPT-4 Deployment
resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiAccount
  name: openAiDeploymentName
  sku: {
    name: 'Standard'
    capacity: openAiCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: openAiModelName
      version: openAiModelVersion
    }
    raiPolicyName: 'Microsoft.Default'
  }
}

// ----------------------------------------------------------------------------
// Key Vault (for secure secret storage)
// ----------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: environment == 'prod' ? true : null
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

// Store OpenAI API key in Key Vault
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'OpenAI-ApiKey'
  properties: {
    value: openAiAccount.listKeys().key1
    contentType: 'text/plain'
  }
}

// Store Storage Account connection string in Key Vault
resource storageConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'Storage-ConnectionString'
  properties: {
    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
    contentType: 'text/plain'
  }
}

// ----------------------------------------------------------------------------
// App Service Plan
// ----------------------------------------------------------------------------

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: appServicePlanSku
  kind: functionPricingTier == 'Premium' ? 'elastic' : 'functionapp'
  properties: {
    reserved: true  // Required for Linux
    zoneRedundant: environment == 'prod' && enableZoneRedundancy
  }
}

// ----------------------------------------------------------------------------
// Function App
// ----------------------------------------------------------------------------

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    reserved: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      alwaysOn: functionPricingTier == 'Premium'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      functionAppScaleLimit: functionPricingTier == 'Premium' ? 20 : 200
      minimumElasticInstanceCount: functionPricingTier == 'Premium' ? 1 : 0
      cors: {
        allowedOrigins: [
          '*'  // Configure specific origins in production
        ]
        supportCredentials: false
      }
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        // Azure OpenAI Configuration
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${openAiKeySecret.properties.secretUri})'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAiAccount.properties.endpoint
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: openAiDeploymentName
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: openAiApiVersion
        }
        // Storage Configuration
        {
          name: 'AZURE_FILES_SHARE_NAME'
          value: fileShareName
        }
        // App Configuration
        {
          name: 'ASSISTANT_NAME'
          value: 'AI Ambassador'
        }
        {
          name: 'CHARACTERISTIC_DESCRIPTION'
          value: 'Your intelligent, emotionally aware AI companion with episodic memory and multi-agent collaboration capabilities'
        }
        {
          name: 'USE_LOCAL_STORAGE'
          value: 'false'
        }
        {
          name: 'USE_LOCAL_LLM'
          value: 'false'
        }
        // Performance tuning
        {
          name: 'PYTHON_ISOLATE_WORKER_DEPENDENCIES'
          value: '1'
        }
        {
          name: 'PYTHON_ENABLE_WORKER_EXTENSIONS'
          value: '1'
        }
      ]
    }
  }
}

// ----------------------------------------------------------------------------
// RBAC: Grant Function App access to Key Vault
// ----------------------------------------------------------------------------

// Key Vault Secrets User role
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Resource Group name')
output resourceGroupName string = resourceGroup().name

@description('Storage Account name')
output storageAccountName string = storageAccount.name

@description('Storage Account connection string')
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'

@description('File Share name')
output fileShareName string = fileShareName

@description('Azure OpenAI endpoint')
output openAiEndpoint string = openAiAccount.properties.endpoint

@description('Azure OpenAI API key')
output openAiApiKey string = openAiAccount.listKeys().key1

@description('Azure OpenAI deployment name')
output openAiDeploymentName string = openAiDeploymentName

@description('Azure OpenAI API version')
output openAiApiVersion string = openAiApiVersion

@description('Function App name')
output functionAppName string = functionApp.name

@description('Function App URL')
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'

@description('Application Insights instrumentation key')
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey

@description('Application Insights connection string')
output appInsightsConnectionString string = appInsights.properties.ConnectionString

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

// ============================================================================
// LOCAL SETTINGS GENERATION OUTPUTS
// ============================================================================

@description('Complete local.settings.json content (as JSON string)')
output localSettingsJson string = string({
  IsEncrypted: false
  Values: {
    AzureWebJobsStorage: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
    FUNCTIONS_WORKER_RUNTIME: 'python'
    AZURE_OPENAI_API_KEY: openAiAccount.listKeys().key1
    AZURE_OPENAI_ENDPOINT: openAiAccount.properties.endpoint
    AZURE_OPENAI_DEPLOYMENT_NAME: openAiDeploymentName
    AZURE_OPENAI_API_VERSION: openAiApiVersion
    AZURE_FILES_SHARE_NAME: fileShareName
    ASSISTANT_NAME: 'AI Ambassador'
    CHARACTERISTIC_DESCRIPTION: 'Your intelligent, emotionally aware AI companion with episodic memory and multi-agent collaboration capabilities'
    USE_LOCAL_STORAGE: 'false'
    USE_LOCAL_LLM: 'false'
    APPINSIGHTS_INSTRUMENTATIONKEY: appInsights.properties.InstrumentationKey
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  }
})

@description('PowerShell script to create local.settings.json')
output powershellScript string = '''
# Generated PowerShell script to create local.settings.json
# Run this script in your Copilot-Agent-365-main directory

$localSettings = @'
${string({
  IsEncrypted: false
  Values: {
    AzureWebJobsStorage: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
    FUNCTIONS_WORKER_RUNTIME: 'python'
    AZURE_OPENAI_API_KEY: openAiAccount.listKeys().key1
    AZURE_OPENAI_ENDPOINT: openAiAccount.properties.endpoint
    AZURE_OPENAI_DEPLOYMENT_NAME: openAiDeploymentName
    AZURE_OPENAI_API_VERSION: openAiApiVersion
    AZURE_FILES_SHARE_NAME: fileShareName
    ASSISTANT_NAME: 'AI Ambassador'
    CHARACTERISTIC_DESCRIPTION: 'Your intelligent, emotionally aware AI companion with episodic memory and multi-agent collaboration capabilities'
    USE_LOCAL_STORAGE: 'false'
    USE_LOCAL_LLM: 'false'
    APPINSIGHTS_INSTRUMENTATIONKEY: appInsights.properties.InstrumentationKey
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  }
})}
'@

$localSettings | Out-File -FilePath "local.settings.json" -Encoding UTF8
Write-Host "✅ local.settings.json created successfully!" -ForegroundColor Green
'''

@description('Bash script to create local.settings.json')
output bashScript string = '''
#!/bin/bash
# Generated Bash script to create local.settings.json
# Run this script in your Copilot-Agent-365-main directory

cat > local.settings.json << 'EOF'
${string({
  IsEncrypted: false
  Values: {
    AzureWebJobsStorage: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
    FUNCTIONS_WORKER_RUNTIME: 'python'
    AZURE_OPENAI_API_KEY: openAiAccount.listKeys().key1
    AZURE_OPENAI_ENDPOINT: openAiAccount.properties.endpoint
    AZURE_OPENAI_DEPLOYMENT_NAME: openAiDeploymentName
    AZURE_OPENAI_API_VERSION: openAiApiVersion
    AZURE_FILES_SHARE_NAME: fileShareName
    ASSISTANT_NAME: 'AI Ambassador'
    CHARACTERISTIC_DESCRIPTION: 'Your intelligent, emotionally aware AI companion with episodic memory and multi-agent collaboration capabilities'
    USE_LOCAL_STORAGE: 'false'
    USE_LOCAL_LLM: 'false'
    APPINSIGHTS_INSTRUMENTATIONKEY: appInsights.properties.InstrumentationKey
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  }
})}
EOF

echo "✅ local.settings.json created successfully!"
'''
