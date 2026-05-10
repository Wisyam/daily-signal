from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / 'scripts' / 'runner.py'
spec = importlib.util.spec_from_file_location('runner', RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_nearest_slot_morning():
    slots = [
        {"name": "morning", "base_utc": "02:00", "jitter_min": 30},
        {"name": "afternoon", "base_utc": "07:00", "jitter_min": 30},
    ]
    dt = datetime(2026, 5, 10, 2, 5, tzinfo=ZoneInfo("UTC"))
    slot = runner.nearest_slot(dt, slots)
    assert slot["name"] == "morning"


def test_parse_hhmm_utc():
    h, m = runner.parse_hhmm_utc("14:30")
    assert h == 14 and m == 30