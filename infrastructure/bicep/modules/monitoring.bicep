// Monitoring module for AI Ambassador Platform
param location string
param namingPrefix string
param uniqueId string
param tags object
param environment string
param alertConfig object

var logAnalyticsName = '${namingPrefix}-logs-${uniqueId}'
var appInsightsName = '${namingPrefix}-appins-${uniqueId}'

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
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
    workspaceCapping: {
      dailyQuotaGb: environment == 'prod' ? 10 : 1
    }
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: environment == 'prod' ? 90 : 30
    SamplingPercentage: environment == 'prod' ? 100 : 50
    DisableIpMasking: false
  }
}

// Action Group for alerts
resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = if (alertConfig.enabled) {
  name: '${namingPrefix}-alerts-ag'
  location: 'global'
  tags: tags
  properties: {
    groupShortName: substring('${environment}-alerts', 0, 12)
    enabled: true
    emailReceivers: [for email in alertConfig.emailRecipients: {
      name: 'email-${uniqueString(email)}'
      emailAddress: email
      useCommonAlertSchema: true
    }]
    webhookReceivers: !empty(alertConfig.slackWebhook) ? [
      {
        name: 'slack-webhook'
        serviceUri: alertConfig.slackWebhook
        useCommonAlertSchema: true
      }
    ] : []
  }
}

// Alert Rules
resource highResponseTimeAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = if (alertConfig.enabled) {
  name: '${namingPrefix}-high-response-time'
  location: 'global'
  tags: tags
  properties: {
    description: 'Alert when average response time exceeds threshold'
    severity: 2
    enabled: true
    scopes: [
      appInsights.id
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'response-time-metric'
          metricName: 'requests/duration'
          operator: 'GreaterThan'
          threshold: environment == 'prod' ? 2000 : 5000
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
  }
}

resource highErrorRateAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = if (alertConfig.enabled) {
  name: '${namingPrefix}-high-error-rate'
  location: 'global'
  tags: tags
  properties: {
    description: 'Alert when error rate exceeds 5%'
    severity: 1
    enabled: true
    scopes: [
      appInsights.id
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'error-rate-metric'
          metricName: 'requests/failed'
          operator: 'GreaterThan'
          threshold: 5
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
  }
}

resource highDependencyFailureAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = if (alertConfig.enabled) {
  name: '${namingPrefix}-dependency-failures'
  location: 'global'
  tags: tags
  properties: {
    description: 'Alert when dependency failure rate is high'
    severity: 1
    enabled: true
    scopes: [
      appInsights.id
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'dependency-failure-metric'
          metricName: 'dependencies/failed'
          operator: 'GreaterThan'
          threshold: 10
          timeAggregation: 'Count'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
  }
}

resource highCpuAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = if (alertConfig.enabled) {
  name: '${namingPrefix}-high-cpu'
  location: 'global'
  tags: tags
  properties: {
    description: 'Alert when CPU usage is consistently high'
    severity: 2
    enabled: true
    scopes: [
      appInsights.id
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT30M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'cpu-metric'
          metricName: 'performanceCounters/processCpuPercentage'
          operator: 'GreaterThan'
          threshold: 80
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
  }
}

resource highMemoryAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = if (alertConfig.enabled) {
  name: '${namingPrefix}-high-memory'
  location: 'global'
  tags: tags
  properties: {
    description: 'Alert when memory usage exceeds threshold'
    severity: 2
    enabled: true
    scopes: [
      appInsights.id
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT30M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'memory-metric'
          metricName: 'performanceCounters/memoryAvailableBytes'
          operator: 'LessThan'
          threshold: 500000000 // 500MB
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
  }
}

// Workbook for dashboard
resource workbook 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: guid(namingPrefix, environment, 'workbook')
  location: location
  tags: tags
  kind: 'shared'
  properties: {
    displayName: '${namingPrefix} Dashboard'
    serializedData: string({
      version: 'Notebook/1.0'
      items: [
        {
          type: 1
          content: {
            json: '## AI Ambassador Platform - ${environment}\n\nOverview of system health and performance metrics'
          }
        }
        {
          type: 10
          content: {
            chartId: 'requests-chart'
            version: 'MetricsItem/2.0'
            size: 0
            chartType: 2
            resourceIds: [
              appInsights.id
            ]
            timeContext: {
              durationMs: 3600000
            }
            metrics: [
              {
                namespace: 'microsoft.insights/components'
                metric: 'requests/count'
                aggregation: 1
              }
            ]
          }
        }
      ]
    })
    category: 'workbook'
    sourceId: appInsights.id
  }
}

output appInsightsName string = appInsights.name
output appInsightsId string = appInsights.id
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output logAnalyticsWorkspaceId string = logAnalytics.id
output actionGroupId string = alertConfig.enabled ? actionGroup.id : ''
