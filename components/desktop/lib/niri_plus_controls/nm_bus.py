"""Small libnm/GIO boundary helpers for isolated and native NetworkManager clients."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import time
from typing import Callable, TypeVar


T = TypeVar("T")


class NMUnavailable(RuntimeError):
    """libnm, its D-Bus connection, or the NetworkManager owner is unavailable."""


@dataclass(frozen=True, slots=True)
class NMModules:
    NM: object
    Gio: object
    GLib: object
    Secret: object


def load_nm_modules() -> NMModules:
    """Load optional native bindings without making module import fail on minimal hosts."""

    try:
        import gi

        gi.require_version("NM", "1.0")
        gi.require_version("Secret", "1")
        from gi.repository import Gio, GLib, NM, Secret
    except (ImportError, ValueError) as error:
        raise NMUnavailable("NetworkManager/libsecret Python bindings are unavailable") from error
    return NMModules(NM, Gio, GLib, Secret)


def dedicated_bus_connection(*, address: str | None = None, bus_type: object | None = None):
    """Create a dedicated bus connection; an explicit address supports private-bus tests."""

    modules = load_nm_modules()
    Gio = modules.Gio
    if address is None:
        kind = bus_type if bus_type is not None else Gio.BusType.SYSTEM
        try:
            address = Gio.dbus_address_get_for_bus_sync(kind, None)
        except Exception as error:
            raise NMUnavailable("Could not locate the NetworkManager D-Bus") from error
    flags = Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION
    try:
        return Gio.DBusConnection.new_for_address_sync(address, flags, None, None)
    except Exception as error:
        raise NMUnavailable("Could not connect to the NetworkManager D-Bus") from error


def owner_epoch(client: object) -> tuple[str, str]:
    """Return the live unique owner and a stable, non-secret epoch token."""

    getter = getattr(client, "get_dbus_name_owner", None)
    owner = getter() if callable(getter) else getattr(client, "dbus_name_owner", None)
    if not isinstance(owner, str) or not owner.startswith(":"):
        raise NMUnavailable("NetworkManager is not currently available")
    return owner, hashlib.sha256(owner.encode("utf-8")).hexdigest()[:24]


class GLibRuntime:
    """Own a GLib context and bound all asynchronous native waits."""

    def __init__(self, GLib: object | None = None, *, context: object | None = None):
        if GLib is None:
            GLib = load_nm_modules().GLib
        self.GLib = GLib
        self.context = context or GLib.MainContext.new()
        self._closed = False

    def push(self) -> None:
        if self._closed:
            raise NMUnavailable("NetworkManager context is closed")
        self.context.push_thread_default()

    def pop(self) -> None:
        self.context.pop_thread_default()

    def run_async(
        self,
        start: Callable[[Callable[..., None]], None],
        finish: Callable[[object], T],
        *,
        timeout: float = 8.0,
        cancellable: object | None = None,
    ) -> T:
        """Run one GI async operation on this context and return its finish value."""

        if self._closed:
            raise NMUnavailable("NetworkManager context is closed")
        loop = self.GLib.MainLoop.new(self.context, False)
        outcome: list[object] = []

        def completed(_source: object, result: object, _data: object = None) -> None:
            if outcome:
                return
            try:
                outcome.extend((True, finish(result)))
            except Exception as error:
                outcome.extend((False, error))
            loop.quit()

        def timed_out() -> bool:
            if not outcome:
                outcome.extend((False, TimeoutError("NetworkManager request timed out")))
                if cancellable is not None:
                    try:
                        cancellable.cancel()
                    except Exception:
                        pass
                loop.quit()
            return False

        source = self.GLib.timeout_source_new(max(1, int(timeout * 1000)))
        source.set_callback(timed_out)
        source.attach(self.context)
        try:
            start(completed)
            if not outcome:
                loop.run()
        except Exception:
            source.destroy()
            raise
        source.destroy()
        succeeded, result = outcome
        if not succeeded:
            if isinstance(result, TimeoutError):
                raise result
            raise result
        return result  # type: ignore[return-value]

    def iterate_for(self, milliseconds: int) -> None:
        """Dispatch pending signals/callbacks for a small, bounded interval."""

        if self._closed:
            return
        until = time.monotonic() + max(0, milliseconds) / 1000
        while self.context.pending():
            self.context.iteration(False)
            if time.monotonic() >= until:
                return
        while time.monotonic() < until:
            self.context.iteration(False)
            if not self.context.pending():
                time.sleep(min(0.005, max(0, until - time.monotonic())))

    def close(self) -> None:
        self._closed = True
