# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Types
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OtaStatus(Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    BACKING_UP = "backing_up"
    INSTALLING = "installing"
    RESTARTING = "restarting"
    HEALTH_CHECK = "health_check"
    ROLLING_BACK = "rolling_back"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class OtaResult:
    success: bool
    status: OtaStatus
    version: Optional[str] = None
    previous_version: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "version": self.version,
            "previous_version": self.previous_version,
            "error": self.error,
            "timestamp": self.timestamp
        }


@dataclass
class OtaConfig:
    backup_dir: Path = field(default_factory=lambda: Path("/home/nodi/nodi-edge-data/backup/ota"))
    download_dir: Path = field(default_factory=lambda: Path("/tmp/nodi-ota"))
    max_backup_count: int = 3
    download_timeout_sec: int = 300
    install_timeout_sec: int = 600
    health_check_retries: int = 3
    health_check_interval_sec: int = 10
    python_path: str = "/root/venv/bin/python3"
    pip_path: str = "/root/venv/bin/pip"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OtaManager
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OtaManager:

    def __init__(self,
                 config: Optional[OtaConfig] = None,
                 on_status_change: Optional[Callable[[OtaStatus], None]] = None) -> None:
        self._config = config or OtaConfig()
        self._on_status_change = on_status_change
        self._status: OtaStatus = OtaStatus.IDLE
        self._current_version: Optional[str] = None
        self._target_version: Optional[str] = None

        # Ensure directories exist
        self._config.backup_dir.mkdir(parents=True, exist_ok=True)
        self._config.download_dir.mkdir(parents=True, exist_ok=True)

    # ────────────────────────────────────────────────────────────
    # Properties
    # ────────────────────────────────────────────────────────────

    @property
    def status(self) -> OtaStatus:
        return self._status

    @property
    def current_version(self) -> Optional[str]:
        return self._current_version

    # ────────────────────────────────────────────────────────────
    # Public Methods
    # ────────────────────────────────────────────────────────────

    def execute_update(self,
                       url: str,
                       checksum: str,
                       version: str,
                       package_name: str = "nodi-edge",
                       services: Optional[List[str]] = None) -> OtaResult:
        if self._status != OtaStatus.IDLE:
            return OtaResult(success=False,
                             status=self._status,
                             error=f"update already in progress: {self._status.value}")

        self._target_version = version
        services = services or ["ne-launcher", "ne-monitor"]
        download_path: Optional[Path] = None
        backup_path: Optional[Path] = None

        try:
            # 1. Download
            self._set_status(OtaStatus.DOWNLOADING)
            download_path = self._download_package(url)

            # 2. Verify
            self._set_status(OtaStatus.VERIFYING)
            if not self._verify_checksum(download_path, checksum):
                raise OtaError("checksum mismatch")

            # 3. Backup
            self._set_status(OtaStatus.BACKING_UP)
            backup_path = self._backup_current(package_name)
            self._current_version = self._get_installed_version(package_name)

            # 4. Install
            self._set_status(OtaStatus.INSTALLING)
            self._install_package(download_path)

            # 5. Restart services
            self._set_status(OtaStatus.RESTARTING)
            self._restart_services(services)

            # 6. Health check
            self._set_status(OtaStatus.HEALTH_CHECK)
            if not self._health_check(services):
                raise OtaError("health check failed")

            # Success
            self._set_status(OtaStatus.SUCCESS)
            self._cleanup_old_backups()

            return OtaResult(success=True,
                             status=OtaStatus.SUCCESS,
                             version=version,
                             previous_version=self._current_version)

        except Exception as exc:
            # Rollback
            self._set_status(OtaStatus.ROLLING_BACK)
            rollback_error = None
            if backup_path and backup_path.exists():
                try:
                    self._rollback(backup_path)
                    self._restart_services(services)
                except Exception as rb_exc:
                    rollback_error = str(rb_exc)

            self._set_status(OtaStatus.FAILED)
            error_msg = str(exc)
            if rollback_error:
                error_msg += f"; rollback error: {rollback_error}"

            return OtaResult(success=False,
                             status=OtaStatus.FAILED,
                             version=version,
                             previous_version=self._current_version,
                             error=error_msg)

        finally:
            # Cleanup download
            if download_path and download_path.exists():
                try:
                    download_path.unlink()
                except Exception:
                    pass
            self._set_status(OtaStatus.IDLE)

    def rollback_to_previous(self,
                             package_name: str = "nodi-edge",
                             services: Optional[List[str]] = None) -> OtaResult:
        if self._status != OtaStatus.IDLE:
            return OtaResult(success=False,
                             status=self._status,
                             error=f"operation in progress: {self._status.value}")

        services = services or ["ne-launcher", "ne-monitor"]
        backups = self._list_backups(package_name)
        if not backups:
            return OtaResult(success=False,
                             status=OtaStatus.FAILED,
                             error="no backup available")

        latest_backup = backups[0]
        try:
            self._set_status(OtaStatus.ROLLING_BACK)
            self._rollback(latest_backup)
            self._restart_services(services)
            self._set_status(OtaStatus.SUCCESS)

            return OtaResult(success=True,
                             status=OtaStatus.SUCCESS,
                             version=self._extract_version_from_backup(latest_backup))

        except Exception as exc:
            self._set_status(OtaStatus.FAILED)
            return OtaResult(success=False,
                             status=OtaStatus.FAILED,
                             error=str(exc))

        finally:
            self._set_status(OtaStatus.IDLE)

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self._status.value,
            "current_version": self._current_version,
            "target_version": self._target_version,
            "backups": [str(p) for p in self._list_backups()]
        }

    # ────────────────────────────────────────────────────────────
    # Private Methods - Download
    # ────────────────────────────────────────────────────────────

    def _download_package(self, url: str) -> Path:
        filename = url.split("/")[-1]
        download_path = self._config.download_dir / filename

        try:
            with urlopen(url, timeout=self._config.download_timeout_sec) as response:
                with open(download_path, "wb") as f:
                    shutil.copyfileobj(response, f)
            return download_path
        except URLError as exc:
            raise OtaError(f"download failed: {exc}")

    def _verify_checksum(self, file_path: Path, expected: str) -> bool:
        # expected format: "sha256:abc123..." or just "abc123..."
        if ":" in expected:
            algo, expected_hash = expected.split(":", 1)
        else:
            algo, expected_hash = "sha256", expected

        hash_func = hashlib.new(algo)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        actual_hash = hash_func.hexdigest()
        return actual_hash.lower() == expected_hash.lower()

    # ────────────────────────────────────────────────────────────
    # Private Methods - Backup
    # ────────────────────────────────────────────────────────────

    def _backup_current(self, package_name: str) -> Path:
        version = self._get_installed_version(package_name) or "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{package_name}-{version}-{timestamp}.tar.gz"
        backup_path = self._config.backup_dir / backup_name

        # Get package location
        pkg_location = self._get_package_location(package_name)
        if not pkg_location:
            raise OtaError(f"package not found: {package_name}")

        # Create tarball
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(pkg_location, arcname=package_name)

        return backup_path

    def _list_backups(self, package_name: str = "nodi-edge") -> List[Path]:
        pattern = f"{package_name}-*.tar.gz"
        backups = sorted(self._config.backup_dir.glob(pattern),
                         key=lambda p: p.stat().st_mtime,
                         reverse=True)
        return backups

    def _cleanup_old_backups(self, package_name: str = "nodi-edge") -> None:
        backups = self._list_backups(package_name)
        for backup in backups[self._config.max_backup_count:]:
            try:
                backup.unlink()
            except Exception:
                pass

    def _extract_version_from_backup(self, backup_path: Path) -> Optional[str]:
        # Format: package_name-version-timestamp.tar.gz
        name = backup_path.stem.replace(".tar", "")
        parts = name.split("-")
        if len(parts) >= 2:
            return parts[1]
        return None

    # ────────────────────────────────────────────────────────────
    # Private Methods - Install
    # ────────────────────────────────────────────────────────────

    def _install_package(self, package_path: Path) -> None:
        cmd = [self._config.pip_path, "install", "--upgrade", str(package_path)]
        try:
            result = subprocess.run(cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=self._config.install_timeout_sec)
            if result.returncode != 0:
                raise OtaError(f"pip install failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise OtaError("pip install timeout")

    def _rollback(self, backup_path: Path) -> None:
        # Extract to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(tmpdir)

            # Find extracted package
            extracted = list(Path(tmpdir).iterdir())
            if not extracted:
                raise OtaError("backup archive is empty")

            # Install from extracted directory
            pkg_dir = extracted[0]
            cmd = [self._config.pip_path, "install", "--upgrade", str(pkg_dir)]
            result = subprocess.run(cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=self._config.install_timeout_sec)
            if result.returncode != 0:
                raise OtaError(f"rollback install failed: {result.stderr}")

    # ────────────────────────────────────────────────────────────
    # Private Methods - Service Management
    # ────────────────────────────────────────────────────────────

    def _restart_services(self, services: List[str]) -> None:
        for service in services:
            cmd = ["sudo", "systemctl", "restart", service]
            try:
                subprocess.run(cmd, capture_output=True, timeout=30)
            except Exception:
                pass  # Best effort

    def _health_check(self, services: List[str]) -> bool:
        for _ in range(self._config.health_check_retries):
            time.sleep(self._config.health_check_interval_sec)
            all_healthy = True
            for service in services:
                if not self._is_service_active(service):
                    all_healthy = False
                    break
            if all_healthy:
                return True
        return False

    def _is_service_active(self, service: str) -> bool:
        cmd = ["sudo", "systemctl", "is-active", "--quiet", service]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    # ────────────────────────────────────────────────────────────
    # Private Methods - Utils
    # ────────────────────────────────────────────────────────────

    def _set_status(self, status: OtaStatus) -> None:
        self._status = status
        if self._on_status_change:
            try:
                self._on_status_change(status)
            except Exception:
                pass

    def _get_installed_version(self, package_name: str) -> Optional[str]:
        cmd = [self._config.pip_path, "show", package_name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return None

    def _get_package_location(self, package_name: str) -> Optional[Path]:
        cmd = [self._config.pip_path, "show", package_name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Location:"):
                        base = Path(line.split(":", 1)[1].strip())
                        pkg_path = base / package_name.replace("-", "_")
                        if pkg_path.exists():
                            return pkg_path
        except Exception:
            pass
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Exceptions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OtaError(Exception):
    pass
