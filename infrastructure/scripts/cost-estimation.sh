#!/bin/bash

# AI Ambassador Platform - Cost Estimation Script
# Usage: ./cost-estimation.sh <environment>

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_cost() {
    echo -e "${YELLOW}[COST]${NC} $1"
}

# Function to estimate Function App costs
estimate_function_app() {
    local env=$1
    local sku=$2

    case $sku in
        "Y1")
            local base_cost=0
            local execution_cost=0.20  # per million executions
            local memory_cost=0.000016  # per GB-second
            ;;
        "EP1")
            local base_cost=169  # per month
            local execution_cost=0
            local memory_cost=0
            ;;
        "EP2")
            local base_cost=338  # per month
            local execution_cost=0
            local memory_cost=0
            ;;
        "EP3")
            local base_cost=676  # per month
            local execution_cost=0
            local memory_cost=0
            ;;
    esac

    echo "$base_cost"
}

# Function to estimate storage costs
estimate_storage() {
    local env=$1
    local redundancy=$2

    case $redundancy in
        "LRS")
            local file_cost=0.0255  # per GB per month
            local blob_hot_cost=0.0184  # per GB per month
            local blob_cool_cost=0.0102  # per GB per month
            ;;
        "ZRS")
            local file_cost=0.0319  # per GB per month
            local blob_hot_cost=0.023  # per GB per month
            local blob_cool_cost=0.0128  # per GB per month
            ;;
    esac

    # Estimate data volumes based on environment
    case $env in
        "dev")
            local file_gb=10
            local blob_hot_gb=5
            local blob_cool_gb=5
            ;;
        "staging")
            local file_gb=100
            local blob_hot_gb=50
            local blob_cool_gb=50
            ;;
        "prod")
            local file_gb=500
            local blob_hot_gb=200
            local blob_cool_gb=300
            ;;
    esac

    local total=$(echo "$file_gb * $file_cost + $blob_hot_gb * $blob_hot_cost + $blob_cool_gb * $blob_cool_cost" | bc -l)
    echo "$total"
}

# Function to estimate OpenAI costs
estimate_openai() {
    local env=$1

    # Pricing per 1K tokens
    local gpt4_input=0.03
    local gpt4_output=0.06

    # Estimate token usage based on environment
    case $env in
        "dev")
            local monthly_input_tokens=1000000  # 1M tokens
            local monthly_output_tokens=500000  # 500K tokens
            ;;
        "staging")
            local monthly_input_tokens=10000000  # 10M tokens
            local monthly_output_tokens=5000000  # 5M tokens
            ;;
        "prod")
            local monthly_input_tokens=100000000  # 100M tokens
            local monthly_output_tokens=50000000  # 50M tokens
            ;;
    esac

    local input_cost=$(echo "$monthly_input_tokens / 1000 * $gpt4_input" | bc -l)
    local output_cost=$(echo "$monthly_output_tokens / 1000 * $gpt4_output" | bc -l)
    local total=$(echo "$input_cost + $output_cost" | bc -l)

    echo "$total"
}

# Function to estimate monitoring costs
estimate_monitoring() {
    local env=$1

    # Application Insights pricing
    local per_gb_cost=2.30
    local retention_cost=0.12  # per GB per month for retention

    case $env in
        "dev")
            local monthly_gb=5
            local retention_gb=10
            ;;
        "staging")
            local monthly_gb=50
            local retention_gb=100
            ;;
        "prod")
            local monthly_gb=200
            local retention_gb=500
            ;;
    esac

    local ingestion_cost=$(echo "$monthly_gb * $per_gb_cost" | bc -l)
    local retention_cost=$(echo "$retention_gb * $retention_cost" | bc -l)
    local total=$(echo "$ingestion_cost + $retention_cost" | bc -l)

    echo "$total"
}

# Function to estimate total costs
estimate_total() {
    local env=$1

    print_info "================================"
    print_info "Cost Estimation for $env"
    print_info "================================"
    echo ""

    # Get SKU based on environment
    case $env in
        "dev")
            sku="Y1"
            redundancy="LRS"
            ;;
        "staging")
            sku="EP1"
            redundancy="LRS"
            ;;
        "prod")
            sku="EP2"
            redundancy="ZRS"
            ;;
    esac

    # Calculate individual costs
    local function_cost=$(estimate_function_app "$env" "$sku")
    local storage_cost=$(estimate_storage "$env" "$redundancy")
    local openai_cost=$(estimate_openai "$env")
    local monitoring_cost=$(estimate_monitoring "$env")

    # Key Vault cost (flat rate)
    local keyvault_cost=0.03  # per 10K operations

    # Virtual Network cost (if enabled)
    local vnet_cost=0
    if [ "$env" = "prod" ]; then
        vnet_cost=7  # per month
    fi

    # Display breakdown
    print_cost "Function App ($sku): \$$function_cost/month"
    print_cost "Storage ($redundancy): \$$storage_cost/month"
    print_cost "Azure OpenAI: \$$openai_cost/month"
    print_cost "Monitoring (App Insights): \$$monitoring_cost/month"
    print_cost "Key Vault: \$$keyvault_cost/month"

    if [ "$vnet_cost" != "0" ]; then
        print_cost "Virtual Network: \$$vnet_cost/month"
    fi

    # Calculate total
    local total=$(echo "$function_cost + $storage_cost + $openai_cost + $monitoring_cost + $keyvault_cost + $vnet_cost" | bc -l)

    echo ""
    print_cost "================================"
    printf "${YELLOW}ESTIMATED TOTAL: \$%.2f/month${NC}\n" "$total"
    print_cost "================================"
    echo ""

    # Add notes
    echo "Notes:"
    echo "  - Costs are estimates based on typical usage patterns"
    echo "  - OpenAI costs can vary significantly based on traffic"
    echo "  - Storage costs depend on data volume and access patterns"
    echo "  - Actual costs may be higher during peak usage"
    echo "  - Does not include bandwidth/egress costs"
    echo ""

    # Cost optimization suggestions
    echo "Cost Optimization Tips:"
    case $env in
        "dev")
            echo "  - Using Consumption plan (Y1) for cost efficiency"
            echo "  - Consider sharing dev environment across team"
            echo "  - Use lifecycle policies to delete old data"
            ;;
        "staging")
            echo "  - Consider using Y1 (Consumption) instead of EP1 if traffic is low"
            echo "  - Enable auto-scaling to optimize costs"
            echo "  - Reduce data retention periods"
            ;;
        "prod")
            echo "  - Review auto-scaling settings regularly"
            echo "  - Implement caching to reduce OpenAI API calls"
            echo "  - Use reserved capacity for predictable workloads"
            echo "  - Monitor and optimize OpenAI token usage"
            echo "  - Consider cheaper storage tiers for infrequently accessed data"
            ;;
    esac
}

# Main script
main() {
    local ENVIRONMENT=$1

    if [ -z "$ENVIRONMENT" ]; then
        echo "Usage: $0 <environment>"
        echo ""
        echo "Arguments:"
        echo "  environment    Environment name (dev, staging, prod)"
        echo ""
        echo "Example:"
        echo "  $0 dev"
        exit 1
    fi

    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        echo "Invalid environment. Must be: dev, staging, or prod"
        exit 1
    fi

    estimate_total "$ENVIRONMENT"
}

main "$@"
