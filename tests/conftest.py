"""Test path setup: import the integration and its vendored puffco_ble."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "custom_components" / "puffco" / "_vendor"))
