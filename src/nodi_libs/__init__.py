# -*- coding: utf-8 -*-
"""nodi-libs: Internal utility libraries collection."""
from __future__ import annotations

__version__ = "0.1.0"

from nodi_libs.sysinfo import SystemInfo, Result
from nodi_libs.fsm import FiniteStateMachine
from nodi_libs.logger import Logger, LoggerConfig, LoggingLevel, TimedRotatingWhen
from nodi_libs.timer import PeriodicTimer
from nodi_libs.ota import OtaManager, OtaConfig, OtaResult, OtaStatus, OtaError
from nodi_libs.backoff import (
    Backoff,
    BackoffStrategy,
    ConstantBackoff,
    ExponentialBackoff,
    FibonacciBackoff,
    LinearBackoff,
    PolynomialBackoff,
    RandomBackoff,
    create_backoff,
)
from nodi_libs.mqtt_client import (
    AuthConfig,
    MqttClient,
    MqttResult,
    MqttTransportType,
    TlsConfig,
    WebsocketConfig,
)

__all__ = [
    # Backoff
    "Backoff",
    "BackoffStrategy",
    "ConstantBackoff",
    "ExponentialBackoff",
    "FibonacciBackoff",
    "LinearBackoff",
    "PolynomialBackoff",
    "RandomBackoff",
    "create_backoff",
    # FSM
    "FiniteStateMachine",
    # Logger
    "Logger",
    "LoggerConfig",
    "LoggingLevel",
    "TimedRotatingWhen",
    # MQTT
    "AuthConfig",
    "MqttClient",
    "MqttResult",
    "MqttTransportType",
    "TlsConfig",
    "WebsocketConfig",
    # OTA
    "OtaConfig",
    "OtaError",
    "OtaManager",
    "OtaResult",
    "OtaStatus",
    # Timer
    "PeriodicTimer",
    # Result
    "Result",
    # SystemInfo
    "SystemInfo",
]
