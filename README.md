# daily-signal

Automated daily heartbeat commits to keep contribution activity consistent with meaningful logs.

## What it does

- Runs every day at **09:10 WIB** (02:10 UTC) via GitHub Actions.
- Appends one line per day to `signal/YYYY-MM.md`.
- Commits only when there is a real content change.

## Files

- `.github/workflows/daily-signal.yml` — schedule + commit workflow
- `scripts/heartbeat.py` — generates daily log entry
- `signal/` — monthly heartbeat logs

## Notes

- You can trigger manually from **Actions > Daily Signal > Run workflow**.
- To change time, edit cron in `.github/workflows/daily-signal.yml`.
- Format uses Asia/Jakarta timezone for the log content.