"""
Recovery Module for AI Ambassador Platform

Provides point-in-time recovery, selective restoration,
full system restoration, and data validation capabilities.

Features:
- Point-in-time recovery
- Selective restoration (specific ambassadors, users)
- Full system restoration
- Data validation on restore
- Rollback capability
- Recovery verification
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from azure_file_storage_manager import AzureFileStorageManager
from backup import BackupManager, BackupEncryption

logger = logging.getLogger(__name__)


class RecoveryManager:
    """Manage recovery operations for AI Ambassador Platform"""

    def __init__(
        self,
        storage_manager: Optional[AzureFileStorageManager] = None,
        backup_manager: Optional[BackupManager] = None
    ):
        """
        Initialize recovery manager

        Args:
            storage_manager: Azure File Storage manager instance
            backup_manager: BackupManager instance
        """
        self.storage = storage_manager or AzureFileStorageManager()
        self.backup_manager = backup_manager or BackupManager(self.storage)
        self.encryption = BackupEncryption()

    def _validate_backup_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate backup data structure

        Args:
            data: Backup data to validate

        Returns:
            Validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # Check for required structure
            if not isinstance(data, dict):
                validation_results['valid'] = False
                validation_results['errors'].append("Backup data is not a dictionary")
                return validation_results

            # Validate each target
            for target, target_data in data.items():
                if not isinstance(target_data, dict):
                    validation_results['warnings'].append(f"Target {target} is not a dictionary")
                    continue

                # Check for required fields
                if 'path' not in target_data:
                    validation_results['warnings'].append(f"Target {target} missing 'path' field")

                if 'files' not in target_data:
                    validation_results['warnings'].append(f"Target {target} missing 'files' field")

                # Validate files structure
                files = target_data.get('files', {})
                if not isinstance(files, dict):
                    validation_results['warnings'].append(f"Target {target} files is not a dictionary")

            return validation_results

        except Exception as e:
            logger.error(f"Error validating backup data: {str(e)}")
            validation_results['valid'] = False
            validation_results['errors'].append(str(e))
            return validation_results

    def _load_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt backup data

        Args:
            backup_id: Backup identifier

        Returns:
            Backup data or None if failed
        """
        try:
            # Load metadata
            metadata_path = f"backups/metadata/{backup_id}.json"
            metadata = self.storage.read_json(metadata_path)

            if not metadata:
                logger.error(f"Backup metadata not found: {backup_id}")
                return None

            # Determine backup type and path
            backup_type = metadata.get('backup_type', 'full')
            backup_path = f"backups/{backup_type}/{backup_id}/backup.dat"

            # Read encrypted backup file
            encrypted_data = self.storage.read_file(backup_path)

            if not encrypted_data:
                logger.error(f"Backup file not found: {backup_path}")
                return None

            # Decrypt
            compressed_data = self.encryption.decrypt(encrypted_data)

            # Decompress
            decompressed_data = self.backup_manager._decompress_data(compressed_data)

            # Parse JSON
            backup_data = json.loads(decompressed_data.decode('utf-8'))

            return backup_data

        except Exception as e:
            logger.error(f"Error loading backup {backup_id}: {str(e)}")
            return None

    async def restore_full(
        self,
        backup_id: str,
        validate_before: bool = True,
        create_snapshot: bool = True
    ) -> Dict[str, Any]:
        """
        Restore full system from backup

        Args:
            backup_id: Backup identifier
            validate_before: Validate backup before restoring
            create_snapshot: Create snapshot of current state before restore

        Returns:
            Restoration results
        """
        logger.info(f"Starting full restoration from backup: {backup_id}")

        results = {
            'backup_id': backup_id,
            'success': False,
            'restored_targets': [],
            'failed_targets': [],
            'snapshot_id': None,
            'validation': None,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # Verify backup integrity
            verification = self.backup_manager.verify_backup(backup_id)
            if not verification.get('valid'):
                results['validation'] = verification
                logger.error(f"Backup verification failed: {verification.get('error')}")
                return results

            # Create snapshot of current state
            if create_snapshot:
                snapshot_id = f"pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                logger.info(f"Creating pre-restore snapshot: {snapshot_id}")
                snapshot_metadata = await self.backup_manager.create_full_backup(backup_id=snapshot_id)
                results['snapshot_id'] = snapshot_id

            # Load backup data
            backup_data = self._load_backup(backup_id)

            if not backup_data:
                results['error'] = "Failed to load backup data"
                return results

            # Validate backup data
            if validate_before:
                validation = self._validate_backup_data(backup_data)
                results['validation'] = validation

                if not validation['valid']:
                    logger.error("Backup data validation failed")
                    return results

            # Restore each target
            for target, target_data in backup_data.items():
                try:
                    await self._restore_target(target, target_data)
                    results['restored_targets'].append(target)
                    logger.info(f"Restored target: {target}")
                except Exception as e:
                    logger.error(f"Failed to restore target {target}: {str(e)}")
                    results['failed_targets'].append({
                        'target': target,
                        'error': str(e)
                    })

            # Check if restoration was successful
            results['success'] = len(results['failed_targets']) == 0

            logger.info(f"Full restoration completed: {results['success']}")

            return results

        except Exception as e:
            logger.error(f"Error during full restoration: {str(e)}")
            results['error'] = str(e)
            return results

    async def _restore_target(self, target: str, target_data: Dict[str, Any]):
        """
        Restore a specific target

        Args:
            target: Target name
            target_data: Target data to restore
        """
        files = target_data.get('files', {})

        for file_path, file_data in files.items():
            # Write file data back to storage
            self.storage.write_json(file_path, file_data)

    async def restore_selective(
        self,
        backup_id: str,
        targets: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Restore specific targets or filtered data

        Args:
            backup_id: Backup identifier
            targets: List of targets to restore (e.g., ['ambassadors', 'user_memories'])
            filters: Optional filters (e.g., {'user_guid': 'abc123', 'ambassador_id': 'xyz'})

        Returns:
            Restoration results
        """
        logger.info(f"Starting selective restoration from backup: {backup_id}")

        results = {
            'backup_id': backup_id,
            'success': False,
            'restored_targets': [],
            'failed_targets': [],
            'filters': filters,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # Load backup data
            backup_data = self._load_backup(backup_id)

            if not backup_data:
                results['error'] = "Failed to load backup data"
                return results

            # Restore only specified targets
            for target in targets:
                if target not in backup_data:
                    results['failed_targets'].append({
                        'target': target,
                        'error': 'Target not found in backup'
                    })
                    continue

                try:
                    target_data = backup_data[target]

                    # Apply filters if provided
                    if filters:
                        target_data = self._apply_filters(target_data, filters)

                    await self._restore_target(target, target_data)
                    results['restored_targets'].append(target)
                    logger.info(f"Restored target: {target}")

                except Exception as e:
                    logger.error(f"Failed to restore target {target}: {str(e)}")
                    results['failed_targets'].append({
                        'target': target,
                        'error': str(e)
                    })

            results['success'] = len(results['failed_targets']) == 0

            logger.info(f"Selective restoration completed: {results['success']}")

            return results

        except Exception as e:
            logger.error(f"Error during selective restoration: {str(e)}")
            results['error'] = str(e)
            return results

    def _apply_filters(
        self,
        target_data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply filters to target data

        Args:
            target_data: Target data
            filters: Filters to apply

        Returns:
            Filtered target data
        """
        filtered_data = {
            'path': target_data.get('path'),
            'files': {},
            'file_count': 0
        }

        files = target_data.get('files', {})

        # Apply filters based on file content or path
        for file_path, file_data in files.items():
            include = True

            # Filter by user_guid
            if 'user_guid' in filters:
                if filters['user_guid'] not in file_path:
                    include = False

            # Filter by ambassador_id
            if 'ambassador_id' in filters:
                if isinstance(file_data, dict) and file_data.get('ambassador_id') != filters['ambassador_id']:
                    include = False

            # Filter by date range
            if 'start_date' in filters or 'end_date' in filters:
                # Extract date from file data or path
                # This is simplified - implement proper date extraction
                include = True

            if include:
                filtered_data['files'][file_path] = file_data

        filtered_data['file_count'] = len(filtered_data['files'])

        return filtered_data

    async def restore_point_in_time(
        self,
        target_datetime: datetime,
        targets: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Restore data to a specific point in time

        Args:
            target_datetime: Target datetime to restore to
            targets: Optional list of specific targets to restore

        Returns:
            Restoration results
        """
        logger.info(f"Starting point-in-time restoration to: {target_datetime.isoformat()}")

        results = {
            'target_datetime': target_datetime.isoformat(),
            'success': False,
            'backup_used': None,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # Find closest backup before target datetime
            backup_id = self._find_closest_backup(target_datetime)

            if not backup_id:
                results['error'] = "No suitable backup found"
                return results

            results['backup_used'] = backup_id

            # Restore from backup
            if targets:
                restore_results = await self.restore_selective(backup_id, targets)
            else:
                restore_results = await self.restore_full(backup_id)

            results.update(restore_results)

            logger.info(f"Point-in-time restoration completed")

            return results

        except Exception as e:
            logger.error(f"Error during point-in-time restoration: {str(e)}")
            results['error'] = str(e)
            return results

    def _find_closest_backup(self, target_datetime: datetime) -> Optional[str]:
        """
        Find the closest backup before target datetime

        Args:
            target_datetime: Target datetime

        Returns:
            Backup ID or None
        """
        try:
            # Get all backups
            backups = self.backup_manager.list_backups()

            # Filter backups before target datetime
            valid_backups = []
            for backup in backups:
                timestamp_str = backup.get('timestamp')
                if timestamp_str:
                    backup_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if backup_time <= target_datetime:
                        valid_backups.append(backup)

            # Sort by timestamp descending
            valid_backups.sort(
                key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')),
                reverse=True
            )

            # Return most recent backup before target
            if valid_backups:
                return valid_backups[0]['backup_id']

            return None

        except Exception as e:
            logger.error(f"Error finding closest backup: {str(e)}")
            return None

    async def rollback_restoration(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Rollback to a snapshot (undo restoration)

        Args:
            snapshot_id: Snapshot backup ID

        Returns:
            Rollback results
        """
        logger.info(f"Rolling back to snapshot: {snapshot_id}")

        return await self.restore_full(
            backup_id=snapshot_id,
            validate_before=True,
            create_snapshot=False  # Don't create snapshot of snapshot
        )

    async def verify_restoration(
        self,
        backup_id: str,
        sample_size: int = 10
    ) -> Dict[str, Any]:
        """
        Verify that restoration was successful

        Args:
            backup_id: Backup ID that was restored
            sample_size: Number of items to sample for verification

        Returns:
            Verification results
        """
        logger.info(f"Verifying restoration from backup: {backup_id}")

        results = {
            'backup_id': backup_id,
            'verified': False,
            'samples_checked': 0,
            'samples_passed': 0,
            'samples_failed': 0,
            'errors': []
        }

        try:
            # Load backup data
            backup_data = self._load_backup(backup_id)

            if not backup_data:
                results['errors'].append("Failed to load backup data")
                return results

            # Sample files from backup
            sampled_files = self._sample_files(backup_data, sample_size)

            # Verify each sampled file
            for file_path, expected_data in sampled_files:
                results['samples_checked'] += 1

                try:
                    # Read current data
                    current_data = self.storage.read_json(file_path)

                    # Compare
                    if current_data == expected_data:
                        results['samples_passed'] += 1
                    else:
                        results['samples_failed'] += 1
                        results['errors'].append({
                            'file': file_path,
                            'error': 'Data mismatch'
                        })

                except Exception as e:
                    results['samples_failed'] += 1
                    results['errors'].append({
                        'file': file_path,
                        'error': str(e)
                    })

            # Verification passes if all samples match
            results['verified'] = results['samples_failed'] == 0

            logger.info(f"Restoration verification completed: {results['verified']}")

            return results

        except Exception as e:
            logger.error(f"Error verifying restoration: {str(e)}")
            results['errors'].append(str(e))
            return results

    def _sample_files(
        self,
        backup_data: Dict[str, Any],
        sample_size: int
    ) -> List[tuple]:
        """
        Sample files from backup data for verification

        Args:
            backup_data: Backup data
            sample_size: Number of files to sample

        Returns:
            List of (file_path, file_data) tuples
        """
        samples = []

        for target, target_data in backup_data.items():
            files = target_data.get('files', {})

            # Sample files from this target
            file_items = list(files.items())
            target_sample_size = min(sample_size, len(file_items))

            for i in range(target_sample_size):
                samples.append(file_items[i])

            if len(samples) >= sample_size:
                break

        return samples[:sample_size]


class RecoveryValidator:
    """Validate recovery operations"""

    def __init__(self, storage_manager: Optional[AzureFileStorageManager] = None):
        """
        Initialize recovery validator

        Args:
            storage_manager: Azure File Storage manager instance
        """
        self.storage = storage_manager or AzureFileStorageManager()

    def validate_data_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data integrity after restoration

        Args:
            data: Data to validate

        Returns:
            Validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Validate structure
        if not isinstance(data, dict):
            results['valid'] = False
            results['errors'].append("Data is not a dictionary")
            return results

        # Validate required fields based on data type
        # This is simplified - implement comprehensive validation

        return results

    def validate_ambassador_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ambassador configuration"""
        results = {
            'valid': True,
            'errors': []
        }

        required_fields = ['ambassador', 'id', 'name']
        for field in required_fields:
            if field not in config and field not in config.get('ambassador', {}):
                results['valid'] = False
                results['errors'].append(f"Missing required field: {field}")

        return results

    def validate_user_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user memory data"""
        results = {
            'valid': True,
            'errors': []
        }

        # Validate memory structure
        # This is simplified - implement comprehensive validation

        return results
