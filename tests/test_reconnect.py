"""Reconnect / hang-safety tests for the Puffco coordinator.

Run:  pip install -r tests/requirements.txt && pytest tests
These build the coordinator without a running Home Assistant (``__new__`` +
the attributes the code under test touches), so they exercise the lock,
timeout and scheduling logic only — not real BLE.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from bleak import BleakClient, BleakError
from homeassistant.components.bluetooth.active_update_coordinator import (
    ActiveBluetoothDataUpdateCoordinator,
)

import custom_components.puffco.coordinator as coord_mod
from custom_components.puffco.coordinator import (
    BleOperationTimeout,
    PuffcoDataUpdateCoordinator,
)
from puffco_ble.ble_client import PuffcoBleakClient
from puffco_ble.client import PuffcoClient

MAC = "F0:AD:4E:42:32:3E"


class FakeClient:
    """Stand-in for PuffcoClient: tracks disconnects, can hang or raise."""

    def __init__(self, connected: bool = True) -> None:
        self.connected = connected
        self.disconnects = 0
        self.disconnect_behaviour: str | None = None  # None | "hang" | "raise"

    @property
    def is_connected(self) -> bool:
        return self.connected

    async def disconnect(self) -> None:
        self.disconnects += 1
        if self.disconnect_behaviour == "hang":
            await asyncio.sleep(3600)
        if self.disconnect_behaviour == "raise":
            raise TimeoutError(
                "Timeout waiting for BluetoothDeviceConnectionResponse after 20.0s"
            )
        self.connected = False

    @property
    def bleak(self):
        if not self.connected:
            raise RuntimeError("Not connected")
        return SimpleNamespace(lantern_color=bytearray(b"\x01\x02\x03"))


def make_coordinator(client: FakeClient | None = None) -> PuffcoDataUpdateCoordinator:
    c = PuffcoDataUpdateCoordinator.__new__(PuffcoDataUpdateCoordinator)
    c.mac = MAC
    c.hass = SimpleNamespace(is_stopping=False)
    c.config_entry = SimpleNamespace(
        async_create_background_task=lambda hass, coro, name: asyncio.ensure_future(
            coro
        ),
        title="Peak Pro test",
    )
    c._client = client or FakeClient()
    c._lock = asyncio.Lock()
    c._ready_event = asyncio.Event()
    c._wake_event = asyncio.Event()
    c._waiting_for_advert = False
    c._last_advert_source = None
    c._last_advert_at = None
    c._shutting_down = False
    c._ble_connected = True
    c._needs_reconnect = False
    c._advertising = False
    c._last_seen = None
    c._last_poll = None
    c._reconnect_task = None
    c._interval_poll_task = None
    c._pending_ble_device = None
    c._session_finishes_at = None
    c._session_timer_unsub = None
    c._on_stop = []
    return c


@pytest.fixture
def short_budgets(monkeypatch):
    monkeypatch.setattr(coord_mod, "LOCKED_GATT_TIMEOUT", 0.05)
    monkeypatch.setattr(coord_mod, "LOCKED_CONNECT_TIMEOUT", 0.05)
    monkeypatch.setattr(coord_mod, "LOCK_ACQUIRE_TIMEOUT", 0.2)
    monkeypatch.setattr(coord_mod, "DISCONNECT_TIMEOUT", 0.05)
    monkeypatch.setattr(coord_mod, "SHUTDOWN_TIMEOUT", 0.5)


def test_hung_op_releases_lock_and_drops_link(short_budgets):
    async def run():
        c = make_coordinator()
        with pytest.raises(BleOperationTimeout):
            async with c._ble_op("fetch"):
                await asyncio.sleep(3600)  # GATT reply that never comes
        assert not c._lock.locked()
        assert c._client.disconnects == 1
        assert c._needs_reconnect and not c._ble_connected
        # The next operation (e.g. the Reconnect button) gets the lock.
        async with c._ble_op("manual reconnect"):
            pass

    asyncio.run(run())


def test_hung_op_with_hanging_disconnect_still_releases(short_budgets):
    async def run():
        c = make_coordinator()
        c._client.disconnect_behaviour = "hang"
        with pytest.raises(BleOperationTimeout):
            async with c._ble_op("fetch"):
                await asyncio.sleep(3600)
        assert not c._lock.locked()

    asyncio.run(run())


def test_body_timeout_error_is_not_treated_as_hang(short_budgets):
    async def run():
        c = make_coordinator()
        with pytest.raises(TimeoutError) as info:
            async with c._ble_op("fetch", timeout=5):
                raise TimeoutError("bleak connect timeout")
        assert not isinstance(info.value, BleOperationTimeout)
        assert c._client.disconnects == 0
        assert not c._lock.locked()

    asyncio.run(run())


def test_lock_wait_is_bounded(short_budgets):
    async def run():
        c = make_coordinator()
        await c._lock.acquire()  # someone else wedged outside _ble_op
        with pytest.raises(BleOperationTimeout):
            async with c._ble_op("command"):
                pass

    asyncio.run(run())


def test_advert_schedules_reconnect_even_if_entity_update_raises(monkeypatch):
    def boom(self, service_info, change):
        raise RuntimeError("Not connected")

    monkeypatch.setattr(
        ActiveBluetoothDataUpdateCoordinator, "_async_handle_bluetooth_event", boom
    )
    c = make_coordinator(FakeClient(connected=False))
    c._needs_reconnect = True
    c._schedule_reconnect = MagicMock()
    info = SimpleNamespace(device=object(), source="C4:9E:7E:12:AB:5E")
    with pytest.raises(RuntimeError):
        c._async_handle_bluetooth_event(info, None)
    c._schedule_reconnect.assert_called_once()
    assert c._advertising


def test_update_listeners_swallows_entity_errors(monkeypatch):
    def boom(self):
        raise RuntimeError("Not connected")

    monkeypatch.setattr(
        ActiveBluetoothDataUpdateCoordinator, "async_update_listeners", boom
    )
    make_coordinator().async_update_listeners()  # must not raise


def test_lantern_color_safe_while_disconnected():
    assert make_coordinator(FakeClient(connected=False)).lantern_color is None
    assert make_coordinator(FakeClient(connected=True)).lantern_color == b"\x01\x02\x03"


def test_new_advert_path_wakes_running_worker():
    async def run():
        c = make_coordinator()
        c._reconnect_task = asyncio.ensure_future(asyncio.sleep(3600))
        c._schedule_reconnect(None)  # same path, no news
        assert not c._wake_event.is_set()
        c._schedule_reconnect(None, wake=True)
        assert c._wake_event.is_set()
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        await c._async_backoff(5)
        assert loop.time() - t0 < 0.5
        assert not c._wake_event.is_set()
        c._reconnect_task.cancel()

    asyncio.run(run())


def test_shutdown_never_raises_on_disconnect_timeout(short_budgets):
    async def run():
        c = make_coordinator()
        c._client.disconnect_behaviour = "raise"
        c._reconnect_task = asyncio.ensure_future(asyncio.sleep(3600))
        c._async_stop = MagicMock()
        await c.async_shutdown()
        assert c._shutting_down
        assert c._reconnect_task is None
        c._async_stop.assert_called_once()

    asyncio.run(run())


def test_puffco_client_disconnect_drops_reference_on_error():
    async def run():
        client = PuffcoClient(MAC)
        backend = MagicMock()
        backend.is_connected = True

        async def fail():
            raise TimeoutError("proxy gone")

        backend.disconnect = fail
        client._client = backend
        with pytest.raises(TimeoutError):
            await client.disconnect()
        assert client._client is None
        assert not client.is_connected

    asyncio.run(run())


def _bare_bleak(monkeypatch, connected: bool) -> PuffcoBleakClient:
    b = PuffcoBleakClient.__new__(PuffcoBleakClient)
    b.transactions = {}
    b.transaction_responses = {}
    b.sequence_id = 0
    b.max_payload = 0
    monkeypatch.setattr(
        PuffcoBleakClient, "is_connected", property(lambda self: connected)
    )

    async def write_gatt_char(self, *args, **kwargs):
        return None  # reply notification never arrives

    monkeypatch.setattr(BleakClient, "write_gatt_char", write_gatt_char)
    return b


def test_lorax_read_short_times_out(monkeypatch):
    async def run():
        b = _bare_bleak(monkeypatch, connected=True)
        with pytest.raises(BleakError, match="timed out"):
            await b.lorax_read_short("/p/bat/cap", timeout=0.05)
        assert b.transactions == {}

    asyncio.run(run())


def test_lorax_read_short_fails_fast_when_disconnected(monkeypatch):
    async def run():
        b = _bare_bleak(monkeypatch, connected=False)
        with pytest.raises(BleakError, match="not connected"):
            await b.lorax_read_short("/p/bat/cap")

    asyncio.run(run())
