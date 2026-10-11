# r/homeassistant

Title: Puffco Peak Pro in Home Assistant: fixed pairing on HA OS with an $8 ESP32 bridge, plus a knob remote

Body:

I got my Peak Pro fully into Home Assistant and packaged it up.

Entities for heat sessions, the four profiles (names, temps, ring colours), battery, dab counters, lantern and effects, stealth mode and LED brightness. A dashboard page is included.

The hard part was pairing. The existing HA-Puff integration speaks the protocol but could not pair on Home Assistant OS. The Peak ignores everything until the BLE link is encrypted, HA OS has no BlueZ pairing agent so the adapter never bonds, and the Pi 5 radio drops the link on a pairing request. Going through an ESPHome Bluetooth proxy (M5Stack ATOM Lite) and pairing first on the ESP32 side made it work. The bond lives in the ESP32 and it reconnects on its own after that.

Optional M5Dial remote: knob picks the profile, hold to start a session, tap for stats. Seven faces.

https://github.com/SRVR-JOE/peakhaus

Fork of HA-Puff/home-assistant-puffco, MIT, installs through HACS as a custom repository. Details and the full pairing story in the README.

# r/puffco

Title: Peak Pro in Home Assistant, with a physical knob remote

Body:

If you run Home Assistant, I packaged up my Peak Pro setup. Start and stop sessions, switch profiles, set profile temps and ring colours, lantern effects, battery and dab counters, all from the dashboard or automations. It needs an $8 ESP32 as a Bluetooth bridge because Home Assistant on a Pi cannot pair with the Peak directly. Optional M5Dial as a knob remote with a few tachometer-style faces.

https://github.com/SRVR-JOE/peakhaus

Tested on a Daybreak with the 3DXL chamber. Not affiliated with Puffco.
