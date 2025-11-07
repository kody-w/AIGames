// Storage Account module for AI Ambassador Platform
param location string
param namingPrefix string
param uniqueId string
param tags object
param environment string
param backupEnabled bool
param retentionDays int

var storageAccountName = replace('${namingPrefix}stor${uniqueId}', '-', '')

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: environment == 'prod' ? 'Standard_ZRS' : 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    defaultToOAuthAuthentication: false
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    encryption: {
      services: {
        file: {
          keyType: 'Account'
          enabled: true
        }
        blob: {
          keyType: 'Account'
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// File Services with backup
resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    shareDeleteRetentionPolicy: {
      enabled: backupEnabled
      days: retentionDays
    }
  }
}

// Blob Services with versioning
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: backupEnabled
      days: retentionDays
    }
    isVersioningEnabled: environment == 'prod'
    changeFeed: {
      enabled: environment == 'prod'
    }
    containerDeleteRetentionPolicy: {
      enabled: backupEnabled
      days: retentionDays
    }
  }
}

// File Shares for ambassador data
resource ambassadorsShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: 'ambassadors'
  properties: {
    shareQuota: environment == 'prod' ? 1024 : 100
    enabledProtocols: 'SMB'
    accessTier: 'TransactionOptimized'
  }
}

resource agentsShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: 'agents'
  properties: {
    shareQuota: environment == 'prod' ? 512 : 50
    enabledProtocols: 'SMB'
    accessTier: 'TransactionOptimized'
  }
}

resource multiAgentsShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: 'multi-agents'
  properties: {
    shareQuota: environment == 'prod' ? 512 : 50
    enabledProtocols: 'SMB'
    accessTier: 'TransactionOptimized'
  }
}

resource memoriesShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: 'memories'
  properties: {
    shareQuota: environment == 'prod' ? 2048 : 100
    enabledProtocols: 'SMB'
    accessTier: 'Hot'
  }
}

resource backupsShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = if (backupEnabled) {
  parent: fileServices
  name: 'backups'
  properties: {
    shareQuota: environment == 'prod' ? 5120 : 200
    enabledProtocols: 'SMB'
    accessTier: 'Cool'
  }
}

// Blob Containers for deployments
resource deploymentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'deployments'
  properties: {
    publicAccess: 'None'
  }
}

resource logsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'logs'
  properties: {
    publicAccess: 'None'
  }
}

// Lifecycle Management
resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          enabled: true
          name: 'move-old-logs-to-cool'
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [
                'blockBlob'
              ]
              prefixMatch: [
                'logs/'
              ]
            }
            actions: {
              baseBlob: {
                tierToCool: {
                  daysAfterModificationGreaterThan: 30
                }
                tierToArchive: {
                  daysAfterModificationGreaterThan: 90
                }
                delete: {
                  daysAfterModificationGreaterThan: retentionDays
                }
              }
            }
          }
        }
        {
          enabled: backupEnabled
          name: 'delete-old-backups'
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [
                'blockBlob'
              ]
              prefixMatch: [
                'backups/'
              ]
            }
            actions: {
              baseBlob: {
                delete: {
                  daysAfterModificationGreaterThan: retentionDays
                }
              }
            }
          }
        }
      ]
    }
  }
}

output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
output primaryEndpoints object = storageAccount.properties.primaryEndpoints
