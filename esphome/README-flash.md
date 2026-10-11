# Flashing the bridge and the Dial

Two ESPHome devices:

| File | Hardware | Role |
|---|---|---|
| `puffco-bridge.yaml` | M5Stack ATOM Lite (ESP32-PICO-D4) | Active Bluetooth proxy between Home Assistant and the Peak. Lives next to the Peak. |
| `puffco-dial.yaml` | M5Stack M5Dial (StampS3 / ESP32-S3) | Remote + display only. Knob = profile, tap = stats, hold = heat session. No BLE. |

## Setup

```sh
uv tool install esphome              # or: pipx install esphome
cp esphome/secrets.example.yaml esphome/secrets.yaml   # fill in Wi-Fi + API keys
```

Run every `esphome` command from the `esphome/` directory so `secrets.yaml` and the images resolve.

## First flash over USB

```sh
cd esphome
esphome run --device /dev/cu.usbserial-XXXX puffco-bridge.yaml   # ATOM Lite (FTDI, shows as "M5stack")
esphome run --device /dev/cu.usbmodemXXXX  puffco-dial.yaml     # M5Dial (USB-JTAG)
```

Both configs keep `improv_serial`, so if you leave the Wi-Fi secrets empty you can provision from
https://web.esphome.io instead. Home Assistant discovers each device over mDNS; paste the matching API key
from `secrets.yaml` when it asks.

## Updates over the air

```sh
cd esphome
esphome run --no-logs --device <bridge-ip> puffco-bridge.yaml
esphome run --no-logs --device <dial-ip>   puffco-dial.yaml
```

**Gotcha:** `esphome upload` flashes whatever was built LAST in that directory's `.esphome/` cache, which may be
the other device. Always use `esphome run` (compile + upload) with an explicit `--device`.

After the Dial reboots, reload the Puffco integration entry in HA if the Peak readings stop updating.

## Pairing the Peak to the bridge

The Bluetooth bond lives in the ESP32, so a new bridge needs one pairing:

1. Flash the bridge and confirm it shows up in HA (Settings → Devices → ESPHome) and as a scanner under the
   Bluetooth integration.
2. Put the Peak in pairing mode: fully OFF, then hold the power button until the ring pulses **blue**. The Peak only
   accepts connections while pulsing.
3. Add (or reload) the Puffco integration. Watch the bridge log if you like:
   `esphome logs --device <bridge-ip> puffco-bridge.yaml` → `Connecting v3 … Connection open … Service discovery complete`.
4. If the first attempt times out, the integration entry can land in `failed_unload`
   ("Timeout waiting for BluetoothDeviceConnectionResponse"). That state cannot be reloaded or disabled/enabled —
   **restart Home Assistant**, re-enter pairing mode, and it connects on the next try.

Once bonded, the bridge reconnects on its own without pairing mode, including after reboots.

## Dial faces

`select.puffco_bt_proxy_gauge_style`: Ring, Race Tach, Ferrari, Porsche, Minimal, Segments, Twin.
The GC9A01 panel on the M5Dial reads green-heavy; bias yellows toward red. IRAM is nearly full on the S3 build, so
adding features may fail to link.
