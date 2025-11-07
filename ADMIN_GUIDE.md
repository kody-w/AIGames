# AI Ambassador Platform - Admin Guide

## Overview

This guide provides comprehensive documentation for administering the AI Ambassador Platform through the admin dashboard and API.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Admin Dashboard](#admin-dashboard)
3. [Admin API Reference](#admin-api-reference)
4. [User Management](#user-management)
5. [Ambassador Management](#ambassador-management)
6. [Security & Monitoring](#security--monitoring)
7. [System Configuration](#system-configuration)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Admin API key (obtained from system administrator)
- Access to Azure Function URL
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Initial Setup

1. **Generate Admin API Key**

```python
from utils.admin_auth import AdminAuth, AdminRole

auth = AdminAuth()
api_key = auth.create_admin_user(
    username="admin@company.com",
    role=AdminRole.ADMIN,
    email="admin@company.com"
)

print(f"Your admin API key: {api_key}")
# Save this key securely - it will not be shown again
```

2. **Access Admin Dashboard**

Open `admin-dashboard.html` in your browser:
- Local development: `http://localhost:7071/admin-dashboard.html`
- Production: `https://your-function-app.azurewebsites.net/admin-dashboard.html`

3. **Login**

Enter your API key when prompted. The dashboard will remember your session until you logout or the session expires (default: 60 minutes).

---

## Admin Dashboard

### Dashboard Overview

The main dashboard provides:

- **Key Metrics**: Total ambassadors, active users, sessions, system status
- **Activity Chart**: Daily session trends
- **Performance Chart**: Ambassador usage statistics
- **Quick Actions**: Create ambassador, view alerts, system health

### Navigation

The sidebar provides access to:

- **📊 Overview**: Dashboard home with key metrics
- **🤖 Ambassadors**: Manage ambassador configurations
- **👥 Users**: View and manage user accounts
- **📈 Analytics**: Detailed usage analytics and insights
- **🔒 Security**: Audit logs and security events
- **⚙️ Configuration**: System settings
- **❤️ System Health**: Service health monitoring

### Dark Mode

Toggle dark mode using the theme button in the header. Your preference is saved locally.

---

## Admin API Reference

### Authentication

All admin API endpoints require Bearer authentication:

```bash
Authorization: Bearer YOUR_API_KEY
```

### Base URL

```
Local: http://localhost:7071/api
Production: https://your-function-app.azurewebsites.net/api
```

### Endpoints

#### 1. Login

**POST** `/admin/login`

Authenticate with API key and receive session token.

**Request:**
```json
{
  "api_key": "your-api-key-here"
}
```

**Response:**
```json
{
  "success": true,
  "session_token": "session-token-here",
  "user": {
    "username": "admin@company.com",
    "role": "admin",
    "email": "admin@company.com"
  }
}
```

#### 2. List Ambassadors

**GET** `/admin/ambassadors`

Get all ambassador configurations.

**Query Parameters:**
- `type` (optional): Filter by world type
- `search` (optional): Search in name/description

**Response:**
```json
{
  "ambassadors": [
    {
      "id": "creative-ambassador-001",
      "name": "Creative Assistant",
      "description": "Helps with creative tasks",
      "world_type": "creative_studio",
      "version": 2,
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 3. Create Ambassador

**POST** `/admin/ambassadors`

Create a new ambassador configuration.

**Request:**
```json
{
  "ambassador": {
    "id": "sales-assistant-001",
    "name": "Sales Assistant",
    "description": "Helps with sales inquiries",
    "avatar": {
      "type": "emoji",
      "value": "💼"
    },
    "world": {
      "type": "sales_floor",
      "environment": {
        "theme": "professional",
        "color_scheme": "blue"
      }
    },
    "capabilities": {
      "voice_enabled": true,
      "visual_responses": true,
      "memory_enabled": true
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ambassador created successfully",
  "ambassador_id": "sales-assistant-001"
}
```

#### 4. Update Ambassador

**PUT** `/admin/ambassadors?id=ambassador-id&notes=Change%20description`

Update an existing ambassador.

**Request:** Same as Create Ambassador

**Response:**
```json
{
  "success": true,
  "message": "Ambassador updated successfully"
}
```

#### 5. Delete Ambassador

**DELETE** `/admin/ambassadors?id=ambassador-id`

Delete an ambassador (archived, not permanently deleted).

**Response:**
```json
{
  "success": true,
  "message": "Ambassador deleted successfully"
}
```

#### 6. List Users

**GET** `/admin/users`

Get all user accounts and activity.

**Response:**
```json
{
  "users": [
    {
      "user_guid": "c0p110t0-aaaa-bbbb-cccc-123456789abc",
      "created_at": "2024-01-01T00:00:00Z",
      "last_active": "2024-01-15T12:00:00Z",
      "session_count": 45
    }
  ]
}
```

#### 7. Security Events

**GET** `/admin/security-events`

Get audit logs and security events.

**Query Parameters:**
- `start_date`: ISO format date
- `end_date`: ISO format date
- `username`: Filter by username
- `event_type`: Filter by event type
- `limit`: Max results (default: 100)

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "event_type": "ambassador_created",
      "username": "admin@company.com",
      "details": {
        "ambassador_id": "new-ambassador"
      }
    }
  ]
}
```

#### 8. System Configuration

**GET** `/admin/config`

Get current system configuration.

**Response:**
```json
{
  "config": {
    "security_settings": {
      "session_timeout_minutes": 60,
      "max_failed_attempts": 5
    },
    "system_settings": {
      "max_ambassadors": 1000,
      "memory_retention_days": 90
    }
  }
}
```

**POST** `/admin/config`

Update system configuration.

**Request:** Same structure as GET response

#### 9. System Health

**GET** `/admin/health`

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "azure_storage": "healthy",
    "azure_openai": "healthy",
    "function_app": "healthy"
  }
}
```

---

## User Management

### User Roles

Three role levels with hierarchical permissions:

1. **Viewer** (Read-only)
   - View ambassadors
   - View users
   - View analytics
   - View system health

2. **Operator** (Modify content)
   - All Viewer permissions
   - Create/update ambassadors
   - Modify configuration

3. **Admin** (Full access)
   - All Operator permissions
   - Delete ambassadors
   - Manage admin users
   - Access security logs

### Creating Admin Users

```python
from utils.admin_auth import AdminAuth, AdminRole

auth = AdminAuth()

# Create viewer
viewer_key = auth.create_admin_user(
    username="viewer@company.com",
    role=AdminRole.VIEWER,
    email="viewer@company.com"
)

# Create operator
operator_key = auth.create_admin_user(
    username="operator@company.com",
    role=AdminRole.OPERATOR,
    email="operator@company.com"
)

# Create admin
admin_key = auth.create_admin_user(
    username="admin@company.com",
    role=AdminRole.ADMIN,
    email="admin@company.com"
)
```

### Deleting Admin Users

```python
auth = AdminAuth()
success = auth.delete_admin_user("username@company.com")
```

### Listing Admin Users

```python
auth = AdminAuth()
users = auth.list_admin_users()

for user in users:
    print(f"{user['username']} - {user['role']}")
```

---

## Ambassador Management

### Creating Ambassadors

Ambassadors are defined using JSON configuration files. The schema includes:

**Required Fields:**
- `id`: Unique identifier (alphanumeric, hyphens, underscores only)
- `name`: Display name
- `avatar`: Avatar configuration (emoji, image, or 3d_model)
- `world`: World/environment settings

**Optional Fields:**
- `description`: Ambassador description
- `capabilities`: Feature flags (voice, visual, memory)
- `agent_mapping`: Custom agent assignments
- `demo_configuration`: Seeded demo settings

### Example Configuration

```json
{
  "ambassador": {
    "id": "retail-assistant-001",
    "name": "Retail Shopping Assistant",
    "description": "Helps customers find products and answer questions",
    "avatar": {
      "type": "emoji",
      "value": "🛍️"
    },
    "world": {
      "type": "sales_floor",
      "environment": {
        "theme": "modern-retail",
        "color_scheme": "warm",
        "background": "store-interior.jpg"
      }
    },
    "capabilities": {
      "voice_enabled": true,
      "visual_responses": true,
      "memory_enabled": true,
      "custom_agents": ["ProductSearchAgent", "InventoryAgent"]
    },
    "agent_mapping": {
      "BasicAgent": "RetailBasicAgent",
      "ContextMemory": "ContextMemoryAgent"
    },
    "demo_configuration": {
      "seeded_run": false
    }
  }
}
```

### Version Control

Every ambassador update creates a new version:

```python
from utils.ambassador_manager import AmbassadorManager

manager = AmbassadorManager()

# View version history
versions = manager.get_ambassador_versions("ambassador-id")
for v in versions:
    print(f"v{v['version']}: {v['change_notes']} by {v['updated_by']}")

# Restore previous version
success, message = manager.restore_version(
    "ambassador-id",
    version=3,
    restored_by="admin@company.com"
)
```

### Bulk Operations

**Export Ambassadors:**

```python
manager = AmbassadorManager()

# Export all
export_data = manager.export_ambassadors()

# Export specific IDs
export_data = manager.export_ambassadors(["id1", "id2", "id3"])

# Save to file
import json
with open('ambassadors_backup.json', 'w') as f:
    json.dump(export_data, f, indent=2)
```

**Import Ambassadors:**

```python
import json

# Load export file
with open('ambassadors_backup.json', 'r') as f:
    import_data = json.load(f)

# Import (skip existing)
success_count, failure_count, errors = manager.import_ambassadors(
    import_data,
    imported_by="admin@company.com",
    overwrite=False
)

print(f"Success: {success_count}, Failed: {failure_count}")
```

### Deploying to Azure

```python
from utils.azure_file_storage import AzureFileStorageManager

storage_manager = AzureFileStorageManager()
manager = AmbassadorManager()

success, message = manager.deploy_to_azure(
    "ambassador-id",
    storage_manager
)

if success:
    print("Ambassador deployed to Azure successfully")
```

---

## Security & Monitoring

### Audit Logging

All admin actions are automatically logged:

- User login attempts
- Ambassador CRUD operations
- Configuration changes
- API access
- Unauthorized access attempts

### Viewing Audit Logs

```python
auth = AdminAuth()

# Get all recent logs
logs = auth.get_audit_logs(limit=100)

# Filter by date range
from datetime import datetime, timedelta

start = (datetime.now() - timedelta(days=7)).isoformat()
end = datetime.now().isoformat()

logs = auth.get_audit_logs(
    start_date=start,
    end_date=end,
    event_type="ambassador_created"
)

for log in logs:
    print(f"{log['timestamp']}: {log['event_type']} by {log['username']}")
```

### Security Settings

Configurable security parameters:

```python
auth = AdminAuth()

auth.config['security_settings'] = {
    "session_timeout_minutes": 60,
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 30,
    "require_audit_log": True
}

auth.save_config()
```

### Rate Limiting

Configure rate limits in `admin_config.json`:

```json
{
  "security_settings": {
    "rate_limit": {
      "enabled": true,
      "max_requests_per_minute": 60,
      "max_requests_per_hour": 1000
    }
  }
}
```

---

## System Configuration

### Configuration File

Located at: `Copilot-Agent-365-main/admin_config.json`

**Structure:**

```json
{
  "api_keys": {},
  "sessions": {},
  "security_settings": {
    "session_timeout_minutes": 60,
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 30,
    "require_audit_log": true
  },
  "system_settings": {
    "max_ambassadors": 1000,
    "max_users_per_ambassador": 10000,
    "memory_retention_days": 90,
    "auto_backup": {
      "enabled": true,
      "frequency_hours": 24,
      "retention_days": 30
    }
  },
  "notification_settings": {
    "email_alerts": {
      "enabled": false,
      "recipients": [],
      "events": ["security_breach", "system_error"]
    }
  }
}
```

### Environment Variables

Required in `local.settings.json`:

```json
{
  "AZURE_OPENAI_API_KEY": "your-key",
  "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
  "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
  "AZURE_OPENAI_API_VERSION": "2025-01-01-preview",
  "AzureWebJobsStorage": "connection-string",
  "AZURE_FILES_SHARE_NAME": "your-share-name"
}
```

---

## Troubleshooting

### Common Issues

#### 1. Login Fails with 401 Unauthorized

**Cause:** Invalid API key or expired session

**Solution:**
```python
# Generate new API key
auth = AdminAuth()
new_key = auth.create_admin_user(username, role, email)
```

#### 2. Ambassador Creation Fails

**Cause:** Invalid configuration or schema validation error

**Solution:** Validate JSON configuration:
```python
manager = AmbassadorManager()
is_valid, error = manager.validate_config(config)
if not is_valid:
    print(f"Validation error: {error}")
```

#### 3. System Health Shows Degraded

**Cause:** Azure service connectivity issues

**Solution:**
1. Check Azure Portal for service status
2. Verify environment variables
3. Test connection strings
4. Review Application Insights logs

#### 4. Audit Logs Not Saving

**Cause:** File system permissions or storage errors

**Solution:**
```python
import os
log_dir = "Copilot-Agent-365-main/audit_logs"
os.makedirs(log_dir, exist_ok=True)
# Check write permissions
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### API Testing

Test endpoints with curl:

```bash
# Test login
curl -X POST http://localhost:7071/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key"}'

# Test health check
curl -X GET http://localhost:7071/api/admin/health \
  -H "Authorization: Bearer your-api-key"

# Test list ambassadors
curl -X GET http://localhost:7071/api/admin/ambassadors \
  -H "Authorization: Bearer your-api-key"
```

### Contact Support

For additional support:
- GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)
- Email: support@your-company.com
- Documentation: [Full Documentation](https://docs.your-company.com)

---

## Best Practices

### Security

1. **Rotate API keys** every 90 days
2. **Use least privilege** - assign minimum required role
3. **Monitor audit logs** weekly for suspicious activity
4. **Enable 2FA** for admin email accounts
5. **Backup configurations** before major changes

### Performance

1. **Limit concurrent users** per ambassador to 10,000
2. **Archive old ambassadors** after 6 months of inactivity
3. **Clean up audit logs** older than 1 year
4. **Monitor Azure costs** monthly

### Maintenance

1. **Weekly health checks** via dashboard
2. **Monthly ambassador audits** for unused configs
3. **Quarterly security reviews** of admin users
4. **Annual disaster recovery testing**

---

## Appendix

### Admin API Key Format

API keys are 43-character base64-encoded strings:

```
Example: 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x
```

### Supported World Types

- `creative_studio` - Creative and artistic tasks
- `sales_floor` - Sales and customer engagement
- `tech_lab` - Technical support and troubleshooting
- `customer_service` - Customer support and inquiries
- `education_center` - Educational content and tutoring

### Supported Avatar Types

- `emoji` - Single emoji character
- `image` - URL to image file
- `3d_model` - Path to 3D model asset

---

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial admin dashboard release
- Basic CRUD operations for ambassadors
- Role-based access control
- Audit logging
- System health monitoring

---

## License

Copyright (c) 2024. All rights reserved.
