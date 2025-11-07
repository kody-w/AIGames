# Backup & Recovery Guide
## AI Ambassador Platform

**Version:** 1.0
**Last Updated:** November 2025
**Document Owner:** Platform Operations Team

---

## Table of Contents

1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [Disaster Recovery Procedures](#disaster-recovery-procedures)
4. [Restore Instructions](#restore-instructions)
5. [Migration Guide](#migration-guide)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance & Testing](#maintenance--testing)

---

## Overview

The AI Ambassador Platform implements a comprehensive backup and disaster recovery system to protect critical data and ensure business continuity. This guide provides detailed procedures for backup operations, disaster recovery, and data migration.

### Key Features

- **Automated Backups**: Scheduled full and incremental backups
- **Encryption**: AES-256 encryption for all backups
- **Compression**: Gzip compression for storage efficiency
- **Verification**: Checksum-based integrity verification
- **Point-in-Time Recovery**: Restore data to specific timestamps
- **Selective Restoration**: Restore specific components
- **Data Export/Import**: Migration support

### Recovery Objectives

- **RTO (Recovery Time Objective)**: < 4 hours
- **RPO (Recovery Point Objective)**: < 1 hour

---

## Backup Strategy

### Backup Types

#### 1. Full Backup
- **Purpose**: Complete snapshot of all platform data
- **Contents**: All ambassadors, user memories, demo configs, agents, analytics, security logs
- **Frequency**: Daily at midnight UTC
- **Retention**: 30 days
- **Size**: Varies (typically 100-500 MB compressed)

#### 2. Incremental Backup
- **Purpose**: Capture changes since last backup
- **Contents**: Modified user memories, analytics, security logs, moderation data
- **Frequency**: Hourly
- **Retention**: 7 days
- **Size**: Varies (typically 10-50 MB compressed)

#### 3. Weekly Archive
- **Purpose**: Long-term archive for compliance
- **Contents**: Full backup snapshot
- **Frequency**: Weekly (Sunday midnight UTC)
- **Retention**: 90 days
- **Size**: Same as full backup

#### 4. Monthly Archive
- **Purpose**: Extended retention for auditing
- **Contents**: Full backup snapshot
- **Frequency**: Monthly (1st of month)
- **Retention**: 365 days
- **Size**: Same as full backup

### Backup Targets

| Target | Description | Priority | Backup Type |
|--------|-------------|----------|-------------|
| `ambassadors` | Ambassador configurations | Critical | Full, Weekly, Monthly |
| `user_memories` | User conversation memories | Critical | All types |
| `demo_configs` | Demo configurations | High | Full, Weekly, Monthly |
| `agents` | Agent code | High | Full, Weekly, Monthly |
| `multi_agents` | Multi-agent configurations | High | Full, Weekly, Monthly |
| `analytics` | Analytics data | Medium | Incremental, Full |
| `security_logs` | Security audit logs | High | Incremental, Full |
| `moderation_data` | Content moderation data | Medium | Incremental, Full |
| `shared_memories` | Shared memory contexts | High | Full, Weekly, Monthly |

### Storage Structure

```
backups/
├── full/
│   ├── full_20251107_000000/
│   │   └── backup.dat
│   ├── full_20251108_000000/
│   │   └── backup.dat
│   └── ...
├── incremental/
│   ├── incr_20251107_010000/
│   │   └── backup.dat
│   ├── incr_20251107_020000/
│   │   └── backup.dat
│   └── ...
├── weekly/
│   └── weekly_2025_W45/
│       └── backup.dat
├── monthly/
│   └── monthly_202511/
│       └── backup.dat
└── metadata/
    ├── full_20251107_000000.json
    ├── incr_20251107_010000.json
    └── ...
```

### Backup Metadata

Each backup includes metadata with:
```json
{
  "backup_id": "full_20251107_000000",
  "backup_type": "full",
  "timestamp": "2025-11-07T00:00:00Z",
  "targets": ["ambassadors", "user_memories", ...],
  "checksum": "sha256_hash",
  "compressed_size": 52428800,
  "original_size": 157286400,
  "compression_ratio": 3.0,
  "encrypted": true,
  "version": "1.0"
}
```

### Encryption

- **Algorithm**: AES-256 using Fernet symmetric encryption
- **Key Derivation**: PBKDF2 with SHA-256, 100,000 iterations
- **Key Storage**: Azure Key Vault (production) or environment variable
- **Salt**: Fixed per environment (use random salt in production)

### Retention Policies

| Backup Type | Retention Period | Auto-Delete |
|-------------|------------------|-------------|
| Incremental | 7 days | Yes |
| Daily Full | 30 days | Yes |
| Weekly Archive | 90 days | Yes |
| Monthly Archive | 365 days | Yes |

Retention enforcement runs daily at 2 AM UTC.

---

## Disaster Recovery Procedures

### Failure Scenarios

#### 1. Data Corruption
**Symptoms**: Invalid data, errors on read operations
**Impact**: Partial or complete data loss
**Recovery Time**: 1-2 hours

**Procedure**:
1. Identify corrupted data scope
2. Create snapshot of current state (if possible)
3. Select most recent valid backup
4. Perform selective restore of corrupted data
5. Verify data integrity
6. Resume operations

#### 2. Complete Data Loss
**Symptoms**: All data unavailable, storage failure
**Impact**: Complete system outage
**Recovery Time**: 2-4 hours

**Procedure**:
1. Notify stakeholders of outage
2. Provision new storage infrastructure
3. Select most recent full backup
4. Perform full system restore
5. Verify all components
6. Test critical workflows
7. Resume operations
8. Monitor for issues

#### 3. Accidental Deletion
**Symptoms**: Specific ambassadors, users, or configs missing
**Impact**: Partial data loss
**Recovery Time**: 30 minutes - 1 hour

**Procedure**:
1. Identify deleted items and deletion time
2. Select backup prior to deletion
3. Perform selective restore with filters
4. Verify restored data
5. Resume operations

#### 4. Security Breach
**Symptoms**: Unauthorized access, data tampering
**Impact**: Potential data corruption, compliance issues
**Recovery Time**: 2-6 hours

**Procedure**:
1. Isolate affected systems
2. Identify breach scope and timeline
3. Select backup from before breach
4. Perform full system restore to clean environment
5. Implement security patches
6. Audit restored data
7. Resume operations with enhanced monitoring
8. Review and update security procedures

### Emergency Contacts

| Role | Contact | Escalation Level |
|------|---------|------------------|
| Platform Admin | admin@company.com | Level 1 |
| DevOps Lead | devops@company.com | Level 1 |
| Engineering Manager | engineering@company.com | Level 2 |
| CTO | cto@company.com | Level 3 |

### Escalation Matrix

- **Level 1** (0-1 hour): Automated monitoring alerts, on-call engineer
- **Level 2** (1-2 hours): Team lead notified, recovery initiated
- **Level 3** (2-4 hours): Management notified, additional resources allocated
- **Level 4** (4+ hours): Executive notification, external support engaged

---

## Restore Instructions

### Using the Web Interface

1. **Open Backup Manager**:
   ```
   http://localhost:7071/backup-manager.html
   ```

2. **Navigate to Restore Tab**

3. **Select Restore Type**:
   - Full System Restore
   - Selective Restore
   - Point-in-Time Restore

4. **Select Backup**:
   - Choose from available backups
   - Review backup metadata (date, size, targets)

5. **Configure Options**:
   - Select data to restore (if selective)
   - Enable snapshot creation (recommended)
   - Set validation options

6. **Execute Restore**:
   - Review confirmation summary
   - Confirm restore operation
   - Monitor progress

7. **Verify Restoration**:
   - Check restored data
   - Test critical workflows
   - Review logs

### Using the API

#### Full Restore

```bash
curl -X POST http://localhost:7071/api/backup/restore \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{
    "backup_id": "full_20251107_000000",
    "restore_type": "full",
    "validate_before": true,
    "create_snapshot": true
  }'
```

#### Selective Restore

```bash
curl -X POST http://localhost:7071/api/backup/restore \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{
    "backup_id": "full_20251107_000000",
    "restore_type": "selective",
    "targets": ["ambassadors", "user_memories"],
    "filters": {
      "user_guid": "abc123",
      "ambassador_id": "creative-001"
    }
  }'
```

#### Point-in-Time Restore

```bash
curl -X POST http://localhost:7071/api/backup/restore \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{
    "restore_type": "point_in_time",
    "target_datetime": "2025-11-07T10:30:00Z",
    "targets": ["user_memories"]
  }'
```

### Manual Restore Process

If API is unavailable:

1. **Access Backup Storage**:
   ```bash
   az storage file download \
     --account-name YOUR_STORAGE \
     --share-name YOUR_SHARE \
     --path backups/full/full_20251107_000000/backup.dat \
     --dest backup.dat
   ```

2. **Decrypt Backup**:
   ```python
   from utils.backup import BackupEncryption

   encryption = BackupEncryption()
   with open('backup.dat', 'rb') as f:
       encrypted_data = f.read()

   compressed_data = encryption.decrypt(encrypted_data)
   ```

3. **Decompress**:
   ```python
   import gzip

   decompressed_data = gzip.decompress(compressed_data)
   backup_data = json.loads(decompressed_data)
   ```

4. **Restore Files**:
   ```python
   from utils.azure_file_storage import AzureFileStorageManager

   storage = AzureFileStorageManager()

   for target, target_data in backup_data.items():
       for file_path, file_data in target_data['files'].items():
           storage.write_json(file_path, file_data)
   ```

---

## Migration Guide

### Exporting Data

#### Via Web Interface

1. Open Backup Manager
2. Navigate to Export/Import tab
3. Select data to export
4. Choose format (JSON recommended)
5. Click "Export Data"
6. Download export file

#### Via API

```bash
curl -X POST http://localhost:7071/api/backup/export \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{
    "format": "json",
    "targets": ["ambassadors", "user_memories", "agents"]
  }'
```

### Importing Data

#### Prerequisites
- Create full backup before import
- Verify import file integrity
- Ensure sufficient storage space
- Schedule during maintenance window

#### Via Web Interface

1. Open Backup Manager
2. Navigate to Export/Import tab
3. Select import file
4. Click "Import Data"
5. Confirm operation
6. Verify imported data

#### Via API

```bash
# First, upload export file to storage
az storage file upload \
  --account-name YOUR_STORAGE \
  --share-name YOUR_SHARE \
  --source export.json \
  --path imports/export.json

# Then trigger import
curl -X POST http://localhost:7071/api/backup/import \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{
    "import_path": "imports/export.json",
    "validate": true
  }'
```

### Migration Scenarios

#### 1. Environment Migration (Dev → Staging → Prod)

```bash
# Export from source environment
SOURCE_ENDPOINT="https://dev.platform.com/api"
curl -X POST $SOURCE_ENDPOINT/backup/export \
  -H "x-functions-key: DEV_KEY" \
  -d '{"format": "json"}' > export.json

# Import to target environment
TARGET_ENDPOINT="https://staging.platform.com/api"
curl -X POST $TARGET_ENDPOINT/backup/import \
  -H "x-functions-key: STAGING_KEY" \
  -d @export.json
```

#### 2. Cross-Region Migration

1. Export data from source region
2. Upload export to target region storage
3. Provision infrastructure in target region
4. Import data to target region
5. Update DNS/endpoints
6. Verify functionality
7. Decommission source region (after verification period)

#### 3. Platform Upgrade

1. Create full backup
2. Test upgrade in non-production environment
3. Schedule maintenance window
4. Create pre-upgrade snapshot
5. Perform upgrade
6. Verify data compatibility
7. Rollback if issues detected (using snapshot)

---

## Troubleshooting

### Backup Issues

#### Backup Creation Fails

**Symptoms**: API returns error, backup not created
**Possible Causes**:
- Storage connection failure
- Insufficient permissions
- Storage capacity full
- Encryption key unavailable

**Resolution**:
1. Check storage connectivity
2. Verify credentials and permissions
3. Check storage capacity
4. Verify encryption key in environment variables
5. Review function logs for errors

#### Backup Verification Fails

**Symptoms**: Checksum mismatch, corruption detected
**Possible Causes**:
- Data corruption during backup
- Storage transmission errors
- Encryption key mismatch

**Resolution**:
1. Attempt re-verification
2. Check storage health
3. Verify encryption key
4. Create new backup
5. Report to system administrator

### Restore Issues

#### Restore Fails to Start

**Symptoms**: API error, restore doesn't begin
**Possible Causes**:
- Invalid backup ID
- Backup file missing
- Insufficient permissions

**Resolution**:
1. Verify backup ID exists
2. Check backup file in storage
3. Verify function permissions
4. Review API request payload

#### Partial Restore Failure

**Symptoms**: Some targets restored, others failed
**Possible Causes**:
- Invalid data in backup
- Permission issues
- Storage write failures

**Resolution**:
1. Review restore results for failed targets
2. Attempt selective restore of failed targets
3. Verify storage permissions
4. Check data validation errors
5. Consider manual restoration

#### Data Mismatch After Restore

**Symptoms**: Restored data doesn't match expected state
**Possible Causes**:
- Wrong backup selected
- Backup corruption
- Concurrent modifications

**Resolution**:
1. Verify correct backup was used
2. Check backup verification status
3. Review restore logs
4. Rollback to snapshot if available
5. Attempt restore from different backup

### Performance Issues

#### Slow Backup Creation

**Symptoms**: Backups take longer than expected
**Expected Time**: 2-5 minutes for full backup

**Resolution**:
1. Check storage performance metrics
2. Verify network connectivity
3. Review data volume growth
4. Consider storage tier upgrade
5. Optimize backup targets

#### Slow Restore Operations

**Symptoms**: Restore takes longer than RTO
**Expected Time**: 1-4 hours for full restore

**Resolution**:
1. Check storage read performance
2. Verify network bandwidth
3. Use selective restore when possible
4. Consider parallel restore operations
5. Upgrade storage tier if needed

---

## Maintenance & Testing

### Regular Maintenance Tasks

#### Weekly
- Review backup success rate
- Check storage capacity
- Verify retention policy enforcement
- Review recent restore operations

#### Monthly
- Test disaster recovery procedures
- Verify backup integrity (sample)
- Review and update documentation
- Test restore from monthly archive
- Audit access logs

#### Quarterly
- Full disaster recovery drill
- Review and update RTO/RPO targets
- Storage capacity planning
- Security audit of backups
- Update emergency contact list

### Backup Verification

#### Automated Verification
Runs automatically after each backup creation:
- Checksum validation
- File integrity check
- Metadata validation
- Size validation

#### Manual Verification

```bash
# Verify specific backup
curl -X POST http://localhost:7071/api/backup/verify \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_KEY" \
  -d '{"backup_id": "full_20251107_000000"}'

# Expected response
{
  "valid": true,
  "backup_id": "full_20251107_000000",
  "checksum": "abc123...",
  "size": 52428800,
  "timestamp": "2025-11-07T00:00:00Z"
}
```

#### Verification Test Plan

1. Select random backup from each type
2. Verify backup integrity
3. Perform test restore to isolated environment
4. Validate restored data sample
5. Document results
6. Archive test results

### Disaster Recovery Drills

#### Quarterly DR Test

**Objectives**:
- Validate backup procedures
- Test restoration process
- Measure actual RTO/RPO
- Identify improvement areas
- Train operations team

**Procedure**:

1. **Preparation** (1 week before):
   - Schedule drill
   - Notify stakeholders
   - Prepare test environment
   - Document baseline metrics

2. **Execution**:
   - Simulate disaster scenario
   - Follow DR procedures
   - Document timeline
   - Measure recovery time
   - Validate data integrity

3. **Post-Drill**:
   - Debrief with team
   - Document findings
   - Update procedures
   - Address identified issues
   - Schedule follow-up

**Success Criteria**:
- Restore completed within RTO (4 hours)
- Data loss within RPO (1 hour)
- All critical systems functional
- No data integrity issues
- Procedures followed correctly

### Monitoring & Alerts

#### Key Metrics

```python
# Backup health metrics
{
  "backup_success_rate": 99.5,  # Target: >99%
  "average_backup_time": 180,    # seconds
  "storage_used_gb": 45.2,
  "storage_capacity_gb": 100,
  "retention_compliance": 100    # %
}
```

#### Alert Configuration

| Alert | Threshold | Action |
|-------|-----------|--------|
| Backup Failure | Any failed backup | Immediate notification |
| Storage Capacity | >80% used | Warning notification |
| Verification Failure | Any failed verification | Immediate notification |
| Backup Age | >25 hours since last | Warning notification |
| Retention Violation | Any non-compliant backup | Daily report |

### Documentation Updates

Keep this guide updated with:
- Procedural changes
- New backup targets
- Infrastructure updates
- Lessons learned from incidents
- DR drill results
- Contact information changes

---

## Appendix

### API Reference

Full API documentation: See `/api/backup/*` endpoints in function_app.py

### Configuration Files

- Backup config: `utils/backup.py`
- Recovery config: `utils/recovery.py`
- Encryption keys: Azure Key Vault or environment variables
- Retention policies: Configured in BackupManager class

### Related Documentation

- Infrastructure Deployment Guide: `README.md`
- AI Ambassador Specification: `AI_Ambassador_Implementation_Spec.md`
- System Architecture: `AI_Ambassador_Integration_Map.md`
- Copilot Agent Framework: `Copilot-Agent-365-main/CLAUDE.md`

### Support Resources

- GitHub Issues: [Platform Repository Issues](https://github.com/yourorg/ai-ambassador-platform/issues)
- Slack Channel: #platform-ops
- Email: support@company.com
- Emergency Hotline: +1-XXX-XXX-XXXX

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-07 | Platform Team | Initial release |

---

**Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Platform Lead | | | |
| Security Lead | | | |
| Operations Manager | | | |

---

*End of Backup & Recovery Guide*
