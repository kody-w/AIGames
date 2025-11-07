# AI Ambassador Platform - Deployment Script (PowerShell)
# Usage: .\deploy.ps1 -Environment <env> -Location <location> [-ValidateOnly]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory=$true)]
    [string]$Location,

    [switch]$ValidateOnly
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check if Azure CLI is installed
    try {
        $azVersion = az version --query '"azure-cli"' -o tsv
        Write-Info "Azure CLI version: $azVersion"
    }
    catch {
        Write-Error "Azure CLI is not installed. Please install it first."
        exit 1
    }

    # Check if logged in
    try {
        $account = az account show | ConvertFrom-Json
        Write-Info "Using subscription: $($account.name) ($($account.id))"
    }
    catch {
        Write-Error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    }

    # Check if Bicep is installed
    try {
        $bicepVersion = az bicep version
        Write-Info "Bicep version: $bicepVersion"
    }
    catch {
        Write-Warn "Bicep is not installed. Installing..."
        az bicep install
    }

    Write-Info "Prerequisites check passed!"
}

# Function to validate parameters
function Test-Parameters {
    param(
        [string]$Env,
        [string]$Loc
    )

    if ($Env -notin @('dev', 'staging', 'prod')) {
        Write-Error "Invalid environment. Must be: dev, staging, or prod"
        exit 1
    }

    if ([string]::IsNullOrEmpty($Loc)) {
        Write-Error "Location is required"
        exit 1
    }

    # Check if location is valid
    $locations = az account list-locations --query "[?name=='$Loc']" -o json | ConvertFrom-Json
    if ($locations.Count -eq 0) {
        Write-Error "Invalid Azure location: $Loc"
        Write-Info "Available locations:"
        az account list-locations --query "[].name" -o table
        exit 1
    }
}

# Function to build Bicep templates
function Build-Bicep {
    Write-Info "Building Bicep templates..."

    $bicepPath = Join-Path $PSScriptRoot "bicep"
    Push-Location $bicepPath

    try {
        # Build main template
        az bicep build --file main.bicep

        # Build all module templates
        Get-ChildItem -Path "modules\*.bicep" | ForEach-Object {
            Write-Info "Building $($_.Name)..."
            az bicep build --file $_.FullName
        }

        Write-Info "Bicep templates built successfully!"
    }
    finally {
        Pop-Location
    }
}

# Function to validate deployment
function Test-Deployment {
    param(
        [string]$Env,
        [string]$Loc,
        [string]$DeploymentName
    )

    Write-Info "Validating deployment..."

    $paramFile = Join-Path $PSScriptRoot "bicep\parameters\$Env.bicepparam"

    if (-not (Test-Path $paramFile)) {
        Write-Error "Parameter file not found: $paramFile"
        exit 1
    }

    $result = az deployment sub validate `
        --name $DeploymentName `
        --location $Loc `
        --template-file (Join-Path $PSScriptRoot "bicep\main.bicep") `
        --parameters $paramFile `
        --query "properties.provisioningState" -o tsv

    if ($LASTEXITCODE -eq 0) {
        Write-Info "Validation passed!"
        return $true
    }
    else {
        Write-Error "Validation failed!"
        return $false
    }
}

# Function to perform what-if analysis
function Show-WhatIf {
    param(
        [string]$Env,
        [string]$Loc,
        [string]$DeploymentName
    )

    Write-Info "Running what-if analysis..."

    $paramFile = Join-Path $PSScriptRoot "bicep\parameters\$Env.bicepparam"

    az deployment sub what-if `
        --name $DeploymentName `
        --location $Loc `
        --template-file (Join-Path $PSScriptRoot "bicep\main.bicep") `
        --parameters $paramFile
}

# Function to create backup before deployment
function New-Backup {
    param([string]$Env)

    Write-Info "Creating backup before deployment..."

    $rgName = "aibast-$Env-rg"

    # Check if resource group exists
    $rgExists = az group exists --name $rgName
    if ($rgExists -eq "true") {
        $backupName = "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        $backupPath = Join-Path $PSScriptRoot "backups\$Env"
        $backupFile = Join-Path $backupPath "$backupName.json"

        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

        # Export resource group template
        az group export --name $rgName --output json | Out-File -FilePath $backupFile -Encoding utf8

        Write-Info "Backup created: $backupFile"

        # Backup Function App settings
        $funcApps = az functionapp list -g $rgName --query "[].name" -o json | ConvertFrom-Json
        foreach ($funcApp in $funcApps) {
            Write-Info "Backing up settings for: $funcApp"
            $settingsFile = Join-Path $backupPath "$funcApp-settings.json"
            az functionapp config appsettings list `
                --name $funcApp `
                --resource-group $rgName `
                --output json | Out-File -FilePath $settingsFile -Encoding utf8
        }
    }
    else {
        Write-Info "Resource group does not exist. Skipping backup."
    }
}

# Function to deploy infrastructure
function Deploy-Infrastructure {
    param(
        [string]$Env,
        [string]$Loc,
        [string]$DeploymentName
    )

    Write-Info "Deploying infrastructure to $Env environment..."

    $paramFile = Join-Path $PSScriptRoot "bicep\parameters\$Env.bicepparam"
    $outputPath = Join-Path $PSScriptRoot "outputs"
    $outputFile = Join-Path $outputPath "$Env-deployment-output.json"

    New-Item -ItemType Directory -Path $outputPath -Force | Out-Null

    # Start deployment
    az deployment sub create `
        --name $DeploymentName `
        --location $Loc `
        --template-file (Join-Path $PSScriptRoot "bicep\main.bicep") `
        --parameters $paramFile `
        --output json | Out-File -FilePath $outputFile -Encoding utf8

    if ($LASTEXITCODE -eq 0) {
        Write-Info "Infrastructure deployment completed successfully!"
        return $true
    }
    else {
        Write-Error "Infrastructure deployment failed!"
        return $false
    }
}

# Function to configure resources post-deployment
function Set-ResourceConfiguration {
    param([string]$Env)

    Write-Info "Configuring resources..."

    $outputFile = Join-Path $PSScriptRoot "outputs\$Env-deployment-output.json"

    if (-not (Test-Path $outputFile)) {
        Write-Warn "Output file not found. Skipping post-deployment configuration."
        return
    }

    $output = Get-Content $outputFile | ConvertFrom-Json

    $rgName = $output.properties.outputs.resourceGroupName.value
    $funcAppName = $output.properties.outputs.functionAppName.value
    $storageName = $output.properties.outputs.storageAccountName.value

    Write-Info "Resource Group: $rgName"
    Write-Info "Function App: $funcAppName"
    Write-Info "Storage Account: $storageName"

    # Enable CORS for Function App
    Write-Info "Configuring CORS..."
    az functionapp cors add `
        --name $funcAppName `
        --resource-group $rgName `
        --allowed-origins "https://ai-ambassadors.app" "https://*.ai-ambassadors.app" 2>$null

    # Enable Application Insights Live Metrics
    Write-Info "Enabling Application Insights Live Metrics..."
    az monitor app-insights component update `
        --app $funcAppName `
        --resource-group $rgName `
        --query-access Enabled 2>$null

    Write-Info "Resource configuration completed!"
}

# Function to verify deployment
function Test-DeploymentHealth {
    param([string]$Env)

    Write-Info "Verifying deployment..."

    $outputFile = Join-Path $PSScriptRoot "outputs\$Env-deployment-output.json"

    if (-not (Test-Path $outputFile)) {
        Write-Error "Output file not found. Cannot verify deployment."
        return $false
    }

    $output = Get-Content $outputFile | ConvertFrom-Json
    $funcAppHostname = $output.properties.outputs.functionAppHostname.value

    # Test health endpoint
    Write-Info "Testing health endpoint..."
    $healthUrl = "https://$funcAppHostname/api/health"

    try {
        $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Info "Function App is responding!"
            return $true
        }
    }
    catch {
        Write-Warn "Function App health check failed: $($_.Exception.Message)"
        Write-Warn "The app may need time to fully start or may require code deployment."
    }

    return $false
}

# Function to display deployment summary
function Show-DeploymentSummary {
    param([string]$Env)

    $outputFile = Join-Path $PSScriptRoot "outputs\$Env-deployment-output.json"

    if (-not (Test-Path $outputFile)) {
        return
    }

    $output = Get-Content $outputFile | ConvertFrom-Json

    Write-Info "================================"
    Write-Info "Deployment Summary"
    Write-Info "================================"

    Write-Host ""
    Write-Host "Environment: $Env"
    Write-Host "Resource Group: $($output.properties.outputs.resourceGroupName.value)"
    Write-Host "Function App: $($output.properties.outputs.functionAppName.value)"
    Write-Host "Function App URL: https://$($output.properties.outputs.functionAppHostname.value)"
    Write-Host "Storage Account: $($output.properties.outputs.storageAccountName.value)"
    Write-Host "Key Vault: $($output.properties.outputs.keyVaultName.value)"
    Write-Host "Application Insights: $($output.properties.outputs.appInsightsName.value)"
    Write-Host "OpenAI Endpoint: $($output.properties.outputs.openAiEndpoint.value)"
    Write-Host ""

    Write-Info "Next steps:"
    Write-Host "1. Deploy Function App code: cd Copilot-Agent-365-main; func azure functionapp publish $($output.properties.outputs.functionAppName.value)"
    Write-Host "2. Upload agent files to Storage Account"
    Write-Host "3. Configure ambassador configurations"
    Write-Host "4. Test the deployment"
}

# Main script
Write-Info "================================"
Write-Info "AI Ambassador Platform Deployment"
Write-Info "================================"
Write-Host ""
Write-Host "Environment: $Environment"
Write-Host "Location: $Location"
Write-Host ""

$deploymentName = "aibast-$Environment-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Create output directories
New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot "outputs") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot "backups\$Environment") -Force | Out-Null

# Check prerequisites
Test-Prerequisites

# Validate parameters
Test-Parameters -Env $Environment -Loc $Location

# Build Bicep templates
Build-Bicep

# Validate deployment
if (-not (Test-Deployment -Env $Environment -Loc $Location -DeploymentName $deploymentName)) {
    Write-Error "Deployment validation failed. Aborting."
    exit 1
}

# Run what-if analysis
Show-WhatIf -Env $Environment -Loc $Location -DeploymentName $deploymentName

if ($ValidateOnly) {
    Write-Info "Validation complete. Exiting (ValidateOnly flag set)."
    exit 0
}

# Confirm deployment
$confirm = Read-Host "Do you want to proceed with the deployment? (yes/no)"
if ($confirm -ne "yes") {
    Write-Info "Deployment cancelled."
    exit 0
}

# Create backup
New-Backup -Env $Environment

# Deploy infrastructure
if (Deploy-Infrastructure -Env $Environment -Loc $Location -DeploymentName $deploymentName) {
    # Configure resources
    Set-ResourceConfiguration -Env $Environment

    # Verify deployment
    Test-DeploymentHealth -Env $Environment

    # Display summary
    Show-DeploymentSummary -Env $Environment

    Write-Info "Deployment completed successfully!"
}
else {
    Write-Error "Deployment failed. Check logs for details."
    exit 1
}
