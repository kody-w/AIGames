using '../main.bicep'

param environment = 'dev'
param location = 'eastus'
param functionAppSku = 'Y1' // Consumption plan
param enableVNet = false

param openAiConfig = {
  gpt4: {
    name: 'gpt-4'
    modelName: 'gpt-4'
    modelVersion: '0613'
    capacity: 10
  }
  gpt4Turbo: {
    name: 'gpt-4-turbo'
    modelName: 'gpt-4'
    modelVersion: '1106-Preview'
    capacity: 0
  }
}

param alertConfig = {
  enabled: true
  emailRecipients: [
    'dev-team@example.com'
  ]
  slackWebhook: ''
}

param backupConfig = {
  enabled: false
  retentionDays: 7
}

param tags = {
  Environment: 'dev'
  Project: 'AI-Ambassador-Platform'
  ManagedBy: 'Bicep'
  CostCenter: 'Development'
  Owner: 'DevTeam'
}
