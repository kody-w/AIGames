# Troubleshooting Deployment Issues

## Common Issues and Solutions

### 1. Deployment Failed - Resource Quota Exceeded

**Error:**
```
Resource quota exceeded for resource type 'cores'
```

**Solution:**
```bash
# Check current quota
az vm list-usage --location eastus --output table

# Request quota increase
az support tickets create \
  --ticket-name "CoreQuotaIncrease" \
  --severity minimal \
  --problem-classification "/providers/Microsoft.Support/services/<service-id>/problemClassifications/<classification-id>"
```

### 2. Function App Deployment Failed

**Error:**
```
Deployment failed with status code 409
```

**Solutions:**

a. Check if app is running:
```bash
az functionapp show \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --query "state"
```

b. Restart the app:
```bash
az functionapp restart \
  --name <function-app-name> \
  --resource-group <resource-group>
```

c. Check deployment logs:
```bash
az functionapp log deployment show \
  --name <function-app-name> \
  --resource-group <resource-group>
```

### 3. Bicep Validation Failed

**Error:**
```
The template is not valid
```

**Solutions:**

```bash
# Validate template
az bicep build --file infrastructure/bicep/main.bicep

# Check for syntax errors
az deployment sub validate \
  --location eastus \
  --template-file infrastructure/bicep/main.bicep \
  --parameters infrastructure/parameters/dev.bicepparam
```

### 4. Python Dependency Issues

**Error:**
```
Module not found or import error
```

**Solutions:**

```bash
# Reinstall dependencies
cd Copilot-Agent-365-main
pip install -r requirements.txt --target .python_packages/lib/site-packages --upgrade

# Check Python version
python --version  # Must be 3.11

# Use virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Azure OpenAI Access Denied

**Error:**
```
Access denied or quota exceeded
```

**Solutions:**

a. Check OpenAI access:
```bash
az cognitiveservices account list --query "[?kind=='OpenAI']"
```

b. Verify API key:
```bash
az cognitiveservices account keys list \
  --name <openai-account> \
  --resource-group <resource-group>
```

c. Check deployment quotas:
```bash
az cognitiveservices account deployment list \
  --name <openai-account> \
  --resource-group <resource-group>
```

### 6. Key Vault Access Denied

**Error:**
```
Forbidden: User or application does not have access
```

**Solutions:**

```bash
# Grant access to managed identity
az keyvault set-policy \
  --name <key-vault-name> \
  --object-id <principal-id> \
  --secret-permissions get list

# Or use RBAC
az role assignment create \
  --assignee <principal-id> \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<kv-name>"
```

### 7. Storage Account Connection Failed

**Error:**
```
Unable to connect to storage account
```

**Solutions:**

```bash
# Check storage account status
az storage account show \
  --name <storage-account> \
  --resource-group <resource-group> \
  --query "statusOfPrimary"

# Test connection
az storage share list \
  --account-name <storage-account>

# Check firewall rules
az storage account show \
  --name <storage-account> \
  --query "networkRuleSet"
```

### 8. GitHub Actions Workflow Failed

**Error:**
```
Azure login failed or resource not found
```

**Solutions:**

a. Verify AZURE_CREDENTIALS secret:
- Check JSON format
- Verify service principal has Contributor role
- Ensure subscription ID is correct

b. Test service principal locally:
```bash
az login --service-principal \
  --username <client-id> \
  --password <client-secret> \
  --tenant <tenant-id>
```

c. Check workflow logs:
```bash
gh run list
gh run view <run-id> --log
```

### 9. Deployment Timeout

**Error:**
```
Deployment exceeded timeout limit
```

**Solutions:**

a. Increase timeout in workflow:
```yaml
timeout-minutes: 30  # Default is 15
```

b. Deploy in stages:
```bash
# Deploy infrastructure first
az deployment sub create ...

# Then deploy code
func azure functionapp publish ...
```

### 10. Managed Identity Not Working

**Error:**
```
ManagedIdentityCredential authentication failed
```

**Solutions:**

```bash
# Enable system-assigned identity
az functionapp identity assign \
  --name <function-app-name> \
  --resource-group <resource-group>

# Get principal ID
PRINCIPAL_ID=$(az functionapp identity show \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --query principalId -o tsv)

# Assign roles
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage>"
```

## Diagnostic Commands

### Check All Resources

```bash
# List all resources in resource group
az resource list \
  --resource-group <resource-group> \
  --output table

# Check resource group deployment history
az deployment group list \
  --resource-group <resource-group> \
  --output table
```

### View Function App Configuration

```bash
# List all app settings
az functionapp config appsettings list \
  --name <function-app-name> \
  --resource-group <resource-group>

# Get specific setting
az functionapp config appsettings list \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --query "[?name=='AZURE_OPENAI_ENDPOINT'].value" -o tsv
```

### View Logs

```bash
# Function App logs
az functionapp log tail \
  --name <function-app-name> \
  --resource-group <resource-group>

# Application Insights logs
az monitor app-insights query \
  --app <app-insights-name> \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc | take 100"

# Deployment logs
az functionapp log deployment show \
  --name <function-app-name> \
  --resource-group <resource-group>
```

### Test Endpoints

```bash
# Health check
curl -v https://<function-app>.azurewebsites.net/api/health

# Full API test
curl -v -X POST https://<function-app>.azurewebsites.net/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'

# Check CORS
curl -v -H "Origin: https://ai-ambassadors.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS https://<function-app>.azurewebsites.net/api/businessinsightbot_function
```

## Emergency Procedures

### Complete Rollback

```bash
cd scripts
./rollback.sh <environment>
```

### Stop All Traffic

```bash
# Disable function app
az functionapp stop \
  --name <function-app-name> \
  --resource-group <resource-group>
```

### Emergency Resource Deletion

```bash
# Delete entire resource group (CAUTION!)
az group delete \
  --name <resource-group> \
  --yes \
  --no-wait
```

## Getting Help

1. Check Azure Portal for detailed error messages
2. View Application Insights for runtime errors
3. Check GitHub Actions logs for deployment errors
4. Review Azure Service Health for outages
5. Contact Azure Support for quota/access issues

## Preventive Measures

1. Always test in dev environment first
2. Use feature flags for risky changes
3. Monitor deployments closely
4. Keep backups up to date
5. Document all manual changes
6. Review logs regularly
7. Set up proper alerts
8. Test rollback procedures

For additional help, see:
- DEPLOYMENT_GUIDE.md
- INFRASTRUCTURE.md
- CICD_SETUP.md
