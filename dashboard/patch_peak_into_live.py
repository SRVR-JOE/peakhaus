"""Add the Peak page (peak_cards.py) and the Home-view Peak battery spot to LIVE home-hub.

- Peak view: inserted after home-v2 (re-run replaces it). The old separate
  `peak-live` panel view is folded into it and is REMOVED from live if present.
- Home view: Peak card at the top of the Batteries section (detected by its
  navigate path, so re-runs replace it), and the Peak battery is excluded from
  the Batteries auto-entities lists so it isn't shown twice.
Every template is rendered via /api/template first; any error aborts.
Supports --dry-run. Backs up live to live_backup_prepeak.json.
"""
import asyncio
import json
import os
import pathlib
import sys
import urllib.request

from ha_ws import HA
from peak_cards import BATT, VIEW_PATH, all_templates, home_battery_card, peak_view

DASH = "home-hub"
AFTER_VIEW = "home-v2"
OLD_LIVE_PATH = "peak-live"
NAV = f"/home-hub/{VIEW_PATH}"
HA_URL = os.environ.get("HA_URL", "http://homeassistant.local:8123")  # your HA base URL
# Long-lived access token (Profile -> Security) saved as a single line in ~/.ha_token
TOKEN = pathlib.Path.home().joinpath(".ha_token").read_text().strip()


def check_templates():
    bad = 0
    for t in all_templates():
        req = urllib.request.Request(
            f"{HA_URL}/api/template",
            data=json.dumps({"template": t}).encode(),
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        try:
            out = urllib.request.urlopen(req, timeout=10).read().decode()
            print(f"  ok  {out[:60]!r}")
        except urllib.error.HTTPError as e:
            bad += 1
            print(f"  BAD {e.read().decode()[:200]}\n      {t[:160]}")
    if bad:
        raise SystemExit(f"{bad} template(s) failed - not pushing")


def headings(sec):
    return [c.get("heading") for c in sec.get("cards", []) if c.get("type") == "heading"]


def is_peak_card(c):
    return (c.get("tap_action") or {}).get("navigation_path") == NAV


def patch(cfg):
    notes = []
    views = cfg["views"]
    views[:] = [v for v in views if v.get("path") != VIEW_PATH]
    idx = next((i + 1 for i, v in enumerate(views) if v.get("path") == AFTER_VIEW), 1)
    views.insert(idx, peak_view())
    notes.append(f"Peak view at index {idx}")
    if any(v.get("path") == OLD_LIVE_PATH for v in views):
        views[:] = [v for v in views if v.get("path") != OLD_LIVE_PATH]
        notes.append(f"removed old '{OLD_LIVE_PATH}' view (merged into '{VIEW_PATH}')")

    home = next(v for v in views if v.get("path") == "home")
    sec = next((s for s in home["sections"] if "Batteries" in headings(s)), None)
    if sec is None:
        raise SystemExit("no Batteries section on the Home view")
    cards = [c for c in sec["cards"] if not is_peak_card(c)]
    h = next(i for i, c in enumerate(cards) if c.get("type") == "heading")
    cards.insert(h + 1, home_battery_card())
    sec["cards"] = cards
    notes.append("Peak battery card at top of Home > Batteries")

    for c in cards:
        if c.get("type") == "custom:auto-entities":
            ex = c["filter"].setdefault("exclude", [])
            if {"entity_id": BATT} not in ex:
                ex.append({"entity_id": BATT})
                notes.append("excluded Peak battery from a Batteries auto-entities list")
    return notes


async def main():
    print("validating templates")
    check_templates()
    async with HA() as ha:
        live = await ha.cmd({"type": "lovelace/config", "url_path": DASH})
        bk = pathlib.Path("live_backup_prepeak.json")
        if not bk.exists():  # keep the FIRST pre-Peak snapshot; re-runs must not overwrite it
            json.dump(live, bk.open("w"), indent=2)
            print(f"backed up live -> {bk} ({len(live['views'])} views)")
        for n in patch(live):
            print("  +", n)
        if "--dry-run" in sys.argv:
            print("DRY RUN - not saving")
            return
        await ha.cmd({"type": "lovelace/config/save", "url_path": DASH, "config": live})
        back = await ha.cmd({"type": "lovelace/config", "url_path": DASH})
        ok = json.dumps(back, sort_keys=True) == json.dumps(live, sort_keys=True)
        print("saved; read-back", "matches" if ok else "DIFFERS")


# Guarded: importing this module must never write to the live dashboard.
if __name__ == "__main__":
    asyncio.run(main())
