"""Puffco Peak Pro page + Home-view battery spot for home-hub.

One sections view (`peak`) replaces the old `peak` + `peak-live` pair. The rig
artwork is a compact portrait picture-elements card from peak_rig.py; every
number next to it is a native HA card, so nothing depends on viewport units.

The Peak talks to HA through the ATOM Lite Bluetooth proxy (`puffco-bridge`);
the M5Dial (`puffco-proxy`, entities puffco_bt_proxy_*) is a remote/display only.
Profile temperatures come from the integration in degC; everything shown is degF.
Colour is state only: orange = heat, grey/amber/red = battery, profile icons use
the profile's own LED colour. Metro Slate ignores card_mod, so none is used.
Templates never nest {{ }} inside {% if %}, are one line each, and are checked
against /api/template by patch_peak_into_live.py before pushing.
"""

P = "peak_pro_02743"
THEME = "Metro Slate"
VIEW_PATH = "peak"

BATT = f"sensor.{P}_battery"
TEMP = f"sensor.{P}_heater_temperature"
REMAIN = f"sensor.{P}_heat_time_remaining"
HEAT = f"switch.{P}_heat_session"
AWAKE = f"binary_sensor.{P}_awake"
PROFILE = f"select.{P}_active_profile"
STATUS_SENSOR = "sensor.peak_status"  # template helper: Not connected / Heating / Ready / Idle / Asleep
LANTERN = f"light.{P}_lantern"
EFFECTS = ["Solid", "Breathing", "Rising", "Circling", "Circling Slow", "Pulsing", "Rotating", "Disco"]

# Fallback artwork if peak_rig.py has not been generated yet (old Peak Live background).
LIVE_BG = "/api/image/serve/e3a984d987dc99ca1494ca21b68da0cd/original"

CONNECTED = f"states('{BATT}') not in ['unavailable', 'unknown']"


def _pf(n):
    """Profile n: name, degF target, duration, LED colour."""
    return {
        "name": f"text.{P}_profile_{n}_name",
        "temp": f"number.{P}_profile_{n}_temperature",
        "dur": f"number.{P}_profile_{n}_duration",
        "color": f"light.{P}_profile_{n}_color",
    }


def _press(entity):
    return {"action": "perform-action", "perform_action": "button.press",
            "target": {"entity_id": entity}}


def _heading(text, icon=None, style="title", badges=None):
    h = {"type": "heading", "heading": text, "heading_style": style}
    if icon:
        h["icon"] = icon
    if badges:
        h["badges"] = badges
    return h


def _tile(entity, name, columns="full", **extra):
    t = {"type": "tile", "entity": entity, "name": name, "grid_options": {"columns": columns}}
    t.update(extra)
    return t


# --------------------------------------------------------------------------- 1. hero

def rig_section():
    try:
        from peak_rig import rig_card
        rig = rig_card(heat_entity=HEAT)
    except ImportError:
        rig = {"type": "picture", "image": LIVE_BG, "tap_action": {"action": "none"},
               "hold_action": {"action": "none"}, "grid_options": {"columns": "full"}}
    return {
        "type": "grid",
        "cards": [
            _heading("Peak Pro", "mdi:fire", badges=[
                {"type": "entity", "entity": STATUS_SENSOR, "icon": "mdi:fire"},
                {"type": "entity", "entity": BATT},
            ]),
            rig,
        ],
    }


# --------------------------------------------------------------------------- 2. session

_DAY_AXIS = {  # shared 6 am -> midnight axis so the two day charts line up
    "graph_span": "18h",
    "span": {"start": "day", "offset": "+6h"},
    "header": {"show": False},
    "now": {"show": True, "color": "#ff7a1a", "label": ""},
}
_DAY_APEX = {
    "chart": {"animations": {"enabled": False}, "parentHeightOffset": 0},
    "grid": {"show": True, "borderColor": "#26282d", "strokeDashArray": 0, "padding": {"left": 8, "right": 8},
             "xaxis": {"lines": {"show": False}}, "yaxis": {"lines": {"show": True}}},
    "xaxis": {"labels": {"style": {"colors": "#9aa0a8"}, "datetimeUTC": False,
                                          "datetimeFormatter": {"hour": "h tt"}},
              "axisBorder": {"show": False}, "axisTicks": {"show": False}},
    "legend": {"show": False},
    "tooltip": {"theme": "dark"},
}


def _day_chart(kind):
    """kind='hits': hits per hour as bars. kind='sessions': 10-min session blocks (binary_sensor.peak_recent_hit)."""
    apex = {k: (dict(v) if isinstance(v, dict) else v) for k, v in _DAY_APEX.items()}
    if kind == "hits":
        apex["chart"]["height"] = 130
        apex["dataLabels"] = {"style": {"colors": ["#ececec"], "fontSize": "11px"}, "offsetY": -4,
                              "background": {"enabled": False}, "dropShadow": {"enabled": False},
                              "formatter": "EVAL:function(v){ return v > 0 ? v : ''; }"}
        apex["xaxis"] = dict(apex["xaxis"], labels={"show": False})
        series = [{
            # stepped histogram rather than apex columns: columns on a time axis get padded on both
            # sides, which shifts the plot relative to the session chart below it
            "entity": f"sensor.{P}_total_dabs", "name": "Hits", "type": "area", "curve": "stepline",
            "color": "#ff7a1a", "opacity": 0.85, "stroke_width": 1, "yaxis_id": "y", "extend_to": "now",
            "group_by": {"func": "diff", "duration": "1h"},
            "show": {"datalabels": True, "legend_value": False},
        }]
        yaxis = [{"id": "y", "min": 0, "decimals": 0,
                  "apex_config": {"tickAmount": 2, "forceNiceScale": True,
                                  "labels": {"minWidth": 28, "maxWidth": 28, "style": {"colors": "#6b6f76"}}}}]
    else:
        apex["chart"]["height"] = 80
        apex["grid"]["yaxis"] = {"lines": {"show": False}}
        series = [{
            "entity": "binary_sensor.peak_recent_hit", "name": "Session", "type": "area", "curve": "stepline", "yaxis_id": "y",
            "color": "#c9a24a", "opacity": 0.35, "stroke_width": 1, "extend_to": "now",
            "transform": "return x === 'on' ? 1 : 0;",
            "show": {"legend_value": False, "in_header": False},
        }]
        # same y-label gutter as the bars chart (labels painted in the card colour) so the plots line up
        yaxis = [{"id": "y", "min": 0, "max": 1,
                  "apex_config": {"tickAmount": 1, "labels": {"minWidth": 28, "maxWidth": 28,
                                                              "style": {"colors": "#15161a"}}}}]
    return dict(_DAY_AXIS, type="custom:apexcharts-card", apex_config=apex, yaxis=yaxis, series=series,
                grid_options={"columns": "full"})


def session_section():
    action_btn = lambda name, icon, entity, color: {
        "type": "custom:mushroom-template-card",
        "primary": name,
        "icon": icon,
        "icon_color": color,
        "layout": "vertical",
        "tap_action": _press(entity),
        "grid_options": {"columns": 4},
    }
    return {
        "type": "grid",
        "cards": [
            _heading("Session", "mdi:fire"),
            _tile(HEAT, "Heat session", features=[{"type": "toggle"}],
                  state_content=["state", "last_changed"]),
            action_btn("Start", "mdi:play", f"button.{P}_start_session", "orange"),
            action_btn("Boost", "mdi:fire-circle", f"button.{P}_boost_session", "orange"),
            action_btn("Stop", "mdi:stop", f"button.{P}_abort_session", "grey"),
            {
                "type": "conditional",
                "conditions": [{"condition": "state", "entity": HEAT, "state": "on"}],
                "card": _tile(REMAIN, "Time left", icon="mdi:timer-outline"),
            },
            {
                "type": "sensor",
                "entity": TEMP,
                "name": "Heater",
                "graph": "line",
                "hours_to_show": 24,
                "detail": 2,
                "unit": "°F",
                "grid_options": {"columns": "full"},
            },
            _heading("Today, 6 am to midnight", style="subtitle"),
            _day_chart("hits"),
            _day_chart("sessions"),
        ],
    }


# --------------------------------------------------------------------------- 3. profiles

def profile_card(n):
    p = _pf(n)
    secondary = (
        f"{{% set c = states('{p['temp']}') | float(0) %}}"
        f"{{% set s = states('{p['dur']}') | float(0) %}}"
        "{{ (c * 9 / 5 + 32) | round(0) | int }}°F · {{ s | round(0) | int }} s"
    )
    icon_color = (
        f"{{% set rgb = state_attr('{p['color']}', 'rgb_color') %}}"
        f"{{% set active = is_state('{PROFILE}', '{n}') %}}"
        "{{ ('rgb(' ~ rgb | join(',') ~ ')') if active and rgb else ('orange' if active else 'disabled') }}"
    )
    return {
        "type": "custom:mushroom-template-card",
        "primary": f"{{{{ states('{p['name']}') }}}}",
        "secondary": secondary,
        "icon": f"mdi:numeric-{n}-circle",
        "icon_color": icon_color,
        "badge_icon": f"{{{{ 'mdi:check' if is_state('{PROFILE}', '{n}') else '' }}}}",
        "badge_color": "orange",
        "tap_action": {
            "action": "perform-action",
            "perform_action": "select.select_option",
            "target": {"entity_id": PROFILE},
            "data": {"option": str(n)},
        },
        "hold_action": {"action": "more-info", "entity": p["temp"]},
        "grid_options": {"columns": 6},
    }


def profiles_section():
    return {
        "type": "grid",
        "cards": [_heading("Profiles", "mdi:tune-variant")]
        + [profile_card(n) for n in range(1, 5)]
        + [_heading("Colors", style="subtitle")]
        + [_profile_color_card(n) for n in range(1, 5)],
    }


# --------------------------------------------------------------------------- 4. battery & use

def battery_usage_section():
    stat = lambda name, entity, icon, fmt: {
        "type": "custom:mushroom-template-card",
        "primary": fmt,
        "secondary": name,
        "icon": icon,
        "icon_color": "grey",
        "layout": "vertical",
        "entity": entity,
        "tap_action": {"action": "more-info"},
        "grid_options": {"columns": 4},
    }
    return {
        "type": "grid",
        "cards": [
            _heading("Battery & use", "mdi:chart-line"),
            {
                "type": "sensor",
                "entity": BATT,
                "name": "Battery",
                "graph": "line",
                "hours_to_show": 168,
                "detail": 2,
                "unit": "%",
                "grid_options": {"columns": "full"},
            },
            stat("Dabs per day", f"sensor.{P}_dabs_per_day", "mdi:calendar-today",
                 f"{{{{ states('sensor.{P}_dabs_per_day') | float(0) | round(1) }}}}"),
            stat("Total dabs", f"sensor.{P}_total_dabs", "mdi:counter",
                 f"{{{{ states('sensor.{P}_total_dabs') | int(0) }}}}"),
            stat("Since reset", f"sensor.{P}_trip_dabs", "mdi:map-marker-distance",
                 f"{{{{ states('sensor.{P}_trip_dabs') | int(0) }}}}"),
        ],
    }


# --------------------------------------------------------------------------- 5. lantern

def _effect_chip(effect):
    active = f"is_state('{LANTERN}', 'on') and state_attr('{LANTERN}', 'effect') == '{effect}'"
    return {
        "type": "template",
        "entity": LANTERN,
        "content": effect,
        "icon_color": f"{{{{ 'orange' if {active} else 'grey' }}}}",
        "tap_action": {"action": "perform-action", "perform_action": "light.turn_on",
                       "target": {"entity_id": LANTERN}, "data": {"effect": effect}},
    }


def lantern_section():
    return {
        "type": "grid",
        "cards": [
            _heading("Lights", "mdi:lightbulb-outline"),
            {
                "type": "custom:mushroom-light-card",
                "entity": LANTERN,
                "name": "Lantern",
                "use_light_color": True,
                "show_brightness_control": True,
                "show_color_control": True,
                "collapsible_controls": False,
                "grid_options": {"columns": "full"},
            },
            {
                "type": "custom:mushroom-chips-card",
                "alignment": "start",
                "chips": [_effect_chip(e) for e in EFFECTS],
                "grid_options": {"columns": "full"},
            },
            _heading("Peak LEDs", style="subtitle"),
            _tile(f"switch.{P}_stealth_mode", "Stealth mode", icon="mdi:eye-off-outline",
                  features=[{"type": "toggle"}]),
            {
                "type": "entities",
                "title": "LED brightness",
                "entities": [
                    {"entity": f"number.{P}_led_brightness_main", "name": "Main"},
                    {"entity": f"number.{P}_led_brightness_ring", "name": "Ring"},
                    {"entity": f"number.{P}_led_brightness_glass", "name": "Glass"},
                    {"entity": f"number.{P}_led_brightness_battery", "name": "Battery"},
                ],
                "grid_options": {"columns": "full"},
            },
        ],
    }


# --------------------------------------------------------------------------- 6. profile colours

def _profile_color_card(n):
    p = _pf(n)
    return {
        "type": "custom:mushroom-template-card",
        "entity": p["color"],
        "primary": f"{{{{ states('{p['name']}') }}}}",
        "secondary": "Tap to change",
        "icon": "mdi:circle",
        "icon_color": (
            f"{{% set rgb = state_attr('{p['color']}', 'rgb_color') %}}"
            "{{ ('rgb(' ~ rgb | join(',') ~ ')') if rgb else 'disabled' }}"
        ),
        "tap_action": {"action": "more-info"},
        "grid_options": {"columns": 6},
    }



# --------------------------------------------------------------------------- 7. bridge & dial

def bridge_section():
    return {
        "type": "grid",
        "cards": [
            _heading("Bridge & Dial", "mdi:bluetooth"),
            {
                "type": "custom:mushroom-template-card",
                "primary": f"{{{{ 'Connected' if {CONNECTED} else 'Not connected' }}}}",
                "secondary": "via Puffco Bridge",
                "icon": "mdi:bluetooth-connect",
                "icon_color": f"{{{{ 'grey' if {CONNECTED} else 'red' }}}}",
                "grid_options": {"columns": "full"},
            },
            _tile("sensor.puffco_bridge_wi_fi_signal", "Bridge Wi-Fi"),
            {
                "type": "custom:mushroom-template-card",
                "primary": "Reconnect",
                "secondary": "Use if the readings look stuck",
                "icon": "mdi:refresh",
                "icon_color": "grey",
                "tap_action": _press(f"button.{P}_reconnect"),
                "grid_options": {"columns": "full"},
            },
            _heading("Dial", style="subtitle"),
            _tile("select.puffco_bt_proxy_gauge_style", "Dial face", icon="mdi:gauge",
                  features=[{"type": "select-options"}]),
            _tile("light.puffco_bt_proxy_screen_backlight", "Dial screen",
                  features=[{"type": "light-brightness"}]),
            _tile("sensor.puffco_bt_proxy_wifi_signal", "Dial Wi-Fi"),
        ],
    }


# --------------------------------------------------------------------------- view

def _plain_view():
    return {
        "type": "sections",
        "path": VIEW_PATH,
        "title": "Peak",
        "icon": "mdi:fire",
        "theme": THEME,
        "max_columns": 3,
        "sections": [
            rig_section(),
            session_section(),
            profiles_section(),
            battery_usage_section(),
            lantern_section(),
            bridge_section(),
        ],
    }


# ------------------------------------------------------------------ Daybreak skin

BANNERS = {  # heading text -> art/ids.json key (peak/make_peak_banners.py)
    "Peak Pro": "peak/banner_peak_pro", "Session": "peak/banner_session", "Profiles": "peak/banner_profiles",
    "Battery & use": "peak/banner_battery", "Lights": "peak/banner_lights", "Bridge & Dial": "peak/banner_bridge",
}


def _role(card):
    """Map a built card to a peak_style role (None = leave alone)."""
    t = card.get("type")
    ent = card.get("entity", "")
    tap = card.get("tap_action") or {}
    if t == "picture-elements":
        return "rig"
    if t == "tile":
        return "heat" if ent == HEAT else ("select" if ent.startswith("select.") else "tile")
    if t == "custom:mushroom-template-card":
        target = (tap.get("target") or {}).get("entity_id", "")
        if target == f"button.{P}_start_session":
            return "action_primary"
        if target in (f"button.{P}_boost_session", f"button.{P}_abort_session"):
            return "action"
        if card.get("layout") == "vertical":
            return "stat"
        if ent.startswith(f"light.{P}_profile_"):
            return "tile"
        if card.get("badge_color") == "orange":  # the four profile cards
            return "profile"
        return "tile"
    if t == "sensor":
        return "sensor"
    if t in ("history-graph", "custom:mini-graph-card", "custom:apexcharts-card"):
        return "tile"
    if t == "custom:mushroom-chips-card":
        return "chips"
    if t == "custom:mushroom-light-card":
        return "light"
    if t == "entities":
        return "entities"
    if t == "conditional":
        return None
    return None


def decorate(view):
    """Daybreak skin: no theme (so card_mod applies), page background, banner headers, per-role card_mod."""
    try:
        import peak_style
    except ImportError:
        return view
    try:
        from peak_rig import _url
    except ImportError:
        _url = None
    view.pop("theme", None)
    if getattr(peak_style, "VIEW_BACKGROUND", None):
        view["background"] = peak_style.VIEW_BACKGROUND
    for sec in view["sections"]:
        cards = []
        for c in sec["cards"]:
            if c.get("type") == "heading" and c.get("heading_style") == "title" and c["heading"] in BANNERS and _url:
                try:
                    url = _url(BANNERS[c["heading"]])
                except KeyError:
                    cards.append(c)
                    continue
                b = peak_style.banner_card(url)
                b["grid_options"] = {"columns": "full"}
                if c.get("badges"):  # keep the live badges as a slim heading under the banner
                    cards.append(b)
                    cards.append({"type": "heading", "heading": "", "heading_style": "subtitle", "badges": c["badges"]})
                    continue
                cards.append(b)
                continue
            role = _role(c)
            if c.get("type") == "tile" and c.get("entity") != HEAT and "color" not in c:
                # default tile icons are HA blue; info tiles go neutral, interactive ones ember
                c["color"] = "orange" if c.get("entity", "").split(".")[0] in ("select", "light", "button") else "grey"
            if role == "profile":
                n = int(c["icon"].rsplit("-", 2)[1])  # mdi:numeric-N-circle
                c = peak_style.style(c, role, n=n)
            elif role:
                c = peak_style.style(c, role)
            if c.get("type") == "conditional" and "card" in c:
                r = _role(c["card"])
                if r:
                    c["card"] = peak_style.style(c["card"], r)
            cards.append(c)
        sec["cards"] = cards
    return view


def peak_view():
    return decorate(_plain_view())


# --------------------------------------------------------------------- home spot

def home_battery_card():
    """Peak battery + heat status for the Home view's Batteries section."""
    return {
        "type": "custom:mushroom-template-card",
        "entity": BATT,
        "primary": "Peak Pro",
        "secondary": (
            f"{{% set s = states('{BATT}') %}}"
            "{{ ((s | float) | round(0) | int ~ '%') if s | is_number else 'Not reporting' }}"
            " · "
            f"{{{{ 'Heating' if is_state('{HEAT}', 'on') else ('Idle' if is_state('{AWAKE}', 'on') else 'Asleep') }}}}"
        ),
        "icon": (
            f"{{% set s = states('{BATT}') %}}{{% set b = ((s | float(0)) / 10) | round(0) | int * 10 %}}"
            "{{ 'mdi:battery-unknown' if not s | is_number else ('mdi:battery' if b >= 100 else "
            "('mdi:battery-outline' if b <= 0 else 'mdi:battery-' ~ b)) }}"
        ),
        "icon_color": (
            f"{{% set s = states('{BATT}') %}}"
            "{{ 'red' if not s | is_number or s | float < 15 else ('amber' if s | float < 30 else 'grey') }}"
        ),
        "badge_icon": f"{{{{ 'mdi:fire' if is_state('{HEAT}', 'on') else '' }}}}",
        "badge_color": "orange",
        "tap_action": {"action": "navigate", "navigation_path": f"/home-hub/{VIEW_PATH}"},
        "grid_options": {"columns": "full"},
    }


def all_templates():
    """Every Jinja string the builders emit, for /api/template validation."""
    out = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and ("{{" in o or "{%" in o):
            out.append(o)

    walk(peak_view())
    walk(home_battery_card())
    return out
