"""card_mod styling for the Peak page ("Daybreak" look).

Pure module: no HA calls, no art, no view assembly. peak_cards.py wraps each card
with style(card, role) and the patch script pushes the result.

Prerequisite: the `peak` view carries NO `theme` (Metro Slate swallows card_mod).

Rules that keep card_mod safe here:
* Every style string is ONE line. card_mod renders it as a Jinja template server-side;
  a newline inside a template ends up in the CSS and breaks the rule.
* No {{ }} inside {% %}. Values are computed with {% set %} then emitted once.
* Prefer CSS custom properties over shadow-DOM selectors: variables cross shadow
  boundaries (tile text, mushroom text/chips), so nothing depends on internal markup.
  The only direct-DOM selectors used are on the HA `sensor` card (.value/.measurement),
  which has no shadow root between ha-card and those spans.
"""

PALETTE = {
    "page": "#0f1012",
    "card": "#15161a",
    "card_active": "#1a1712",
    "hairline": "#26282d",
    "ember": "#ff7a1a",
    "red": "#d63031",
    "gold": "#c9a24a",
    "cream": "#ececec",
    "mid": "#9aa0a8",
    "dim": "#6b6f76",
}

# Sections-view background. This is the legacy CSS-string form, which HA still
# accepts for `background:` on a view (it becomes --lovelace-background). The
# object form only documents image/opacity/size/alignment/repeat/attachment and
# has no plain colour key, so the string is the one that is certain to render a
# flat colour. Drop it if the view ever shows the default background instead.
VIEW_BACKGROUND = "#0e0f11"  # matches the rig artwork background so the rig card has no visible frame

P = PALETTE
HEAT = "switch.peak_pro_02743_heat_session"
PROFILE = "select.peak_pro_02743_active_profile"

# Base shell shared by almost every role.
_SHELL = (
    f"background: {P['card']}; border: 1px solid {P['hairline']}; "
    f"border-radius: 12px; box-shadow: none; --primary-color: {P['ember']};"
)
_BARE = "background: none; border: none; box-shadow: none;"


def _ha_card(body):
    return "ha-card { " + body + " }"


def _profile_rule(n):
    """One-line template: tile shell + 3px profile-colour bar + ember when active."""
    rgb = (
        f"{{% set rgb = state_attr('light.peak_pro_02743_profile_{n}_color', 'rgb_color') %}}"
        "{% set bar = ('rgb(' ~ rgb | join(',') ~ ')') if rgb else '#3a3d44' %}"
    )
    active = (
        f"{{% if is_state('{PROFILE}', '{n}') %}}"
        f"border-color: {P['ember']}; background: {P['card_active']};"
        "{% endif %}"
    )
    # The bar is an inset shadow so the active border-color never recolours it.
    return rgb + _ha_card(_SHELL + " box-shadow: inset 3px 0 0 {{ bar }}; " + active)


_HEAT_RULE = _ha_card(
    _SHELL
    + f" {{% if is_state('{HEAT}', 'on') %}}"
    + f"border-color: {P['ember']}; box-shadow: inset 0 1px 0 rgba(255,122,26,.35); "
    + f"--secondary-text-color: {P['ember']}; --tile-color: {P['ember']};"
    + "{% endif %}"
)

ROLES = {
    "rig": _ha_card(_BARE + " overflow: hidden;"),
    "tile": _ha_card(_SHELL),
    "select": _ha_card(_SHELL),
    "dial": _ha_card(_SHELL),
    "light": _ha_card(_SHELL),
    "heat": _HEAT_RULE,
    "action_primary": _ha_card(
        f"background: {P['ember']}; border: 1px solid {P['ember']}; border-radius: 12px; "
        f"box-shadow: none; --primary-text-color: {P['cream']}; --card-primary-color: {P['cream']}; "
        f"--icon-color: {P['cream']}; --card-primary-font-weight: 600;"
    ),
    "action": _ha_card(_SHELL + " --card-primary-font-weight: 500;"),
    "stat": _ha_card(
        _SHELL
        + " --card-primary-font-size: 22px; --card-primary-font-weight: 300; "
        + f"--card-secondary-font-size: 11px; --card-secondary-color: {P['mid']}; "
        + "font-variant-numeric: tabular-nums;"
    ),
    "sensor": (
        _ha_card(_SHELL + f" font-variant-numeric: tabular-nums; --state-icon-color: {P['mid']}; "
                 f"--state-sensor-battery-high-color: {P['mid']}; --state-sensor-battery-medium-color: {P['gold']}; "
                 f"--state-sensor-battery-low-color: {P['red']};")
        + " ha-card .value { font-size: 32px; font-weight: 300; }"
        + " ha-card .measurement { color: " + P["mid"] + "; font-size: 14px; }"
    ),
    "chips": _ha_card(
        f"--chip-background: {P['card']}; --chip-border-width: 1px; "
        f"--chip-border-color: {P['hairline']}; --chip-border-radius: 999px;"
    ),
    "banner": _ha_card(_BARE + " border-radius: 10px; overflow: hidden;")
    + " ha-card img { display: block; width: 100%; }",
    "entities": _ha_card(
        _SHELL + f" --ha-card-header-font-size: 14px; --ha-card-header-color: {P['mid']};"
    ),
}


def _rule(role, **kw):
    if role == "profile":
        n = int(kw["n"])
        assert 1 <= n <= 4, "profile role needs n=1..4"
        return _profile_rule(n)
    return ROLES[role]


def _merge(existing, rule):
    """Merge a new ha-card rule into whatever card_mod the card already carries."""
    if not existing:
        return {"style": rule}
    old = existing.get("style")
    if isinstance(old, str):
        return {**existing, "style": old + " " + rule}
    if isinstance(old, dict):
        new = dict(old)
        new["."] = (new.get(".", "") + " " + rule).strip()
        return {**existing, "style": new}
    return {**existing, "style": rule}


def style(card, role, **kw):
    """Return `card` with the Daybreak card_mod style for `role` merged in."""
    card["card_mod"] = _merge(card.get("card_mod"), _rule(role, **kw))
    return card


def banner_card(url, nav=None):
    """A `picture` card used as a section header image (800x120 art)."""
    tap = {"action": "navigate", "navigation_path": nav} if nav else {"action": "none"}
    card = {
        "type": "picture",
        "image": url,
        "tap_action": tap,
        "hold_action": {"action": "none"},
        "grid_options": {"columns": "full"},
    }
    return style(card, "banner")


# --------------------------------------------------------------------- self-test

def _emitted():
    out = []
    for role in ROLES:
        out.append((role, style({}, role)["card_mod"]["style"]))
    for n in range(1, 5):
        out.append((f"profile {n}", style({}, "profile", n=n)["card_mod"]["style"]))
    out.append(("banner_card", banner_card("/api/image/serve/x/original")["card_mod"]["style"]))
    merged = style({"card_mod": {"style": "ha-card { opacity: .9; }"}}, "tile")
    out.append(("merge:string", merged["card_mod"]["style"]))
    return out


def _check(text):
    assert "\n" not in text, "style must be one line"
    # No {{ }} inside a {% %} tag.
    i = 0
    while True:
        a = text.find("{%", i)
        if a < 0:
            break
        b = text.find("%}", a)
        assert b > a, "unterminated {% %}"
        assert "{{" not in text[a:b], "{{ }} nested inside {% %}"
        i = b + 2


if __name__ == "__main__":
    for name, s in _emitted():
        _check(s)
        print(f"[{name}]\n  {s}\n")
    print("ok:", len(_emitted()), "styles, all one line, no nested braces")
