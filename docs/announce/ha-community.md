Category: Share your Projects!

Title: PEAKHAUS: Puffco Peak Pro in Home Assistant, with an ESP32 bridge and a knob remote

I have had my Puffco Peak Pro in Home Assistant for about a week now and it is solid enough to share.

What you get: heat session control, the four profiles with their names, temperatures and ring colours, battery, dab counters, the lantern with all its effects, stealth mode and the LED brightness zones. All normal entities, so automations and dashboards work the way you expect. There is a ready-made dashboard page in the repo too.

![Peak page](https://raw.githubusercontent.com/SRVR-JOE/peakhaus/main/docs/img/peak-page.jpg)

The part that took the time was pairing. The existing HA-Puff integration knows the protocol, but on Home Assistant OS pairing failed in a fraction of a second every time. The Peak ignores every command until the BLE link is encrypted, and Home Assistant OS has no BlueZ pairing agent, so its adapter never bonds. The Pi 5 radio drops the link on a pairing request anyway.

The fix is an ESPHome Bluetooth proxy. I use an M5Stack ATOM Lite, about eight dollars. The integration detects the ESPHome backend and pairs first, before the protocol handshake. The bond lives in the ESP32 and the Peak reconnects on its own after that first pairing. I also fixed profile colours, which the Peak stores as CBOR and which the original parser truncated.

Optional extra: an M5Dial as a physical remote. Turn the knob to pick a profile, hold it to start a session, tap for stats. It reads from Home Assistant, so it does not need to be near the rig. Seven faces, including a couple of tachometer liveries.

Repo, with install steps and the full story: https://github.com/SRVR-JOE/peakhaus

Install through HACS as a custom repository. The integration is a fork of HA-Puff/home-assistant-puffco and keeps its MIT licence. Happy to answer questions, particularly if you have a different Peak firmware or a non-Pi host.
