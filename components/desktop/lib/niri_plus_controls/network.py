"""NetworkManager-backed, invocation-scoped Wi-Fi controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import pwd
import threading
import time
import unicodedata
import uuid
from typing import Callable, Mapping, Sequence

from .model import (
    ActionKind,
    ActionSpec,
    Availability,
    DetailFact,
    DetailsSnapshot,
    InventorySnapshot,
    OperationRequest,
    OperationResult,
    PendingRef,
    ResultKind,
    TargetRef,
    TargetSnapshot,
    Utility,
)
from .nm_agent import (
    LibsecretStore,
    NetworkSecretAgent,
    SecretRequest,
    SecretStore,
    SecretStoreError,
    WIFI_PSK_KEY,
    WIFI_SECURITY_SETTING,
)
from .nm_bus import GLibRuntime, NMUnavailable, dedicated_bus_connection, load_nm_modules, owner_epoch


MAX_SECRET_BYTES = 256
MAX_SCAN_AGE_SECONDS = 2.0
OPERATION_WAIT_SECONDS = 0.7
PENDING_LIMIT = 128
_DEVICE_WIFI = 2
_DEVICE_ETHERNET = 1
_DEVICE_VETH = 20
_DEVICE_UNMANAGED = 10
_DEVICE_UNAVAILABLE = 20
_DEVICE_DISCONNECTED = 30
_DEVICE_FAILED = 120
_ACTIVE_ACTIVATING = 1
_ACTIVE_ACTIVATED = 2
_ACTIVE_DEACTIVATED = 4
_SECRET_AGENT_OWNED = 1
_SECRET_NOT_SAVED = 2
_KEY_MGMT_PSK = 256
_KEY_MGMT_EAP = 512
_KEY_MGMT_SAE = 1024
_KEY_MGMT_OWE = 2048
_KEY_MGMT_OWE_TM = 4096
_KEY_MGMT_EAP_SUITE_B = 8192
_PRIVACY = 1
_WIFI_CONNECTION_TYPE = "802-11-wireless"
_ETHERNET_CONNECTION_TYPE = "802-3-ethernet"
_VPN_CONNECTION_TYPE = "vpn"


class NetworkError(RuntimeError):
    """A bounded native NetworkManager operation failed or went stale."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _fingerprint_value(value: object) -> object:
    unpack = getattr(value, "unpack", None)
    if callable(unpack):
        value = unpack()
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, Mapping):
        return {str(key): _fingerprint_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_fingerprint_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("unsupported profile fingerprint value")


def _method(obj: object, name: str, *args: object, default: object = None) -> object:
    function = getattr(obj, name, None)
    return function(*args) if callable(function) else default


def _prop(obj: object, name: str, default: object = None) -> object:
    try:
        return getattr(obj, name.replace("-", "_"), default)
    except Exception:
        return default


def _path(obj: object | None) -> str:
    # NM.Device.get_path() shadows NM.Object.get_path(): it returns the udev
    # path, which may be absent, rather than this object's D-Bus identity.
    if obj is not None:
        try:
            from gi.repository import NM
            if isinstance(obj, NM.Object):
                return NM.Object.get_path(obj) or ""
        except ImportError:
            pass
    value = _method(obj, "get_path", default=None) if obj is not None else None
    if value is None and obj is not None:
        value = _prop(obj, "path", "")
    return value if isinstance(value, str) else ""


def _bytes(value: object) -> bytes:
    if isinstance(value, bytes):
        return value
    getter = getattr(value, "get_data", None)
    if callable(getter):
        data = getter()
        return data if isinstance(data, bytes) else bytes(data)
    if isinstance(value, bytearray):
        return bytes(value)
    return b""


def _display_ssid(raw: bytes) -> str:
    if not raw:
        return "Open Wi-Fi network"
    try:
        value = raw.decode("utf-8", "replace")
    except Exception:
        value = raw.hex(" ")
    value = "".join(
        " " if unicodedata.category(char).startswith("C") or unicodedata.category(char) in {"Zl", "Zp"} else char
        for char in value
    )
    value = " ".join(value.split())
    return value or "Wi-Fi network"


def _network_security_name(key_mgmt: str, *, hidden: bool = False) -> str:
    if hidden:
        return "Advanced"
    if key_mgmt == "wpa-psk":
        return "WPA2/WPA3 Personal"
    if key_mgmt == "sae":
        return "WPA3 Personal"
    if key_mgmt in {"", "none"}:
        return "Open"
    return "Advanced"


def _ap_security(ap: object, NM: object) -> tuple[str, str]:
    try:
        wpa = int(_method(ap, "get_wpa_flags", default=0) or 0)
        rsn = int(_method(ap, "get_rsn_flags", default=0) or 0)
        flags = wpa | rsn
        ap_flags = int(_method(ap, "get_flags", default=0) or 0)
    except Exception:
        return "advanced", "Security unknown"
    unsupported = _KEY_MGMT_EAP | _KEY_MGMT_OWE | _KEY_MGMT_OWE_TM | _KEY_MGMT_EAP_SUITE_B
    # The low eight bits describe pairwise/group ciphers, not key management.
    # Real APs normally advertise these alongside PSK/SAE.
    known = 0xff | _KEY_MGMT_PSK | _KEY_MGMT_SAE | unsupported
    if flags & unsupported or flags & ~known:
        return "advanced", "Enterprise or advanced security"
    if rsn & (_KEY_MGMT_PSK | _KEY_MGMT_SAE):
        if rsn & _KEY_MGMT_SAE and not rsn & _KEY_MGMT_PSK:
            return "sae", "WPA3 Personal"
        return "wpa-psk", "WPA2/WPA3 Personal"
    if flags & (_KEY_MGMT_PSK | _KEY_MGMT_SAE):
        return "advanced", "Legacy WPA is outside the supported personal security modes"
    if ap_flags & _PRIVACY:
        return "advanced", "WEP or unsupported security"
    return "open", "Open"


@dataclass(slots=True)
class _Node:
    target: TargetSnapshot
    kind: str
    native: object | None = None
    device: object | None = None
    ap: object | None = None
    profile: object | None = None
    active: object | None = None
    security: str = "advanced"
    ssid: bytes = b""
    profile_matches: tuple[str, ...] = ()
    aps: tuple[object, ...] = ()


@dataclass(slots=True)
class _Operation:
    pending: PendingRef
    request_id: str
    owner: str
    epoch: str
    target_ref: TargetRef
    action_id: str
    kind: str
    device_path: str = ""
    ap_path: str = ""
    profile_uuid: str = ""
    active_path: str = ""
    active: object | None = None
    accepted: bool = False
    error: str = ""
    secret_request: PendingRef | None = None
    persistence: str = ""
    security: str = ""
    ssid: bytes = b""
    created_profile_uuid: str = ""
    created_profile_path: str = ""
    created_profile_fingerprint: str = ""
    created_volatile: bool = False
    desired_radio: bool | None = None
    last_scan: int = 0
    scan_device: object | None = None
    cancellable: object | None = None
    agent: NetworkSecretAgent | None = None
    prompt_count: int = 0
    state_changed: bool = False
    waiting_secret: bool = False
    profile_reentry: bool = False
    created_profile: object | None = None
    submitted: bool = False
    created_at: float = field(default_factory=time.monotonic)
    deadline: float = field(default_factory=lambda: time.monotonic() + 30.0)


class NetworkBackend:
    """Thin libnm adapter; every mutation revalidates live daemon and target facts."""

    def __init__(
        self,
        *,
        client: object | None = None,
        dbus_connection: object | None = None,
        client_factory: Callable[[object], object] | None = None,
        agent_factory: Callable[..., NetworkSecretAgent] | None = None,
        secret_store: SecretStore | None = None,
        bus_address: str | None = None,
        username: str | None = None,
        runtime: GLibRuntime | None = None,
        timeout: float = 6.0,
    ):
        self._init_error = ""
        self._modules = None
        self._runtime = runtime
        self._client_connection = dbus_connection
        self._bus_address = bus_address
        self._client = client
        self._client_factory = client_factory
        self._agent_factory = agent_factory or NetworkSecretAgent
        self._secret_store = secret_store
        self._username = username or pwd.getpwuid(__import__("os").getuid()).pw_name
        self._timeout = max(0.25, min(float(timeout), 20.0))
        self._nodes: dict[TargetRef, _Node] = {}
        self._profiles_by_uuid: dict[str, object] = {}
        self._device_by_path: dict[str, object] = {}
        self._active_by_path: dict[str, object] = {}
        self._owner = ""
        self._epoch = ""
        self._inventory: InventorySnapshot | None = None
        self._operations: dict[str, _Operation] = {}
        self._results: dict[str, tuple[str, OperationResult]] = {}
        self._generations: dict[TargetRef, int] = {}
        self._retry_profiles: set[str] = set()
        self._closed = False
        self._owns_client_connection = dbus_connection is None
        try:
            self._modules = load_nm_modules()
            if self._runtime is None:
                self._runtime = GLibRuntime(self._modules.GLib)
            if self._client is None:
                self._runtime.push()
                try:
                    if self._client_connection is None:
                        self._client_connection = dedicated_bus_connection(address=bus_address)
                    if self._client_factory:
                        self._client = self._client_factory(self._client_connection)
                    else:
                        # The GObject constructor alone does not initialize the
                        # libnm cache. Keep construction, init and later signal
                        # dispatch on the same invocation-owned context.
                        self._client = self._modules.NM.Client(dbus_connection=self._client_connection)
                        cancellable = self._modules.Gio.Cancellable.new()
                        self._runtime.run_async(
                            lambda callback: self._client.init_async(
                                self._modules.GLib.PRIORITY_DEFAULT, cancellable, callback, None),
                            lambda result: self._client.init_finish(result),
                            timeout=self._timeout, cancellable=cancellable,
                        )
                finally:
                    self._runtime.pop()
            if self._secret_store is None:
                self._secret_store = LibsecretStore(secret_module=self._modules.Secret)
        except (NMUnavailable, Exception) as error:
            self._init_error = "NetworkManager client initialization failed"
            if isinstance(error, NMUnavailable):
                self._init_error = str(error)

    def _need_modules(self):
        if self._modules is None or self._client is None or self._runtime is None:
            raise NetworkError(self._init_error or "NetworkManager is unavailable")
        return self._modules

    @staticmethod
    def _connection_setting(profile: object):
        return _method(profile, "get_setting_connection", default=None)

    @staticmethod
    def _wireless_setting(profile: object):
        return _method(profile, "get_setting_wireless", default=None)

    @staticmethod
    def _security_setting(profile: object):
        return _method(profile, "get_setting_wireless_security", default=None)

    def _owner_epoch(self) -> tuple[str, str]:
        try:
            return owner_epoch(self._client)
        except NMUnavailable as error:
            raise NetworkError(str(error)) from error

    def _fresh(self) -> InventorySnapshot:
        """Refresh libnm caches and inspect them on this invocation's GLib context."""

        if self._runtime is None:
            raise NetworkError(self._init_error or "NetworkManager is unavailable")
        self._runtime.push()
        try:
            return self._fresh_on_context()
        finally:
            self._runtime.pop()

    def _fresh_on_context(self) -> InventorySnapshot:
        if self._closed:
            raise NetworkError("Network controls are closed")
        if self._init_error:
            raise NetworkError(self._init_error)
        NM = self._need_modules().NM
        self._runtime.iterate_for(5)
        owner, epoch = self._owner_epoch()
        try:
            devices = list(_method(self._client, "get_devices", default=[]) or [])
            profiles = list(_method(self._client, "get_connections", default=[]) or [])
            actives = list(_method(self._client, "get_active_connections", default=[]) or [])
        except Exception as error:
            raise NetworkError("NetworkManager inventory could not be read") from error
        if len(devices) > 1024 or len(profiles) > 4096 or len(actives) > 4096:
            raise NetworkError("NetworkManager inventory exceeded its bounded item limit")
        wifi_devices: list[object] = []
        ethernet_devices: list[object] = []
        self._device_by_path = {}
        for device in devices:
            try:
                device_type = int(_method(device, "get_device_type", default=-1))
            except (TypeError, ValueError):
                device_type = -1
            if device_type not in {_DEVICE_WIFI, _DEVICE_ETHERNET, _DEVICE_VETH}:
                continue
            path = _path(device)
            iface = _method(device, "get_iface", default="")
            if not path or not isinstance(iface, str) or not iface:
                continue
            self._device_by_path[path] = device
            if device_type == _DEVICE_WIFI:
                wifi_devices.append(device)
            else:
                ethernet_devices.append(device)
        self._profiles_by_uuid = {}
        for profile in profiles:
            uuid_value = _method(profile, "get_uuid", default=None)
            setting = self._connection_setting(profile)
            profile_type = _method(setting, "get_connection_type", default=None) if setting else None
            if isinstance(uuid_value, str) and profile_type in {_WIFI_CONNECTION_TYPE, _ETHERNET_CONNECTION_TYPE, _VPN_CONNECTION_TYPE}:
                self._profiles_by_uuid[uuid_value] = profile
        self._active_by_path = {_path(active): active for active in actives if _path(active)}
        self._owner, self._epoch = owner, epoch
        self._nodes = {}
        radio_enabled = bool(_method(self._client, "wireless_get_enabled", default=_prop(self._client, "wireless_enabled", False)))
        radio_hw = bool(_method(self._client, "wireless_hardware_get_enabled", default=_prop(self._client, "wireless_hardware_enabled", True)))
        managed_devices = [
            device for device in wifi_devices
            if bool(_method(device, "get_managed", default=_method(device, "is_managed", default=True)))
        ]
        managed_paths = {_path(device) for device in managed_devices}
        interfaces = sorted(str(_method(device, "get_iface", default="")) for device in managed_devices)
        active_names = sorted(
            str(_method(_method(active, "get_connection", default=None), "get_id", default="Wi-Fi connection"))
            for active in actives
            if int(_method(active, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED
            and self._active_has_wifi(active) and self._active_device_paths(active).intersection(managed_paths)
        )
        radio_ref = self._ref("wifi-radio", [epoch])
        radio_status = "Global Wi-Fi on" if radio_enabled else "Global Wi-Fi off"
        radio_facts = (
            DetailFact("Scope", "Global NetworkManager Wi-Fi radio"),
            DetailFact("Affected adapters", (", ".join(interfaces) or "None detected")[:4096]),
            DetailFact("Active Wi-Fi connections", (", ".join(active_names) or "None")[:4096]),
            DetailFact("Hardware switch", "Enabled" if radio_hw else "Blocked"),
        )
        radio_state = {
            "kind": "radio", "powered": radio_enabled,
            "interfaces": (", ".join(interfaces) or "None detected")[:512],
            "active_profiles": (", ".join(active_names) or "None")[:512],
        }
        impact_fingerprint = _digest([interfaces, active_names])
        radio_revision = _digest([epoch, radio_enabled, radio_hw, interfaces, active_names])
        radio_target = TargetSnapshot(
            radio_ref, "Wi-Fi radio", radio_status,
            Availability.AVAILABLE if radio_hw and managed_devices else Availability.UNAVAILABLE,
            radio_revision, status=radio_status, active=False,
            filter_terms=("wifi", "wireless", "radio", *interfaces), facts=radio_facts,
            state={**radio_state, "impact_fingerprint": impact_fingerprint},
        )
        self._nodes[radio_ref] = _Node(radio_target, "radio")

        ap_nodes: list[_Node] = []
        for device in wifi_devices:
            device_path = _path(device)
            iface = str(_method(device, "get_iface", default="Wi-Fi adapter"))
            managed = bool(_method(device, "get_managed", default=_method(device, "is_managed", default=True)))
            device_state = int(_method(device, "get_state", default=0) or 0)
            available = managed and device_state not in {_DEVICE_UNMANAGED, _DEVICE_UNAVAILABLE} and radio_hw and radio_enabled
            device_ref = self._ref("wifi-device", [epoch, device_path])
            device_status = "Wi-Fi on" if radio_enabled else "Wi-Fi off"
            if not managed:
                device_status = "Unmanaged"
            elif not radio_hw:
                device_status = "Blocked by hardware switch"
            device_facts = (
                DetailFact("Adapter", iface),
                DetailFact("Interface", device_path),
                DetailFact("Managed", "Yes" if managed else "No"),
                DetailFact("Radio", radio_status),
                DetailFact("Device state", self._device_state_name(device_state)),
                *self._device_network_facts(device),
            )
            device_state_values = {"kind": "device", "interface": iface, "device_path": device_path, "managed": managed, "radio": radio_enabled, "saved": False, "new_wifi": False}
            device_revision = _digest([epoch, device_path, iface, managed, device_state, radio_enabled, radio_hw])
            device_target = TargetSnapshot(
                device_ref, iface, device_status, Availability.AVAILABLE if available else Availability.UNAVAILABLE,
                device_revision, status=device_status, active=False,
                filter_terms=(iface, "adapter", "wifi", "scan"), facts=device_facts, state=device_state_values,
            )
            self._nodes[device_ref] = _Node(device_target, "device", native=device, device=device)
            try:
                access_points = list(_method(device, "get_access_points", default=[]) or [])
            except Exception as error:
                raise NetworkError("NetworkManager access-point cache could not be read") from error
            if len(access_points) > 4096:
                raise NetworkError("Access-point cache exceeded its bounded item limit")
            groups: dict[tuple[bytes, str], list[object]] = {}
            for ap in access_points:
                raw_ssid = _bytes(_method(ap, "get_ssid", default=b""))
                security_group = self._ap_security_group(ap, NM)
                groups.setdefault((raw_ssid, security_group), []).append(ap)
            for group_aps in groups.values():
                ordered_aps = tuple(sorted(
                    group_aps,
                    key=lambda ap: (-int(_method(ap, "get_strength", default=0) or 0), _path(ap)),
                ))
                self._add_ap_node(NM, epoch, device, ordered_aps[0], radio_enabled, available, ap_nodes, ordered_aps)

        for device in ethernet_devices:
            self._add_ethernet_device_node(epoch, device, actives)

        profile_nodes: list[_Node] = []
        for profile in self._profiles_by_uuid.values():
            profile_nodes.extend(self._add_profile_nodes(epoch, profile, wifi_devices, ethernet_devices, actives, radio_enabled, radio_hw))

        all_nodes = [self._nodes[radio_ref], *self._nodes.values()]
        # The dictionary contains the radio already; de-duplicate before ordering.
        unique: dict[TargetRef, _Node] = {node.target.ref: node for node in all_nodes}
        ordered = sorted(unique.values(), key=lambda n: (
            not n.target.active, n.kind in {"radio", "device"},
            n.target.availability != Availability.AVAILABLE,
            n.target.title.casefold(), n.target.ref.stable_id,
        ))
        revision = _digest([node.target.revision for node in ordered])
        notice = ""
        if not any(bool(_method(device, "get_managed", default=True)) for device in wifi_devices):
            notice = "No managed Wi-Fi adapters are available. Ethernet connections remain listed separately."
        elif not radio_hw:
            notice = "Wi-Fi is blocked by a hardware switch; NetworkManager state is read-only until unblocked."
        elif not radio_enabled:
            notice = "Wi-Fi is globally off. Turning it on affects all listed Wi-Fi adapters and active connections."
        inventory = InventorySnapshot(Utility.NETWORK, revision, datetime.now(timezone.utc).isoformat(), tuple(node.target for node in ordered), notice)
        current_owner, current_epoch = self._owner_epoch()
        if current_owner != owner or current_epoch != epoch:
            self._nodes = {}
            raise NetworkError("NetworkManager restarted during refresh; review the current inventory")
        self._inventory = inventory
        return inventory

    @staticmethod
    def _device_state_name(state: int) -> str:
        return {
            10: "Unmanaged", 20: "Unavailable", 30: "Disconnected", 40: "Preparing", 50: "Configuring",
            60: "Needs authentication", 70: "Configuring IP", 80: "Checking", 90: "Finalizing", 100: "Connected",
            110: "Disconnecting", 120: "Failed",
        }.get(state, "Unknown")

    @staticmethod
    def _active_has_wifi(active: object) -> bool:
        connection = _method(active, "get_connection", default=None)
        setting = _method(connection, "get_setting_connection", default=None) if connection else None
        return _method(setting, "get_connection_type", default=None) == _WIFI_CONNECTION_TYPE if setting else False

    @staticmethod
    def _active_has_ethernet(active: object) -> bool:
        connection = _method(active, "get_connection", default=None)
        setting = _method(connection, "get_setting_connection", default=None) if connection else None
        return _method(setting, "get_connection_type", default=None) == _ETHERNET_CONNECTION_TYPE if setting else False

    @staticmethod
    def _profile_uuid(profile: object) -> str:
        value = _method(profile, "get_uuid", default="")
        return value if isinstance(value, str) else ""

    @staticmethod
    def _has_secondaries(connection: object | None) -> bool:
        if connection is None:
            return False
        count = _method(connection, "get_num_secondaries", default=None)
        if count is not None:
            try:
                return int(count) > 0
            except (TypeError, ValueError):
                return True
        values = _method(connection, "get_property", "secondaries", default=_prop(connection, "secondaries", ()))
        return bool(values)

    def _available_profile_uuids(self, device: object) -> set[str] | None:
        getter = getattr(device, "get_available_connections", None)
        if not callable(getter):
            return None
        try:
            available = list(getter() or [])
        except Exception:
            return None
        if len(available) > 4096:
            return None
        return {value for item in available if (value := self._profile_uuid(item))}

    def _profile_available_on_device(self, profile: object, device: object) -> bool:
        uuid_value = self._profile_uuid(profile)
        available = self._available_profile_uuids(device)
        return bool(uuid_value and available is not None and uuid_value in available)

    @staticmethod
    def _ap_accepts_profile(ap: object, profile: object) -> bool:
        check = getattr(ap, "connection_valid", None)
        if not callable(check):
            return False
        try:
            return check(profile) is True
        except Exception:
            return False

    def _device_network_facts(self, device: object) -> tuple[DetailFact, ...]:
        facts: list[DetailFact] = []
        for version, getter_name in ((4, "get_ip4_config"), (6, "get_ip6_config")):
            config = _method(device, getter_name, default=None)
            addresses = _method(config, "get_addresses", default=[]) if config is not None else []
            values: set[str] = set()
            try:
                for item in addresses or ():
                    raw = _method(item, "get_address", default="")
                    parsed = ipaddress.ip_address(str(raw))
                    if parsed.version == version:
                        values.add(str(parsed))
            except Exception:
                # One unreadable address does not invalidate the rest of the
                # native device snapshot.
                continue
            if values:
                facts.append(DetailFact(f"IPv{version} addresses", ", ".join(sorted(values))[:1024]))
        connectivity = _method(self._client, "get_connectivity", default=None)
        try:
            value = int(connectivity) if connectivity is not None else None
        except (TypeError, ValueError):
            value = None
        labels = {0: "Unknown", 1: "None", 2: "Portal", 3: "Limited", 4: "Full"}
        if value in labels:
            facts.append(DetailFact("NetworkManager connectivity check", labels[value]))
        return tuple(facts)

    def _add_ethernet_device_node(self, epoch: str, device: object, actives: Sequence[object]) -> None:
        path = _path(device)
        iface = str(_method(device, "get_iface", default="Ethernet adapter"))
        managed = bool(_method(device, "get_managed", default=_method(device, "is_managed", default=True)))
        device_state = int(_method(device, "get_state", default=0) or 0)
        device_actives = [
            active for active in actives
            if path in self._active_device_paths(active)
            and self._active_has_ethernet(active)
            and int(_method(active, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED
        ]
        active = next((item for item in device_actives if int(_method(item, "get_state", default=0) or 0) == _ACTIVE_ACTIVATED), None)
        pending_active = next((item for item in device_actives if int(_method(item, "get_state", default=0) or 0) != _ACTIVE_ACTIVATED), None)
        selected = active or pending_active
        connected = active is not None
        profile_name = str(_method(_method(selected, "get_connection", default=None), "get_id", default="") or "") if selected else ""
        carrier_value = _method(device, "get_carrier", default=None)
        carrier = bool(carrier_value) if carrier_value is not None else None
        if not managed:
            status = "Unmanaged"
        elif connected:
            status = f"Connected · {profile_name}" if profile_name else "Connected"
        elif pending_active is not None:
            status = f"Connecting · {profile_name}" if profile_name else "Connecting"
        elif carrier is False:
            status = "No carrier"
        else:
            status = "Disconnected"
        available = managed and device_state not in {_DEVICE_UNMANAGED, _DEVICE_UNAVAILABLE}
        if carrier is False and not connected:
            available = False
        state = {
            "kind": "ethernet-device", "interface": iface, "device_path": path,
            "managed": managed, "connected": connected, "active_state": int(_method(selected, "get_state", default=0) or 0) if selected else 0,
            "carrier": carrier,
        }
        if selected is not None:
            state["profile_uuid"] = self._active_profile_uuid(selected)
            state["active_path"] = _path(selected)
        facts = (
            DetailFact("Adapter", iface), DetailFact("Interface", path),
            DetailFact("Managed", "Yes" if managed else "No"),
            DetailFact("Device state", self._device_state_name(device_state)),
            DetailFact("Carrier", "Present" if carrier else "Absent" if carrier is False else "Unknown"),
            *((DetailFact("Active profile", profile_name),) if profile_name else ()),
            *self._device_network_facts(device),
        )
        ref = self._ref("ethernet-device", [epoch, path])
        revision = _digest([epoch, path, iface, managed, device_state, carrier, _path(selected), state["active_state"], connected])
        target = TargetSnapshot(
            ref, f"Ethernet · {iface}", status,
            Availability.AVAILABLE if available else Availability.UNAVAILABLE,
            revision, status=status, active=connected,
            filter_terms=tuple(term for term in ("ethernet", "wired", iface, profile_name, status) if term), facts=facts, state=state,
        )
        self._nodes[ref] = _Node(target, "ethernet-device", native=device, device=device, active=selected)

    def _ref(self, kind: str, identity: object) -> TargetRef:
        return TargetRef(kind, _digest(["NetworkManager", self._epoch, identity]))

    def _add_ap_node(
        self,
        NM: object,
        epoch: str,
        device: object,
        ap: object,
        radio_enabled: bool,
        device_available: bool,
        output: list[_Node],
        aps: tuple[object, ...],
    ) -> None:
        raw_ssid = _bytes(_method(ap, "get_ssid", default=b""))
        bssid = _method(ap, "get_bssid", default="")
        ap_path = _path(ap)
        device_path = _path(device)
        iface = str(_method(device, "get_iface", default="Wi-Fi"))
        if not raw_ssid or len(raw_ssid) > 32 or not isinstance(bssid, str) or not bssid or not ap_path:
            return
        security, security_label = _ap_security(ap, NM)
        security_group = self._ap_security_group(ap, NM)
        title = _display_ssid(raw_ssid)
        strength = max(0, min(100, int(_method(ap, "get_strength", default=0) or 0)))
        matched = self._matching_profiles(raw_ssid, security, device, aps)
        active = next((
            item for item in self._active_by_path.values()
            if int(_method(item, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED
            and _path(device) in self._active_device_paths(item)
            and _method(item, "get_specific_object_path", default="") in {_path(value) for value in aps}
        ), None)
        active = active or next((
            item for item in self._active_by_path.values()
            if int(_method(item, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED
            and _path(device) in self._active_device_paths(item)
            and self._active_profile_uuid(item) in matched
        ), None)
        connected = active is not None and int(_method(active, "get_state", default=0) or 0) == _ACTIVE_ACTIVATED
        status = "Connected" if connected else "Connecting" if active else "Saved" if matched else "New network"
        available = device_available and radio_enabled and security in {"open", "wpa-psk", "sae"}
        identity = [epoch, device_path, security_group, raw_ssid.hex()]
        ref = self._ref("wifi-ap", identity)
        facts = (
            DetailFact("Network", title), DetailFact("Adapter", iface), DetailFact("BSSID", bssid),
            DetailFact("Security", security_label), DetailFact("Signal", f"{strength}%"),
            DetailFact("Saved profile matches", str(len(matched))),
        )
        state = {
            "kind": "access-point", "interface": iface, "device_path": device_path, "ap_path": ap_path,
            "bssid": bssid, "ssid_hex": raw_ssid.hex(), "security": security, "security_group": security_group, "strength": strength,
            "saved_profiles": len(matched), "saved": bool(matched), "new_wifi": not bool(matched),
            "connected": connected, "active_state": int(_method(active, "get_state", default=0) or 0) if active else 0,
        }
        if active is not None:
            state["active_path"] = _path(active)
        revision = _digest([epoch, device_path, raw_ssid.hex(), security_group, tuple(matched), _path(active), connected, device_available])
        target = TargetSnapshot(
            ref, f"{title} · {iface}" + (f" · {security_label}" if security == "advanced" else ""), f"{security_label} · {strength}% signal", Availability.AVAILABLE if available else Availability.UNAVAILABLE,
            revision, status=status, active=connected,
            filter_terms=(title, iface, bssid, security_label, "wifi"), facts=(*facts, *self._device_network_facts(device)), state=state,
        )
        node = _Node(target, "ap", native=ap, device=device, ap=ap, active=active, security=security, ssid=raw_ssid, profile_matches=tuple(matched), aps=aps)
        output.append(node)
        self._nodes[ref] = node

    @staticmethod
    def _active_device_paths(active: object) -> set[str]:
        return {_path(device) for device in (_method(active, "get_devices", default=[]) or []) if _path(device)}

    @staticmethod
    def _active_profile_uuid(active: object) -> str:
        connection = _method(active, "get_connection", default=None)
        value = _method(connection, "get_uuid", default="") if connection else ""
        return value if isinstance(value, str) else ""

    @staticmethod
    def _ap_security_group(ap: object, NM: object) -> str:
        security = _ap_security(ap, NM)[0]
        if security != "advanced":
            return security
        try:
            wpa = int(_method(ap, "get_wpa_flags", default=0) or 0)
            rsn = int(_method(ap, "get_rsn_flags", default=0) or 0)
            flags = int(_method(ap, "get_flags", default=0) or 0)
        except Exception:
            return "advanced:unknown"
        return f"advanced:{flags:x}:{wpa:x}:{rsn:x}"

    def _matching_profiles(self, ssid: bytes, security: str, device: object, aps: Sequence[object]) -> list[str]:
        result: list[str] = []
        available = self._available_profile_uuids(device)
        if available is None:
            return result
        for uuid_value, profile in self._profiles_by_uuid.items():
            wireless = self._wireless_setting(profile)
            connection = self._connection_setting(profile)
            profile_ssid = _bytes(_method(wireless, "get_ssid", default=b"")) if wireless else b""
            interface = _method(connection, "get_interface_name", default="") if connection else ""
            profile_security = self._profile_security(profile)[0]
            if (
                uuid_value in available
                and profile_ssid == ssid
                and profile_security == security
                and (not interface or interface == _method(device, "get_iface", default=""))
                and any(self._ap_accepts_profile(ap, profile) for ap in aps)
            ):
                result.append(uuid_value)
        return sorted(result)

    def _profile_security(self, profile: object) -> tuple[str, str]:
        connection = self._connection_setting(profile)
        if self._has_secondaries(connection):
            return "advanced", "Secondary VPN profile"
        wireless = self._wireless_setting(profile)
        hidden = bool(_method(wireless, "get_hidden", default=False)) if wireless else False
        mode = _method(wireless, "get_mode", default=None) if wireless else None
        security = self._security_setting(profile)
        key_mgmt = str(_method(security, "get_key_mgmt", default="") or "") if security else ""
        if hidden or mode is not None and str(mode).casefold() not in {"infrastructure", "infra"}:
            return "advanced", "Hidden network profile"
        if security is not None and (not key_mgmt or any(_method(security, "get_wep_key", index, default=None) for index in range(4))):
            return "advanced", "WEP or unsupported security profile"
        if key_mgmt in {"wpa-psk", "sae"}:
            return key_mgmt, _network_security_name(key_mgmt)
        if not key_mgmt:
            return "open", "Open"
        return "advanced", "Enterprise or advanced security"

    def _add_profile_nodes(
        self,
        epoch: str,
        profile: object,
        wifi_devices: Sequence[object],
        ethernet_devices: Sequence[object],
        actives: Sequence[object],
        radio_enabled: bool,
        radio_hw: bool,
    ) -> list[_Node]:
        connection = self._connection_setting(profile)
        if connection is None:
            return []
        uuid_value = _method(profile, "get_uuid", default="")
        if not isinstance(uuid_value, str) or not uuid_value:
            return []
        connection_type = str(_method(connection, "get_connection_type", default="") or "")
        name = str(_method(connection, "get_id", default="Saved Wi-Fi profile") or "Saved Wi-Fi profile")
        interface = str(_method(connection, "get_interface_name", default="") or "")
        path = _path(profile)
        if not path:
            return []
        if connection_type == _WIFI_CONNECTION_TYPE:
            wireless = self._wireless_setting(profile)
            raw_ssid = _bytes(_method(wireless, "get_ssid", default=b"")) if wireless else b""
            if not raw_ssid or len(raw_ssid) > 32:
                return []
            return self._add_wifi_profile_nodes(
                epoch, profile, wifi_devices, actives, radio_enabled, radio_hw,
                name, interface, path, uuid_value, raw_ssid,
            )
        if connection_type == _ETHERNET_CONNECTION_TYPE:
            return self._add_ethernet_profile_nodes(
                epoch, profile, ethernet_devices, actives, name, interface, path, uuid_value,
            )
        if connection_type == _VPN_CONNECTION_TYPE:
            return self._add_advanced_vpn_node(epoch, profile, actives, name, path, uuid_value)
        return []

    def _add_wifi_profile_nodes(
        self,
        epoch: str,
        profile: object,
        wifi_devices: Sequence[object],
        actives: Sequence[object],
        radio_enabled: bool,
        radio_hw: bool,
        name: str,
        interface: str,
        path: str,
        uuid_value: str,
        raw_ssid: bytes,
    ) -> list[_Node]:
        connection = self._connection_setting(profile)
        profile_type, security_label = self._profile_security(profile)
        security_setting = self._security_setting(profile)
        secret_flags = int(_method(security_setting, "get_psk_flags", default=0) or 0) if security_setting else 0
        matching_devices = [d for d in wifi_devices if not interface or _method(d, "get_iface", default="") == interface]
        active_for_profile = [
            item for item in actives
            if self._active_profile_uuid(item) == uuid_value
            and int(_method(item, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED
        ]
        if active_for_profile:
            active_devices = {_path(device) for item in active_for_profile for device in (_method(item, "get_devices", default=[]) or [])}
            target_devices = [device for device in matching_devices if _path(device) in active_devices]
            if not target_devices:
                target_devices = matching_devices[:1]
        elif matching_devices:
            target_devices = matching_devices
        else:
            target_devices = [None]
        nodes: list[_Node] = []
        fingerprint = self._profile_fingerprint(profile)
        for device in target_devices:
            device_path = _path(device) if device is not None else ""
            display_interface = str(_method(device, "get_iface", default=interface or "Adapter unavailable")) if device is not None else (interface or "Adapter unavailable")
            active = next((item for item in active_for_profile if not device_path or device_path in self._active_device_paths(item)), None)
            state_value = int(_method(active, "get_state", default=0) or 0) if active else 0
            connected = active is not None and state_value == _ACTIVE_ACTIVATED
            status = "Connected" if connected else "Connecting" if active else "Saved · disconnected"
            if device is None:
                availability = Availability.UNAVAILABLE
                status = "Saved · required adapter unavailable"
            elif not radio_enabled or not radio_hw:
                availability = Availability.UNAVAILABLE
                status = "Saved · Wi-Fi off" if not radio_enabled else "Saved · hardware switch blocked"
            elif profile_type == "advanced":
                availability = Availability.AVAILABLE
                status = "Saved · advanced profile"
            elif active is not None:
                availability = Availability.AVAILABLE
            else:
                managed = bool(_method(device, "get_managed", default=True))
                device_state = int(_method(device, "get_state", default=0) or 0)
                availability = Availability.AVAILABLE if (
                    managed and device_state not in {_DEVICE_UNMANAGED, _DEVICE_UNAVAILABLE}
                    and self._profile_available_on_device(profile, device)
                ) else Availability.UNAVAILABLE
                if availability == Availability.UNAVAILABLE:
                    status = "Saved · unavailable on this adapter"
            facts = (
                DetailFact("Profile", name), DetailFact("SSID", _display_ssid(raw_ssid)),
                DetailFact("Adapter", display_interface), DetailFact("Security", security_label),
                DetailFact("Credential storage", self._credential_storage(secret_flags, profile_type)),
                DetailFact("Autoconnect", "Enabled" if bool(_method(connection, "get_autoconnect", default=False)) else "Disabled"),
                *(self._device_network_facts(device) if device is not None else ()),
            )
            state = {
                "kind": "profile", "uuid": uuid_value, "profile_path": path, "ssid_hex": raw_ssid.hex(),
                "interface": display_interface,
                "security": profile_type, "storage_flags": secret_flags, "saved": True, "new_wifi": False,
                "active_state": state_value, "connected": connected, "connection_type": _WIFI_CONNECTION_TYPE,
            }
            if device_path:
                state["device_path"] = device_path
            if active is not None:
                state["active_path"] = _path(active)
            ref = self._ref("wifi-profile", [epoch, uuid_value, path, device_path])
            revision = _digest([epoch, uuid_value, path, fingerprint, device_path, state_value, connected, availability.value, radio_enabled, radio_hw])
            title = f"{name} · {display_interface}" if len(target_devices) > 1 else name
            target = TargetSnapshot(
                ref, title[:1024], f"{security_label} · {display_interface}", availability, revision,
                status=status, active=connected,
                filter_terms=(name, _display_ssid(raw_ssid), display_interface, security_label, "saved", "wifi"),
                facts=facts, state=state,
            )
            node = _Node(target, "profile", native=profile, profile=profile, device=device, active=active, security=profile_type, ssid=raw_ssid)
            nodes.append(node)
            self._nodes[ref] = node
        return nodes

    def _add_ethernet_profile_nodes(
        self,
        epoch: str,
        profile: object,
        ethernet_devices: Sequence[object],
        actives: Sequence[object],
        name: str,
        interface: str,
        path: str,
        uuid_value: str,
    ) -> list[_Node]:
        connection = self._connection_setting(profile)
        advanced = self._has_secondaries(connection) or _method(profile, "get_setting_802_1x", default=None) is not None
        security = "advanced" if advanced else "wired"
        security_label = "802.1X or secondary profile" if advanced else "Ethernet"
        matching_devices = [device for device in ethernet_devices if not interface or _method(device, "get_iface", default="") == interface]
        active_for_profile = [
            active for active in actives
            if self._active_profile_uuid(active) == uuid_value
            and int(_method(active, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED
        ]
        if active_for_profile:
            active_paths = {_path(device) for active in active_for_profile for device in (_method(active, "get_devices", default=[]) or [])}
            target_devices = [device for device in matching_devices if _path(device) in active_paths]
            if not target_devices:
                target_devices = matching_devices[:1]
        elif matching_devices:
            target_devices = matching_devices
        else:
            target_devices = [None]
        fingerprint = self._profile_fingerprint(profile)
        nodes: list[_Node] = []
        for device in target_devices:
            device_path = _path(device) if device is not None else ""
            display_interface = str(_method(device, "get_iface", default=interface or "Adapter unavailable")) if device is not None else (interface or "Adapter unavailable")
            active = next((item for item in active_for_profile if not device_path or device_path in self._active_device_paths(item)), None)
            active_state = int(_method(active, "get_state", default=0) or 0) if active else 0
            connected = active is not None and active_state == _ACTIVE_ACTIVATED
            status = "Connected" if connected else "Connecting" if active else "Saved · disconnected"
            managed = bool(_method(device, "get_managed", default=True)) if device is not None else False
            device_state = int(_method(device, "get_state", default=0) or 0) if device is not None else _DEVICE_UNAVAILABLE
            carrier = _method(device, "get_carrier", default=None) if device is not None else None
            available = bool(
                device is not None and managed
                and device_state not in {_DEVICE_UNMANAGED, _DEVICE_UNAVAILABLE}
                and carrier is not False and self._profile_available_on_device(profile, device)
            )
            if device is None:
                status = "Saved · required adapter unavailable"
            elif not available and active is None:
                status = "Saved · unavailable on this adapter"
            elif advanced and active is None:
                status = "Saved · advanced profile"
            facts = (
                DetailFact("Profile", name), DetailFact("Connection type", "Ethernet"),
                DetailFact("Adapter", display_interface), DetailFact("Interface", device_path or interface or "No matching adapter"),
                DetailFact("Activation", "Advanced profile; use NetworkManager settings" if advanced else "Existing saved profile"),
                DetailFact("Autoconnect", "Enabled" if bool(_method(connection, "get_autoconnect", default=False)) else "Disabled"),
                *(self._device_network_facts(device) if device is not None else ()),
            )
            state = {
                "kind": "wired-profile", "uuid": uuid_value, "profile_path": path,
                "connection_type": _ETHERNET_CONNECTION_TYPE, "interface": display_interface,
                "security": security, "saved": True, "new_wifi": False,
                "active_state": active_state, "connected": connected, "managed": managed,
            }
            if device_path:
                state["device_path"] = device_path
            if active is not None:
                state["active_path"] = _path(active)
            ref = self._ref("ethernet-profile", [epoch, uuid_value, path, device_path])
            revision = _digest([epoch, uuid_value, path, fingerprint, device_path, active_state, connected, available, managed, carrier])
            title = f"{name} · {display_interface}" if len(target_devices) > 1 else name
            target = TargetSnapshot(
                ref, title[:1024], f"{security_label} · {display_interface}",
                Availability.AVAILABLE if available or active is not None else Availability.UNAVAILABLE,
                revision, status=status, active=connected,
                filter_terms=(name, display_interface, "ethernet", "wired", security_label, "saved"),
                facts=facts, state=state,
            )
            node = _Node(target, "profile", native=profile, profile=profile, device=device, active=active, security=security)
            nodes.append(node)
            self._nodes[ref] = node
        return nodes

    def _add_advanced_vpn_node(
        self,
        epoch: str,
        profile: object,
        actives: Sequence[object],
        name: str,
        path: str,
        uuid_value: str,
    ) -> list[_Node]:
        active = next((item for item in actives if self._active_profile_uuid(item) == uuid_value and int(_method(item, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED), None)
        active_state = int(_method(active, "get_state", default=0) or 0) if active else 0
        connected = active is not None and active_state == _ACTIVE_ACTIVATED
        status = "Connected" if connected else "Connecting" if active else "Advanced · VPN profile"
        ref = self._ref("network-profile", [epoch, uuid_value, path])
        state = {
            "kind": "advanced-profile", "uuid": uuid_value, "profile_path": path,
            "connection_type": _VPN_CONNECTION_TYPE, "security": "advanced", "saved": True,
            "connected": connected, "active_state": active_state,
        }
        if active is not None:
            state["active_path"] = _path(active)
        facts = (
            DetailFact("Profile", name), DetailFact("Connection type", "VPN"),
            DetailFact("Activation", "Advanced profile; use NetworkManager settings"),
        )
        target = TargetSnapshot(
            ref, name[:1024], "VPN · Advanced profile", Availability.AVAILABLE,
            _digest([epoch, uuid_value, path, self._profile_fingerprint(profile), active_state, connected]),
            status=status, active=connected,
            filter_terms=(name, "vpn", "advanced", "saved"), facts=facts, state=state,
        )
        self._nodes[ref] = _Node(target, "advanced-profile", native=profile, profile=profile, active=active, security="advanced")
        return [self._nodes[ref]]

    @staticmethod
    def _credential_storage(flags: int, security: str) -> str:
        if security not in {"wpa-psk", "sae"}:
            return "No personal Wi-Fi credential"
        if flags == _SECRET_AGENT_OWNED:
            return "Secret Service agent-owned"
        if flags == _SECRET_NOT_SAVED:
            return "Not saved; request each time"
        return "NetworkManager-managed"

    def _profile_fingerprint(self, profile: object) -> str:
        serializer = getattr(profile, "to_dbus", None)
        if callable(serializer) and self._modules is not None:
            try:
                native = serializer(self._modules.NM.ConnectionSerializationFlags.WITH_NON_SECRET)
                return _digest(_fingerprint_value(native))
            except Exception:
                return ""
        return ""

    def snapshot(self, utility: Utility = Utility.NETWORK) -> InventorySnapshot:
        if Utility(utility) != Utility.NETWORK:
            return InventorySnapshot(Utility.NETWORK, "unavailable", datetime.now(timezone.utc).isoformat(), (), "Network adapter received another utility scope.")
        try:
            return self._fresh()
        except NetworkError as error:
            self._nodes = {}
            self._inventory = InventorySnapshot(
                Utility.NETWORK, "unavailable", datetime.now(timezone.utc).isoformat(), (), str(error)[:1024],
            )
            return self._inventory
        except Exception:
            self._nodes = {}
            self._inventory = InventorySnapshot(
                Utility.NETWORK, "unavailable", datetime.now(timezone.utc).isoformat(), (),
                "NetworkManager inventory could not be read.",
            )
            return self._inventory

    def target(self, ref: TargetRef) -> TargetSnapshot | None:
        try:
            self._fresh()
        except Exception:
            return None
        node = self._nodes.get(ref)
        return node.target if node else None

    def details(self, ref: TargetRef) -> DetailsSnapshot | None:
        target = self.target(ref)
        if target is None:
            return None
        return DetailsSnapshot(ref, target.title, target.facts, target.revision)

    def actions(self, ref: TargetRef) -> Sequence[ActionSpec]:
        try:
            self._fresh()
        except Exception:
            return ()
        node = self._nodes.get(ref)
        if node is None:
            return ()
        if node.kind == "radio":
            if node.target.availability != Availability.AVAILABLE:
                return ()
            powered = bool(node.target.state.get("powered"))
            interfaces = str(node.target.state.get("interfaces") or "No Wi-Fi adapters found")
            active = str(node.target.state.get("active_profiles") or "No active Wi-Fi connections")
            parameters = {"desired_on": not powered, "impact_fingerprint": node.target.state.get("impact_fingerprint", "")}
            if powered:
                return (ActionSpec("set-wifi-radio", "Turn Wi-Fi off", ActionKind.CONFIRM, parameters, f"Turn off Wi-Fi for all adapters ({interfaces}) and disconnect active Wi-Fi connections ({active})? Ethernet and Bluetooth remain unchanged."),)
            if node.target.availability == Availability.UNAVAILABLE:
                return ()
            return (ActionSpec("set-wifi-radio", "Turn Wi-Fi on", ActionKind.OPERATION, parameters),)
        if node.kind == "device":
            if node.target.availability != Availability.AVAILABLE:
                return ()
            device_path = str(node.target.state.get("device_path", ""))
            return (ActionSpec("rescan", "Rescan this adapter", ActionKind.OPERATION, {"device_path": device_path}),)
        if node.kind in {"ethernet-device", "advanced-profile"}:
            if node.kind == "advanced-profile":
                return (ActionSpec(
                    "advanced-settings", "Advanced network profile", ActionKind.OPERATION,
                    {"profile_uuid": str(node.target.state.get("uuid", ""))}, enabled=False,
                    disabled_reason="VPN profiles require NetworkManager's native editor.",
                ),)
            return ()
        if node.kind == "ap":
            if node.active is not None:
                profile_name = self._active_connection_name(node.active)
                return (ActionSpec(
                    "disconnect", "Disconnect", ActionKind.CONFIRM,
                    {"active_path": _path(node.active), "device_path": _path(node.device), "profile_uuid": self._active_profile_uuid(node.active)},
                    f"Disconnect {profile_name} on {node.target.state.get('interface', 'the selected adapter')}?",
                ),)
            if node.security not in {"open", "wpa-psk", "sae"}:
                return (ActionSpec("advanced-settings", "Open advanced network settings", ActionKind.OPERATION, {"device_path": _path(node.device), "ap_path": _path(node.ap)}, enabled=False, disabled_reason="Enterprise, legacy WPA, WEP, and advanced security require NetworkManager's native editor."),)
            if node.target.availability != Availability.AVAILABLE:
                return ()
            if node.profile_matches:
                if len(node.profile_matches) == 1:
                    profile_uuid = node.profile_matches[0]
                    retry = profile_uuid in self._retry_profiles
                    return (ActionSpec(
                        "connect", "Retry with a new password" if retry else "Connect saved profile",
                        ActionKind.OPERATION,
                        {"profile_uuid": profile_uuid, "device_path": _path(node.device), "reentry": retry},
                    ),)
                return (ActionSpec("connect", "Choose a saved profile", ActionKind.OPERATION, enabled=False, disabled_reason="More than one saved profile matches; select the exact profile row."),)
            if node.security in {"open", "wpa-psk", "sae"}:
                return (ActionSpec("connect", "Connect", ActionKind.OPERATION, {"persistence_choice_required": True, "device_path": _path(node.device), "ssid_hex": node.ssid.hex(), "security": node.security}),)
            return (ActionSpec("advanced-settings", "Open advanced network settings", ActionKind.OPERATION, {"device_path": _path(node.device), "ap_path": _path(node.ap)}, enabled=False, disabled_reason="Enterprise, legacy WPA, WEP, and advanced security require NetworkManager's native editor."),)
        if node.kind == "profile":
            if node.active is not None:
                profile_name = self._active_connection_name(node.active)
                return (ActionSpec(
                    "disconnect", "Disconnect", ActionKind.CONFIRM,
                    {"active_path": _path(node.active), "profile_uuid": str(node.target.state.get("uuid", "")), "device_path": _path(node.device)},
                    f"Disconnect {profile_name} on {node.target.state.get('interface', 'the selected adapter')}?",
                ),)
            if node.security == "advanced":
                return (ActionSpec("advanced-settings", "Advanced network profile", ActionKind.OPERATION, {"profile_uuid": str(node.target.state.get("uuid", ""))}, enabled=False, disabled_reason="Hidden, enterprise, WEP, 802.1X, or secondary profiles require NetworkManager's native editor."),)
            if node.target.availability != Availability.AVAILABLE:
                return ()
            if node.target.state.get("connection_type") == _ETHERNET_CONNECTION_TYPE:
                return (ActionSpec(
                    "connect", "Connect", ActionKind.OPERATION,
                    {"profile_uuid": str(node.target.state.get("uuid", "")), "device_path": str(node.target.state.get("device_path", ""))},
                ),)
            device_path = str(node.target.state.get("device_path", ""))
            profile_uuid = str(node.target.state.get("uuid", ""))
            reentry = profile_uuid in self._retry_profiles
            return (ActionSpec(
                "connect", "Retry with a new password" if reentry else "Connect", ActionKind.OPERATION,
                {"profile_uuid": profile_uuid, "device_path": device_path, "reentry": reentry},
            ),)
        if node.kind == "advanced-profile":
            return (ActionSpec(
                "advanced-settings", "Advanced network profile", ActionKind.OPERATION,
                {"profile_uuid": str(node.target.state.get("uuid", ""))}, enabled=False,
                disabled_reason="VPN profiles require NetworkManager's native editor.",
            ),)
        return ()

    @staticmethod
    def _active_connection_name(active: object) -> str:
        connection = _method(active, "get_connection", default=None)
        value = _method(connection, "get_id", default="Wi-Fi connection") if connection is not None else "Wi-Fi connection"
        name = str(value or "Network connection").strip()
        return f"‘{name[:160]}’"

    def _canonical_request_parameters(self, action: ActionSpec, request: OperationRequest) -> dict[str, object] | None:
        expected = dict(action.parameters)
        actual = dict(request.parameters)
        if expected.pop("persistence_choice_required", False):
            persistence = actual.pop("persistence", None)
            if persistence not in {"remember", "once"}:
                return None
            if actual != expected:
                return None
            actual["persistence"] = persistence
            return actual
        return actual if actual == expected else None

    def _new_operation(self, request: OperationRequest, node: _Node, kind: str) -> _Operation:
        owner, epoch = self._owner_epoch()
        generation = self._generations.get(node.target.ref, 0) + 1
        self._generations[node.target.ref] = generation
        pending = PendingRef(uuid.uuid4().hex, request.target, generation)
        op = _Operation(
            pending=pending,
            request_id=request.request_id,
            owner=owner,
            epoch=epoch,
            target_ref=request.target,
            action_id=request.action_id,
            kind=kind,
            cancellable=self._need_modules().Gio.Cancellable.new(),
        )
        self._operations[pending.request_id] = op
        return op

    @staticmethod
    def _request_signature(request: OperationRequest) -> str:
        return _digest([
            request.invocation_id, request.target.to_json(), request.action_id,
            request.expected_revision, dict(request.parameters),
        ])

    def _cache_result(self, request: OperationRequest, result: OperationResult) -> OperationResult:
        self._results[request.request_id] = (self._request_signature(request), result)
        if len(self._results) > PENDING_LIMIT:
            self._results.pop(next(iter(self._results)))
        return result

    def execute(self, request: OperationRequest) -> OperationResult:
        signature = self._request_signature(request)
        prior = self._results.get(request.request_id)
        if prior:
            if prior[0] == signature:
                return prior[1]
            return OperationResult(ResultKind.ERROR, "Request identity was reused for a different network operation.")
        try:
            self._fresh()
            node = self._nodes.get(request.target)
            if node is None:
                raise NetworkError("NetworkManager target changed; refresh and select it again")
            if node.target.revision != request.expected_revision:
                raise NetworkError("Network state changed; review the refreshed action before retrying")
            actions = self.actions(request.target)
            action = next((item for item in actions if item.action_id == request.action_id), None)
            if action is None or not action.enabled:
                raise NetworkError(action.disabled_reason if action else "Network action is no longer available")
            parameters = self._canonical_request_parameters(action, request)
            if parameters is None:
                raise NetworkError("Network action parameters changed; review the current choice")
            if request.action_id == "set-wifi-radio":
                desired_on = parameters.get("desired_on")
                if type(desired_on) is not bool:
                    raise NetworkError("Global Wi-Fi radio intent is invalid")
                if desired_on is False and action.kind != ActionKind.CONFIRM:
                    raise NetworkError("Turning off global Wi-Fi requires the current confirmation")
                if desired_on is True and action.kind == ActionKind.CONFIRM:
                    raise NetworkError("Global Wi-Fi state changed; review the current confirmation")
                return self._set_radio(request, node, desired_on)
            if request.action_id == "rescan":
                return self._rescan(request, node)
            if request.action_id == "disconnect":
                return self._disconnect(request, node, parameters)
            if request.action_id == "connect" and node.kind == "ap":
                if node.profile_matches:
                    if len(node.profile_matches) != 1:
                        raise NetworkError("Several saved profiles match; select one exact profile")
                    profile = self._profiles_by_uuid.get(node.profile_matches[0])
                    if profile is None:
                        raise NetworkError("Saved profile disappeared; refresh the network list")
                    compatible_ap = next((ap for ap in node.aps if self._ap_accepts_profile(ap, profile)), None)
                    if compatible_ap is None:
                        raise NetworkError("Saved profile is no longer compatible with a scanned access point")
                    op = self._new_operation(request, node, "activate")
                    op.profile_uuid = str(_method(profile, "get_uuid", default=""))
                    op.device_path = _path(node.device)
                    op.ap_path = _path(compatible_ap)
                    op.persistence = "saved"
                    op.security = node.security
                    op.ssid = node.ssid
                    if bool(parameters.get("reentry")):
                        op.kind = "profile-reentry"
                        op.profile_reentry = True
                        op.waiting_secret = True
                        return self._cache_result(request, OperationResult(
                            ResultKind.NEEDS_SECRET,
                            self._storage_message("saved", int(_method(self._security_setting(profile), "get_psk_flags", default=0) or 0)),
                            pending=op.pending, secret_prompt="Wi-Fi password",
                        ))
                    self._start_existing_activation(op, profile, node.device, compatible_ap)
                    return self._submit_result(op)
                if parameters.get("persistence") not in {"remember", "once"}:
                    raise NetworkError("Choose whether to remember this new Wi-Fi connection first")
                op = self._new_operation(request, node, "new-profile")
                op.persistence = str(parameters["persistence"])
                op.device_path = _path(node.device)
                op.ap_path = _path(node.ap)
                op.security = node.security
                op.ssid = node.ssid
                if op.security in {"wpa-psk", "sae"}:
                    op.waiting_secret = True
                    return self._cache_result(request, OperationResult(
                        ResultKind.NEEDS_SECRET,
                        message=self._storage_message(op.persistence, 0),
                        pending=op.pending,
                        secret_prompt="Wi-Fi password",
                    ))
                return self._start_new_profile(op, None)
            if request.action_id == "connect" and node.kind == "profile":
                profile_uuid = str(node.target.state.get("uuid", ""))
                profile = self._profiles_by_uuid.get(profile_uuid)
                if profile is None or self._profile_uuid(profile) != profile_uuid:
                    raise NetworkError("Saved network profile disappeared; refresh the list")
                if node.target.state.get("connection_type") == _ETHERNET_CONNECTION_TYPE:
                    if node.target.availability != Availability.AVAILABLE:
                        raise NetworkError("Saved Ethernet profile is unavailable on this adapter")
                    device_path = str(parameters.get("device_path", ""))
                    if device_path != str(node.target.state.get("device_path", "")) or not device_path:
                        raise NetworkError("Selected Ethernet adapter changed; review the current profile row")
                    device = self._device_by_path.get(device_path)
                    if device is None or int(_method(device, "get_device_type", default=-1)) not in {_DEVICE_ETHERNET, _DEVICE_VETH}:
                        raise NetworkError("Selected Ethernet adapter disappeared")
                    if not bool(_method(device, "get_managed", default=True)) or _method(device, "get_carrier", default=None) is False:
                        raise NetworkError("Selected Ethernet adapter is unmanaged or has no carrier")
                    if not self._profile_available_on_device(profile, device):
                        raise NetworkError("Saved Ethernet profile is no longer available on this adapter")
                    op = self._new_operation(request, node, "activate")
                    op.profile_uuid = profile_uuid
                    op.device_path = device_path
                    op.persistence = "saved"
                    self._start_existing_activation(op, profile, device, None)
                    return self._submit_result(op)
                reentry = bool(parameters.get("reentry"))
                op = self._new_operation(request, node, "profile-reentry" if reentry else "activate")
                op.profile_uuid = profile_uuid
                op.device_path = str(parameters.get("device_path") or node.target.state.get("device_path") or "")
                op.persistence = "saved"
                op.security = node.security
                op.ssid = node.ssid
                if reentry:
                    op.waiting_secret = True
                    op.profile_reentry = True
                    return self._cache_result(request, OperationResult(
                        ResultKind.NEEDS_SECRET,
                        message=self._storage_message(
                            "saved",
                            int(_method(self._security_setting(profile), "get_psk_flags", default=0) or 0),
                        ),
                        pending=op.pending,
                        secret_prompt="Wi-Fi password",
                    ))
                device = self._device_by_path.get(op.device_path) if op.device_path else self._select_device_for_profile(profile)
                if device is None:
                    raise NetworkError("No compatible Wi-Fi adapter is available for this saved profile")
                op.device_path = _path(device)
                self._start_existing_activation(op, profile, device, None)
                return self._submit_result(op)
            if request.action_id == "advanced-settings":
                raise NetworkError("Use NetworkManager's native editor for this advanced profile")
            raise NetworkError("Unsupported NetworkManager action")
        except (NetworkError, NMUnavailable, ValueError, TypeError) as error:
            return self._cache_result(request, OperationResult(ResultKind.ERROR, str(error)[:1024]))
        except Exception as error:
            # Do not include exception text: third-party/native exception strings
            # can contain values copied from connection settings.
            return self._cache_result(request, OperationResult(ResultKind.ERROR, "NetworkManager rejected the operation"))

    @staticmethod
    def _storage_message(persistence: str, flags: int) -> str:
        if persistence == "once":
            return "This password stays in the volatile NetworkManager profile and is removed on disconnect."
        if flags == _SECRET_AGENT_OWNED:
            return "This credential will be saved in Secret Service for this NetworkManager profile."
        if flags == _SECRET_NOT_SAVED:
            return "This credential will be used for this connection attempt and will not be saved."
        if persistence == "saved":
            return "NetworkManager manages this profile's credential storage."
        return "NetworkManager will store this password in the new per-user profile."

    def _result_target(self, ref: TargetRef) -> TargetSnapshot | None:
        try:
            self._fresh()
        except Exception:
            return None
        node = self._nodes.get(ref)
        return node.target if node else None

    def _submit_result(self, op: _Operation) -> OperationResult:
        self._drive(op, OPERATION_WAIT_SECONDS)
        if op.secret_request:
            profile = self._profiles_by_uuid.get(op.profile_uuid)
            security = self._security_setting(profile) if profile else None
            flags = int(_method(security, "get_psk_flags", default=0) or 0) if security else 0
            return OperationResult(
                ResultKind.NEEDS_SECRET, message=self._storage_message("saved", flags),
                target=self._result_target(op.target_ref), pending=op.pending,
                secret_prompt="Wi-Fi password",
            )
        if op.error:
            self._cleanup_created_profile(op)
            return OperationResult(ResultKind.ERROR, op.error, target=self._result_target(op.target_ref))
        observed = self._operation_observation(op)
        if observed is not None:
            return observed
        return OperationResult(ResultKind.PENDING, "NetworkManager accepted the request; connection state is still being observed.", target=self._result_target(op.target_ref), pending=op.pending)

    def _start_existing_activation(self, op: _Operation, profile: object, device: object, ap: object | None) -> None:
        client = self._client
        modules = self._need_modules()
        self._ensure_agent(op, profile)
        op.accepted = False

        def finished(_source: object, result: object, _data: object = None) -> None:
            try:
                op.active = client.activate_connection_finish(result)
                op.active_path = _path(op.active)
                op.accepted = bool(op.active_path)
                if not op.accepted:
                    op.error = "NetworkManager did not return the requested active connection"
            except Exception as error:
                op.error = self._friendly_nm_error(error)

        self._runtime.push()
        try:
            op.submitted = True
            client.activate_connection_async(profile, device, _path(ap) if ap else None, op.cancellable, finished, None)
        except Exception as error:
            op.error = self._friendly_nm_error(error)
        finally:
            self._runtime.pop()

    def _ensure_agent(self, op: _Operation, profile: object) -> None:
        security = self._security_setting(profile)
        if security is None:
            return
        flags = int(_method(security, "get_psk_flags", default=0) or 0)
        if flags not in {_SECRET_AGENT_OWNED, _SECRET_NOT_SAVED}:
            return
        uuid_value = str(_method(profile, "get_uuid", default=""))
        profile_path = _path(profile)
        if not uuid_value or not profile_path:
            raise NetworkError("Saved profile identity is unavailable for its secret agent")
        if op.agent is not None:
            return
        modules = self._need_modules()
        bus_address = self._bus_address
        if bus_address is None and self._client_connection is not None:
            bus_address = _method(self._client_connection, "get_address", default=None)
        if self._agent_factory is NetworkSecretAgent:
            agent_context, agent_connection = NetworkSecretAgent.new_context_connection(bus_address)
        else:
            agent_context, agent_connection = self._runtime.context, self._client_connection
        op.agent = self._agent_factory(
            identifier=f"org.niri_plus.rofi.{uuid.uuid4().hex}",
            dbus_connection=agent_connection,
            secret_store=self._secret_store,
            expected_uuid=uuid_value,
            expected_connection_path=profile_path,
            request_secret=lambda secret_request: self._agent_needs_secret(op, secret_request),
            context=agent_context,
        )
        if hasattr(op.agent, "register"):
            try:
                op.agent.register(timeout=self._timeout)
            except Exception as error:
                op.agent.close()
                op.agent = None
                raise NetworkError("No compatible NetworkManager secret agent could be registered") from error
        elif hasattr(op.agent, "register_async"):
            try:
                self._runtime.push()
                self._runtime.run_async(
                    lambda callback: op.agent.register_async(None, callback, None),
                    lambda result: op.agent.register_finish(result),
                    timeout=self._timeout,
                )
            except Exception as error:
                op.agent.close()
                op.agent = None
                raise NetworkError("No compatible NetworkManager secret agent could be registered") from error
            finally:
                self._runtime.pop()

    def _agent_needs_secret(self, op: _Operation, request: SecretRequest) -> PendingRef | None:
        if self._closed or op.error or op.prompt_count >= 1:
            return None
        if request.connection_uuid != op.profile_uuid or request.connection_path != _path(self._profiles_by_uuid.get(op.profile_uuid)):
            return None
        if request.setting_name != WIFI_SECURITY_SETTING:
            return None
        op.prompt_count += 1
        op.secret_request = op.pending
        op.waiting_secret = True
        return op.pending

    def _start_new_profile(self, op: _Operation, password: str | None) -> OperationResult:
        NM = self._need_modules().NM
        if op.security not in {"open", "wpa-psk", "sae"} or not op.ssid:
            raise NetworkError("New network security could not be identified safely")
        device = self._device_by_path.get(op.device_path)
        if device is None:
            raise NetworkError("Selected Wi-Fi adapter disappeared")
        connection = NM.SimpleConnection.new()
        setting_connection = NM.SettingConnection.new()
        ssid_name = _display_ssid(op.ssid)
        setting_connection.set_property("id", f"Wi-Fi {ssid_name}"[:240])
        setting_connection.set_property("uuid", str(uuid.uuid4()))
        setting_connection.set_property("type", "802-11-wireless")
        setting_connection.set_property("autoconnect", op.persistence == "remember")
        setting_connection.set_property("permissions", [f"user:{self._username}:"])
        setting_wireless = NM.SettingWireless.new()
        setting_wireless.set_property("ssid", self._modules.GLib.Bytes.new(op.ssid))
        setting_wireless.set_property("mode", "infrastructure")
        connection.add_setting(setting_connection)
        connection.add_setting(setting_wireless)
        ip4 = NM.SettingIP4Config.new()
        ip4.set_property("method", "auto")
        ip6 = NM.SettingIP6Config.new()
        ip6.set_property("method", "auto")
        connection.add_setting(ip4)
        connection.add_setting(ip6)
        if op.security in {"wpa-psk", "sae"}:
            if password is None:
                raise NetworkError("A Wi-Fi password is required before creating this profile")
            security = NM.SettingWirelessSecurity.new()
            security.set_property("key-mgmt", op.security)
            security.set_property("psk-flags", 0)
            security.set_property("psk", password)
            connection.add_setting(security)
        options = self._modules.GLib.Variant("a{sv}", {
            "persist": self._modules.GLib.Variant("s", "disk" if op.persistence == "remember" else "volatile"),
        })
        client = self._client

        def finished(_source: object, result: object, _data: object = None) -> None:
            try:
                returned = client.add_and_activate_connection2_finish(result)
                op.active = returned[0] if isinstance(returned, tuple) else returned
                op.active_path = _path(op.active)
                op.accepted = bool(op.active_path)
                profile = _method(op.active, "get_connection", default=None) if op.active else None
                if profile is not None:
                    op.created_profile = profile
                    op.created_profile_uuid = str(_method(profile, "get_uuid", default=""))
                    op.created_profile_path = _path(profile)
                    op.profile_uuid = op.created_profile_uuid
                    op.created_profile_fingerprint = self._profile_fingerprint(profile)
                    op.created_volatile = op.persistence == "once"
                if not op.accepted:
                    op.error = "NetworkManager did not accept the new connection request"
            except Exception as error:
                op.error = self._friendly_nm_error(error)

        self._runtime.push()
        try:
            op.submitted = True
            self._client.add_and_activate_connection2(
                connection, device, op.ap_path or None, options, op.cancellable, finished, None,
            )
        except Exception as error:
            op.error = self._friendly_nm_error(error)
        finally:
            self._runtime.pop()
        self._drive(op, OPERATION_WAIT_SECONDS)
        if op.error:
            return OperationResult(ResultKind.ERROR, op.error, target=self._result_target(op.target_ref))
        observed = self._operation_observation(op)
        if observed is not None:
            return observed
        return OperationResult(ResultKind.PENDING, "NetworkManager accepted the new profile; connection state is still being observed.", target=self._result_target(op.target_ref), pending=op.pending)

    def _profile_reentry(self, op: _Operation, password: str) -> OperationResult:
        profile = self._profiles_by_uuid.get(op.profile_uuid)
        if profile is None:
            raise NetworkError("Saved profile changed before the new credential was submitted")
        security = self._security_setting(profile)
        if security is None:
            raise NetworkError("Saved profile no longer has a personal Wi-Fi credential")
        flags = int(_method(security, "get_psk_flags", default=0) or 0)
        if flags == _SECRET_AGENT_OWNED:
            self._ensure_agent(op, profile)
            try:
                op.agent.prime_secret(password, secret_flags=flags)
            except (SecretStoreError, NMUnavailable) as error:
                raise NetworkError(str(error)) from error
        elif flags == _SECRET_NOT_SAVED:
            self._ensure_agent(op, profile)
            op.agent.prime_secret(password, secret_flags=flags)
        else:
            # Update only the PSK value through NetworkManager. The existing
            # profile's secret flags and all non-secret settings are retained.
            clone = self._modules.NM.SimpleConnection.new_clone(profile)
            clone_security = self._security_setting(clone)
            clone_security.set_property("psk", password)
            serialized = clone.to_dbus(self._modules.NM.ConnectionSerializationFlags.ALL)
            flags_type = self._modules.NM.SettingsUpdate2Flags.TO_DISK
            try:
                self._runtime.push()
                self._runtime.run_async(
                    lambda callback: profile.update2(serialized, flags_type, None, op.cancellable, callback, None),
                    lambda result: profile.update2_finish(result),
                    timeout=self._timeout,
                    cancellable=op.cancellable,
                )
            except Exception as error:
                raise NetworkError("NetworkManager could not update the saved PSK") from error
            finally:
                self._runtime.pop()
            profile = self._profiles_by_uuid.get(op.profile_uuid, profile)
        device = self._device_by_path.get(op.device_path) if op.device_path else self._select_device_for_profile(profile)
        if device is None:
            raise NetworkError("No compatible Wi-Fi adapter is available for this profile")
        self._start_existing_activation(op, profile, device, None)
        return self._submit_result(op)

    def _select_device_for_profile(self, profile: object):
        connection = self._connection_setting(profile)
        interface = str(_method(connection, "get_interface_name", default="") or "") if connection else ""
        expected_types = {_DEVICE_WIFI} if _method(connection, "get_connection_type", default="") == _WIFI_CONNECTION_TYPE else {_DEVICE_ETHERNET, _DEVICE_VETH}
        devices = [
            d for d in self._device_by_path.values()
            if int(_method(d, "get_device_type", default=-1)) in expected_types
            and (not interface or _method(d, "get_iface", default="") == interface)
        ]
        if len(devices) == 1:
            return devices[0]
        return None

    def _set_radio(self, request: OperationRequest, node: _Node, enabled: bool) -> OperationResult:
        if node.kind != "radio":
            raise NetworkError("Global Wi-Fi radio target changed")
        if not bool(_method(self._client, "wireless_hardware_get_enabled", default=True)):
            raise NetworkError("Wi-Fi is blocked by the hardware switch")
        current = bool(_method(self._client, "wireless_get_enabled", default=False))
        if current == enabled:
            return self._cache_result(request, OperationResult(ResultKind.COMPLETE, "Wi-Fi radio is already in the requested state.", target=node.target))
        self._client.wireless_set_enabled(enabled)
        op = self._new_operation(request, node, "radio")
        op.desired_radio = enabled
        op.submitted = True
        op.accepted = True
        self._drive(op, OPERATION_WAIT_SECONDS)
        result = self._operation_observation(op)
        if result is None:
            result = OperationResult(ResultKind.PENDING, "NetworkManager accepted the global radio change; waiting for observed state.", target=self._result_target(node.target.ref), pending=op.pending)
        return self._cache_result(request, result)

    def _rescan(self, request: OperationRequest, node: _Node) -> OperationResult:
        if node.kind != "device" or node.target.availability != Availability.AVAILABLE:
            raise NetworkError("Selected Wi-Fi adapter is unavailable")
        device = node.device
        device_path = _path(device)
        now = int(_method(device, "get_last_scan", default=0) or 0)
        existing = next((
            op for op in self._operations.values()
            if op.kind == "scan" and op.device_path == device_path and not op.error and not self._terminal(op)
        ), None)
        if existing:
            return self._cache_result(request, OperationResult(ResultKind.PENDING, "A scan for this adapter is already in progress.", target=node.target, pending=existing.pending))
        monotonic_now = int(_method(self._need_modules().GLib, "get_monotonic_time", default=0) or 0)
        if now and monotonic_now >= now and monotonic_now - now < int(MAX_SCAN_AGE_SECONDS * 1_000_000):
            return self._cache_result(request, OperationResult(ResultKind.COMPLETE, "A fresh scan is already available for this adapter.", target=node.target))
        op = self._new_operation(request, node, "scan")
        op.device_path = device_path
        op.last_scan = now
        op.scan_device = device
        self._runtime.push()
        try:
            op.submitted = True
            device.request_scan_async(op.cancellable, self._scan_finished(op), None)
        except Exception as error:
            op.error = self._friendly_nm_error(error)
        finally:
            self._runtime.pop()
        self._drive(op, 0.2)
        if op.error:
            return self._cache_result(request, OperationResult(ResultKind.ERROR, op.error, target=self._result_target(node.target.ref)))
        return self._cache_result(request, OperationResult(ResultKind.PENDING, "NetworkManager accepted a rescan for this adapter.", target=node.target, pending=op.pending))

    def _scan_finished(self, op: _Operation):
        def finished(device: object, result: object, _data: object = None) -> None:
            try:
                device.request_scan_finish(result)
                op.accepted = True
            except Exception as error:
                op.error = self._friendly_nm_error(error)
        return finished

    def _disconnect(self, request: OperationRequest, node: _Node, parameters: Mapping[str, object]) -> OperationResult:
        active_path = str(parameters.get("active_path", ""))
        profile_uuid = str(parameters.get("profile_uuid", ""))
        device_path = str(parameters.get("device_path", ""))
        active = self._active_by_path.get(active_path)
        if not active or _path(active) != active_path:
            raise NetworkError("The exact active connection disappeared; no replacement was disconnected")
        if profile_uuid and self._active_profile_uuid(active) != profile_uuid:
            raise NetworkError("The active profile changed; no replacement was disconnected")
        if device_path and device_path not in self._active_device_paths(active):
            raise NetworkError("The active adapter changed; no replacement was disconnected")
        op = self._new_operation(request, node, "disconnect")
        op.active_path = active_path
        op.active = active
        op.profile_uuid = self._active_profile_uuid(active)
        op.device_path = next(iter(sorted(self._active_device_paths(active))), "")
        self._start_deactivation(op, active)
        self._drive(op, OPERATION_WAIT_SECONDS)
        if op.error:
            return self._cache_result(request, OperationResult(ResultKind.ERROR, op.error, target=self._result_target(request.target)))
        observed = self._operation_observation(op)
        if observed is None:
            observed = OperationResult(ResultKind.PENDING, "Disconnect request accepted; waiting for this active connection to stop.", target=self._result_target(request.target), pending=op.pending)
        return self._cache_result(request, observed)

    def _start_deactivation(self, op: _Operation, active: object) -> None:
        def finished(_source: object, result: object, _data: object = None) -> None:
            try:
                self._client.deactivate_connection_finish(result)
                op.accepted = True
            except Exception as error:
                op.error = self._friendly_nm_error(error)
        self._runtime.push()
        try:
            op.submitted = True
            self._client.deactivate_connection_async(active, op.cancellable, finished, None)
        except Exception as error:
            op.error = self._friendly_nm_error(error)
        finally:
            self._runtime.pop()

    def _drive(self, op: _Operation, seconds: float) -> None:
        deadline = time.monotonic() + max(0.0, seconds)
        while time.monotonic() < deadline and not op.error:
            if op.secret_request or op.accepted and self._terminal(op):
                return
            self._runtime.iterate_for(5)
            if op.agent is not None:
                iterate = getattr(op.agent, "iterate_for", None)
                if callable(iterate):
                    iterate(5)

    def _terminal(self, op: _Operation) -> bool:
        if op.kind == "radio":
            return bool(_method(self._client, "wireless_get_enabled", default=False)) == op.desired_radio
        if op.kind == "scan":
            return bool(_method(op.scan_device, "get_last_scan", default=0) and int(_method(op.scan_device, "get_last_scan", default=0)) > op.last_scan)
        active = self._active_by_path.get(op.active_path) if op.active_path else op.active
        if active is None:
            return False
        state = int(_method(active, "get_state", default=0) or 0)
        return state in {_ACTIVE_ACTIVATED, _ACTIVE_DEACTIVATED}

    def _operation_observation(self, op: _Operation) -> OperationResult | None:
        if op.error:
            return OperationResult(ResultKind.ERROR, op.error, target=self._result_target(op.target_ref))
        try:
            owner, epoch = self._owner_epoch()
        except NetworkError:
            return OperationResult(ResultKind.UNAVAILABLE, "NetworkManager disappeared; request state is unknown.")
        if owner != op.owner or epoch != op.epoch:
            return OperationResult(ResultKind.ERROR, "NetworkManager restarted; this operation handle is stale.")
        target = self._result_target(op.target_ref)
        try:
            owner, epoch = self._owner_epoch()
        except NetworkError:
            return OperationResult(ResultKind.UNAVAILABLE, "NetworkManager disappeared; request state is unknown.")
        if owner != op.owner or epoch != op.epoch:
            return OperationResult(ResultKind.ERROR, "NetworkManager restarted; this operation handle is stale.")
        if op.secret_request:
            profile = self._profiles_by_uuid.get(op.profile_uuid)
            security = self._security_setting(profile) if profile else None
            flags = int(_method(security, "get_psk_flags", default=0) or 0) if security else 0
            return OperationResult(
                ResultKind.NEEDS_SECRET, self._storage_message("saved", flags), target=target,
                pending=op.pending, secret_prompt="Wi-Fi password",
            )
        if op.kind == "radio":
            current = bool(_method(self._client, "wireless_get_enabled", default=False))
            if current == op.desired_radio:
                return OperationResult(ResultKind.COMPLETE, "Observed the requested global Wi-Fi radio state.", target=target)
            return None
        if op.kind == "scan":
            current = int(_method(op.scan_device, "get_last_scan", default=0) or 0)
            if current > op.last_scan:
                return OperationResult(ResultKind.COMPLETE, "Observed a fresh scan for the selected adapter.", target=target)
            if op.error:
                return OperationResult(ResultKind.ERROR, op.error, target=target)
            return None
        if op.kind == "disconnect":
            try:
                self._fresh()
            except Exception:
                return OperationResult(ResultKind.UNAVAILABLE, "Could not read current connection state.")
            if self._owner != op.owner or self._epoch != op.epoch:
                return OperationResult(ResultKind.ERROR, "NetworkManager restarted; this operation handle is stale.")
            current = self._active_by_path.get(op.active_path)
            if current is None:
                return OperationResult(ResultKind.COMPLETE, "Observed that the selected active connection ended.", target=self._nodes.get(op.target_ref).target if op.target_ref in self._nodes else None)
            if self._active_profile_uuid(current) != op.profile_uuid or (op.device_path and op.device_path not in self._active_device_paths(current)):
                return OperationResult(ResultKind.ERROR, "Active connection identity changed; no replacement was disconnected.", target=target)
            if int(_method(current, "get_state", default=0) or 0) == _ACTIVE_DEACTIVATED:
                return OperationResult(ResultKind.COMPLETE, "Observed the selected active connection stop.", target=target)
            return None
        if not op.active_path:
            return None
        try:
            self._fresh()
        except Exception:
            return OperationResult(ResultKind.UNAVAILABLE, "Could not read current connection state.")
        if self._owner != op.owner or self._epoch != op.epoch:
            return OperationResult(ResultKind.ERROR, "NetworkManager restarted; this operation handle is stale.")
        active = self._active_by_path.get(op.active_path)
        if active is None:
            active = op.active
        if active is None or _path(active) != op.active_path:
            return OperationResult(ResultKind.ERROR, "Accepted connection handle is no longer available.", target=target)
        if self._active_profile_uuid(active) != op.profile_uuid and op.profile_uuid:
            return OperationResult(ResultKind.ERROR, "Accepted connection now refers to a different profile.", target=target)
        if op.device_path and op.device_path not in self._active_device_paths(active):
            return OperationResult(ResultKind.ERROR, "Accepted connection now refers to a different Wi-Fi adapter.", target=target)
        state = int(_method(active, "get_state", default=0) or 0)
        if state == _ACTIVE_ACTIVATED:
            if op.profile_uuid:
                self._retry_profiles.discard(op.profile_uuid)
            return OperationResult(ResultKind.COMPLETE, "Observed NetworkManager activate the selected profile.", target=target)
        if state == _ACTIVE_DEACTIVATED:
            reason = int(_method(active, "get_state_reason", default=0) or 0)
            if reason in {9, 10}:
                if op.profile_uuid:
                    self._retry_profiles.add(op.profile_uuid)
                return OperationResult(ResultKind.ERROR, "Wi-Fi authentication failed. Retry explicitly with a new password.", target=target)
            return OperationResult(ResultKind.ERROR, "NetworkManager ended the connection before activation.", target=target)
        return None

    @staticmethod
    def _friendly_nm_error(error: object) -> str:
        domain = str(getattr(error, "domain", ""))
        code = str(getattr(error, "code", ""))
        message = str(getattr(error, "message", ""))
        folded = (domain + " " + code + " " + message).casefold()
        if "usercanceled" in folded or "user canceled" in folded:
            return "Credential entry was canceled; no connection was accepted."
        if "nosecrets" in folded or "no secrets" in folded:
            return "No compatible NetworkManager credential agent provided the requested secret."
        if "permission" in folded or "not authorized" in folded:
            return "NetworkManager denied this operation for the current user."
        return "NetworkManager rejected the requested operation."

    def _read_secret(self, stream: object) -> bytearray:
        try:
            value = stream.read(MAX_SECRET_BYTES + 1)
        except Exception as error:
            raise NetworkError("Credential input could not be read") from error
        if not isinstance(value, (bytes, bytearray)) or not value or len(value) > MAX_SECRET_BYTES:
            raise NetworkError("Credential is empty or exceeds its size limit")
        return bytearray(value)

    @staticmethod
    def _validate_psk(secret: bytearray, security: str) -> str:
        try:
            value = secret.decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            raise NetworkError("Wi-Fi credentials must be valid UTF-8 text") from error
        if "\x00" in value:
            raise NetworkError("Wi-Fi credential contains an invalid character")
        encoded = value.encode("utf-8")
        if not encoded:
            raise NetworkError("Wi-Fi credential is empty")
        if security == "wpa-psk":
            valid = (8 <= len(encoded) <= 63) or (len(encoded) == 64 and all(c in "0123456789abcdefABCDEF" for c in value))
            if not valid:
                raise NetworkError("WPA personal passwords must be 8–63 characters or a 64-digit hexadecimal key")
        elif security == "sae" and not 8 <= len(encoded) <= 63:
            raise NetworkError("WPA3 passwords must be 8–63 characters")
        return value

    def provide_secret(self, pending: PendingRef, secret_stream: object) -> OperationResult:
        if self._closed:
            return OperationResult(ResultKind.ERROR, "Network controls closed; this credential prompt was canceled.")
        op = self._find_operation(pending)
        raw = self._read_secret(secret_stream)
        try:
            secret = self._validate_psk(raw, op.security)
            if not op.waiting_secret:
                raise NetworkError("This operation is not waiting for a credential")
            op.waiting_secret = False
            if op.kind == "new-profile":
                result = self._start_new_profile(op, secret)
                if result.kind in {ResultKind.ERROR, ResultKind.CANCELLED}:
                    self._cleanup_created_profile(op)
                return result
            if op.profile_reentry:
                result = self._profile_reentry(op, secret)
                return result
            if op.agent is None or op.secret_request != pending:
                raise NetworkError("Credential request is stale or no longer owned by this invocation")
            op.agent.complete_secret(pending, secret)
            op.secret_request = None
            op.waiting_secret = False
            self._drive(op, OPERATION_WAIT_SECONDS)
            observed = self._operation_observation(op)
            if observed is not None:
                return observed
            return OperationResult(ResultKind.PENDING, "Credential submitted; waiting for NetworkManager's current connection state.", target=self._result_target(op.target_ref), pending=op.pending)
        except (NetworkError, NMUnavailable, SecretStoreError) as error:
            op.error = str(error)[:1024]
            self._cleanup_created_profile(op)
            return OperationResult(ResultKind.ERROR, op.error, target=self._result_target(op.target_ref))
        except Exception:
            op.error = "NetworkManager could not complete this credential attempt"
            self._cleanup_created_profile(op)
            return OperationResult(ResultKind.ERROR, op.error, target=self._result_target(op.target_ref))
        finally:
            raw[:] = b"\x00" * len(raw)

    def _find_operation(self, pending: PendingRef) -> _Operation:
        op = self._operations.get(pending.request_id)
        if op is None or op.pending != pending or op.target_ref != pending.target:
            raise NetworkError("Pending network operation is unknown or stale")
        owner, epoch = self._owner_epoch()
        if op.owner != owner or op.epoch != epoch:
            raise NetworkError("NetworkManager restarted; pending operation is stale")
        return op

    def refresh(self, pending: PendingRef) -> OperationResult:
        try:
            op = self._find_operation(pending)
            self._drive(op, 0.15)
            result = self._operation_observation(op)
            if result is not None:
                return result
            return OperationResult(ResultKind.PENDING, "NetworkManager accepted the request; waiting for observed native state.", target=self._result_target(op.target_ref), pending=op.pending)
        except NetworkError as error:
            return OperationResult(ResultKind.ERROR, str(error))

    def cancel(self, pending: PendingRef) -> OperationResult:
        try:
            op = self._find_operation(pending)
            if op.kind in {"new-profile", "profile-reentry"} and not op.submitted:
                if op.agent:
                    op.agent.close()
                    op.agent = None
                op.waiting_secret = False
                op.secret_request = None
                op.error = "Credential entry was canceled; no NetworkManager request was submitted."
                return OperationResult(ResultKind.CANCELLED, "Credential entry canceled; no NetworkManager profile or connection was submitted.", target=self._result_target(op.target_ref))
            if op.kind == "scan":
                if op.cancellable is not None and not op.accepted:
                    op.cancellable.cancel()
                    return OperationResult(ResultKind.CANCELLED, "The unaccepted scan request was canceled.", target=self._result_target(op.target_ref))
                return OperationResult(ResultKind.ERROR, "NetworkManager accepted the scan; it cannot be canceled safely, so only its result will be observed.", target=self._result_target(op.target_ref))
            if op.kind in {"radio", "disconnect"}:
                return OperationResult(ResultKind.ERROR, "NetworkManager accepted this operation; use the current native state before making another change.", target=self._result_target(op.target_ref))
            if not op.active_path or op.active is None:
                if op.agent and op.secret_request:
                    op.agent.cancel_pending(op.secret_request)
                    op.secret_request = None
                    op.waiting_secret = False
                if not op.submitted and op.cancellable is not None:
                    op.cancellable.cancel()
                    return OperationResult(ResultKind.CANCELLED, "The unsubmitted NetworkManager request was canceled.", target=self._result_target(op.target_ref))
                return OperationResult(ResultKind.ERROR, "NetworkManager has not returned the exact active connection handle; cancellation was not broadened to the device.", target=self._result_target(op.target_ref))
            self._fresh()
            if self._owner != op.owner or self._epoch != op.epoch:
                return OperationResult(ResultKind.ERROR, "NetworkManager restarted; no replacement connection was canceled.")
            active = self._active_by_path.get(op.active_path)
            if active is None or _path(active) != op.active_path:
                return OperationResult(ResultKind.ERROR, "Exact active connection is no longer present; no replacement was disconnected.", target=self._result_target(op.target_ref))
            if self._active_profile_uuid(active) != op.profile_uuid:
                return OperationResult(ResultKind.ERROR, "Active connection profile changed; no replacement was disconnected.", target=self._result_target(op.target_ref))
            if op.device_path and op.device_path not in self._active_device_paths(active):
                return OperationResult(ResultKind.ERROR, "Active connection adapter changed; no replacement was disconnected.", target=self._result_target(op.target_ref))
            if op.agent and op.secret_request:
                op.agent.cancel_pending(op.secret_request)
                op.secret_request = None
                op.waiting_secret = False
            self._start_deactivation(op, active)
            self._drive(op, OPERATION_WAIT_SECONDS)
            self._fresh()
            if self._owner != op.owner or self._epoch != op.epoch:
                return OperationResult(ResultKind.ERROR, "NetworkManager restarted; no replacement connection was canceled.")
            current = self._active_by_path.get(op.active_path)
            if current is None:
                self._cleanup_created_profile(op)
                return OperationResult(ResultKind.CANCELLED, "Canceled this exact active connection.", target=self._result_target(op.target_ref))
            if _path(current) != op.active_path or self._active_profile_uuid(current) != op.profile_uuid:
                return OperationResult(ResultKind.ERROR, "Active connection identity changed; no replacement was canceled.", target=self._result_target(op.target_ref))
            if op.device_path and op.device_path not in self._active_device_paths(current):
                return OperationResult(ResultKind.ERROR, "Active connection adapter changed; no replacement was canceled.", target=self._result_target(op.target_ref))
            if int(_method(current, "get_state", default=0) or 0) == _ACTIVE_DEACTIVATED:
                self._cleanup_created_profile(op)
                return OperationResult(ResultKind.CANCELLED, "Canceled this exact active connection.", target=self._result_target(op.target_ref))
            return OperationResult(ResultKind.PENDING, "Cancellation was submitted for this exact active connection.", target=self._result_target(op.target_ref), pending=op.pending)
        except (NetworkError, NMUnavailable) as error:
            return OperationResult(ResultKind.ERROR, str(error))

    def _cleanup_created_profile(self, op: _Operation) -> None:
        if not op.created_profile_uuid or op.persistence != "once":
            return
        try:
            self._fresh()
            profile = self._profiles_by_uuid.get(op.created_profile_uuid)
            if profile is None or _path(profile) != op.created_profile_path:
                return
            if not op.created_profile_fingerprint or self._profile_fingerprint(profile) != op.created_profile_fingerprint:
                return
            if any(
                self._active_profile_uuid(active) == op.created_profile_uuid
                and int(_method(active, "get_state", default=0) or 0) != _ACTIVE_DEACTIVATED
                for active in self._active_by_path.values()
            ):
                return
            remover = getattr(profile, "delete_async", None)
            if callable(remover):
                self._runtime.push()
                try:
                    self._runtime.run_async(
                        lambda callback: remover(op.cancellable, callback, None),
                        lambda result: profile.delete_finish(result),
                        timeout=min(self._timeout, 3.0),
                    )
                finally:
                    self._runtime.pop()
        except Exception:
            return

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        monitored: list[_Operation] = []
        for op in tuple(self._operations.values()):
            if op.agent:
                if op.secret_request is not None:
                    try:
                        op.agent.cancel_pending(op.secret_request)
                    except Exception:
                        pass
                    op.secret_request = None
                    op.waiting_secret = False
                op.agent.close()
                op.agent = None
            if op.submitted:
                monitored.append(op)
            elif op.cancellable is not None:
                op.waiting_secret = False
                op.secret_request = None
                op.error = "Credential staging was closed before submission."
                try:
                    op.cancellable.cancel()
                except Exception:
                    pass
        self._nodes.clear()
        if monitored:
            # Keep only the bounded, noninteractive request monitor alive after
            # the launcher returns. A daemon thread would die at interpreter
            # exit and violate the accepted native-request lifetime.
            worker = threading.Thread(target=self._monitor_after_close, args=(tuple(monitored),), daemon=False)
            worker.start()
        else:
            self._operations.clear()
            self._close_runtime()

    def _monitor_after_close(self, operations: Sequence[_Operation]) -> None:
        """Observe accepted native requests briefly without prompts or mutation."""

        deadline = min(time.monotonic() + 30.0, *(op.deadline for op in operations))
        try:
            while time.monotonic() < deadline:
                if self._runtime is None:
                    return
                self._runtime.iterate_for(20)
                remaining: list[_Operation] = []
                try:
                    owner, epoch = self._owner_epoch()
                    if owner != self._owner or epoch != self._epoch:
                        break
                except NetworkError:
                    break
                for op in operations:
                    if op.error:
                        continue
                    if op.kind == "radio":
                        current = bool(_method(self._client, "wireless_get_enabled", default=False))
                        if current != op.desired_radio:
                            remaining.append(op)
                    elif op.kind == "scan":
                        if int(_method(op.scan_device, "get_last_scan", default=0) or 0) <= op.last_scan:
                            remaining.append(op)
                    elif op.active_path:
                        active = op.active or next(
                            (item for item in (_method(self._client, "get_active_connections", default=[]) or []) if _path(item) == op.active_path),
                            None,
                        )
                        if active is None or int(_method(active, "get_state", default=0) or 0) not in {_ACTIVE_ACTIVATED, _ACTIVE_DEACTIVATED}:
                            remaining.append(op)
                    elif not op.accepted:
                        remaining.append(op)
                if not remaining:
                    break
                time.sleep(0.025)
        finally:
            self._operations.clear()
            self._close_runtime()

    def _close_runtime(self) -> None:
        if self._owns_client_connection and self._client_connection is not None:
            try:
                self._client_connection.close_sync(None)
            except Exception:
                pass
        if self._runtime is not None:
            self._runtime.close()
