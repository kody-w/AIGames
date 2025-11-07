// Azure OpenAI module for AI Ambassador Platform
param location string
param namingPrefix string
param uniqueId string
param tags object
param environment string
param deploymentConfig object

var openAiAccountName = '${namingPrefix}-openai-${uniqueId}'

// Azure OpenAI Account
resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
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
    }
  }
}

// GPT-4 Deployment
resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAiAccount
  name: deploymentConfig.gpt4.name
  sku: {
    name: 'Standard'
    capacity: deploymentConfig.gpt4.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: deploymentConfig.gpt4.modelName
      version: deploymentConfig.gpt4.modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
}

// GPT-4 Turbo Deployment (for high-throughput scenarios)
resource gpt4TurboDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = if (environment == 'prod') {
  parent: openAiAccount
  name: deploymentConfig.gpt4Turbo.name
  sku: {
    name: 'Standard'
    capacity: deploymentConfig.gpt4Turbo.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: deploymentConfig.gpt4Turbo.modelName
      version: deploymentConfig.gpt4Turbo.modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
  dependsOn: [
    gpt4Deployment
  ]
}

// Embeddings Deployment (for future RAG capabilities)
resource embeddingsDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = if (contains(deploymentConfig, 'embeddings')) {
  parent: openAiAccount
  name: deploymentConfig.embeddings.name
  sku: {
    name: 'Standard'
    capacity: deploymentConfig.embeddings.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: deploymentConfig.embeddings.modelName
      version: deploymentConfig.embeddings.modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
  dependsOn: [
    gpt4Deployment
    gpt4TurboDeployment
  ]
}

// Diagnostic Settings
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: openAiAccount
  name: 'openai-diagnostics'
  properties: {
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: environment == 'prod' ? 90 : 30
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: environment == 'prod' ? 90 : 30
        }
      }
    ]
  }
}

output accountName string = openAiAccount.name
output accountId string = openAiAccount.id
output endpoint string = openAiAccount.properties.endpoint
output deploymentName string = gpt4Deployment.name
output apiKey string = openAiAccount.listKeys().key1
output customDomain string = 'https://${openAiAccount.properties.customSubDomainName}.openai.azure.com/'
