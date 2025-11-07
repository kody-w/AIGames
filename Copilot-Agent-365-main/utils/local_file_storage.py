"""
Local File Storage Manager - Offline/Edge Mode
Provides local filesystem storage for agents, memories, and data
No internet or cloud dependencies required
"""
import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class LocalFileStorageManager:
    """
    Local file storage manager for offline/edge deployment.
    Stores all data on local filesystem - no cloud required.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize local storage manager.

        Args:
            base_path: Base directory for storage. Defaults to ~/.copilot-agent-local
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Default to user's home directory
            self.base_path = Path.home() / '.copilot-agent-local'

        self.base_path.mkdir(parents=True, exist_ok=True)

        # Directory structure
        self.shared_memory_path = "shared_memories"
        self.default_file_name = 'memory.json'
        self.current_guid = None
        self.current_memory_path = self.shared_memory_path

        logger.info(f"🏠 Local storage initialized at: {self.base_path}")
        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        """Create default directory structure for offline operation."""
        dirs = [
            self.shared_memory_path,
            'agents',           # Local agent storage
            'multi_agents',     # Multi-agent configurations
            'demos',            # Demo scenarios
            'agent_config',     # Agent configurations
            'memory',           # User-specific memories
            'logs',             # Local logs
            'cache'             # Local cache for faster operations
        ]

        for dir_name in dirs:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create default shared memory file
        memory_file = self.base_path / self.shared_memory_path / self.default_file_name
        if not memory_file.exists():
            memory_file.write_text('{}')
            logger.info(f"✓ Created default memory file: {memory_file}")

    def set_memory_context(self, guid: Optional[str] = None) -> bool:
        """
        Set the memory context for user-specific or shared memory.

        Args:
            guid: User GUID for user-specific memory, None for shared

        Returns:
            True if context was set successfully
        """
        if not guid:
            self.current_guid = None
            self.current_memory_path = self.shared_memory_path
            logger.info("📝 Memory context: SHARED")
            return True

        # Validate GUID format
        import re
        guid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )

        if not guid_pattern.match(guid):
            logger.warning(f"⚠️  Invalid GUID format: {guid}. Using shared memory.")
            self.current_guid = None
            self.current_memory_path = self.shared_memory_path
            return False

        # Create GUID-specific directory
        guid_dir = self.base_path / 'memory' / guid
        guid_dir.mkdir(parents=True, exist_ok=True)

        # Create user memory file if it doesn't exist
        user_memory_file = guid_dir / 'user_memory.json'
        if not user_memory_file.exists():
            user_memory_file.write_text('{}')
            logger.info(f"✓ Created user memory for: {guid}")

        self.current_guid = guid
        self.current_memory_path = f"memory/{guid}"
        logger.info(f"📝 Memory context: USER {guid[:8]}...")
        return True

    def read_file(self, directory: str, filename: str) -> Optional[str]:
        """
        Read file from local storage.

        Args:
            directory: Directory path relative to base
            filename: Filename to read

        Returns:
            File contents as string, None if not found
        """
        try:
            file_path = self.base_path / directory / filename
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                logger.debug(f"📖 Read: {directory}/{filename}")
                return content
            else:
                logger.debug(f"📭 Not found: {directory}/{filename}")
                return None
        except Exception as e:
            logger.error(f"❌ Error reading {directory}/{filename}: {e}")
            return None

    def write_file(self, directory: str, filename: str, content: str) -> bool:
        """
        Write file to local storage.

        Args:
            directory: Directory path relative to base
            filename: Filename to write
            content: Content to write

        Returns:
            True if successful
        """
        try:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)

            file_path = dir_path / filename
            file_path.write_text(content, encoding='utf-8')
            logger.debug(f"💾 Wrote: {directory}/{filename}")
            return True
        except Exception as e:
            logger.error(f"❌ Error writing {directory}/{filename}: {e}")
            return False

    def list_files(self, directory: str) -> List[Any]:
        """
        List files in directory.

        Args:
            directory: Directory path relative to base

        Returns:
            List of file objects with 'name' attribute
        """
        try:
            dir_path = self.base_path / directory
            if not dir_path.exists():
                logger.debug(f"📭 Directory not found: {directory}")
                return []

            # Return file objects with name attribute (Azure SDK compatible)
            class FileItem:
                def __init__(self, name: str):
                    self.name = name

            files = [FileItem(f.name) for f in dir_path.iterdir() if f.is_file()]
            logger.debug(f"📂 Listed {len(files)} files in {directory}")
            return files
        except Exception as e:
            logger.error(f"❌ Error listing files in {directory}: {e}")
            return []

    def delete_file(self, directory: str, filename: str) -> bool:
        """
        Delete file from local storage.

        Args:
            directory: Directory path relative to base
            filename: Filename to delete

        Returns:
            True if successful
        """
        try:
            file_path = self.base_path / directory / filename
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"🗑️  Deleted: {directory}/{filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting {directory}/{filename}: {e}")
            return False

    def ensure_directory_exists(self, directory: str) -> bool:
        """
        Ensure directory exists in local storage.

        Args:
            directory: Directory path relative to base

        Returns:
            True if successful
        """
        try:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"❌ Error creating directory {directory}: {e}")
            return False

    def read_json(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Read JSON from current memory context.

        Args:
            filename: Optional filename, defaults to memory.json

        Returns:
            Parsed JSON dict
        """
        if filename is None:
            filename = self.default_file_name

        try:
            if self.current_guid:
                file_path = self.base_path / 'memory' / self.current_guid / 'user_memory.json'
            else:
                file_path = self.base_path / self.shared_memory_path / filename

            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                data = json.loads(content) if content else {}
                logger.debug(f"📖 Read JSON: {file_path.name}")
                return data
            return {}
        except Exception as e:
            logger.error(f"❌ Error reading JSON: {e}")
            return {}

    def write_json(self, data: Dict[str, Any], filename: Optional[str] = None) -> bool:
        """
        Write JSON to current memory context.

        Args:
            data: Data to write as JSON
            filename: Optional filename, defaults to memory.json

        Returns:
            True if successful
        """
        if filename is None:
            filename = self.default_file_name

        try:
            if self.current_guid:
                file_path = self.base_path / 'memory' / self.current_guid / 'user_memory.json'
            else:
                file_path = self.base_path / self.shared_memory_path / filename

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
            logger.debug(f"💾 Wrote JSON: {file_path.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error writing JSON: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for monitoring edge device capacity.

        Returns:
            Dict with storage statistics
        """
        try:
            total_size = 0
            file_count = 0

            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
                    file_count += 1

            return {
                'base_path': str(self.base_path),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'directories': list(os.listdir(self.base_path))
            }
        except Exception as e:
            logger.error(f"❌ Error getting storage stats: {e}")
            return {}
