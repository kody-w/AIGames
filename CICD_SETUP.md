# CI/CD Setup Guide

## GitHub Actions Workflows

### Continuous Integration (ci.yml)
Runs on every push and PR

**Jobs:**
- Test (unit, integration, e2e)
- Lint (flake8, black, isort, pylint)
- Security (safety, bandit)
- Coverage (80% minimum)
- Bicep validation

### Development Deployment (cd-dev.yml)
Triggers: Push to `develop` branch

**Steps:**
1. Deploy infrastructure (Bicep)
2. Configure managed identity
3. Store secrets in Key Vault
4. Deploy Function App code
5. Run smoke tests
6. Send notifications

**Environment:** dev (no approval)

### Staging Deployment (cd-staging.yml)
Triggers: Push to `main` branch

**Steps:**
1. Deploy infrastructure
2. Configure permissions
3. Deploy code
4. Run smoke tests
5. Run integration tests
6. Run performance tests
7. Send notifications

**Environment:** staging (manual approval required)

### Production Deployment (cd-prod.yml)
Triggers: Release created

**Steps:**
1. Pre-deployment validation
2. Deploy to staging slot (blue)
3. Run comprehensive tests
4. Monitor error rate (5 min)
5. Manual approval to swap
6. Swap slots (blue-green)
7. Monitor production (10 min)
8. Auto-rollback on failure

**Environment:** production (2 approvals required)

### Destroy Environment (destroy.yml)
Manual workflow to destroy dev/staging

**Requirements:**
- Type "DESTROY" to confirm
- Cannot destroy production
- Creates final backup
- Manual approval required

## GitHub Secrets Setup

### Required Secrets

**AZURE_CREDENTIALS**
```json
{
  "clientId": "<service-principal-id>",
  "clientSecret": "<service-principal-secret>",
  "subscriptionId": "<subscription-id>",
  "tenantId": "<tenant-id>"
}
```

Create service principal:
```bash
az ad sp create-for-rbac \
  --name "ai-ambassador-cicd" \
  --role Contributor \
  --scopes /subscriptions/<subscription-id> \
  --sdk-auth
```

**AZURE_OPENAI_API_KEY**
Your Azure OpenAI API key

### Optional Secrets

- `SLACK_WEBHOOK` - Slack notifications
- `BACKUP_ENCRYPTION_KEY` - Backup encryption
- `JWT_SECRET` - JWT signing

## Environment Setup

### 1. Enable GitHub Actions
Settings → Actions → General → Allow all actions

### 2. Create Environments

**dev:**
- No protection rules
- Secrets: None required

**staging:**
- Required reviewers: 1
- Secrets: None required

**prod:**
- Required reviewers: 2
- Deployment branches: main only
- Wait timer: 5 minutes

**production-swap:**
- Required reviewers: 1
- For slot swap approval

**dev-destroy, staging-destroy:**
- Required reviewers: 1
- For environment destruction

### 3. Branch Protection Rules

**develop:**
- Require PR before merging
- Require status checks:
  - test
  - lint
  - security
  - coverage

**main:**
- Require PR before merging
- Require 1 approval
- Require status checks:
  - All CI checks
- Require signed commits (optional)

## Workflow Triggers

```
Push → develop → CI + Deploy Dev
Push → main → CI + Deploy Staging
Release → Create → CI + Deploy Prod
Manual → Destroy → Destroy Environment
```

## Monitoring CI/CD

### View Workflow Runs
https://github.com/<org>/<repo>/actions

### View Deployments
https://github.com/<org>/<repo>/deployments

### View Logs
```bash
gh run list
gh run view <run-id>
gh run view <run-id> --log
```

## Troubleshooting

### Failed Deployment

1. Check workflow logs
2. Verify secrets are set
3. Check Azure resource limits
4. Verify service principal permissions

### Failed Tests

1. Run tests locally
2. Check test reports (artifacts)
3. Fix issues and push

### Rollback

Automatic on production failure, or manual:
```bash
./scripts/rollback.sh <environment>
```

## Best Practices

1. Always run CI on feature branches
2. Merge to develop first, then main
3. Create releases for production
4. Use semantic versioning
5. Tag releases properly
6. Monitor deployments
7. Keep secrets updated
8. Review and merge PRs promptly

## Cost Optimization

### GitHub Actions Minutes
- Free tier: 2,000 min/month
- Paid tier: $0.008/min

### Tips
- Cache dependencies
- Run tests in parallel
- Skip redundant jobs
- Use self-hosted runners (optional)

See DEPLOYMENT_GUIDE.md for complete deployment process.
