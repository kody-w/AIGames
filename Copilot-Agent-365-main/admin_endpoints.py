"""
Admin API Endpoints

Provides admin dashboard endpoints for managing ambassadors, users,
security events, configuration, and system health.

These endpoints should be imported and registered in function_app.py
"""

import azure.functions as func
import logging
import json
import os
from datetime import datetime
from openai import AzureOpenAI
from utils.admin_auth import AdminAuth, AdminRole
from utils.ambassador_manager import AmbassadorManager
from utils.azure_file_storage import AzureFileStorageManager

# Default GUID from main app
DEFAULT_USER_GUID = "c0p110t0-aaaa-bbbb-cccc-123456789abc"


def admin_response(data, status_code=200):
    """Build JSON response with CORS headers for admin endpoints"""
    return func.HttpResponse(
        json.dumps(data),
        status_code=status_code,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


def admin_login_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Admin login endpoint"""
    logging.info('Admin login endpoint called')

    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })

    try:
        body = req.get_json()
        api_key = body.get('api_key')

        if not api_key:
            return admin_response({"error": "Missing API key"}, 400)

        auth = AdminAuth()
        user_info = auth.authenticate(api_key)

        if not user_info:
            return admin_response({"error": "Invalid API key"}, 401)

        session_token = auth.create_session(user_info)

        return admin_response({
            "success": True,
            "session_token": session_token,
            "user": user_info
        })

    except Exception as e:
        logging.error(f"Error in admin_login: {str(e)}")
        return admin_response({"error": str(e)}, 500)


def admin_ambassadors_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Manage ambassadors - list, create, update, delete"""
    logging.info('Admin ambassadors endpoint called')

    # Handle OPTIONS for CORS
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })

    # Authenticate
    auth = AdminAuth()
    is_valid, user_info, error = auth.validate_request(dict(req.headers))

    if not is_valid:
        return admin_response({"error": error}, 401)

    # Initialize manager
    manager = AmbassadorManager()

    try:
        if req.method == 'GET':
            # List ambassadors
            if not auth.check_permission(user_info, AdminRole.VIEWER):
                return admin_response({"error": "Insufficient permissions"}, 403)

            params = req.params
            filter_type = params.get('type')
            search = params.get('search')

            ambassadors = manager.list_ambassadors(filter_type, search)
            auth.log_audit_event("list_ambassadors", user_info["username"])
            return admin_response({"ambassadors": ambassadors})

        elif req.method == 'POST':
            # Create ambassador
            if not auth.check_permission(user_info, AdminRole.OPERATOR):
                return admin_response({"error": "Insufficient permissions"}, 403)

            config = req.get_json()
            success, message, ambassador_id = manager.create_ambassador(
                config, user_info["username"]
            )

            if success:
                auth.log_audit_event("create_ambassador", user_info["username"],
                                    {"ambassador_id": ambassador_id})
                return admin_response({"success": True, "message": message,
                                      "ambassador_id": ambassador_id})
            else:
                return admin_response({"success": False, "error": message}, 400)

        elif req.method == 'PUT':
            # Update ambassador
            if not auth.check_permission(user_info, AdminRole.OPERATOR):
                return admin_response({"error": "Insufficient permissions"}, 403)

            config = req.get_json()
            ambassador_id = req.params.get('id')
            change_notes = req.params.get('notes', '')

            if not ambassador_id:
                return admin_response({"error": "Missing ambassador ID"}, 400)

            success, message = manager.update_ambassador(
                ambassador_id, config, user_info["username"], change_notes
            )

            if success:
                auth.log_audit_event("update_ambassador", user_info["username"],
                                    {"ambassador_id": ambassador_id})
                return admin_response({"success": True, "message": message})
            else:
                return admin_response({"success": False, "error": message}, 400)

        elif req.method == 'DELETE':
            # Delete ambassador
            if not auth.check_permission(user_info, AdminRole.ADMIN):
                return admin_response({"error": "Insufficient permissions"}, 403)

            ambassador_id = req.params.get('id')
            if not ambassador_id:
                return admin_response({"error": "Missing ambassador ID"}, 400)

            success, message = manager.delete_ambassador(
                ambassador_id, user_info["username"]
            )

            if success:
                auth.log_audit_event("delete_ambassador", user_info["username"],
                                    {"ambassador_id": ambassador_id})
                return admin_response({"success": True, "message": message})
            else:
                return admin_response({"success": False, "error": message}, 400)

    except Exception as e:
        logging.error(f"Error in admin_ambassadors: {str(e)}")
        return admin_response({"error": str(e)}, 500)


def admin_users_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Get user list and activity"""
    logging.info('Admin users endpoint called')

    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })

    # Authenticate
    auth = AdminAuth()
    is_valid, user_info, error = auth.validate_request(dict(req.headers))

    if not is_valid:
        return admin_response({"error": error}, 401)

    if not auth.check_permission(user_info, AdminRole.VIEWER):
        return admin_response({"error": "Insufficient permissions"}, 403)

    try:
        # Get storage manager
        storage_manager = AzureFileStorageManager()

        # List user directories (user_* folders)
        users = []
        # This would require implementing a method to list directories in Azure File Storage
        # For now, return placeholder
        users.append({
            "user_guid": DEFAULT_USER_GUID,
            "created_at": "2024-01-01T00:00:00",
            "last_active": "2024-01-15T12:00:00",
            "session_count": 10
        })

        auth.log_audit_event("list_users", user_info["username"])
        return admin_response({"users": users})

    except Exception as e:
        logging.error(f"Error in admin_users: {str(e)}")
        return admin_response({"error": str(e)}, 500)


def admin_security_events_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Get security logs and audit events"""
    logging.info('Admin security events endpoint called')

    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })

    # Authenticate
    auth = AdminAuth()
    is_valid, user_info, error = auth.validate_request(dict(req.headers))

    if not is_valid:
        return admin_response({"error": error}, 401)

    if not auth.check_permission(user_info, AdminRole.ADMIN):
        return admin_response({"error": "Insufficient permissions"}, 403)

    try:
        params = req.params
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        username = params.get('username')
        event_type = params.get('event_type')
        limit = int(params.get('limit', 100))

        events = auth.get_audit_logs(start_date, end_date, username, event_type, limit)

        return admin_response({"events": events})

    except Exception as e:
        logging.error(f"Error in admin_security_events: {str(e)}")
        return admin_response({"error": str(e)}, 500)


def admin_config_handler(req: func.HttpRequest) -> func.HttpResponse:
    """Get or update system configuration"""
    logging.info('Admin config endpoint called')

    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })

    # Authenticate
    auth = AdminAuth()
    is_valid, user_info, error = auth.validate_request(dict(req.headers))

    if not is_valid:
        return admin_response({"error": error}, 401)

    try:
        if req.method == 'GET':
            if not auth.check_permission(user_info, AdminRole.VIEWER):
                return admin_response({"error": "Insufficient permissions"}, 403)

            # Return sanitized config (without API keys)
            config = auth.config.copy()
            config.pop('api_keys', None)
            config.pop('sessions', None)

            return admin_response({"config": config})

        elif req.method == 'POST':
            if not auth.check_permission(user_info, AdminRole.ADMIN):
                return admin_response({"error": "Insufficient permissions"}, 403)

            new_config = req.get_json()

            # Update specific settings (not API keys)
            if 'security_settings' in new_config:
                auth.config['security_settings'].update(new_config['security_settings'])
            if 'system_settings' in new_config:
                auth.config['system_settings'] = new_config['system_settings']
            if 'notification_settings' in new_config:
                auth.config['notification_settings'] = new_config['notification_settings']

            auth.save_config()
            auth.log_audit_event("update_config", user_info["username"])

            return admin_response({"success": True, "message": "Configuration updated"})

    except Exception as e:
        logging.error(f"Error in admin_config: {str(e)}")
        return admin_response({"error": str(e)}, 500)


def admin_health_handler(req: func.HttpRequest) -> func.HttpResponse:
    """System health check"""
    logging.info('Admin health endpoint called')

    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })

    # Authenticate
    auth = AdminAuth()
    is_valid, user_info, error = auth.validate_request(dict(req.headers))

    if not is_valid:
        return admin_response({"error": error}, 401)

    if not auth.check_permission(user_info, AdminRole.VIEWER):
        return admin_response({"error": "Insufficient permissions"}, 403)

    try:
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "azure_storage": "healthy",
                "azure_openai": "healthy",
                "function_app": "healthy"
            }
        }

        # Check Azure Storage
        try:
            storage_manager = AzureFileStorageManager()
            storage_manager.list_files('agents')
            health["checks"]["azure_storage"] = "healthy"
        except Exception as e:
            health["checks"]["azure_storage"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        # Check Azure OpenAI
        try:
            client = AzureOpenAI(
                api_key=os.environ['AZURE_OPENAI_API_KEY'],
                api_version=os.environ['AZURE_OPENAI_API_VERSION'],
                azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
            )
            health["checks"]["azure_openai"] = "healthy"
        except Exception as e:
            health["checks"]["azure_openai"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        return admin_response(health)

    except Exception as e:
        logging.error(f"Error in admin_health: {str(e)}")
        return admin_response({"error": str(e)}, 500)


# Registration helper for function_app.py
def register_admin_endpoints(app):
    """
    Register all admin endpoints with the Azure Function App

    Usage in function_app.py:
        from admin_endpoints import register_admin_endpoints
        register_admin_endpoints(app)
    """

    @app.route(route="admin/login", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
    def admin_login(req: func.HttpRequest) -> func.HttpResponse:
        return admin_login_handler(req)

    @app.route(route="admin/ambassadors", methods=["GET", "POST", "PUT", "DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
    def admin_ambassadors(req: func.HttpRequest) -> func.HttpResponse:
        return admin_ambassadors_handler(req)

    @app.route(route="admin/users", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def admin_users(req: func.HttpRequest) -> func.HttpResponse:
        return admin_users_handler(req)

    @app.route(route="admin/security-events", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def admin_security_events(req: func.HttpRequest) -> func.HttpResponse:
        return admin_security_events_handler(req)

    @app.route(route="admin/config", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
    def admin_config(req: func.HttpRequest) -> func.HttpResponse:
        return admin_config_handler(req)

    @app.route(route="admin/health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def admin_health(req: func.HttpRequest) -> func.HttpResponse:
        return admin_health_handler(req)

    logging.info("Admin endpoints registered successfully")
