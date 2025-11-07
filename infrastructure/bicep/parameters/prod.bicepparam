using '../main.bicep'

param environment = 'prod'
param location = 'eastus'
param functionAppSku = 'EP2' // Elastic Premium 2
param enableVNet = true

param openAiConfig = {
  gpt4: {
    name: 'gpt-4'
    modelName: 'gpt-4'
    modelVersion: '0613'
    capacity: 100
  }
  gpt4Turbo: {
    name: 'gpt-4-turbo'
    modelName: 'gpt-4'
    modelVersion: '1106-Preview'
    capacity: 80
  }
  embeddings: {
    name: 'text-embedding-ada-002'
    modelName: 'text-embedding-ada-002'
    modelVersion: '2'
    capacity: 50
  }
}

param alertConfig = {
  enabled: true
  emailRecipients: [
    'ops-team@example.com'
    'oncall@example.com'
  ]
  slackWebhook: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
}

param backupConfig = {
  enabled: true
  retentionDays: 30
}

param tags = {
  Environment: 'prod'
  Project: 'AI-Ambassador-Platform'
  ManagedBy: 'Bicep'
  CostCenter: 'Production'
  Owner: 'Platform-Team'
  Compliance: 'Required'
}
