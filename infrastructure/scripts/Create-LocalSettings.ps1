<#
.SYNOPSIS
    Generates local.settings.json from Azure deployment outputs

.DESCRIPTION
    This script retrieves outputs from an Azure Bicep deployment and creates
    a local.settings.json file for local Function App development.

.PARAMETER ResourceGroupName
    Name of the Azure Resource Group

.PARAMETER DeploymentName
    Name of the deployment (default: "ai-ambassador-deployment")

.PARAMETER OutputPath
    Path where local.settings.json will be created (default: current directory)

.EXAMPLE
    .\Create-LocalSettings.ps1 -ResourceGroupName "aiambassador-dev-rg"

.EXAMPLE
    .\Create-LocalSettings.ps1 -ResourceGroupName "aiambassador-dev-rg" -OutputPath "../Copilot-Agent-365-main"

.NOTES
    Author: AI Ambassador Platform Team
    Version: 1.0.0
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory=$false)]
    [string]$DeploymentName = "ai-ambassador-deployment",

    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "."
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 AI Ambassador Platform - Local Settings Generator" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
try {
    $azVersion = az version 2>$null
    if (-not $azVersion) {
        throw "Azure CLI not found"
    }
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI is not installed or not in PATH" -ForegroundColor Red
    Write-Host "   Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Check if logged in to Azure
Write-Host "🔍 Checking Azure login status..." -ForegroundColor Yellow
try {
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        throw "Not logged in"
    }
    Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "✅ Subscription: $($account.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in to Azure" -ForegroundColor Red
    Write-Host "   Run: az login" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Get deployment outputs
Write-Host "📥 Retrieving deployment outputs from Azure..." -ForegroundColor Yellow
try {
    $outputs = az deployment group show `
        --resource-group $ResourceGroupName `
        --name $DeploymentName `
        --query properties.outputs `
        2>$null | ConvertFrom-Json

    if (-not $outputs) {
        throw "Deployment not found"
    }
    Write-Host "✅ Deployment outputs retrieved successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to retrieve deployment outputs" -ForegroundColor Red
    Write-Host "   Resource Group: $ResourceGroupName" -ForegroundColor Yellow
    Write-Host "   Deployment Name: $DeploymentName" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Available deployments:" -ForegroundColor Yellow
    az deployment group list --resource-group $ResourceGroupName --query "[].name" -o table
    exit 1
}

Write-Host ""

# Extract values from outputs
Write-Host "🔧 Extracting configuration values..." -ForegroundColor Yellow

$storageConnectionString = $outputs.storageConnectionString.value
$openAiApiKey = $outputs.openAiApiKey.value
$openAiEndpoint = $outputs.openAiEndpoint.value
$openAiDeploymentName = $outputs.openAiDeploymentName.value
$openAiApiVersion = $outputs.openAiApiVersion.value
$fileShareName = $outputs.fileShareName.value
$appInsightsKey = $outputs.appInsightsInstrumentationKey.value
$appInsightsConnectionString = $outputs.appInsightsConnectionString.value

# Validate required values
$requiredValues = @{
    "Storage Connection String" = $storageConnectionString
    "OpenAI API Key" = $openAiApiKey
    "OpenAI Endpoint" = $openAiEndpoint
    "OpenAI Deployment Name" = $openAiDeploymentName
}

$missingValues = @()
foreach ($key in $requiredValues.Keys) {
    if ([string]::IsNullOrWhiteSpace($requiredValues[$key])) {
        $missingValues += $key
    }
}

if ($missingValues.Count -gt 0) {
    Write-Host "❌ Missing required values:" -ForegroundColor Red
    $missingValues | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    exit 1
}

Write-Host "✅ All required values extracted" -ForegroundColor Green
Write-Host ""

# Create local.settings.json content
$localSettings = @{
    IsEncrypted = $false
    Values = @{
        AzureWebJobsStorage = $storageConnectionString
        FUNCTIONS_WORKER_RUNTIME = "python"
        AZURE_OPENAI_API_KEY = $openAiApiKey
        AZURE_OPENAI_ENDPOINT = $openAiEndpoint
        AZURE_OPENAI_DEPLOYMENT_NAME = $openAiDeploymentName
        AZURE_OPENAI_API_VERSION = $openAiApiVersion
        AZURE_FILES_SHARE_NAME = $fileShareName
        ASSISTANT_NAME = "AI Ambassador"
        CHARACTERISTIC_DESCRIPTION = "Your intelligent, emotionally aware AI companion with episodic memory and multi-agent collaboration capabilities"
        USE_LOCAL_STORAGE = "false"
        USE_LOCAL_LLM = "false"
        APPINSIGHTS_INSTRUMENTATIONKEY = $appInsightsKey
        APPLICATIONINSIGHTS_CONNECTION_STRING = $appInsightsConnectionString
    }
}

# Ensure output directory exists
$outputDir = Resolve-Path -Path $OutputPath -ErrorAction SilentlyContinue
if (-not $outputDir) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    $outputDir = Resolve-Path -Path $OutputPath
}

$outputFile = Join-Path -Path $outputDir -ChildPath "local.settings.json"

# Check if file already exists
if (Test-Path $outputFile) {
    Write-Host "⚠️  local.settings.json already exists at: $outputFile" -ForegroundColor Yellow
    $response = Read-Host "   Overwrite? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "❌ Operation cancelled" -ForegroundColor Red
        exit 0
    }
}

# Write to file
Write-Host "📝 Creating local.settings.json..." -ForegroundColor Yellow
try {
    $localSettings | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputFile -Encoding UTF8
    Write-Host "✅ local.settings.json created successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create local.settings.json: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📁 File location: $outputFile" -ForegroundColor Cyan
Write-Host ""

# Display configuration summary
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "📊 Configuration Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Azure OpenAI:" -ForegroundColor White
Write-Host "  Endpoint:       $openAiEndpoint" -ForegroundColor Gray
Write-Host "  Deployment:     $openAiDeploymentName" -ForegroundColor Gray
Write-Host "  API Version:    $openAiApiVersion" -ForegroundColor Gray
Write-Host ""
Write-Host "Storage:" -ForegroundColor White
Write-Host "  File Share:     $fileShareName" -ForegroundColor Gray
Write-Host ""
Write-Host "Monitoring:" -ForegroundColor White
Write-Host "  App Insights:   Configured" -ForegroundColor Gray
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Next steps
Write-Host "🎉 Next Steps:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Navigate to your function app directory:" -ForegroundColor White
Write-Host "   cd Copilot-Agent-365-main" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the local function app:" -ForegroundColor White
Write-Host "   ./run.ps1  (Windows)" -ForegroundColor Gray
Write-Host "   ./run.sh   (Mac/Linux)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test the API:" -ForegroundColor White
Write-Host '   curl -X POST http://localhost:7071/api/businessinsightbot_function `' -ForegroundColor Gray
Write-Host '     -H "Content-Type: application/json" `' -ForegroundColor Gray
Write-Host '     -d ''{"user_input": "Hello!", "conversation_history": []}''' -ForegroundColor Gray
Write-Host ""
Write-Host "✨ Your AI Ambassador Platform is ready to run locally!" -ForegroundColor Green
Write-Host ""
