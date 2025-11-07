"""
Admin Authentication and Authorization Module

Provides secure authentication, role-based access control, and audit logging
for the AI Ambassador Platform admin dashboard.
"""

import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum


class AdminRole(Enum):
    """Admin user roles with hierarchical permissions"""
    VIEWER = "viewer"      # Read-only access
    OPERATOR = "operator"  # Can modify ambassadors and configs
    ADMIN = "admin"        # Full access including user management


class AdminAuth:
    """Handles admin authentication and authorization"""

    def __init__(self, config_path: str = None):
        """Initialize admin auth with configuration"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "admin_config.json"
            )
        self.config_path = config_path
        self.sessions: Dict[str, dict] = {}
        self.audit_log: List[dict] = []
        self.load_config()

    def load_config(self):
        """Load admin configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default config
                self.config = {
                    "api_keys": {},
                    "sessions": {},
                    "security_settings": {
                        "session_timeout_minutes": 60,
                        "max_failed_attempts": 5,
                        "lockout_duration_minutes": 30,
                        "require_audit_log": True
                    }
                }
                self.save_config()
        except Exception as e:
            print(f"Error loading admin config: {e}")
            self.config = {"api_keys": {}, "sessions": {}}

    def save_config(self):
        """Save admin configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving admin config: {e}")

    def generate_api_key(self) -> str:
        """Generate a secure random API key"""
        return secrets.token_urlsafe(32)

    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_admin_user(
        self,
        username: str,
        role: AdminRole,
        email: str = None
    ) -> str:
        """
        Create a new admin user and return their API key

        Args:
            username: Unique username for the admin
            role: AdminRole enum value
            email: Optional email address

        Returns:
            API key for the new user
        """
        api_key = self.generate_api_key()
        key_hash = self.hash_api_key(api_key)

        if "api_keys" not in self.config:
            self.config["api_keys"] = {}

        self.config["api_keys"][key_hash] = {
            "username": username,
            "role": role.value,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "failed_attempts": 0,
            "locked_until": None
        }

        self.save_config()
        self.log_audit_event(
            "admin_user_created",
            username,
            {"role": role.value}
        )

        return api_key

    def authenticate(self, api_key: str) -> Optional[Dict]:
        """
        Authenticate an API key and return user info

        Args:
            api_key: The API key to validate

        Returns:
            User info dict if valid, None if invalid
        """
        key_hash = self.hash_api_key(api_key)

        if key_hash not in self.config.get("api_keys", {}):
            return None

        user_info = self.config["api_keys"][key_hash]

        # Check if account is locked
        if user_info.get("locked_until"):
            locked_until = datetime.fromisoformat(user_info["locked_until"])
            if datetime.utcnow() < locked_until:
                return None
            else:
                # Unlock account
                user_info["locked_until"] = None
                user_info["failed_attempts"] = 0

        # Update last used timestamp
        user_info["last_used"] = datetime.utcnow().isoformat()
        self.save_config()

        return {
            "username": user_info["username"],
            "role": user_info["role"],
            "email": user_info.get("email")
        }

    def create_session(self, user_info: Dict) -> str:
        """
        Create a new session for an authenticated user

        Args:
            user_info: User information from authentication

        Returns:
            Session token
        """
        session_token = secrets.token_urlsafe(32)
        timeout_minutes = self.config.get("security_settings", {}).get(
            "session_timeout_minutes", 60
        )

        self.sessions[session_token] = {
            "username": user_info["username"],
            "role": user_info["role"],
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=timeout_minutes)
        }

        return session_token

    def validate_session(self, session_token: str) -> Optional[Dict]:
        """
        Validate a session token

        Args:
            session_token: The session token to validate

        Returns:
            Session info if valid, None if invalid/expired
        """
        if session_token not in self.sessions:
            return None

        session = self.sessions[session_token]

        if datetime.utcnow() > session["expires_at"]:
            del self.sessions[session_token]
            return None

        return session

    def revoke_session(self, session_token: str):
        """Revoke a session token"""
        if session_token in self.sessions:
            del self.sessions[session_token]

    def check_permission(
        self,
        user_info: Dict,
        required_role: AdminRole
    ) -> bool:
        """
        Check if user has required permission level

        Args:
            user_info: User information dict
            required_role: Minimum required role

        Returns:
            True if user has permission, False otherwise
        """
        role_hierarchy = {
            AdminRole.VIEWER.value: 0,
            AdminRole.OPERATOR.value: 1,
            AdminRole.ADMIN.value: 2
        }

        user_role_level = role_hierarchy.get(user_info["role"], -1)
        required_level = role_hierarchy.get(required_role.value, 999)

        return user_role_level >= required_level

    def log_audit_event(
        self,
        event_type: str,
        username: str,
        details: Dict = None
    ):
        """
        Log an admin action for audit trail

        Args:
            event_type: Type of event (e.g., "ambassador_created")
            username: Username who performed the action
            details: Additional event details
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "username": username,
            "details": details or {}
        }

        self.audit_log.append(event)

        # Also write to file for persistence
        try:
            log_dir = os.path.join(os.path.dirname(self.config_path), "audit_logs")
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(
                log_dir,
                f"audit_{datetime.utcnow().strftime('%Y%m%d')}.json"
            )

            # Load existing logs for today
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)

            logs.append(event)

            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"Error writing audit log: {e}")

    def get_audit_logs(
        self,
        start_date: str = None,
        end_date: str = None,
        username: str = None,
        event_type: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve audit logs with optional filtering

        Args:
            start_date: Filter logs after this date (ISO format)
            end_date: Filter logs before this date (ISO format)
            username: Filter by username
            event_type: Filter by event type
            limit: Maximum number of logs to return

        Returns:
            List of audit log entries
        """
        logs = self.audit_log.copy()

        # Apply filters
        if start_date:
            start = datetime.fromisoformat(start_date)
            logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) >= start]

        if end_date:
            end = datetime.fromisoformat(end_date)
            logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) <= end]

        if username:
            logs = [l for l in logs if l["username"] == username]

        if event_type:
            logs = [l for l in logs if l["event_type"] == event_type]

        # Sort by timestamp descending and limit
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]

    def validate_request(self, headers: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Validate an incoming admin API request

        Args:
            headers: HTTP request headers

        Returns:
            Tuple of (is_valid, user_info, error_message)
        """
        # Check for API key in Authorization header
        auth_header = headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return False, None, "Missing or invalid Authorization header"

        api_key = auth_header.replace("Bearer ", "")

        user_info = self.authenticate(api_key)

        if not user_info:
            return False, None, "Invalid API key"

        return True, user_info, ""

    def list_admin_users(self) -> List[Dict]:
        """Get list of all admin users (admin only)"""
        users = []
        for key_hash, user_data in self.config.get("api_keys", {}).items():
            users.append({
                "username": user_data["username"],
                "role": user_data["role"],
                "email": user_data.get("email"),
                "created_at": user_data["created_at"],
                "last_used": user_data.get("last_used"),
                "failed_attempts": user_data.get("failed_attempts", 0),
                "is_locked": user_data.get("locked_until") is not None
            })
        return users

    def delete_admin_user(self, username: str) -> bool:
        """Delete an admin user by username"""
        key_to_delete = None
        for key_hash, user_data in self.config.get("api_keys", {}).items():
            if user_data["username"] == username:
                key_to_delete = key_hash
                break

        if key_to_delete:
            del self.config["api_keys"][key_to_delete]
            self.save_config()
            return True

        return False


def require_admin_auth(role: AdminRole = AdminRole.VIEWER):
    """
    Decorator for Azure Functions that require admin authentication

    Usage:
        @require_admin_auth(AdminRole.OPERATOR)
        def my_admin_function(req):
            # Function code here
    """
    def decorator(func):
        def wrapper(req):
            auth = AdminAuth()

            # Validate request
            is_valid, user_info, error = auth.validate_request(dict(req.headers))

            if not is_valid:
                return {
                    "statusCode": 401,
                    "body": json.dumps({"error": error})
                }

            # Check permissions
            if not auth.check_permission(user_info, role):
                auth.log_audit_event(
                    "unauthorized_access_attempt",
                    user_info["username"],
                    {"required_role": role.value, "endpoint": req.url}
                )
                return {
                    "statusCode": 403,
                    "body": json.dumps({"error": "Insufficient permissions"})
                }

            # Add user info to request for use in function
            req.user_info = user_info

            # Call the actual function
            result = func(req)

            # Log successful access
            auth.log_audit_event(
                "admin_api_access",
                user_info["username"],
                {"endpoint": req.url}
            )

            return result

        return wrapper
    return decorator
