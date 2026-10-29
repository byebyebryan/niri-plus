"""Invocation-scoped NetworkManager secret agent and Secret Service adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol
import uuid
import time

from .model import PendingRef
from .nm_bus import NMUnavailable, load_nm_modules


NM_SECRET_SCHEMA_NAME = "org.freedesktop.NetworkManager.Connection"
WIFI_SECURITY_SETTING = "802-11-wireless-security"
WIFI_PSK_KEY = "psk"
MAX_SECRET_BYTES = 512
UNREGISTER_TIMEOUT_SECONDS = 1.0


class SecretStoreError(RuntimeError):
    """The configured Secret Service could not fulfill an operation."""


class SecretStore(Protocol):
    def lookup(self, connection_uuid: str, setting_name: str, setting_key: str) -> str | None: ...

    def store(self, connection_uuid: str, setting_name: str, setting_key: str, secret: str) -> None: ...

    def delete(self, connection_uuid: str, setting_name: str, setting_key: str) -> None: ...


class LibsecretStore:
    """The upstream NetworkManager connection schema used by nm-applet."""

    def __init__(self, *, secret_module: object | None = None):
        if secret_module is None:
            secret_module = load_nm_modules().Secret
        self._secret = secret_module
        try:
            self._schema = secret_module.Schema.new(
                NM_SECRET_SCHEMA_NAME,
                secret_module.SchemaFlags.DONT_MATCH_NAME,
                {
                    "connection-uuid": secret_module.SchemaAttributeType.STRING,
                    "setting-name": secret_module.SchemaAttributeType.STRING,
                    "setting-key": secret_module.SchemaAttributeType.STRING,
                },
            )
        except Exception as error:
            raise SecretStoreError("Could not initialize the NetworkManager Secret Service schema") from error

    @staticmethod
    def _attributes(connection_uuid: str, setting_name: str, setting_key: str) -> dict[str, str]:
        if not connection_uuid or not setting_name or not setting_key:
            raise SecretStoreError("Secret identity is incomplete")
        return {
            "connection-uuid": connection_uuid,
            "setting-name": setting_name,
            "setting-key": setting_key,
        }

    def lookup(self, connection_uuid: str, setting_name: str, setting_key: str) -> str | None:
        try:
            return self._secret.password_lookup_sync(
                self._schema,
                self._attributes(connection_uuid, setting_name, setting_key),
                None,
            )
        except Exception as error:
            raise SecretStoreError("Secret Service lookup failed") from error

    def store(self, connection_uuid: str, setting_name: str, setting_key: str, secret: str) -> None:
        if not isinstance(secret, str) or not secret or len(secret.encode("utf-8")) > MAX_SECRET_BYTES:
            raise SecretStoreError("Secret value is empty or exceeds its size limit")
        label = f"NetworkManager {setting_name}/{setting_key}"
        try:
            stored = self._secret.password_store_sync(
                self._schema,
                self._attributes(connection_uuid, setting_name, setting_key),
                None,
                label,
                secret,
                None,
            )
        except Exception as error:
            raise SecretStoreError("Secret Service could not store this credential") from error
        if stored is not True:
            raise SecretStoreError("Secret Service did not confirm storage")

    def delete(self, connection_uuid: str, setting_name: str, setting_key: str) -> None:
        try:
            self._secret.password_clear_sync(
                self._schema,
                self._attributes(connection_uuid, setting_name, setting_key),
                None,
            )
        except Exception as error:
            raise SecretStoreError("Secret Service could not delete this credential") from error


@dataclass(frozen=True, slots=True)
class SecretRequest:
    connection_uuid: str
    connection_path: str
    setting_name: str
    setting_key: str
    secret_flags: int
    request_new: bool


try:
    _MODULES = load_nm_modules()
    _NM = _MODULES.NM
    _GLib = _MODULES.GLib
    _AgentBase = _NM.SecretAgentOld
except NMUnavailable:
    _MODULES = None
    _NM = None
    _GLib = None
    _AgentBase = object


class NetworkSecretAgent(_AgentBase):
    """A one-invocation agent that only serves its pinned Wi-Fi profile.

    The `request_secret` callback records an in-memory pending operation. It
    never receives or serializes the secret itself. The controller later calls
    `provide_secret` with its private byte stream, after which this object
    completes the exact NetworkManager callback that was waiting.
    """

    if _AgentBase is not object:
        __gtype_name__ = "NiriPlusInvocationNetworkSecretAgent"

    def __init__(
        self,
        *,
        identifier: str | None = None,
        dbus_connection: object,
        secret_store: SecretStore,
        expected_uuid: str,
        expected_connection_path: str,
        expected_setting: str = WIFI_SECURITY_SETTING,
        request_secret: Callable[[SecretRequest], PendingRef | None],
        context: object | None = None,
        owns_connection: bool = True,
    ):
        if _AgentBase is object:
            raise NMUnavailable("NetworkManager secret-agent bindings are unavailable")
        self._secret_store = secret_store
        self._expected_uuid = expected_uuid
        self._expected_path = expected_connection_path
        self._expected_setting = expected_setting
        self._request_secret = request_secret
        self._context = context or _GLib.MainContext.new()
        self._dbus_connection = dbus_connection
        self._owns_connection = owns_connection
        self._requests: dict[tuple[str, str], tuple[PendingRef, object, object, object]] = {}
        self._closed = False
        self._initialized = False
        self._registered = False
        self._prompted = False
        self._provided_secret: str | None = None
        unique_identifier = identifier or f"org.niri_plus.rofi.{uuid.uuid4().hex}"
        self._context.push_thread_default()
        try:
            super().__init__(
                identifier=unique_identifier,
                auto_register=False,
                dbus_connection=dbus_connection,
            )
        finally:
            self._context.pop_thread_default()

    @staticmethod
    def new_context_connection(address: str | None = None) -> tuple[object, object]:
        """Create the agent's dedicated connection inside its owned GLib context."""

        modules = load_nm_modules()
        context = modules.GLib.MainContext.new()
        context.push_thread_default()
        try:
            from .nm_bus import dedicated_bus_connection
            connection = dedicated_bus_connection(address=address)
        finally:
            context.pop_thread_default()
        return context, connection

    def register(self, *, timeout: float = 6.0) -> None:
        if self._closed:
            raise NMUnavailable("NetworkManager secret agent is closed")
        if self.get_registered():
            return
        self.initialize(timeout=timeout)
        from .nm_bus import GLibRuntime
        runtime = GLibRuntime(_GLib, context=self._context)
        self._context.push_thread_default()
        try:
            registered = runtime.run_async(
                lambda callback: self.register_async(None, callback, None),
                lambda result: self.register_finish(result),
                timeout=timeout,
            )
        finally:
            self._context.pop_thread_default()
        self._registered = bool(registered)
        if not self._registered:
            raise NMUnavailable("NetworkManager did not accept the secret-agent registration")

    def initialize(self, *, timeout: float = 6.0) -> None:
        """Finish the GAsyncInitable export on this agent's private context."""

        if self._closed:
            raise NMUnavailable("NetworkManager secret agent is closed")
        if self._initialized:
            return
        from .nm_bus import GLibRuntime
        runtime = GLibRuntime(_GLib, context=self._context)
        self._context.push_thread_default()
        try:
            runtime.run_async(
                lambda callback: self.init_async(_GLib.PRIORITY_DEFAULT, None, callback, None),
                lambda result: self.init_finish(result),
                timeout=timeout,
            )
            self._initialized = True
        finally:
            self._context.pop_thread_default()

    def iterate_for(self, milliseconds: int) -> None:
        if self._closed:
            return
        deadline = time.monotonic() + max(0, milliseconds) / 1000
        while time.monotonic() < deadline:
            if self._context.pending():
                self._context.iteration(False)
            else:
                time.sleep(min(0.003, max(0, deadline - time.monotonic())))

    def cancel_pending(self, pending: PendingRef) -> bool:
        for (path, setting), value in tuple(self._requests.items()):
            if value[0] == pending:
                self.do_cancel_get_secrets(path, setting)
                return True
        return False

    @property
    def expected_uuid(self) -> str:
        return self._expected_uuid

    @property
    def expected_connection_path(self) -> str:
        return self._expected_path

    @property
    def has_pending_secret(self) -> bool:
        return bool(self._requests)

    def _error(self, code: object, message: str):
        domain = _NM.secret_agent_error_quark()
        return _GLib.Error.new_literal(domain, message, int(code))

    @staticmethod
    def _identity(connection: object) -> str | None:
        getter = getattr(connection, "get_uuid", None)
        return getter() if callable(getter) else None

    @staticmethod
    def _wifi_security(connection: object):
        getter = getattr(connection, "get_setting_wireless_security", None)
        return getter() if callable(getter) else None

    @staticmethod
    def _flags(setting: object) -> int:
        getter = getattr(setting, "get_psk_flags", None)
        if callable(getter):
            return int(getter())
        getter = getattr(setting, "get_secret_flags", None)
        if callable(getter):
            try:
                result = getter(WIFI_PSK_KEY)
                return int(result[0] if isinstance(result, tuple) else result)
            except Exception:
                return 0
        return 0

    def _return_secret(self, connection: object, secret: str, callback: object, user_data: object) -> None:
        try:
            setting = _NM.SettingWirelessSecurity.new()
            setting.set_property("psk", secret)
            result = _NM.SimpleConnection.new()
            result.add_setting(setting)
            serialized = result.to_dbus(_NM.ConnectionSerializationFlags.WITH_SECRETS)
            callback(self, connection, serialized, None)
        except Exception:
            error = self._error(_NM.SecretAgentError.FAILED, "Could not return the requested credential")
            callback(self, connection, None, error)

    def _return_error(self, connection: object, callback: object, user_data: object, code: object, message: str) -> None:
        error = self._error(code, message)
        callback(self, connection, None, error)

    def do_get_secrets(
        self,
        connection: object,
        connection_path: str,
        setting_name: str,
        hints: object,
        flags: object,
        callback: object,
        user_data: object,
    ) -> None:
        if self._closed:
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.AGENTCANCELED, "Agent is closed")
            return
        if (
            connection_path != self._expected_path
            or setting_name != self._expected_setting
            or self._identity(connection) != self._expected_uuid
        ):
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.NOSECRETS, "Request is outside this invocation")
            return
        setting = self._wifi_security(connection)
        if setting is None:
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.INVALIDCONNECTION, "Wi-Fi security settings are unavailable")
            return
        secret_flags = self._flags(setting)
        request_flags = int(flags)
        request_new = bool(request_flags & int(_NM.SecretAgentGetSecretsFlags.REQUEST_NEW))
        allow_interaction = bool(request_flags & int(_NM.SecretAgentGetSecretsFlags.ALLOW_INTERACTION))
        key = (connection_path, setting_name)
        if key in self._requests:
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.AGENTCANCELED, "A request for this profile is already pending")
            return

        if self._provided_secret is not None:
            provided, self._provided_secret = self._provided_secret, None
            self._return_secret(connection, provided, callback, user_data)
            return

        if secret_flags == int(_NM.SettingSecretFlags.AGENT_OWNED) and not request_new:
            try:
                stored = self._secret_store.lookup(self._expected_uuid, setting_name, WIFI_PSK_KEY)
            except SecretStoreError:
                stored = None
                if not allow_interaction:
                    self._return_error(connection, callback, user_data, _NM.SecretAgentError.FAILED, "Secret Service is unavailable")
                    return
            if stored:
                self._return_secret(connection, stored, callback, user_data)
                return

        if not allow_interaction:
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.NOSECRETS, "No stored credential is available")
            return
        if self._prompted:
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.NOSECRETS, "Credential retry limit reached; start an explicit retry")
            return

        self._prompted = True
        operation = self._request_secret(
            SecretRequest(
                connection_uuid=self._expected_uuid,
                connection_path=connection_path,
                setting_name=setting_name,
                setting_key=WIFI_PSK_KEY,
                secret_flags=secret_flags,
                request_new=request_new,
            )
        )
        if operation is None:
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.NOSECRETS, "The controller is not accepting credential prompts")
            return
        if not isinstance(operation, PendingRef):
            self._return_error(connection, callback, user_data, _NM.SecretAgentError.NOSECRETS, "The controller did not return an owned credential request")
            return
        self._requests[key] = (operation, connection, callback, user_data)

    def prime_secret(self, secret: str, *, secret_flags: int) -> None:
        """Supply one user-entered value to the next exact GetSecrets request."""

        if self._closed or self._provided_secret is not None or self._requests:
            raise NMUnavailable("NetworkManager credential attempt is not available")
        if not secret or len(secret.encode("utf-8")) > MAX_SECRET_BYTES:
            raise NMUnavailable("Credential is empty or exceeds its size limit")
        if secret_flags == int(_NM.SettingSecretFlags.AGENT_OWNED):
            try:
                self._secret_store.store(self._expected_uuid, self._expected_setting, WIFI_PSK_KEY, secret)
            except SecretStoreError as error:
                raise NMUnavailable("Secret Service did not save the requested credential") from error
        # Keep the explicit value available for the matching GetSecrets call.
        # In particular, REQUEST_NEW must bypass the cache while still using
        # this just-entered value for this exact attempt.
        self._provided_secret = secret
        self._prompted = True

    def complete_secret(self, pending: PendingRef, secret: str) -> None:
        if self._closed:
            raise NMUnavailable("NetworkManager secret agent is closed")
        entry = next((item for item in self._requests.values() if item[0] == pending), None)
        if entry is None:
            raise NMUnavailable("Credential request is stale or no longer owned")
        _pending, connection, callback, user_data = entry
        setting = self._wifi_security(connection)
        flags = self._flags(setting)
        if flags == int(_NM.SettingSecretFlags.AGENT_OWNED):
            try:
                self._secret_store.store(self._expected_uuid, self._expected_setting, WIFI_PSK_KEY, secret)
            except SecretStoreError:
                self._drop_pending(pending)
                error = self._error(_NM.SecretAgentError.FAILED, "Secret Service did not save the requested credential")
                callback(self, connection, None, error)
                raise
        self._drop_pending(pending)
        self._return_secret(connection, secret, callback, user_data)

    def _drop_pending(self, pending: PendingRef) -> None:
        for key, value in tuple(self._requests.items()):
            if value[0] == pending:
                del self._requests[key]
                return

    def _save_callback(self, connection: object, callback: object, user_data: object, *, deleting: bool) -> None:
        uuid_value = self._identity(connection)
        setting = self._wifi_security(connection)
        if uuid_value != self._expected_uuid or setting is None:
            error = self._error(_NM.SecretAgentError.INVALIDCONNECTION, "Connection identity is unavailable")
            callback(self, connection, error)
            return
        flags = self._flags(setting)
        if flags != int(_NM.SettingSecretFlags.AGENT_OWNED):
            callback(self, connection, None)
            return
        secret = setting.get_psk()
        try:
            if deleting:
                self._secret_store.delete(uuid_value, WIFI_SECURITY_SETTING, WIFI_PSK_KEY)
            elif secret:
                self._secret_store.store(uuid_value, WIFI_SECURITY_SETTING, WIFI_PSK_KEY, secret)
            else:
                error = self._error(_NM.SecretAgentError.NOSECRETS, "No agent-owned Wi-Fi credential was provided to save")
                callback(self, connection, error)
                return
        except SecretStoreError:
            error = self._error(_NM.SecretAgentError.FAILED, "Secret Service operation failed")
            callback(self, connection, error)
            return
        callback(self, connection, None)

    def do_save_secrets(self, connection: object, connection_path: str, callback: object, user_data: object) -> None:
        if connection_path != self._expected_path:
            error = self._error(_NM.SecretAgentError.NOSECRETS, "Request path is outside this invocation")
            callback(self, connection, error)
            return
        if self._identity(connection) != self._expected_uuid:
            error = self._error(_NM.SecretAgentError.NOSECRETS, "Request identity is outside this invocation")
            callback(self, connection, error)
            return
        self._save_callback(connection, callback, user_data, deleting=False)

    def do_delete_secrets(self, connection: object, connection_path: str, callback: object, user_data: object) -> None:
        if connection_path != self._expected_path:
            error = self._error(_NM.SecretAgentError.NOSECRETS, "Request path is outside this invocation")
            callback(self, connection, error)
            return
        if self._identity(connection) != self._expected_uuid:
            error = self._error(_NM.SecretAgentError.NOSECRETS, "Request identity is outside this invocation")
            callback(self, connection, error)
            return
        self._save_callback(connection, callback, user_data, deleting=True)

    def do_cancel_get_secrets(self, connection_path: str, setting_name: str) -> None:
        entry = self._requests.pop((connection_path, setting_name), None)
        if entry is None:
            return
        _pending, connection, callback, user_data = entry
        error = self._error(_NM.SecretAgentError.AGENTCANCELED, "Credential request was canceled")
        callback(self, connection, None, error)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for _key, (_pending, connection, callback, user_data) in tuple(self._requests.items()):
            error = self._error(_NM.SecretAgentError.AGENTCANCELED, "Credential request was canceled")
            callback(self, connection, None, error)
        self._requests.clear()
        self._provided_secret = None
        if self._registered:
            try:
                self._context.push_thread_default()
                try:
                    from .nm_bus import GLibRuntime
                    runtime = GLibRuntime(_GLib, context=self._context)
                    runtime.run_async(
                        lambda callback: self.unregister_async(None, callback, None),
                        lambda result: self.unregister_finish(result),
                        timeout=UNREGISTER_TIMEOUT_SECONDS,
                    )
                finally:
                    self._context.pop_thread_default()
            except Exception:
                # Closing the dedicated D-Bus connection also removes its
                # registration if NetworkManager is unavailable to acknowledge.
                pass
            finally:
                self._registered = False
        try:
            self._context.push_thread_default()
            try:
                self.destroy()
            finally:
                self._context.pop_thread_default()
        except Exception:
            pass
        if self._owns_connection:
            try:
                self._dbus_connection.close_sync(None)
            except Exception:
                pass
