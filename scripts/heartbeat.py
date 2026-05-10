from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

TZ = ZoneInfo("Asia/Jakarta")
now = datetime.now(TZ)
month_file = Path("signal") / f"{now:%Y-%m}.md"
month_file.parent.mkdir(parents=True, exist_ok=True)

line = f"- {now:%Y-%m-%d %H:%M} WIB | daily-signal heartbeat | status: active\n"

if month_file.exists():
    existing = month_file.read_text(encoding="utf-8")
else:
    existing = f"# Daily Signal {now:%Y-%m}\n\n"

if f"- {now:%Y-%d" in existing:
    print("Entry for today already exists. Skipping.")
else:
    month_file.write_text(existing + line, encoding="utf-8")
    print(f"Updated {month_file}")