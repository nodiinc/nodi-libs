# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import platform
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from threading import Thread
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

import psutil


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Types
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    ok: bool
    value: Optional[T]
    error: Optional[str] = None

    @staticmethod
    def success(value: T) -> Result[T]:
        return Result(ok=True, value=value)

    @staticmethod
    def failure(error: str) -> Result[T]:
        return Result(ok=False, value=None, error=error)


# Type aliases
CpuLoadInfo = Dict[str, float]
DiskIoInfo = Dict[str, float]
NetworkIoInfo = Dict[str, float]
TemperatureInfo = Dict[str, Dict[str, Dict[str, Optional[float]]]]
TemperatureStats = Dict[str, Dict[str, float]]
BatteryInfo = Dict[str, Any]
SpeedtestInfo = Dict[str, Any]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KB: int = 1024
MB: int = 1024 ** 2
GB: int = 1024 ** 3
MEGABITS: int = 1_000_000
MEASURE_DECIMAL: int = 3
PERCENT_DECIMAL: int = 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SystemInfo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SystemInfo:

    def __init__(self) -> None:
        self._cpu_usage_result: Optional[float] = None
        self._cpu_measure_thread: Optional[Thread] = None
        self._speedtest_result: Optional[SpeedtestInfo] = None
        self._speedtest_error: Optional[str] = None
        self._speedtest_thread: Optional[Thread] = None
        self._prev_net_io: Optional[Tuple[int, int, int, int]] = None
        self._prev_net_time: Optional[float] = None
        self._prev_disk_io: Optional[Tuple[int, int]] = None
        self._prev_disk_time: Optional[float] = None
        self._temperature_stats: TemperatureStats = {}

    # ────────────────────────────────────────────────────────────
    # Static Info
    # ────────────────────────────────────────────────────────────

    def get_time_zone(self) -> Result[str]:
        try:
            _, non_dst_tm = time.tzname
            return Result.success(non_dst_tm)
        except Exception as exc:
            return Result.failure(str(exc))

    def get_system_os_type(self) -> Result[str]:
        try:
            return Result.success(platform.system())
        except Exception as exc:
            return Result.failure(str(exc))

    def get_system_os_version(self) -> Result[str]:
        try:
            info = platform.freedesktop_os_release()
            version = info.get("VERSION")
            if version is None:
                return Result.failure("VERSION not found in os-release")
            return Result.success(version)
        except Exception as exc:
            return Result.failure(str(exc))

    def get_system_kernel_version(self) -> Result[str]:
        try:
            return Result.success(platform.release())
        except Exception as exc:
            return Result.failure(str(exc))

    def get_cpu_architecture(self) -> Result[str]:
        try:
            return Result.success(platform.machine())
        except Exception as exc:
            return Result.failure(str(exc))

    def get_system_libc_version(self) -> Result[str]:
        try:
            info = platform.libc_ver()
            return Result.success("-".join(info))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_system_python_version(self) -> Result[str]:
        try:
            return Result.success(platform.python_version())
        except Exception as exc:
            return Result.failure(str(exc))

    def get_cpu_model(self) -> Result[str]:
        # Try /proc/cpuinfo first (Linux)
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("model name"):
                        return Result.success(line.split(":")[1].strip())
        except Exception:
            pass
        # Fallback to platform.processor()
        try:
            result = platform.processor()
            if result:
                return Result.success(result)
        except Exception:
            pass
        return Result.failure("cpu model not available")

    def get_cpu_frequency_ghz(self) -> Result[float]:
        try:
            frequency = psutil.cpu_freq()
            if frequency is None:
                return Result.failure("cpu frequency not available")
            return Result.success(round(frequency.max / KB, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_cpu_core_count(self) -> Result[int]:
        try:
            count = psutil.cpu_count()
            if count is None:
                return Result.failure("cpu count not available")
            return Result.success(count)
        except Exception as exc:
            return Result.failure(str(exc))

    def get_memory_total_gb(self) -> Result[float]:
        try:
            memory = psutil.virtual_memory()
            return Result.success(round(memory.total / GB, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_swap_total_gb(self) -> Result[float]:
        try:
            swap = psutil.swap_memory()
            return Result.success(round(swap.total / GB, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_disk_total_gb(self) -> Result[float]:
        try:
            disk = psutil.disk_usage("/")
            return Result.success(round(disk.total / GB, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_time_system_boot_ts(self) -> Result[str]:
        try:
            boot_ts = psutil.boot_time()
            return Result.success(datetime.fromtimestamp(boot_ts).isoformat())
        except Exception as exc:
            return Result.failure(str(exc))

    def get_network_nic_all(self) -> Result[List[str]]:
        try:
            stats = psutil.net_if_stats()
            return Result.success([iface for iface, info in stats.items() if info.isup])
        except Exception as exc:
            return Result.failure(str(exc))

    # ────────────────────────────────────────────────────────────
    # Dynamic Info
    # ────────────────────────────────────────────────────────────

    def get_cpu_usage_percent(self, interval: float = 1.0) -> Result[float]:
        # Start new measurement thread only if previous one finished
        if self._cpu_measure_thread is None or not self._cpu_measure_thread.is_alive():
            def _measure(interval: float) -> None:
                try:
                    self._cpu_usage_result = psutil.cpu_percent(interval=interval)
                except Exception:
                    self._cpu_usage_result = None
            self._cpu_measure_thread = Thread(target=_measure, args=(interval,), daemon=True)
            self._cpu_measure_thread.start()
        if self._cpu_usage_result is None:
            return Result.failure("measurement pending")
        return Result.success(self._cpu_usage_result)

    def get_memory_usage_gb(self) -> Result[float]:
        try:
            memory = psutil.virtual_memory()
            return Result.success(round(memory.used / GB, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_memory_usage_percent(self) -> Result[float]:
        try:
            memory = psutil.virtual_memory()
            return Result.success(round(memory.percent, PERCENT_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_swap_usage_gb(self) -> Result[float]:
        try:
            swap = psutil.swap_memory()
            return Result.success(round(swap.used / GB, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_swap_usage_percent(self) -> Result[float]:
        try:
            swap = psutil.swap_memory()
            return Result.success(round(swap.percent, PERCENT_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_disk_usage_gb(self) -> Result[float]:
        try:
            disk = psutil.disk_usage("/")
            return Result.success(round(disk.used / GB, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_disk_usage_percent(self) -> Result[float]:
        try:
            disk = psutil.disk_usage("/")
            return Result.success(round(disk.percent, PERCENT_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_sensors_temperature(self) -> Result[TemperatureInfo]:
        try:
            data = psutil.sensors_temperatures()
            if not data:
                return Result.failure("no temperature sensors available")
            results: TemperatureInfo = {}
            for board, contents in data.items():
                results[board] = {}
                for entry in contents:
                    label = entry.label if entry.label else "default"
                    results[board][label] = {
                        "curr": entry.current,
                        "high": entry.high,
                        "crit": entry.critical
                    }
            return Result.success(results)
        except Exception as exc:
            return Result.failure(str(exc))

    def get_time_system_uptime_hrs(self) -> Result[float]:
        try:
            boot_ts = psutil.boot_time()
            uptime_sec = time.time() - boot_ts
            return Result.success(round(uptime_sec / 3600, MEASURE_DECIMAL))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_cpu_load_average(self) -> Result[CpuLoadInfo]:
        try:
            load1, load5, load15 = psutil.getloadavg()
            core_count = psutil.cpu_count() or 1
            return Result.success({
                "load_avg_1min": round(load1, MEASURE_DECIMAL),
                "load_avg_5min": round(load5, MEASURE_DECIMAL),
                "load_avg_15min": round(load15, MEASURE_DECIMAL),
                "load_percent_1min": round(load1 / core_count * 100, PERCENT_DECIMAL),
                "load_percent_5min": round(load5 / core_count * 100, PERCENT_DECIMAL),
                "load_percent_15min": round(load15 / core_count * 100, PERCENT_DECIMAL)
            })
        except Exception as exc:
            return Result.failure(str(exc))

    def get_process_count(self) -> Result[int]:
        try:
            return Result.success(len(psutil.pids()))
        except Exception as exc:
            return Result.failure(str(exc))

    def get_thread_count(self) -> Result[int]:
        try:
            total = 0
            for proc in psutil.process_iter(["num_threads"]):
                try:
                    total += proc.info["num_threads"] or 0
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return Result.success(total)
        except Exception as exc:
            return Result.failure(str(exc))

    def get_network_io_speed(self) -> Result[NetworkIoInfo]:
        try:
            net_io = psutil.net_io_counters()
            current_time = time.time()
            current_data = (net_io.bytes_sent, net_io.bytes_recv,
                            net_io.packets_sent, net_io.packets_recv)
            if self._prev_net_io is None or self._prev_net_time is None:
                self._prev_net_io = current_data
                self._prev_net_time = current_time
                return Result.failure("first measurement, waiting for next cycle")
            elapsed = current_time - self._prev_net_time
            if elapsed <= 0:
                return Result.failure("elapsed time is zero or negative")
            prev_sent, prev_recv, prev_pkt_sent, prev_pkt_recv = self._prev_net_io
            send_mbps = (net_io.bytes_sent - prev_sent) / elapsed / MB * 8
            recv_mbps = (net_io.bytes_recv - prev_recv) / elapsed / MB * 8
            send_pps = (net_io.packets_sent - prev_pkt_sent) / elapsed
            recv_pps = (net_io.packets_recv - prev_pkt_recv) / elapsed
            self._prev_net_io = current_data
            self._prev_net_time = current_time
            return Result.success({
                "send_mbps": round(send_mbps, MEASURE_DECIMAL),
                "recv_mbps": round(recv_mbps, MEASURE_DECIMAL),
                "send_pps": round(send_pps, MEASURE_DECIMAL),
                "recv_pps": round(recv_pps, MEASURE_DECIMAL)
            })
        except Exception as exc:
            return Result.failure(str(exc))

    def get_disk_io_speed(self) -> Result[DiskIoInfo]:
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io is None:
                return Result.failure("disk io counters not available")
            current_time = time.time()
            current_data = (disk_io.read_bytes, disk_io.write_bytes)
            if self._prev_disk_io is None or self._prev_disk_time is None:
                self._prev_disk_io = current_data
                self._prev_disk_time = current_time
                return Result.failure("first measurement, waiting for next cycle")
            elapsed = current_time - self._prev_disk_time
            if elapsed <= 0:
                return Result.failure("elapsed time is zero or negative")
            prev_read, prev_write = self._prev_disk_io
            read_mbps = (disk_io.read_bytes - prev_read) / elapsed / MB * 8
            write_mbps = (disk_io.write_bytes - prev_write) / elapsed / MB * 8
            self._prev_disk_io = current_data
            self._prev_disk_time = current_time
            return Result.success({
                "read_mbps": round(read_mbps, MEASURE_DECIMAL),
                "write_mbps": round(write_mbps, MEASURE_DECIMAL)
            })
        except Exception as exc:
            return Result.failure(str(exc))

    def get_battery(self) -> Result[BatteryInfo]:
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return Result.failure("battery not available")
            return Result.success({
                "percent": battery.percent,
                "plugged": battery.power_plugged,
                "secs_left": battery.secsleft if battery.secsleft > 0 else None
            })
        except Exception as exc:
            return Result.failure(str(exc))

    def measure_internet_speed(self) -> None:
        # Start new measurement thread only if previous one finished
        if self._speedtest_thread is not None and self._speedtest_thread.is_alive():
            return
        self._speedtest_error = None
        def _measure() -> None:
            try:
                proc = subprocess.run(
                    ["speedtest", "-f", "json", "--accept-license"],
                    capture_output=True, text=True, timeout=120)
                if proc.returncode != 0:
                    self._speedtest_error = (
                        f"speedtest exit {proc.returncode}: {proc.stderr.strip()}")
                    return
                data = json.loads(proc.stdout)
                download_mbps = data["download"]["bandwidth"] * 8 / MEGABITS
                upload_mbps = data["upload"]["bandwidth"] * 8 / MEGABITS
                self._speedtest_result = {
                    "download_mbps": round(download_mbps, MEASURE_DECIMAL),
                    "upload_mbps": round(upload_mbps, MEASURE_DECIMAL),
                    "measured_ts": datetime.now().isoformat()
                }
                self._speedtest_error = None
            except Exception as exc:
                self._speedtest_error = f"{type(exc).__name__}: {exc}"
        self._speedtest_thread = Thread(target=_measure, daemon=True)
        self._speedtest_thread.start()

    def get_internet_speed(self) -> Result[SpeedtestInfo]:
        # Check if measurement is in progress
        if self._speedtest_thread is not None and self._speedtest_thread.is_alive():
            return Result.failure("speedtest in progress")
        # Check if error occurred
        if self._speedtest_error is not None:
            return Result.failure(self._speedtest_error)
        # Check if result is available
        if self._speedtest_result is None:
            return Result.failure("speedtest not started")
        return Result.success(self._speedtest_result)

    def get_temperature_stats(self) -> Result[TemperatureStats]:
        sensors_result = self.get_sensors_temperature()
        if not sensors_result.ok:
            if self._temperature_stats:
                return Result.success(self._temperature_stats)
            return Result.failure(sensors_result.error or "no temperature data")
        sensors = sensors_result.value
        if sensors is None:
            return Result.failure("no sensor data")
        for device, components in sensors.items():
            temps = [comp["curr"] for comp in components.values() if comp["curr"] is not None]
            if temps:
                mean_temp = sum(temps) / len(temps)
                std_temp = (sum((t - mean_temp) ** 2 for t in temps) / len(temps)) ** 0.5
                self._temperature_stats[device] = {
                    "mean": round(mean_temp, MEASURE_DECIMAL),
                    "std": round(std_temp, MEASURE_DECIMAL)
                }
        return Result.success(self._temperature_stats)
