using '../main.bicep'

param environment = 'staging'
param location = 'eastus'
param functionAppSku = 'EP1' // Elastic Premium 1
param enableVNet = false

param openAiConfig = {
  gpt4: {
    name: 'gpt-4'
    modelName: 'gpt-4'
    modelVersion: '0613'
    capacity: 30
  }
  gpt4Turbo: {
    name: 'gpt-4-turbo'
    modelName: 'gpt-4'
    modelVersion: '1106-Preview'
    capacity: 0
  }
  embeddings: {
    name: 'text-embedding-ada-002'
    modelName: 'text-embedding-ada-002'
    modelVersion: '2'
    capacity: 20
  }
}

param alertConfig = {
  enabled: true
  emailRecipients: [
    'staging-team@example.com'
  ]
  slackWebhook: ''
}

param backupConfig = {
  enabled: true
  retentionDays: 14
}

param tags = {
  Environment: 'staging'
  Project: 'AI-Ambassador-Platform'
  ManagedBy: 'Bicep'
  CostCenter: 'Staging'
  Owner: 'DevOps'
}
