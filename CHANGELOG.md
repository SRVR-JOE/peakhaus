# Changelog

Upstream history (HA-Puff/home-assistant-puffco up to 1.1.24) is in docs/UPSTREAM-CHANGELOG.md.

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
