"""Compact Peak "rig card" for the home-hub Peak page.

Art is rendered by peak/make_peak_rig.py (900x1200 portrait, no baked text) and hosted in HA's image
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
        raise KeyError(f"{key} missing from {_IDS}; run peak/make_peak_rig.py then upload_art.py on a dir named 'peak'")


RIG_BG = _url("peak/peak_rig_bg")
RIG_GLOW = _url("peak/peak_rig_glow")
RIG_NONE = _url("peak/peak_rig_none")


def _profile_glows():
    """Per-profile ring glows (peak_rig_glow_p1..p4); empty if the art hasn't been uploaded yet."""
    out = {}
    for n in range(1, 5):
        try:
            out[str(n)] = _url(f"peak/peak_rig_glow_p{n}")
        except KeyError:
            return {}
    return out


_OVERLAY = {"left": "50%", "top": "50%", "width": "100%", "pointer-events": "none"}


def _overlay(entity, state_image):
    return {"type": "image", "entity": entity, "image": RIG_NONE, "state_image": state_image,
            "tap_action": {"action": "none"}, "hold_action": {"action": "none"}, "style": dict(_OVERLAY)}


def rig_card(heat_entity="switch.peak_pro_02743_heat_session",
             profile_entity="select.peak_pro_02743_active_profile",
             awake_entity="binary_sensor.peak_pro_02743_awake"):
    """Idle + awake: ring glows in the active profile's colour. Heating: ember glow. Asleep: nothing."""
    elements = []
    glows = _profile_glows()
    if glows:
        elements.append({
            "type": "conditional",
            "conditions": [{"entity": heat_entity, "state_not": "on"},
                           {"entity": awake_entity, "state": "on"}],
            "elements": [_overlay(profile_entity, glows)],
        })
    elements.append(_overlay(heat_entity, {"on": RIG_GLOW, "off": RIG_NONE}))
    return {
        "type": "picture-elements",
        "image": RIG_BG,
        "elements": elements,
        # on phones the portrait art would fill a whole screen; shrink the card (overlays scale with it)
        "card_mod": {"style": "@media (max-width: 600px) { ha-card { max-width: 240px; margin: 0 auto; } }"},
        "grid_options": {"columns": "full"},
    }
