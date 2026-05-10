# daily-signal

Automated daily heartbeat commits to keep contribution activity consistent with meaningful logs.

## What it does

- Runs every day at **09:00 WIB** base schedule (02:00 UTC) via GitHub Actions.
- Adds a **random delay 0-30 minutes** to make commit timing more natural.
- Appends one line per day to `signal/YYYY-MM.md`.
- Commits only when there is a real content change.

## Files

- `.github/workflows/daily-signal.yml` — schedule + random window + optional notifications
- `scripts/heartbeat.py` — generates daily log entry
- `signal/` — monthly heartbeat logs

## Optional failure notifications

Set repository secrets if you want alerts:

### Telegram

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Discord

- `DISCORD_WEBHOOK_URL`

If secrets are not set, notification steps are automatically skipped.

## Notes

- You can trigger manually from **Actions > Daily Signal > Run workflow**.
- To change base time, edit cron in `.github/workflows/daily-signal.yml`.
- Format uses Asia/Jakarta timezone for the log content.