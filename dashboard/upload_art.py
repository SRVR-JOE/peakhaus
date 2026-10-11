"""Upload dashboard art to Home Assistant's image store and record the ids.

config/www is not reachable from this machine, but HA's own image upload API
(POST /api/image/upload, bearer token) is, and uploads serve from
/api/image/serve/<id>/original. This script uploads every PNG under the given
directories and writes art/ids.json mapping "<group>/<name>" -> id, which the
patch scripts read. Re-uploading a changed file gets a new id; the old one is
left in place (delete via the websocket `image/delete` if it matters).

    python3 upload_art.py <dir> [<dir> ...]     # group = dir basename (only *.png is uploaded)

Idempotent by content: a file whose sha1 matches the recorded one is skipped.
"""
import hashlib
import json
import os
import pathlib
import sys
import urllib.request
import uuid

HA = os.environ.get("HA_URL", "http://homeassistant.local:8123")  # your HA base URL
# Long-lived access token (Profile -> Security) saved as a single line in ~/.ha_token
TOKEN = pathlib.Path.home().joinpath(".ha_token").read_text().strip()
IDS = pathlib.Path("art/ids.json")


def upload(png):
    """POST one PNG as multipart/form-data with only the standard library
    (the venv has no `requests` and PyPI is not reachable from here)."""
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{png.name}\"\r\nContent-Type: image/png\r\n\r\n").encode() \
        + png.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{HA}/api/image/upload", data=body, method="POST",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main(dirs):
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    for d in dirs:
        d = pathlib.Path(d)
        for png in sorted(d.glob("*.png")):
            key = f"{d.name}/{png.stem}"
            sha = hashlib.sha1(png.read_bytes()).hexdigest()
            if ids.get(key, {}).get("sha1") == sha:
                print(f"  {key:32s} unchanged ({ids[key]['id']})")
                continue
            ids[key] = {"id": upload(png)["id"], "sha1": sha}
            print(f"  {key:32s} uploaded  ({ids[key]['id']})")
            # keep the source next to the ids so a restore can re-upload it
            dest = pathlib.Path("art") / d.name
            dest.mkdir(parents=True, exist_ok=True)
            (dest / png.name).write_bytes(png.read_bytes())
            svg = png.with_suffix(".svg")
            if svg.exists():
                (dest / svg.name).write_bytes(svg.read_bytes())
    IDS.parent.mkdir(exist_ok=True)
    IDS.write_text(json.dumps(ids, indent=1, sort_keys=True))
    print(f"wrote {IDS} ({len(ids)} entries)")


if __name__ == "__main__":
    main(sys.argv[1:])
