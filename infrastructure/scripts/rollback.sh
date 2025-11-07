#!/bin/bash

# AI Ambassador Platform - Rollback Script
# Usage: ./rollback.sh <environment> <backup-file>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to rollback Function App
rollback_function_app() {
    local env=$1
    local rg_name="aibast-${env}-rg"

    print_info "Rolling back Function App..."

    # Get Function App name
    local func_app_name=$(az functionapp list \
        --resource-group "$rg_name" \
        --query "[0].name" -o tsv)

    if [ -z "$func_app_name" ]; then
        print_error "Function App not found"
        return 1
    fi

    print_info "Function App: $func_app_name"

    # Check if staging slot exists
    local has_slot=$(az functionapp deployment slot list \
        --name "$func_app_name" \
        --resource-group "$rg_name" \
        --query "[?name=='staging']" -o tsv)

    if [ -n "$has_slot" ]; then
        print_info "Swapping staging slot back to production..."

        az functionapp deployment slot swap \
            --name "$func_app_name" \
            --resource-group "$rg_name" \
            --slot staging \
            --target-slot production

        print_info "Slot swap completed"
    else
        print_warn "No staging slot found. Cannot perform slot swap rollback."
        print_info "Attempting to restore from previous deployment..."

        # Get previous deployment
        local deployments=$(az functionapp deployment list \
            --name "$func_app_name" \
            --resource-group "$rg_name" \
            --query "[?status=='Success']|[0:2].[id]" -o tsv)

        if [ -n "$deployments" ]; then
            local previous_deployment=$(echo "$deployments" | sed -n '2p')

            if [ -n "$previous_deployment" ]; then
                print_info "Rolling back to previous deployment: $previous_deployment"

                az functionapp deployment source config-zip \
                    --name "$func_app_name" \
                    --resource-group "$rg_name" \
                    --src "$previous_deployment"
            fi
        fi
    fi
}

# Function to rollback configuration
rollback_configuration() {
    local env=$1
    local backup_file=$2
    local rg_name="aibast-${env}-rg"

    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        return 1
    fi

    print_info "Rolling back configuration from: $backup_file"

    # Get Function App name
    local func_app_name=$(az functionapp list \
        --resource-group "$rg_name" \
        --query "[0].name" -o tsv)

    # Restore app settings
    print_info "Restoring application settings..."

    local settings=$(jq -r '.[] | "\(.name)=\(.value)"' "$backup_file")

    while IFS= read -r setting; do
        local name=$(echo "$setting" | cut -d'=' -f1)
        local value=$(echo "$setting" | cut -d'=' -f2-)

        az functionapp config appsettings set \
            --name "$func_app_name" \
            --resource-group "$rg_name" \
            --settings "$name=$value" > /dev/null
    done <<< "$settings"

    print_info "Configuration rollback completed"
}

# Function to rollback database/storage
rollback_storage() {
    local env=$1
    local backup_path=$2
    local rg_name="aibast-${env}-rg"

    print_info "Rolling back storage data..."

    # Get storage account
    local storage_account=$(az storage account list \
        --resource-group "$rg_name" \
        --query "[0].name" -o tsv)

    if [ -z "$storage_account" ]; then
        print_error "Storage account not found"
        return 1
    fi

    print_info "Storage account: $storage_account"

    # Get connection string
    local conn_string=$(az storage account show-connection-string \
        --name "$storage_account" \
        --resource-group "$rg_name" \
        --query connectionString -o tsv)

    # List all file shares
    local shares=$(az storage share list \
        --connection-string "$conn_string" \
        --query "[].name" -o tsv)

    # Restore each share from backup
    for share in $shares; do
        print_info "Restoring share: $share"

        local backup_share_path="$backup_path/$share"

        if [ -d "$backup_share_path" ]; then
            # Upload files from backup
            find "$backup_share_path" -type f | while read file; do
                local relative_path="${file#$backup_share_path/}"

                az storage file upload \
                    --share-name "$share" \
                    --source "$file" \
                    --path "$relative_path" \
                    --connection-string "$conn_string" || true
            done
        else
            print_warn "No backup found for share: $share"
        fi
    done

    print_info "Storage rollback completed"
}

# Function to verify rollback
verify_rollback() {
    local env=$1
    local rg_name="aibast-${env}-rg"

    print_info "Verifying rollback..."

    # Get Function App hostname
    local func_app_hostname=$(az functionapp show \
        --name "$(az functionapp list --resource-group "$rg_name" --query "[0].name" -o tsv)" \
        --resource-group "$rg_name" \
        --query "defaultHostName" -o tsv)

    # Test health endpoint
    local health_url="https://${func_app_hostname}/api/health"
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" || echo "000")

    if [ "$response" = "200" ]; then
        print_info "Function App is responding correctly"
    else
        print_warn "Function App health check returned: $response"
    fi

    # Test main function
    print_info "Testing main function..."
    curl -X POST "https://${func_app_hostname}/api/businessinsightbot_function" \
        -H "Content-Type: application/json" \
        -d '{"user_input": "Rollback test", "conversation_history": []}' \
        -o /dev/null -s -w "HTTP Status: %{http_code}\n"
}

# Main script
main() {
    local ENVIRONMENT=$1
    local BACKUP_FILE=$2
    local BACKUP_PATH=$3

    if [ -z "$ENVIRONMENT" ]; then
        echo "Usage: $0 <environment> [backup-settings-file] [backup-storage-path]"
        echo ""
        echo "Arguments:"
        echo "  environment              Environment name (dev, staging, prod)"
        echo "  backup-settings-file     Path to backup settings JSON file (optional)"
        echo "  backup-storage-path      Path to storage backup directory (optional)"
        echo ""
        echo "Example:"
        echo "  $0 staging settings-backup.json storage-backup/"
        exit 1
    fi

    print_info "================================"
    print_info "AI Ambassador Platform Rollback"
    print_info "================================"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo ""

    # Confirm rollback
    read -p "Are you sure you want to rollback the $ENVIRONMENT environment? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "Rollback cancelled."
        exit 0
    fi

    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi

    # Perform rollback
    rollback_function_app "$ENVIRONMENT"

    if [ -n "$BACKUP_FILE" ]; then
        rollback_configuration "$ENVIRONMENT" "$BACKUP_FILE"
    fi

    if [ -n "$BACKUP_PATH" ]; then
        rollback_storage "$ENVIRONMENT" "$BACKUP_PATH"
    fi

    # Verify rollback
    verify_rollback "$ENVIRONMENT"

    print_info "Rollback completed successfully!"
}

main "$@"
