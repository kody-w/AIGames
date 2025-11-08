#!/bin/bash

###############################################################################
# AI Ambassador Platform - Local Settings Generator
#
# Generates local.settings.json from Azure deployment outputs
#
# Usage:
#   ./create-local-settings.sh <resource-group-name> [deployment-name] [output-path]
#
# Example:
#   ./create-local-settings.sh aiambassador-dev-rg
#   ./create-local-settings.sh aiambassador-dev-rg ai-ambassador-deployment ../Copilot-Agent-365-main
#
# Author: AI Ambassador Platform Team
# Version: 1.0.0
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Parameters
RESOURCE_GROUP_NAME=${1:-}
DEPLOYMENT_NAME=${2:-"ai-ambassador-deployment"}
OUTPUT_PATH=${3:-"."}

# Functions
print_header() {
    echo -e "${CYAN}🚀 AI Ambassador Platform - Local Settings Generator${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}🔍 $1${NC}"
}

# Check parameters
if [ -z "$RESOURCE_GROUP_NAME" ]; then
    print_header
    print_error "Resource Group name is required"
    echo ""
    echo "Usage:"
    echo "  $0 <resource-group-name> [deployment-name] [output-path]"
    echo ""
    echo "Example:"
    echo "  $0 aiambassador-dev-rg"
    echo "  $0 aiambassador-dev-rg ai-ambassador-deployment ../Copilot-Agent-365-main"
    echo ""
    exit 1
fi

print_header

# Check if Azure CLI is installed
print_info "Checking Azure CLI installation..."
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed or not in PATH"
    echo -e "${YELLOW}   Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli${NC}"
    exit 1
fi
print_success "Azure CLI found"

# Check if logged in to Azure
print_info "Checking Azure login status..."
ACCOUNT_INFO=$(az account show 2>/dev/null || echo "")
if [ -z "$ACCOUNT_INFO" ]; then
    print_error "Not logged in to Azure"
    echo -e "${YELLOW}   Run: az login${NC}"
    exit 1
fi

ACCOUNT_NAME=$(echo "$ACCOUNT_INFO" | jq -r '.user.name')
SUBSCRIPTION_NAME=$(echo "$ACCOUNT_INFO" | jq -r '.name')
print_success "Logged in as: $ACCOUNT_NAME"
print_success "Subscription: $SUBSCRIPTION_NAME"
echo ""

# Get deployment outputs
print_info "Retrieving deployment outputs from Azure..."
OUTPUTS=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs \
    2>/dev/null || echo "")

if [ -z "$OUTPUTS" ] || [ "$OUTPUTS" == "null" ]; then
    print_error "Failed to retrieve deployment outputs"
    echo -e "${YELLOW}   Resource Group: $RESOURCE_GROUP_NAME${NC}"
    echo -e "${YELLOW}   Deployment Name: $DEPLOYMENT_NAME${NC}"
    echo ""
    echo -e "${YELLOW}   Available deployments:${NC}"
    az deployment group list --resource-group "$RESOURCE_GROUP_NAME" --query "[].name" -o table
    exit 1
fi

print_success "Deployment outputs retrieved successfully"
echo ""

# Extract values from outputs
print_info "Extracting configuration values..."

STORAGE_CONNECTION_STRING=$(echo "$OUTPUTS" | jq -r '.storageConnectionString.value')
OPENAI_API_KEY=$(echo "$OUTPUTS" | jq -r '.openAiApiKey.value')
OPENAI_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.openAiEndpoint.value')
OPENAI_DEPLOYMENT_NAME=$(echo "$OUTPUTS" | jq -r '.openAiDeploymentName.value')
OPENAI_API_VERSION=$(echo "$OUTPUTS" | jq -r '.openAiApiVersion.value')
FILE_SHARE_NAME=$(echo "$OUTPUTS" | jq -r '.fileShareName.value')
APPINSIGHTS_KEY=$(echo "$OUTPUTS" | jq -r '.appInsightsInstrumentationKey.value')
APPINSIGHTS_CONNECTION_STRING=$(echo "$OUTPUTS" | jq -r '.appInsightsConnectionString.value')

# Validate required values
MISSING_VALUES=()
[ -z "$STORAGE_CONNECTION_STRING" ] && MISSING_VALUES+=("Storage Connection String")
[ -z "$OPENAI_API_KEY" ] && MISSING_VALUES+=("OpenAI API Key")
[ -z "$OPENAI_ENDPOINT" ] && MISSING_VALUES+=("OpenAI Endpoint")
[ -z "$OPENAI_DEPLOYMENT_NAME" ] && MISSING_VALUES+=("OpenAI Deployment Name")

if [ ${#MISSING_VALUES[@]} -gt 0 ]; then
    print_error "Missing required values:"
    for value in "${MISSING_VALUES[@]}"; do
        echo -e "${YELLOW}   - $value${NC}"
    done
    exit 1
fi

print_success "All required values extracted"
echo ""

# Ensure output directory exists
mkdir -p "$OUTPUT_PATH"
OUTPUT_FILE="$OUTPUT_PATH/local.settings.json"

# Check if file already exists
if [ -f "$OUTPUT_FILE" ]; then
    print_warning "local.settings.json already exists at: $OUTPUT_FILE"
    read -p "   Overwrite? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Operation cancelled"
        exit 0
    fi
fi

# Create local.settings.json content
print_info "Creating local.settings.json..."

cat > "$OUTPUT_FILE" << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "$STORAGE_CONNECTION_STRING",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_API_KEY": "$OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT": "$OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "$OPENAI_DEPLOYMENT_NAME",
    "AZURE_OPENAI_API_VERSION": "$OPENAI_API_VERSION",
    "AZURE_FILES_SHARE_NAME": "$FILE_SHARE_NAME",
    "ASSISTANT_NAME": "AI Ambassador",
    "CHARACTERISTIC_DESCRIPTION": "Your intelligent, emotionally aware AI companion with episodic memory and multi-agent collaboration capabilities",
    "USE_LOCAL_STORAGE": "false",
    "USE_LOCAL_LLM": "false",
    "APPINSIGHTS_INSTRUMENTATIONKEY": "$APPINSIGHTS_KEY",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "$APPINSIGHTS_CONNECTION_STRING"
  }
}
EOF

print_success "local.settings.json created successfully!"
echo ""
echo -e "${CYAN}📁 File location: $OUTPUT_FILE${NC}"
echo ""

# Display configuration summary
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}📊 Configuration Summary${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "${NC}Azure OpenAI:${NC}"
echo -e "${GRAY}  Endpoint:       $OPENAI_ENDPOINT${NC}"
echo -e "${GRAY}  Deployment:     $OPENAI_DEPLOYMENT_NAME${NC}"
echo -e "${GRAY}  API Version:    $OPENAI_API_VERSION${NC}"
echo ""
echo -e "${NC}Storage:${NC}"
echo -e "${GRAY}  File Share:     $FILE_SHARE_NAME${NC}"
echo ""
echo -e "${NC}Monitoring:${NC}"
echo -e "${GRAY}  App Insights:   Configured${NC}"
echo ""
echo -e "${CYAN}============================================================${NC}"
echo ""

# Next steps
echo -e "${GREEN}🎉 Next Steps:${NC}"
echo ""
echo -e "${NC}1. Navigate to your function app directory:${NC}"
echo -e "${GRAY}   cd Copilot-Agent-365-main${NC}"
echo ""
echo -e "${NC}2. Start the local function app:${NC}"
echo -e "${GRAY}   ./run.sh${NC}"
echo ""
echo -e "${NC}3. Test the API:${NC}"
echo -e "${GRAY}   curl -X POST http://localhost:7071/api/businessinsightbot_function \\${NC}"
echo -e "${GRAY}     -H \"Content-Type: application/json\" \\${NC}"
echo -e "${GRAY}     -d '{\"user_input\": \"Hello!\", \"conversation_history\": []}'${NC}"
echo ""
echo -e "${GREEN}✨ Your AI Ambassador Platform is ready to run locally!${NC}"
echo ""
