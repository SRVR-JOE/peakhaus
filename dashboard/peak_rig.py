"""Compact Peak "rig card" for the home-hub Peak page.

Art is rendered by art/make_peak_rig.py (900x1200 portrait, no baked text) and hosted in HA's image
store via upload_art.py; ids live in art/ids.json under peak/peak_rig_*. The card is a picture-elements
with a single state image overlay: a warm spill under the base ring while a heat session runs.
All text/controls belong in native cards beside it.
"""
import json
import pathlib

_IDS = pathlib.Path(__file__).with_name("art").joinpath("ids.json")
_SERVE = "/api/image/serve/{}/original"


def _url(key):
    ids = json.loads(_IDS.read_text())
    try:
        return _SERVE.format(ids[key]["id"])
    except KeyError:
        raise KeyError(f"{key} missing from {_IDS}; run art/make_peak_rig.py then upload_art.py on a dir named 'peak'")


RIG_BG = _url("peak/peak_rig_bg")
RIG_GLOW = _url("peak/peak_rig_glow")
RIG_NONE = _url("peak/peak_rig_none")


def rig_card(heat_entity="switch.peak_pro_02743_heat_session"):
    return {
        "type": "picture-elements",
        "image": RIG_BG,
        "elements": [{
            "type": "image",
            "entity": heat_entity,
            "image": RIG_NONE,
            "state_image": {"on": RIG_GLOW, "off": RIG_NONE},
            "tap_action": {"action": "none"},
            "hold_action": {"action": "none"},
            "style": {"left": "50%", "top": "50%", "width": "100%", "pointer-events": "none"},
        }],
        "grid_options": {"columns": "full"},
    }
