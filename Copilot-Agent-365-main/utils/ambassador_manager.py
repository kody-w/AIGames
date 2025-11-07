"""
Ambassador Management Module

Provides CRUD operations, validation, versioning, and deployment
for AI Ambassador configurations.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import copy
from jsonschema import validate, ValidationError


class AmbassadorManager:
    """Manages AI Ambassador configurations and deployments"""

    # JSON Schema for ambassador configuration validation
    AMBASSADOR_SCHEMA = {
        "type": "object",
        "required": ["ambassador"],
        "properties": {
            "ambassador": {
                "type": "object",
                "required": ["id", "name", "avatar", "world"],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "name": {"type": "string", "minLength": 1},
                    "description": {"type": "string"},
                    "avatar": {
                        "type": "object",
                        "required": ["type", "value"],
                        "properties": {
                            "type": {"enum": ["emoji", "image", "3d_model"]},
                            "value": {"type": "string"}
                        }
                    },
                    "world": {
                        "type": "object",
                        "required": ["type", "environment"],
                        "properties": {
                            "type": {"type": "string"},
                            "environment": {"type": "object"}
                        }
                    },
                    "capabilities": {
                        "type": "object",
                        "properties": {
                            "voice_enabled": {"type": "boolean"},
                            "visual_responses": {"type": "boolean"},
                            "memory_enabled": {"type": "boolean"},
                            "custom_agents": {"type": "array"}
                        }
                    },
                    "agent_mapping": {"type": "object"},
                    "demo_configuration": {"type": "object"}
                }
            }
        }
    }

    def __init__(self, storage_path: str = None):
        """
        Initialize ambassador manager

        Args:
            storage_path: Path to store ambassador configurations
        """
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "ambassadors"
            )
        self.storage_path = storage_path
        self.versions_path = os.path.join(storage_path, "versions")
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(self.versions_path, exist_ok=True)

    def validate_config(self, config: Dict) -> Tuple[bool, str]:
        """
        Validate ambassador configuration against schema

        Args:
            config: Ambassador configuration dict

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validate(instance=config, schema=self.AMBASSADOR_SCHEMA)

            # Additional custom validations
            ambassador = config["ambassador"]

            # Validate ID format (no spaces, lowercase, hyphens only)
            ambassador_id = ambassador["id"]
            if not ambassador_id.replace("-", "").replace("_", "").isalnum():
                return False, "Ambassador ID must contain only alphanumeric characters, hyphens, and underscores"

            # Validate avatar type
            avatar_type = ambassador["avatar"]["type"]
            if avatar_type not in ["emoji", "image", "3d_model"]:
                return False, f"Invalid avatar type: {avatar_type}"

            # Validate world type
            valid_world_types = [
                "creative_studio",
                "sales_floor",
                "tech_lab",
                "customer_service",
                "education_center"
            ]
            world_type = ambassador["world"]["type"]
            if world_type not in valid_world_types:
                return False, f"Invalid world type: {world_type}. Must be one of {valid_world_types}"

            return True, ""

        except ValidationError as e:
            return False, f"Schema validation error: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def create_ambassador(
        self,
        config: Dict,
        created_by: str = "system"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new ambassador configuration

        Args:
            config: Ambassador configuration dict
            created_by: Username of creator

        Returns:
            Tuple of (success, message, ambassador_id)
        """
        # Validate configuration
        is_valid, error = self.validate_config(config)
        if not is_valid:
            return False, error, None

        ambassador_id = config["ambassador"]["id"]

        # Check if ambassador already exists
        if self.get_ambassador(ambassador_id):
            return False, f"Ambassador with ID '{ambassador_id}' already exists", None

        # Add metadata
        config["_metadata"] = {
            "created_at": datetime.utcnow().isoformat(),
            "created_by": created_by,
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": created_by,
            "version": 1
        }

        # Save configuration
        config_path = self._get_config_path(ambassador_id)
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            # Create initial version backup
            self._save_version(ambassador_id, config, 1, "Initial creation")

            return True, "Ambassador created successfully", ambassador_id

        except Exception as e:
            return False, f"Error saving ambassador: {str(e)}", None

    def get_ambassador(self, ambassador_id: str) -> Optional[Dict]:
        """
        Retrieve an ambassador configuration by ID

        Args:
            ambassador_id: The ambassador ID

        Returns:
            Ambassador configuration dict or None if not found
        """
        config_path = self._get_config_path(ambassador_id)

        if not os.path.exists(config_path):
            return None

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading ambassador {ambassador_id}: {e}")
            return None

    def update_ambassador(
        self,
        ambassador_id: str,
        config: Dict,
        updated_by: str = "system",
        change_notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Update an existing ambassador configuration

        Args:
            ambassador_id: The ambassador ID to update
            config: New configuration dict
            updated_by: Username of updater
            change_notes: Description of changes

        Returns:
            Tuple of (success, message)
        """
        # Check if ambassador exists
        existing = self.get_ambassador(ambassador_id)
        if not existing:
            return False, f"Ambassador '{ambassador_id}' not found"

        # Validate new configuration
        is_valid, error = self.validate_config(config)
        if not is_valid:
            return False, error

        # Ensure ID matches
        if config["ambassador"]["id"] != ambassador_id:
            return False, "Cannot change ambassador ID during update"

        # Increment version
        old_version = existing.get("_metadata", {}).get("version", 1)
        new_version = old_version + 1

        # Update metadata
        config["_metadata"] = {
            "created_at": existing.get("_metadata", {}).get("created_at"),
            "created_by": existing.get("_metadata", {}).get("created_by", "system"),
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": updated_by,
            "version": new_version,
            "change_notes": change_notes
        }

        # Save updated configuration
        config_path = self._get_config_path(ambassador_id)
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            # Save version backup
            self._save_version(ambassador_id, config, new_version, change_notes)

            return True, "Ambassador updated successfully"

        except Exception as e:
            return False, f"Error updating ambassador: {str(e)}"

    def delete_ambassador(
        self,
        ambassador_id: str,
        deleted_by: str = "system"
    ) -> Tuple[bool, str]:
        """
        Delete an ambassador configuration

        Args:
            ambassador_id: The ambassador ID to delete
            deleted_by: Username of deleter

        Returns:
            Tuple of (success, message)
        """
        config_path = self._get_config_path(ambassador_id)

        if not os.path.exists(config_path):
            return False, f"Ambassador '{ambassador_id}' not found"

        try:
            # Archive before deleting
            config = self.get_ambassador(ambassador_id)
            if config:
                archive_path = os.path.join(
                    self.storage_path,
                    "archived",
                    f"{ambassador_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                )
                os.makedirs(os.path.dirname(archive_path), exist_ok=True)

                config["_metadata"]["deleted_at"] = datetime.utcnow().isoformat()
                config["_metadata"]["deleted_by"] = deleted_by

                with open(archive_path, 'w') as f:
                    json.dump(config, f, indent=2)

            # Delete the active configuration
            os.remove(config_path)

            return True, "Ambassador deleted successfully"

        except Exception as e:
            return False, f"Error deleting ambassador: {str(e)}"

    def list_ambassadors(
        self,
        filter_type: str = None,
        search: str = None
    ) -> List[Dict]:
        """
        List all ambassadors with optional filtering

        Args:
            filter_type: Filter by world type
            search: Search in name/description

        Returns:
            List of ambassador summary dicts
        """
        ambassadors = []

        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json') and not filename.startswith('_'):
                ambassador_id = filename.replace('.json', '')
                config = self.get_ambassador(ambassador_id)

                if config:
                    ambassador = config["ambassador"]

                    # Apply filters
                    if filter_type and ambassador["world"]["type"] != filter_type:
                        continue

                    if search:
                        search_lower = search.lower()
                        name_match = search_lower in ambassador["name"].lower()
                        desc_match = search_lower in ambassador.get("description", "").lower()
                        id_match = search_lower in ambassador["id"].lower()

                        if not (name_match or desc_match or id_match):
                            continue

                    # Create summary
                    ambassadors.append({
                        "id": ambassador["id"],
                        "name": ambassador["name"],
                        "description": ambassador.get("description", ""),
                        "avatar": ambassador["avatar"],
                        "world_type": ambassador["world"]["type"],
                        "version": config.get("_metadata", {}).get("version", 1),
                        "updated_at": config.get("_metadata", {}).get("updated_at"),
                        "created_at": config.get("_metadata", {}).get("created_at")
                    })

        # Sort by updated date (newest first)
        ambassadors.sort(
            key=lambda x: x.get("updated_at", ""),
            reverse=True
        )

        return ambassadors

    def get_ambassador_versions(self, ambassador_id: str) -> List[Dict]:
        """
        Get version history for an ambassador

        Args:
            ambassador_id: The ambassador ID

        Returns:
            List of version info dicts
        """
        versions = []
        version_dir = os.path.join(self.versions_path, ambassador_id)

        if not os.path.exists(version_dir):
            return versions

        for filename in os.listdir(version_dir):
            if filename.endswith('.json'):
                version_path = os.path.join(version_dir, filename)
                try:
                    with open(version_path, 'r') as f:
                        config = json.load(f)

                    metadata = config.get("_metadata", {})
                    versions.append({
                        "version": metadata.get("version", 0),
                        "updated_at": metadata.get("updated_at"),
                        "updated_by": metadata.get("updated_by"),
                        "change_notes": metadata.get("change_notes", "")
                    })
                except Exception as e:
                    print(f"Error loading version {filename}: {e}")

        versions.sort(key=lambda x: x["version"], reverse=True)
        return versions

    def restore_version(
        self,
        ambassador_id: str,
        version: int,
        restored_by: str = "system"
    ) -> Tuple[bool, str]:
        """
        Restore an ambassador to a previous version

        Args:
            ambassador_id: The ambassador ID
            version: Version number to restore
            restored_by: Username of restorer

        Returns:
            Tuple of (success, message)
        """
        version_path = os.path.join(
            self.versions_path,
            ambassador_id,
            f"v{version}.json"
        )

        if not os.path.exists(version_path):
            return False, f"Version {version} not found"

        try:
            with open(version_path, 'r') as f:
                config = json.load(f)

            # Update with restore info
            success, message = self.update_ambassador(
                ambassador_id,
                config,
                restored_by,
                f"Restored to version {version}"
            )

            return success, message

        except Exception as e:
            return False, f"Error restoring version: {str(e)}"

    def export_ambassadors(self, ambassador_ids: List[str] = None) -> Dict:
        """
        Export ambassadors to a single JSON file for backup/migration

        Args:
            ambassador_ids: List of specific IDs to export, or None for all

        Returns:
            Dict containing all ambassador configurations
        """
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "ambassadors": []
        }

        if ambassador_ids is None:
            # Export all
            ambassador_ids = [
                f.replace('.json', '')
                for f in os.listdir(self.storage_path)
                if f.endswith('.json') and not f.startswith('_')
            ]

        for ambassador_id in ambassador_ids:
            config = self.get_ambassador(ambassador_id)
            if config:
                export_data["ambassadors"].append(config)

        return export_data

    def import_ambassadors(
        self,
        import_data: Dict,
        imported_by: str = "system",
        overwrite: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Import ambassadors from export data

        Args:
            import_data: Export data dict
            imported_by: Username of importer
            overwrite: Whether to overwrite existing ambassadors

        Returns:
            Tuple of (success_count, failure_count, error_messages)
        """
        success_count = 0
        failure_count = 0
        errors = []

        for config in import_data.get("ambassadors", []):
            ambassador_id = config["ambassador"]["id"]

            # Check if exists
            exists = self.get_ambassador(ambassador_id) is not None

            if exists and not overwrite:
                errors.append(f"Ambassador '{ambassador_id}' already exists (skipped)")
                failure_count += 1
                continue

            # Import/Update
            if exists:
                success, message = self.update_ambassador(
                    ambassador_id,
                    config,
                    imported_by,
                    "Imported from bulk import"
                )
            else:
                success, message, _ = self.create_ambassador(config, imported_by)

            if success:
                success_count += 1
            else:
                failure_count += 1
                errors.append(f"{ambassador_id}: {message}")

        return success_count, failure_count, errors

    def _get_config_path(self, ambassador_id: str) -> str:
        """Get file path for ambassador configuration"""
        return os.path.join(self.storage_path, f"{ambassador_id}.json")

    def _save_version(
        self,
        ambassador_id: str,
        config: Dict,
        version: int,
        notes: str
    ):
        """Save a version backup of ambassador configuration"""
        version_dir = os.path.join(self.versions_path, ambassador_id)
        os.makedirs(version_dir, exist_ok=True)

        version_path = os.path.join(version_dir, f"v{version}.json")

        try:
            with open(version_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving version backup: {e}")

    def deploy_to_azure(
        self,
        ambassador_id: str,
        storage_manager=None
    ) -> Tuple[bool, str]:
        """
        Deploy ambassador configuration to Azure File Storage

        Args:
            ambassador_id: The ambassador ID to deploy
            storage_manager: AzureFileStorageManager instance

        Returns:
            Tuple of (success, message)
        """
        if storage_manager is None:
            return False, "Azure storage manager not provided"

        config = self.get_ambassador(ambassador_id)
        if not config:
            return False, f"Ambassador '{ambassador_id}' not found"

        try:
            # Deploy to Azure File Storage
            # Store in ambassadors/ directory
            file_path = f"ambassadors/{ambassador_id}.json"

            storage_manager.write_file(
                file_path,
                json.dumps(config, indent=2)
            )

            return True, "Ambassador deployed to Azure successfully"

        except Exception as e:
            return False, f"Error deploying to Azure: {str(e)}"
