from datetime import datetime
from zoneinfo import ZoneInfo

import scripts.runner as runner


def test_detect_slot_by_config_morning():
    slots = [
        {"name": "morning", "base_utc": "02:00", "jitter_min": 30},
        {"name": "afternoon", "base_utc": "07:00", "jitter_min": 30},
    ]
    dt = datetime(2026, 5, 10, 2, 5, tzinfo=ZoneInfo("UTC"))
    slot = runner.detect_slot_by_config(dt, slots)
    assert slot["name"] == "morning"


def test_parse_utc_hhmm():
    h, m = runner.parse_utc_hhmm("14:30")
    assert h == 14 and m == 30