// Function App module for AI Ambassador Platform
param location string
param namingPrefix string
param uniqueId string
param tags object
param environment string
param sku string
param storageAccountName string
param appInsightsConnectionString string
param appInsightsInstrumentationKey string
param keyVaultName string
param openAiEndpoint string
param openAiDeploymentName string
param subnetId string = ''

var functionAppName = '${namingPrefix}-func-${uniqueId}'
var appServicePlanName = '${namingPrefix}-plan-${uniqueId}'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: sku
    tier: sku == 'Y1' ? 'Dynamic' : 'ElasticPremium'
  }
  kind: 'functionapp'
  properties: {
    reserved: true // Linux
  }
}

// Function App
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
    reserved: true
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      pythonVersion: '3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      alwaysOn: sku != 'Y1' // Not available in Consumption
      functionAppScaleLimit: environment == 'prod' ? 200 : (environment == 'staging' ? 100 : 10)
      cors: {
        allowedOrigins: [
          'https://ai-ambassadors.app'
          'https://*.ai-ambassadors.app'
        ]
        supportCredentials: false
      }
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=storage-connection-string)'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=storage-connection-string)'
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
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsightsInstrumentationKey
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: openAiDeploymentName
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=openai-api-key)'
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2025-01-01-preview'
        }
        {
          name: 'AZURE_FILES_SHARE_NAME'
          value: 'ambassadors'
        }
        {
          name: 'ASSISTANT_NAME'
          value: 'AI Ambassador'
        }
        {
          name: 'CHARACTERISTIC_DESCRIPTION'
          value: 'Your AI companion'
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'KEY_VAULT_NAME'
          value: keyVaultName
        }
        {
          name: 'PYTHON_ENABLE_WORKER_EXTENSIONS'
          value: '1'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        // Deployment slot settings
        {
          name: 'DEPLOYMENT_SLOT'
          value: 'production'
        }
        // Health check endpoint
        {
          name: 'WEBSITE_HEALTHCHECK_MAXPINGFAILURES'
          value: '3'
        }
      ]
      healthCheckPath: '/api/health'
    }
    virtualNetworkSubnetId: !empty(subnetId) ? subnetId : null
  }
}

// Deployment Slot for blue-green deployment
resource functionAppSlot 'Microsoft.Web/sites/slots@2023-01-01' = if (environment != 'dev') {
  parent: functionApp
  name: 'staging'
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      pythonVersion: '3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      alwaysOn: sku != 'Y1'
      appSettings: [
        {
          name: 'DEPLOYMENT_SLOT'
          value: 'staging'
        }
        // Copy all other settings from main slot
      ]
    }
  }
}

// Grant Function App access to Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource keyVaultAccessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2023-07-01' = {
  parent: keyVault
  name: 'add'
  properties: {
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: functionApp.identity.principalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

// Autoscale settings for Elastic Premium
resource autoscaleSettings 'Microsoft.Insights/autoscalesettings@2022-10-01' = if (startsWith(sku, 'EP')) {
  name: '${functionAppName}-autoscale'
  location: location
  tags: tags
  properties: {
    enabled: true
    targetResourceUri: appServicePlan.id
    profiles: [
      {
        name: 'Auto scale based on CPU and memory'
        capacity: {
          minimum: environment == 'prod' ? '3' : (environment == 'staging' ? '2' : '1')
          maximum: environment == 'prod' ? '20' : (environment == 'staging' ? '10' : '5')
          default: environment == 'prod' ? '3' : (environment == 'staging' ? '2' : '1')
        }
        rules: [
          {
            metricTrigger: {
              metricName: 'CpuPercentage'
              metricResourceUri: appServicePlan.id
              timeGrain: 'PT1M'
              statistic: 'Average'
              timeWindow: 'PT5M'
              timeAggregation: 'Average'
              operator: 'GreaterThan'
              threshold: 70
            }
            scaleAction: {
              direction: 'Increase'
              type: 'ChangeCount'
              value: '2'
              cooldown: 'PT5M'
            }
          }
          {
            metricTrigger: {
              metricName: 'CpuPercentage'
              metricResourceUri: appServicePlan.id
              timeGrain: 'PT1M'
              statistic: 'Average'
              timeWindow: 'PT10M'
              timeAggregation: 'Average'
              operator: 'LessThan'
              threshold: 30
            }
            scaleAction: {
              direction: 'Decrease'
              type: 'ChangeCount'
              value: '1'
              cooldown: 'PT10M'
            }
          }
          {
            metricTrigger: {
              metricName: 'MemoryPercentage'
              metricResourceUri: appServicePlan.id
              timeGrain: 'PT1M'
              statistic: 'Average'
              timeWindow: 'PT5M'
              timeAggregation: 'Average'
              operator: 'GreaterThan'
              threshold: 75
            }
            scaleAction: {
              direction: 'Increase'
              type: 'ChangeCount'
              value: '2'
              cooldown: 'PT5M'
            }
          }
        ]
      }
    ]
  }
}

output functionAppName string = functionApp.name
output functionAppId string = functionApp.id
output hostname string = functionApp.properties.defaultHostName
output principalId string = functionApp.identity.principalId
output slotName string = environment != 'dev' ? functionAppSlot.name : ''
