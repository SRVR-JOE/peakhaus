Tag: v1.2.0
Title: PEAKHAUS 1.2.0

First packaged release. Everything needed to run a Puffco Peak Pro from Home Assistant, in one repo.

## In the box

- `custom_components/puffco`: the integration, forked from HA-Puff/home-assistant-puffco. Pairs through an ESPHome Bluetooth proxy by calling pair first on the ESPHome backend, which is what the Peak needs before it will answer any Lorax command. Reads and writes profile colours in the Peak's own CBOR shape, so animated profiles no longer truncate and colours set from Home Assistant stick.
- `esphome/puffco-bridge.yaml`: Bluetooth bridge for an M5Stack ATOM Lite. Active proxy, two connection slots, button and LED exposed.
- `esphome/puffco-dial.yaml`: M5Dial knob remote. Profile wheel, hold to start or stop, stats page, seven faces, no sounds. Talks to Home Assistant only.
- `dashboard/`: the Peak page builder (`peak_cards.py`), the push script that validates every template against your instance before saving, and the rig artwork pipeline.
- `docs/`: install guide, the pairing story, and paste-ready announcement posts.

## Upgrading

From the earlier SRVR-JOE fork (`bluez-agent-pairing` branch): same `puffco` domain, same entity ids, no re-pairing. Point HACS at this repository, download, restart.

From upstream HA-Puff: remove the HA-Puff repository in HACS first, then install this one and restart. Pair the Peak again through an ESPHome proxy: Peak fully off, hold power until the ring pulses blue, then add the integration. The bond moves to the ESP32.

Do not keep both repositories installed. They share the `custom_components/puffco` folder and an update from one overwrites the other.

## Known issues

- A connection timeout can leave the integration in `failed_unload`. Only a Home Assistant restart clears it.
- One API subscriber per ESPHome proxy. A test script that subscribes to advertisements knocks Home Assistant off; reload the ESPHome entry afterwards.
- Rebooting the bridge mid-connection needs a reload of the Puffco entry.

Tested on Peak Pro firmware AW-1d90ae, Home Assistant 2026.9, ESPHome 2026.9.1.
