# Changelog

Upstream history (HA-Puff/home-assistant-puffco up to 1.1.24) is in docs/UPSTREAM-CHANGELOG.md.

## [1.2.1] - 2026-11-25 — auto-reconnect

### Fixed

- **Reconnect after a proxy reboot / Peak wake without reloading the entry.** The lantern light read
  `PuffcoClient.bleak` while disconnected and raised `RuntimeError: Not connected` inside the Bluetooth
  advertisement, unavailable and disconnect callbacks, aborting them before they scheduled a reconnect
  (1,259 "Error in bluetooth callback" entries on the live install). The light now reads the colour only with a
  live session, the coordinator isolates entity update errors, and reconnects are scheduled before entities
  are touched.
- **A hung GATT op can no longer wedge the BLE lock.** Lorax short reads waited on a reply notification with no
  timeout; a proxy dying mid-read held the coordinator lock forever, stalling the reconnect worker and the
  Reconnect button. Reads now time out (and fail fast when the link is down), and every locked operation runs
  under a budget (150 s with a connect, 45 s otherwise) that force-drops the link and releases the lock.
- **Unload can no longer end in `failed_unload`.** Coordinator teardown is bounded and never raises (an ESPHome
  disconnect timing out after 20 s used to fail the unload); `PuffcoClient.disconnect()` drops its reference even
  when the backend errors. Coordinator tasks are entry background tasks, cancelled on unload.
- A fresh advertisement (new proxy, or the first after a 20 s gap) cuts a running reconnect worker's backoff
  short; the worker prefers HA's current `BLEDevice` over the one cached before a proxy reboot.

### Added

- `tests/` — hang/reconnect unit tests (`pip install -r tests/requirements.txt && pytest tests`).
- `docs/peak_bridge_watchdog.automation.json` — watchdog covering both the ATOM bridge and the watch.

## [1.2.0] - 2026-10-11 — PEAKHAUS

First packaged release: integration + ESPHome Bluetooth bridge + M5Dial remote + dashboard page in one repo.
The integration keeps the `puffco` domain, so existing entity ids are unchanged.

### Fixed (integration, from the SRVR-JOE fork)

- **Pair before Lorax init (652acc4)** — the Peak ignores Lorax commands until the link is encrypted. Reading the
  PUP app-version characteristic forces OS pairing on BlueZ/macOS before GET_LIMITS / seed / UNLOCK.
- **BlueZ pairing agent (911c01d)** — HA OS has no `org.bluez.Agent1`, so the adapter was never bondable. A
  temporary auto-accept agent is registered around the bond trigger and `pair()`, then removed.
- **ESPHome proxies pair first (de31f3a)** — the PUP trigger read returns GATT 0x0F (insufficient encryption) and
  the ESP32 will not start SMP from it, so on an ESPHome backend `pair()` is called before the trigger read.
- **Profile colours as CBOR (1c22cf9)** — `/u/app/hc/N/colr` is `{lamp:{name,param:{color:h'RRGGBB'}}}`; the parser
  now finds the `color` key (animated profiles carry long colour strings) and writes use the same shape. Raw bytes are
  logged at debug level (c4e2481).

### Added

- `esphome/puffco-bridge.yaml` — M5Stack ATOM Lite as a dedicated active Bluetooth proxy next to the Peak.
- `esphome/puffco-dial.yaml` — M5Dial remote/display (tach faces, profile wheel, stats page), no BLE proxy.
- `dashboard/` — single `peak` sections view generator, rig card art and the push/validate script.
