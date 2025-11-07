#!/bin/bash

# AI Ambassador Platform - Deployment Script (Bash)
# Usage: ./deploy.sh <environment> <location> [--validate-only]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi

    # Check Azure CLI version
    AZ_VERSION=$(az version --query '"azure-cli"' -o tsv)
    print_info "Azure CLI version: $AZ_VERSION"

    # Check if logged in
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi

    # Display current subscription
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    print_info "Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

    # Check if Bicep is installed
    if ! az bicep version &> /dev/null; then
        print_warn "Bicep is not installed. Installing..."
        az bicep install
    fi

    BICEP_VERSION=$(az bicep version)
    print_info "Bicep version: $BICEP_VERSION"

    print_info "Prerequisites check passed!"
}

# Function to validate parameters
validate_parameters() {
    local env=$1
    local location=$2

    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        print_error "Invalid environment. Must be: dev, staging, or prod"
        exit 1
    fi

    if [ -z "$location" ]; then
        print_error "Location is required"
        exit 1
    fi

    # Check if location is valid
    if ! az account list-locations --query "[?name=='$location']" -o tsv | grep -q .; then
        print_error "Invalid Azure location: $location"
        print_info "Available locations:"
        az account list-locations --query "[].name" -o table
        exit 1
    fi
}

# Function to build Bicep templates
build_bicep() {
    print_info "Building Bicep templates..."

    cd "$(dirname "$0")/bicep"

    # Build main template
    az bicep build --file main.bicep

    # Build all module templates
    for module in modules/*.bicep; do
        print_info "Building $module..."
        az bicep build --file "$module"
    done

    cd - > /dev/null
    print_info "Bicep templates built successfully!"
}

# Function to validate deployment
validate_deployment() {
    local env=$1
    local location=$2
    local deployment_name=$3

    print_info "Validating deployment..."

    local param_file="$(dirname "$0")/bicep/parameters/${env}.bicepparam"

    if [ ! -f "$param_file" ]; then
        print_error "Parameter file not found: $param_file"
        exit 1
    fi

    az deployment sub validate \
        --name "$deployment_name" \
        --location "$location" \
        --template-file "$(dirname "$0")/bicep/main.bicep" \
        --parameters "$param_file" \
        --query "properties.provisioningState" -o tsv

    if [ $? -eq 0 ]; then
        print_info "Validation passed!"
        return 0
    else
        print_error "Validation failed!"
        return 1
    fi
}

# Function to perform what-if analysis
whatif_deployment() {
    local env=$1
    local location=$2
    local deployment_name=$3

    print_info "Running what-if analysis..."

    local param_file="$(dirname "$0")/bicep/parameters/${env}.bicepparam"

    az deployment sub what-if \
        --name "$deployment_name" \
        --location "$location" \
        --template-file "$(dirname "$0")/bicep/main.bicep" \
        --parameters "$param_file"
}

# Function to create backup before deployment
create_backup() {
    local env=$1
    local rg_name="aibast-${env}-rg"

    print_info "Creating backup before deployment..."

    # Check if resource group exists
    if az group exists --name "$rg_name" | grep -q "true"; then
        local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
        local backup_file="$(dirname "$0")/backups/${env}/${backup_name}.json"

        mkdir -p "$(dirname "$backup_file")"

        # Export resource group template
        az group export \
            --name "$rg_name" \
            --output json > "$backup_file"

        print_info "Backup created: $backup_file"

        # Backup Function App settings
        local func_apps=$(az functionapp list -g "$rg_name" --query "[].name" -o tsv)
        for func_app in $func_apps; do
            print_info "Backing up settings for: $func_app"
            az functionapp config appsettings list \
                --name "$func_app" \
                --resource-group "$rg_name" \
                --output json > "$(dirname "$backup_file")/${func_app}-settings.json"
        done
    else
        print_info "Resource group does not exist. Skipping backup."
    fi
}

# Function to deploy infrastructure
deploy_infrastructure() {
    local env=$1
    local location=$2
    local deployment_name=$3

    print_info "Deploying infrastructure to $env environment..."

    local param_file="$(dirname "$0")/bicep/parameters/${env}.bicepparam"

    # Start deployment
    az deployment sub create \
        --name "$deployment_name" \
        --location "$location" \
        --template-file "$(dirname "$0")/bicep/main.bicep" \
        --parameters "$param_file" \
        --output json > "$(dirname "$0")/outputs/${env}-deployment-output.json"

    if [ $? -eq 0 ]; then
        print_info "Infrastructure deployment completed successfully!"
        return 0
    else
        print_error "Infrastructure deployment failed!"
        return 1
    fi
}

# Function to configure resources post-deployment
configure_resources() {
    local env=$1
    local output_file="$(dirname "$0")/outputs/${env}-deployment-output.json"

    print_info "Configuring resources..."

    if [ ! -f "$output_file" ]; then
        print_warn "Output file not found. Skipping post-deployment configuration."
        return
    fi

    # Extract outputs
    local rg_name=$(jq -r '.properties.outputs.resourceGroupName.value' "$output_file")
    local func_app_name=$(jq -r '.properties.outputs.functionAppName.value' "$output_file")
    local storage_name=$(jq -r '.properties.outputs.storageAccountName.value' "$output_file")

    print_info "Resource Group: $rg_name"
    print_info "Function App: $func_app_name"
    print_info "Storage Account: $storage_name"

    # Enable CORS for Function App
    print_info "Configuring CORS..."
    az functionapp cors add \
        --name "$func_app_name" \
        --resource-group "$rg_name" \
        --allowed-origins "https://ai-ambassadors.app" "https://*.ai-ambassadors.app" || true

    # Enable Application Insights Live Metrics
    print_info "Enabling Application Insights Live Metrics..."
    az monitor app-insights component update \
        --app "$func_app_name" \
        --resource-group "$rg_name" \
        --query-access Enabled || true

    print_info "Resource configuration completed!"
}

# Function to verify deployment
verify_deployment() {
    local env=$1
    local output_file="$(dirname "$0")/outputs/${env}-deployment-output.json"

    print_info "Verifying deployment..."

    if [ ! -f "$output_file" ]; then
        print_error "Output file not found. Cannot verify deployment."
        return 1
    fi

    local func_app_hostname=$(jq -r '.properties.outputs.functionAppHostname.value' "$output_file")

    # Test health endpoint
    print_info "Testing health endpoint..."
    local health_url="https://${func_app_hostname}/api/health"

    local response=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" || echo "000")

    if [ "$response" = "200" ] || [ "$response" = "404" ]; then
        print_info "Function App is responding!"
    else
        print_warn "Function App health check returned: $response"
        print_warn "The app may need time to fully start or may require code deployment."
    fi
}

# Function to display deployment summary
display_summary() {
    local env=$1
    local output_file="$(dirname "$0")/outputs/${env}-deployment-output.json"

    if [ ! -f "$output_file" ]; then
        return
    fi

    print_info "================================"
    print_info "Deployment Summary"
    print_info "================================"

    echo ""
    echo "Environment: $env"
    echo "Resource Group: $(jq -r '.properties.outputs.resourceGroupName.value' "$output_file")"
    echo "Function App: $(jq -r '.properties.outputs.functionAppName.value' "$output_file")"
    echo "Function App URL: https://$(jq -r '.properties.outputs.functionAppHostname.value' "$output_file")"
    echo "Storage Account: $(jq -r '.properties.outputs.storageAccountName.value' "$output_file")"
    echo "Key Vault: $(jq -r '.properties.outputs.keyVaultName.value' "$output_file")"
    echo "Application Insights: $(jq -r '.properties.outputs.appInsightsName.value' "$output_file")"
    echo "OpenAI Endpoint: $(jq -r '.properties.outputs.openAiEndpoint.value' "$output_file")"
    echo ""

    print_info "Next steps:"
    echo "1. Deploy Function App code: cd Copilot-Agent-365-main && func azure functionapp publish $(jq -r '.properties.outputs.functionAppName.value' "$output_file")"
    echo "2. Upload agent files to Storage Account"
    echo "3. Configure ambassador configurations"
    echo "4. Test the deployment"
}

# Main script
main() {
    local ENVIRONMENT=$1
    local LOCATION=$2
    local VALIDATE_ONLY=false

    # Parse optional flags
    shift 2 || true
    while [[ $# -gt 0 ]]; do
        case $1 in
            --validate-only)
                VALIDATE_ONLY=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Show usage if parameters missing
    if [ -z "$ENVIRONMENT" ] || [ -z "$LOCATION" ]; then
        echo "Usage: $0 <environment> <location> [--validate-only]"
        echo ""
        echo "Arguments:"
        echo "  environment    Environment name (dev, staging, prod)"
        echo "  location       Azure region (e.g., eastus, westus2)"
        echo ""
        echo "Options:"
        echo "  --validate-only    Only validate the deployment without deploying"
        echo ""
        echo "Example:"
        echo "  $0 dev eastus"
        echo "  $0 prod eastus --validate-only"
        exit 1
    fi

    # Create outputs directory
    mkdir -p "$(dirname "$0")/outputs"
    mkdir -p "$(dirname "$0")/backups/${ENVIRONMENT}"

    local DEPLOYMENT_NAME="aibast-${ENVIRONMENT}-deployment-$(date +%Y%m%d-%H%M%S)"

    print_info "================================"
    print_info "AI Ambassador Platform Deployment"
    print_info "================================"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Location: $LOCATION"
    echo "Deployment Name: $DEPLOYMENT_NAME"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Validate parameters
    validate_parameters "$ENVIRONMENT" "$LOCATION"

    # Build Bicep templates
    build_bicep

    # Validate deployment
    if ! validate_deployment "$ENVIRONMENT" "$LOCATION" "$DEPLOYMENT_NAME"; then
        print_error "Deployment validation failed. Aborting."
        exit 1
    fi

    # Run what-if analysis
    whatif_deployment "$ENVIRONMENT" "$LOCATION" "$DEPLOYMENT_NAME"

    if [ "$VALIDATE_ONLY" = true ]; then
        print_info "Validation complete. Exiting (--validate-only flag set)."
        exit 0
    fi

    # Confirm deployment
    read -p "Do you want to proceed with the deployment? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "Deployment cancelled."
        exit 0
    fi

    # Create backup
    create_backup "$ENVIRONMENT"

    # Deploy infrastructure
    if deploy_infrastructure "$ENVIRONMENT" "$LOCATION" "$DEPLOYMENT_NAME"; then
        # Configure resources
        configure_resources "$ENVIRONMENT"

        # Verify deployment
        verify_deployment "$ENVIRONMENT"

        # Display summary
        display_summary "$ENVIRONMENT"

        print_info "Deployment completed successfully!"
    else
        print_error "Deployment failed. Check logs for details."
        exit 1
    fi
}

# Run main function
main "$@"
