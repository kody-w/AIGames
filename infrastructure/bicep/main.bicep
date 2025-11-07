// Main Bicep template for AI Ambassador Platform
targetScope = 'subscription'

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string

@description('Azure region for resources')
param location string

@description('Unique identifier for resource naming')
param uniqueId string = substring(uniqueString(subscription().subscriptionId, environment), 0, 8)

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'AI-Ambassador-Platform'
  ManagedBy: 'Bicep'
  CostCenter: 'AI-Platform'
}

@description('Enable advanced networking features')
param enableVNet bool = false

@description('SKU tier for Function App')
@allowed([
  'Y1' // Consumption
  'EP1' // Elastic Premium 1
  'EP2' // Elastic Premium 2
  'EP3' // Elastic Premium 3
])
param functionAppSku string

@description('Azure OpenAI deployment configuration')
param openAiConfig object

@description('Alert configuration')
param alertConfig object = {
  enabled: true
  emailRecipients: []
  slackWebhook: ''
}

@description('Backup configuration')
param backupConfig object = {
  enabled: environment == 'prod'
  retentionDays: environment == 'prod' ? 30 : 7
}

// Resource naming convention: aibast-{env}-{resource}-{uniqueId}
var resourceGroupName = 'aibast-${environment}-rg'
var namingPrefix = 'aibast-${environment}'

// Create Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Deploy Key Vault (must be first for secrets)
module keyVault 'modules/key-vault.bicep' = {
  scope: rg
  name: 'keyVault-deployment'
  params: {
    location: location
    namingPrefix: namingPrefix
    uniqueId: uniqueId
    tags: tags
    environment: environment
  }
}

// Deploy Storage Account
module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage-deployment'
  params: {
    location: location
    namingPrefix: namingPrefix
    uniqueId: uniqueId
    tags: tags
    environment: environment
    backupEnabled: backupConfig.enabled
    retentionDays: backupConfig.retentionDays
  }
}

// Deploy Application Insights and Log Analytics
module monitoring 'modules/monitoring.bicep' = {
  scope: rg
  name: 'monitoring-deployment'
  params: {
    location: location
    namingPrefix: namingPrefix
    uniqueId: uniqueId
    tags: tags
    environment: environment
    alertConfig: alertConfig
  }
}

// Deploy Azure OpenAI
module openai 'modules/openai.bicep' = {
  scope: rg
  name: 'openai-deployment'
  params: {
    location: location
    namingPrefix: namingPrefix
    uniqueId: uniqueId
    tags: tags
    environment: environment
    deploymentConfig: openAiConfig
  }
}

// Deploy VNet (optional)
module networking 'modules/networking.bicep' = if (enableVNet) {
  scope: rg
  name: 'networking-deployment'
  params: {
    location: location
    namingPrefix: namingPrefix
    uniqueId: uniqueId
    tags: tags
    environment: environment
  }
}

// Deploy Function App
module functionApp 'modules/function-app.bicep' = {
  scope: rg
  name: 'functionApp-deployment'
  params: {
    location: location
    namingPrefix: namingPrefix
    uniqueId: uniqueId
    tags: tags
    environment: environment
    sku: functionAppSku
    storageAccountName: storage.outputs.storageAccountName
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    appInsightsInstrumentationKey: monitoring.outputs.appInsightsInstrumentationKey
    keyVaultName: keyVault.outputs.keyVaultName
    openAiEndpoint: openai.outputs.endpoint
    openAiDeploymentName: openai.outputs.deploymentName
    subnetId: enableVNet ? networking.outputs.functionSubnetId : ''
  }
  dependsOn: [
    keyVault
    storage
    monitoring
    openai
  ]
}

// Store secrets in Key Vault
module secrets 'modules/key-vault-secrets.bicep' = {
  scope: rg
  name: 'secrets-deployment'
  params: {
    keyVaultName: keyVault.outputs.keyVaultName
    storageConnectionString: storage.outputs.connectionString
    openAiKey: openai.outputs.apiKey
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
  }
  dependsOn: [
    keyVault
    storage
    openai
    monitoring
  ]
}

// Outputs for CI/CD pipelines
output resourceGroupName string = resourceGroupName
output functionAppName string = functionApp.outputs.functionAppName
output functionAppHostname string = functionApp.outputs.hostname
output storageAccountName string = storage.outputs.storageAccountName
output keyVaultName string = keyVault.outputs.keyVaultName
output appInsightsName string = monitoring.outputs.appInsightsName
output openAiEndpoint string = openai.outputs.endpoint
output openAiDeploymentName string = openai.outputs.deploymentName
