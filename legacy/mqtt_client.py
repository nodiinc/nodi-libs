# -*- coding: utf-8 -*-
from __future__ import annotations

# Import standard libraries
from typing import Optional, Callable, Any, List, Dict, Deque
from dataclasses import dataclass
from collections import deque
from enum import Enum
from queue import Queue, Full
import ssl
import threading
import time
import os

# Import third-party libraries
from paho.mqtt import client as paho_mqtt
from paho.mqtt.enums import CallbackAPIVersion, MQTTProtocolVersion
from paho.mqtt.reasoncodes import ReasonCode

# Import local application modules
from nodi_spb.package.backoff import Backoff, BackoffStrategy, create_backoff


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Transport Type
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MqttTransportType(Enum):
    TCP = "tcp"
    WEBSOCKETS = "websockets"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Result
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class MqttResult:
    ok: bool
    rc: int = 0
    mid: Optional[int] = None
    error: Optional[Exception] = None
    message: Optional[str] = None

    def __bool__(self) -> bool:
        return self.ok


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass(frozen=True)
class AuthConfig:
    username: str
    password: Optional[str] = None


@dataclass(frozen=True)
class TlsConfig:
    ca_certs: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    key_password: Optional[str] = None
    tls_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2
    cert_reqs: ssl.VerifyMode = ssl.VerifyMode.CERT_REQUIRED
    ciphers: Optional[str] = None
    alpn_protocols: Optional[tuple] = None
    tls_insecure: bool = False


@dataclass(frozen=True)
class WebsocketConfig:
    path: str = "/mqtt"
    headers: Optional[tuple] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Client
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MqttClient:

    def __init__(self,
                 client_id: str,
                 host: str = "localhost",
                 port: int = 1883,
                 keepalive: int = 60,
                 transport: MqttTransportType = MqttTransportType.TCP,
                 clean_start: bool = True,
                 protocol_version: MQTTProtocolVersion = MQTTProtocolVersion.MQTTv5,
                 callback_api_version: CallbackAPIVersion = CallbackAPIVersion.VERSION2,
                 reconnect_min_delay: float = 1.0,
                 reconnect_max_delay: float = 30.0,
                 callback_queue_max_size: int = 10000,
                 callback_worker_count: Optional[int] = None):

        # Connection settings
        self._client_id = client_id
        self._host = host
        self._port = port
        self._keepalive = keepalive
        self._transport = transport
        self._clean_start = clean_start
        self._protocol_version = protocol_version
        self._callback_api_version = callback_api_version

        # Reconnection settings
        self._reconnect_min_delay = reconnect_min_delay
        self._reconnect_max_delay = reconnect_max_delay

        # History settings
        self._record_history = False
        self._history_max_size = 100

        # Security config (stored for cloning)
        self._auth_config: Optional[AuthConfig] = None
        self._tls_config: Optional[TlsConfig] = None
        self._ws_config: Optional[WebsocketConfig] = None

        # Connection state
        self._is_connected: bool = False
        self._running: bool = False
        self._lock = threading.RLock()
        self._connect_event = threading.Event()

        # Supervisor
        self._supervisor_enabled: bool = False
        self._supervisor_thread: Optional[threading.Thread] = None
        self._supervisor_interval: float = 5.0
        self._supervisor_backoff: Optional[Backoff] = None
        self._supervisor_stop_event = threading.Event()

        # Callbacks
        self._on_connect_callback: Optional[Callable] = None
        self._on_disconnect_callback: Optional[Callable] = None
        self._on_message_callback: Optional[Callable] = None
        self._on_publish_callback: Optional[Callable] = None
        self._on_subscribe_callback: Optional[Callable] = None
        self._on_unsubscribe_callback: Optional[Callable] = None
        self._on_error_callback: Optional[Callable] = None

        # Callback worker queue (for non-blocking message processing)
        self._callback_queue_max_size: int = callback_queue_max_size
        self._callback_queue: Queue = Queue(maxsize=self._callback_queue_max_size)
        self._callback_workers: List[threading.Thread] = []
        if callback_worker_count is not None:
            self._callback_worker_count: int = callback_worker_count
        else:
            self._callback_worker_count: int = max(1, (os.cpu_count() or 2) // 2)
        self._callback_worker_running: bool = False

        # History (deque for O(1) append/pop)
        self._history: Dict[str, Deque[Dict[str, Any]]] = {
            "publish": deque(maxlen=self._history_max_size),
            "subscribe": deque(maxlen=self._history_max_size),
            "unsubscribe": deque(maxlen=self._history_max_size),
            "connect": deque(maxlen=self._history_max_size),
            "disconnect": deque(maxlen=self._history_max_size),
            "errors": deque(maxlen=self._history_max_size)
        }

        # MQTT Client
        self._mqtt_client = paho_mqtt.Client(callback_api_version=self._callback_api_version,
                                             client_id=self._client_id,
                                             protocol=self._protocol_version,
                                             transport=self._transport.value)

        # Set internal callbacks
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.on_publish = self._on_publish
        self._mqtt_client.on_subscribe = self._on_subscribe
        self._mqtt_client.on_unsubscribe = self._on_unsubscribe

        # Apply default reconnect settings
        self._mqtt_client.reconnect_delay_set(min_delay=self._reconnect_min_delay,
                                              max_delay=self._reconnect_max_delay)

    # ────────────────────────────────────────────────────────────
    # Setup Methods
    # ────────────────────────────────────────────────────────────

    def setup_auth(self,
                   username: str,
                   password: Optional[str] = None) -> None:
        self._auth_config = AuthConfig(username=username,
                                       password=password)
        self._mqtt_client.username_pw_set(username=username,
                                          password=password)

    def setup_tls(self,
                  ca_certs: Optional[str] = None,
                  cert_file: Optional[str] = None,
                  key_file: Optional[str] = None,
                  key_password: Optional[str] = None,
                  tls_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2,
                  cert_reqs: ssl.VerifyMode = ssl.VerifyMode.CERT_REQUIRED,
                  ciphers: Optional[str] = None,
                  alpn_protocols: Optional[List[str]] = None,
                  tls_insecure: bool = False) -> None:
        if cert_file and not key_file:
            raise ValueError("key_file is required when cert_file is provided")
        if key_file and not cert_file:
            raise ValueError("cert_file is required when key_file is provided")

        # Store config (convert list to tuple for hashability)
        alpn_tuple = tuple(alpn_protocols) if alpn_protocols else None
        self._tls_config = TlsConfig(ca_certs=ca_certs,
                                     cert_file=cert_file,
                                     key_file=key_file,
                                     key_password=key_password,
                                     tls_version=tls_version,
                                     cert_reqs=cert_reqs,
                                     ciphers=ciphers,
                                     alpn_protocols=alpn_tuple,
                                     tls_insecure=tls_insecure)

        self._mqtt_client.tls_set(ca_certs=ca_certs,
                                  certfile=cert_file,
                                  keyfile=key_file,
                                  keyfile_password=key_password,
                                  cert_reqs=cert_reqs,
                                  tls_version=tls_version,
                                  ciphers=ciphers,
                                  alpn_protocols=alpn_protocols)

        if tls_insecure:
            self._mqtt_client.tls_insecure_set(True)

        if self._port == 1883:
            self._port = 8883

    def setup_websocket(self,
                        path: str = "/mqtt",
                        headers: Optional[dict] = None) -> None:
        # Store config (convert dict to tuple for hashability)
        headers_tuple = tuple(headers.items()) if headers else None
        self._ws_config = WebsocketConfig(path=path,
                                          headers=headers_tuple)
        if self._transport == MqttTransportType.WEBSOCKETS:
            self._mqtt_client.ws_set_options(path=path,
                                             headers=headers)

    # ────────────────────────────────────────────────────────────
    # History
    # ────────────────────────────────────────────────────────────

    def enable_history(self, max_size: int = 100) -> None:
        self._record_history = True
        if self._history_max_size != max_size:
            self._history_max_size = max_size
            # Recreate deques with new maxlen, preserving existing data
            for key in self._history:
                self._history[key] = deque(self._history[key], maxlen=max_size)

    def disable_history(self) -> None:
        self._record_history = False

    def _add_history(self, category: str, data: Dict[str, Any]) -> None:
        if not self._record_history:
            return
        data["timestamp"] = time.time()
        self._history[category].append(data)

    def get_history(self, category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        if category:
            return {category: list(self._history.get(category, deque()))}
        return {k: list(v) for k, v in self._history.items()}

    def clear_history(self) -> None:
        for key in self._history:
            self._history[key].clear()

    # ────────────────────────────────────────────────────────────
    # Properties
    # ────────────────────────────────────────────────────────────

    @property
    def client_id(self) -> str:
        return self._client_id

    @client_id.setter
    def client_id(self, value: str) -> None:
        if self._running:
            raise RuntimeError("Cannot change client_id while running")
        self._client_id = value
        self._mqtt_client._client_id = value.encode('utf-8')

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def mqtt_client(self) -> paho_mqtt.Client:
        return self._mqtt_client

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._is_connected

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def endpoint(self) -> str:
        if self._transport == MqttTransportType.WEBSOCKETS:
            protocol = "wss" if self._tls_config else "ws"
            ws_path = self._ws_config.path if self._ws_config else "/mqtt"
            return f"{protocol}://{self._host}:{self._port}{ws_path}"
        return f"{self._host}:{self._port}"

    @property
    def has_auth(self) -> bool:
        return self._auth_config is not None

    @property
    def has_tls(self) -> bool:
        return self._tls_config is not None

    @property
    def auth_config(self) -> Optional[AuthConfig]:
        return self._auth_config

    @property
    def tls_config(self) -> Optional[TlsConfig]:
        return self._tls_config

    @property
    def ws_config(self) -> Optional[WebsocketConfig]:
        return self._ws_config

    @property
    def is_supervisor_enabled(self) -> bool:
        return self._supervisor_enabled

    @property
    def is_supervisor_running(self) -> bool:
        return (self._supervisor_thread is not None and
                self._supervisor_thread.is_alive())

    # ────────────────────────────────────────────────────────────
    # Internal Callbacks
    # ────────────────────────────────────────────────────────────

    def _on_connect(self, client: paho_mqtt.Client, userdata: Any,
                    flags: dict, reason_code: ReasonCode, properties: Any = None):
        with self._lock:
            if not reason_code.is_failure:
                self._is_connected = True
            else:
                self._is_connected = False
            self._connect_event.set()

        self._add_history("connect", {"success": not reason_code.is_failure,
                                      "reason_code": str(reason_code),
                                      "endpoint": self.endpoint})

        if self._on_connect_callback:
            try:
                self._on_connect_callback(client, userdata, flags, reason_code, properties)
            except Exception as exc:
                self._add_history("errors", {"callback": "on_connect", "error": str(exc)})

    def _on_disconnect(self, client: paho_mqtt.Client, userdata: Any,
                       disconnect_flags: dict, reason_code: ReasonCode, properties: Any = None):
        with self._lock:
            self._is_connected = False
            self._connect_event.clear()

        self._add_history("disconnect", {"reason_code": str(reason_code),
                                         "endpoint": self.endpoint})

        if self._on_disconnect_callback:
            try:
                self._on_disconnect_callback(client, userdata, disconnect_flags, reason_code, properties)
            except Exception as exc:
                self._add_history("errors", {"callback": "on_disconnect", "error": str(exc)})

    def _on_message(self, client: paho_mqtt.Client, userdata: Any, message: Any):
        if self._on_message_callback:
            # Offload to worker queue for non-blocking MQTT thread
            try:
                self._callback_queue.put_nowait((self._on_message_callback,
                                                 (client, userdata, message)))
            except Full:
                self._add_history("errors", {"operation": "message_queue",
                                             "error": "queue_full",
                                             "topic": message.topic})

    def _on_publish(self, client: paho_mqtt.Client, userdata: Any, mid: int,
                    reason_code: ReasonCode = None, properties: Any = None):
        if self._on_publish_callback:
            try:
                self._on_publish_callback(client, userdata, mid, reason_code, properties)
            except Exception as exc:
                self._add_history("errors", {"callback": "on_publish", "error": str(exc)})

    def _on_subscribe(self, client: paho_mqtt.Client, userdata: Any, mid: int,
                      reason_codes: list, properties: Any = None):
        if self._on_subscribe_callback:
            try:
                self._on_subscribe_callback(client, userdata, mid, reason_codes, properties)
            except Exception as exc:
                self._add_history("errors", {"callback": "on_subscribe", "error": str(exc)})

    def _on_unsubscribe(self, client: paho_mqtt.Client, userdata: Any, mid: int,
                        reason_codes: list = None, properties: Any = None):
        if self._on_unsubscribe_callback:
            try:
                self._on_unsubscribe_callback(client, userdata, mid, reason_codes, properties)
            except Exception as exc:
                self._add_history("errors", {"callback": "on_unsubscribe", "error": str(exc)})

    # ────────────────────────────────────────────────────────────
    # Callback Setters (method style)
    # ────────────────────────────────────────────────────────────

    def set_on_connect(self, callback: Callable) -> None:
        self._on_connect_callback = callback

    def set_on_disconnect(self, callback: Callable) -> None:
        self._on_disconnect_callback = callback

    def set_on_message(self, callback: Callable) -> None:
        self._on_message_callback = callback

    def set_on_publish(self, callback: Callable) -> None:
        self._on_publish_callback = callback

    def set_on_subscribe(self, callback: Callable) -> None:
        self._on_subscribe_callback = callback

    def set_on_unsubscribe(self, callback: Callable) -> None:
        self._on_unsubscribe_callback = callback

    # ────────────────────────────────────────────────────────────
    # Callback Decorators
    # ────────────────────────────────────────────────────────────

    def on_connect(self, func: Callable) -> Callable:
        self._on_connect_callback = func
        return func

    def on_disconnect(self, func: Callable) -> Callable:
        self._on_disconnect_callback = func
        return func

    def on_message(self, func: Callable) -> Callable:
        self._on_message_callback = func
        return func

    def on_publish(self, func: Callable) -> Callable:
        self._on_publish_callback = func
        return func

    def on_subscribe(self, func: Callable) -> Callable:
        self._on_subscribe_callback = func
        return func

    def on_unsubscribe(self, func: Callable) -> Callable:
        self._on_unsubscribe_callback = func
        return func

    def on_error(self, func: Callable) -> Callable:
        self._on_error_callback = func
        return func

    # ────────────────────────────────────────────────────────────
    # Error Handler
    # ────────────────────────────────────────────────────────────

    def set_on_error(self, callback: Callable[[str, Exception], None]) -> None:
        self._on_error_callback = callback

    def _invoke_error_callback(self, operation: str, error: Exception) -> None:
        if self._on_error_callback:
            try:
                self._on_error_callback(operation, error)
            except Exception:
                pass  # Silently ignore callback errors

    # ────────────────────────────────────────────────────────────
    # Callback Worker Queue
    # ────────────────────────────────────────────────────────────

    def _callback_worker_loop(self) -> None:
        while self._callback_worker_running:
            try:
                item = self._callback_queue.get(timeout=1.0)
                if item is None:
                    break
                callback, args = item
                callback(*args)
            except Exception as exc:
                if self._callback_worker_running:
                    self._invoke_error_callback("callback_worker", exc)

    def _start_callback_workers(self) -> None:
        if self._callback_worker_running:
            return
        self._callback_worker_running = True
        for i in range(self._callback_worker_count):
            t = threading.Thread(target=self._callback_worker_loop,
                                 daemon=True,
                                 name=f"BrokerCallbackWorker-{i}")
            t.start()
            self._callback_workers.append(t)

    def _stop_callback_workers(self) -> None:
        self._callback_worker_running = False
        # Send poison pills to wake up workers
        for _ in self._callback_workers:
            self._callback_queue.put(None)
        # Wait for workers to finish
        for t in self._callback_workers:
            t.join(timeout=2.0)
        self._callback_workers.clear()

    # ────────────────────────────────────────────────────────────
    # Will Message (LWT)
    # ────────────────────────────────────────────────────────────

    def set_will(self,
                 topic: str,
                 payload: bytes,
                 qos: int = 0,
                 retain: bool = False) -> None:
        self._mqtt_client.will_set(topic, payload, qos, retain)

    def clear_will(self) -> None:
        self._mqtt_client.will_clear()

    # ────────────────────────────────────────────────────────────
    # Supervisor
    # ────────────────────────────────────────────────────────────

    def _supervisor_loop(self) -> None:
        while self._running and self._supervisor_enabled:
            # Use Event.wait() instead of time.sleep() for immediate wake-up on stop
            if self._supervisor_stop_event.wait(timeout=self._supervisor_interval):
                break

            if not self._running or not self._supervisor_enabled:
                break

            with self._lock:
                is_connected = self._is_connected

            if is_connected:
                # Reset backoff on successful connection
                if self._supervisor_backoff:
                    self._supervisor_backoff.reset()
                continue

            try:
                self._mqtt_client.reconnect()
                # NOTE: Do NOT call loop_start() here.
                # loop_start() should only be called once during initial connect.
                # reconnect() reuses the existing network thread.
                if self._supervisor_backoff:
                    self._supervisor_backoff.reset()
            except Exception as exc:
                self._add_history("errors", {"supervisor": "reconnect_failed",
                                             "error": str(exc)})
                self._invoke_error_callback("supervisor_reconnect", exc)

                # Apply backoff
                if self._supervisor_backoff:
                    delay = self._supervisor_backoff.next_delay()
                    if self._supervisor_stop_event.wait(timeout=delay):
                        break

    def _start_supervisor_thread(self) -> None:
        if self._supervisor_thread is None or not self._supervisor_thread.is_alive():
            self._supervisor_stop_event.clear()
            self._supervisor_thread = threading.Thread(target=self._supervisor_loop,
                                                       daemon=True,
                                                       name="BrokerSupervisor")
            self._supervisor_thread.start()

    def _stop_supervisor_thread(self) -> None:
        if self._supervisor_thread is not None and self._supervisor_thread.is_alive():
            self._supervisor_stop_event.set()
            self._supervisor_thread.join(timeout=self._supervisor_interval + 1.0)
        self._supervisor_thread = None

    def enable_supervisor(self,
                          interval: float = 5.0,
                          min_delay: float = 1.0,
                          max_delay: float = 30.0,
                          backoff_strategy: BackoffStrategy = BackoffStrategy.FIBONACCI,
                          backoff_jitter: bool = True) -> None:
        self._supervisor_enabled = True
        self._supervisor_interval = interval
        self._supervisor_backoff = create_backoff(backoff_strategy,
                                                  min_delay,
                                                  max_delay,
                                                  backoff_jitter)
        if self._running:
            self._start_supervisor_thread()

    def disable_supervisor(self) -> None:
        self._supervisor_enabled = False
        self._stop_supervisor_thread()

    # ────────────────────────────────────────────────────────────
    # Lifecycle: start / stop
    # ────────────────────────────────────────────────────────────

    def start(self,
              blocking: bool = False,
              timeout: float = 10.0,
              retry: bool = False,
              retry_interval: float = 5.0,
              max_retries: int = 0) -> MqttResult:
        with self._lock:
            if self._running:
                return MqttResult(ok=True, message="Already running")
            self._running = True
            self._connect_event.clear()

        # Start callback workers for non-blocking message processing
        self._start_callback_workers()

        result = self._connect_internal(blocking=blocking,
                                        timeout=timeout,
                                        retry=retry,
                                        retry_interval=retry_interval,
                                        max_retries=max_retries)

        if result.ok and self._supervisor_enabled:
            self._start_supervisor_thread()

        return result

    def stop(self) -> MqttResult:
        with self._lock:
            if not self._running:
                return MqttResult(ok=True, message="Already stopped")
            self._running = False

        # Stop supervisor thread first
        self._stop_supervisor_thread()

        # Disconnect and stop the network loop
        result = self._disconnect_internal(stop_loop=True)

        # Stop callback workers after disconnect
        self._stop_callback_workers()

        if result.ok:
            return MqttResult(ok=True, message="Stopped successfully")
        return result

    # ────────────────────────────────────────────────────────────
    # Connection Methods
    # ────────────────────────────────────────────────────────────

    def _connect_internal(self,
                          blocking: bool = False,
                          timeout: float = 10.0,
                          retry: bool = False,
                          retry_interval: float = 5.0,
                          max_retries: int = 0) -> MqttResult:
        # WARNING: blocking=True runs loop_forever() which blocks the calling thread.
        # Not recommended for Sparkplug nodes. Use for CLI tools or simple scripts only.
        attempt = 0
        last_error: Optional[str] = None

        while True:
            attempt += 1

            try:
                self._connect_event.clear()
                self._mqtt_client.connect(host=self._host,
                                          port=self._port,
                                          keepalive=self._keepalive,
                                          clean_start=self._clean_start)

                if blocking:
                    self._mqtt_client.loop_forever()
                    with self._lock:
                        return MqttResult(ok=self._is_connected,
                                          message="Blocking loop ended")

                self._mqtt_client.loop_start()

                if self._connect_event.wait(timeout):
                    with self._lock:
                        if self._is_connected:
                            return MqttResult(ok=True, message="Connected")
                        last_error = "Connection rejected by broker"
                else:
                    last_error = f"Connection timeout after {timeout}s"

            except Exception as exc:
                last_error = f"Connection error: {exc}"
                self._add_history("errors", {"operation": "connect", "error": str(exc)})
                if not retry:
                    return MqttResult(ok=False, error=exc, message=last_error)

            # Exit conditions for retry loop
            if not retry:
                return MqttResult(ok=False, message=last_error)

            if not self._running:
                return MqttResult(ok=False, message="Stopped during connection retry")

            if max_retries > 0 and attempt >= max_retries:
                return MqttResult(ok=False,
                                  message=f"Max retries ({max_retries}) exceeded: {last_error}")

            time.sleep(retry_interval)

    def _disconnect_internal(self, stop_loop: bool = False) -> MqttResult:
        try:
            self._mqtt_client.disconnect()

            # Only stop the network loop when fully stopping the client
            # For reconnect scenarios, the loop should remain active
            if stop_loop:
                self._mqtt_client.loop_stop()

            with self._lock:
                self._is_connected = False
                self._connect_event.clear()

            return MqttResult(ok=True, message="Disconnected")

        except Exception as exc:
            self._add_history("errors", {"operation": "disconnect", "error": str(exc)})
            return MqttResult(ok=False, error=exc, message=str(exc))

    def connect(self,
                blocking: bool = False,
                timeout: float = 10.0,
                retry: bool = False,
                retry_interval: float = 5.0,
                max_retries: int = 0) -> MqttResult:
        with self._lock:
            if self._is_connected:
                return MqttResult(ok=True, message="Already connected")
            if not self._running:
                self._running = True

        return self._connect_internal(blocking=blocking,
                                      timeout=timeout,
                                      retry=retry,
                                      retry_interval=retry_interval,
                                      max_retries=max_retries)

    def disconnect(self) -> MqttResult:
        with self._lock:
            if not self._is_connected:
                return MqttResult(ok=True, message="Not connected")

        return self._disconnect_internal()

    def reconnect(self, timeout: float = 10.0) -> MqttResult:
        # Full reconnect: stop loop and restart completely
        # This is required because paho-mqtt's disconnect() destroys the socket,
        # making fast reconnect impossible after user-initiated disconnect.
        # For automatic reconnection (broker-side disconnect), use supervisor instead.
        self._disconnect_internal(stop_loop=True)
        return self._connect_internal(timeout=timeout)

    # ────────────────────────────────────────────────────────────
    # Pub/Sub Methods
    # ────────────────────────────────────────────────────────────

    def publish(self,
                topic: str,
                payload: Any = None,
                qos: int = 0,
                retain: bool = False,
                auto_reconnect: bool = False) -> MqttResult:
        # NOTE: auto_reconnect does NOT restore previous subscriptions.
        # Upper layer (e.g. Sparkplug node) must handle re-subscription after reconnect.
        # _is_connected read is atomic for Python bool, no lock needed for performance
        if not self._is_connected:
            if auto_reconnect:
                reconnect_result = self.reconnect()
                if not reconnect_result.ok:
                    return MqttResult(ok=False,
                                      message=f"Auto-reconnect failed: {reconnect_result.message}")
            else:
                return MqttResult(ok=False, message="Not connected")

        try:
            result = self._mqtt_client.publish(topic, payload, qos, retain)
            if result.rc == paho_mqtt.MQTT_ERR_SUCCESS:
                self._add_history("publish", {"topic": topic,
                                              "qos": qos,
                                              "retain": retain,
                                              "mid": result.mid})
                return MqttResult(ok=True, rc=result.rc, mid=result.mid)
            else:
                return MqttResult(ok=False, rc=result.rc, message=f"Publish failed: rc={result.rc}")

        except Exception as exc:
            self._add_history("errors", {"operation": "publish", "topic": topic, "error": str(exc)})
            return MqttResult(ok=False, error=exc, message=str(exc))

    def subscribe(self,
                  topic: str,
                  qos: int = 0,
                  auto_reconnect: bool = False) -> MqttResult:
        # _is_connected read is atomic for Python bool, no lock needed for performance
        if not self._is_connected:
            if auto_reconnect:
                reconnect_result = self.reconnect()
                if not reconnect_result.ok:
                    return MqttResult(ok=False,
                                      message=f"Auto-reconnect failed: {reconnect_result.message}")
            else:
                return MqttResult(ok=False, message="Not connected")

        try:
            result, mid = self._mqtt_client.subscribe(topic, qos)
            if result == paho_mqtt.MQTT_ERR_SUCCESS:
                self._add_history("subscribe", {"topic": topic, "qos": qos, "mid": mid})
                return MqttResult(ok=True, rc=result, mid=mid)
            else:
                return MqttResult(ok=False, rc=result, message=f"Subscribe failed: rc={result}")

        except Exception as exc:
            self._add_history("errors", {"operation": "subscribe", "topic": topic, "error": str(exc)})
            return MqttResult(ok=False, error=exc, message=str(exc))

    def unsubscribe(self, topic: str, auto_reconnect: bool = False) -> MqttResult:
        # _is_connected read is atomic for Python bool, no lock needed for performance
        if not self._is_connected:
            if auto_reconnect:
                reconnect_result = self.reconnect()
                if not reconnect_result.ok:
                    return MqttResult(ok=False,
                                      message=f"Auto-reconnect failed: {reconnect_result.message}")
            else:
                return MqttResult(ok=False, message="Not connected")

        try:
            result, mid = self._mqtt_client.unsubscribe(topic)
            if result == paho_mqtt.MQTT_ERR_SUCCESS:
                self._add_history("unsubscribe", {"topic": topic, "mid": mid})
                return MqttResult(ok=True, rc=result, mid=mid)
            else:
                return MqttResult(ok=False, rc=result, message=f"Unsubscribe failed: rc={result}")

        except Exception as exc:
            self._add_history("errors", {"operation": "unsubscribe", "topic": topic, "error": str(exc)})
            return MqttResult(ok=False, error=exc, message=str(exc))
