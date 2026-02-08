# -*- coding: utf-8 -*-
from __future__ import annotations

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Libraries
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Optional, Dict, Any, Callable, TypeVar
from pathlib import Path
import tempfile
import shutil
import os

T = TypeVar("T")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Snapshot Manager
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SnapshotManager:
    """General-purpose snapshot manager with atomic write support.

    Supports any serialization format via pluggable serializer/deserializer.

    Usage:
        # With msgpack
        import msgpack
        snap = SnapshotManager(
            path=Path("/var/lib/myapp/snapshot.msgpack"),
            serializer=lambda data: msgpack.packb(data, use_bin_type=True),
            deserializer=lambda raw: msgpack.unpackb(raw, raw=False)
        )

        # With JSON
        import json
        snap = SnapshotManager(
            path=Path("/var/lib/myapp/snapshot.json"),
            serializer=lambda data: json.dumps(data).encode("utf-8"),
            deserializer=lambda raw: json.loads(raw.decode("utf-8"))
        )

        # With pickle
        import pickle
        snap = SnapshotManager(
            path=Path("/var/lib/myapp/snapshot.pkl"),
            serializer=pickle.dumps,
            deserializer=pickle.loads
        )

        # Save
        snap.save({"key": "value", "count": 123})

        # Load
        data = snap.load()
    """

    def __init__(self,
                 path: Path,
                 serializer: Callable[[Any], bytes],
                 deserializer: Callable[[bytes], Any],
                 tmp_prefix: Optional[str] = None):
        """Initialize snapshot manager.

        Args:
            path: Path to snapshot file
            serializer: Function to convert data to bytes
            deserializer: Function to convert bytes to data
            tmp_prefix: Prefix for temporary files (default: ".snap.")
        """
        self._path = Path(path)
        self._serializer = serializer
        self._deserializer = deserializer
        self._tmp_prefix = tmp_prefix or ".snap."
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def save(self, data: Any) -> bool:
        """Save data to snapshot file with atomic write.

        Uses write-to-temp + rename pattern to ensure atomicity.
        Includes fsync for durability.

        Args:
            data: Data to serialize and save

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = self._serializer(data)
            fd, tmp_path = tempfile.mkstemp(dir=self._path.parent,
                                            prefix=self._tmp_prefix,
                                            suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as file:
                    file.write(serialized)
                    file.flush()
                    os.fsync(file.fileno())
                shutil.move(tmp_path, self._path)
                return True
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
        except Exception:
            return False

    def load(self, default: T = None) -> Any:
        """Load data from snapshot file.

        Args:
            default: Value to return if file doesn't exist or load fails

        Returns:
            Deserialized data or default value
        """
        self._cleanup_temp_files()

        if not self._path.exists():
            return default

        try:
            with self._path.open("rb") as file:
                raw = file.read()
            return self._deserializer(raw)
        except Exception:
            return default

    def delete(self) -> bool:
        """Delete snapshot file and cleanup temp files.

        Returns:
            True if file was deleted, False if it didn't exist
        """
        self._cleanup_temp_files()

        if not self._path.exists():
            return False
        try:
            self._path.unlink()
            return True
        except OSError:
            return False

    def exists(self) -> bool:
        """Check if snapshot file exists."""
        return self._path.exists()

    def _cleanup_temp_files(self) -> int:
        """Remove orphaned temporary files.

        Returns:
            Number of temp files deleted
        """
        count = 0
        pattern = f"{self._tmp_prefix}*.tmp"
        for tmp_file in self._path.parent.glob(pattern):
            try:
                tmp_file.unlink()
                count += 1
            except OSError:
                pass
        return count


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Convenience Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_msgpack_snapshot(path: Path, tmp_prefix: Optional[str] = None) -> SnapshotManager:
    """Create a SnapshotManager with msgpack serialization.

    Args:
        path: Path to snapshot file
        tmp_prefix: Prefix for temporary files

    Returns:
        Configured SnapshotManager instance
    """
    import msgpack
    return SnapshotManager(
        path=path,
        serializer=lambda data: msgpack.packb(data, use_bin_type=True),
        deserializer=lambda raw: msgpack.unpackb(raw, raw=False),
        tmp_prefix=tmp_prefix
    )


def create_json_snapshot(path: Path, tmp_prefix: Optional[str] = None) -> SnapshotManager:
    """Create a SnapshotManager with JSON serialization.

    Args:
        path: Path to snapshot file
        tmp_prefix: Prefix for temporary files

    Returns:
        Configured SnapshotManager instance
    """
    import json
    return SnapshotManager(
        path=path,
        serializer=lambda data: json.dumps(data, ensure_ascii=False).encode("utf-8"),
        deserializer=lambda raw: json.loads(raw.decode("utf-8")),
        tmp_prefix=tmp_prefix
    )


def create_pickle_snapshot(path: Path, tmp_prefix: Optional[str] = None) -> SnapshotManager:
    """Create a SnapshotManager with pickle serialization.

    Args:
        path: Path to snapshot file
        tmp_prefix: Prefix for temporary files

    Returns:
        Configured SnapshotManager instance
    """
    import pickle
    return SnapshotManager(
        path=path,
        serializer=pickle.dumps,
        deserializer=pickle.loads,
        tmp_prefix=tmp_prefix
    )
