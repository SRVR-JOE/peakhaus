"""Minimal Home Assistant websocket client.

Usage:
    from ha_ws import HA
    async with HA() as ha:
        res = await ha.cmd({"type": "lovelace/resources"})
"""
import asyncio
import json
import os
import pathlib

import websockets

HA_URL = os.environ.get("HA_URL", "http://homeassistant.local:8123")  # your HA base URL
URL = os.environ.get("HA_WS", HA_URL.replace("http", "ws", 1) + "/api/websocket")
# Long-lived access token (Profile -> Security) saved as a single line in ~/.ha_token
TOKEN = pathlib.Path.home().joinpath(".ha_token").read_text().strip()


class HA:
    def __init__(self, url=URL, token=TOKEN):
        self.url, self.token, self._id = url, token, 0

    async def __aenter__(self):
        self.ws = await websockets.connect(self.url, max_size=32 * 1024 * 1024)
        await self.ws.recv()  # auth_required
        await self.ws.send(json.dumps({"type": "auth", "access_token": self.token}))
        ok = json.loads(await self.ws.recv())
        if ok.get("type") != "auth_ok":
            raise RuntimeError(f"auth failed: {ok}")
        return self

    async def __aexit__(self, *exc):
        await self.ws.close()

    async def cmd(self, payload):
        self._id += 1
        mid = self._id
        await self.ws.send(json.dumps({"id": mid, **payload}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == mid and msg.get("type") == "result":
                if not msg.get("success"):
                    raise RuntimeError(f"{payload.get('type')} failed: {msg.get('error')}")
                return msg.get("result")


async def _main():
    import sys
    async with HA() as ha:
        print(json.dumps(await ha.cmd(json.loads(sys.argv[1])), indent=2)[:6000])


if __name__ == "__main__":
    asyncio.run(_main())
