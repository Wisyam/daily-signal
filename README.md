# daily-signal

Reusable automation template for meaningful contribution heartbeat.

## Features

- Setup wizard (`workflow_dispatch`) for initial configuration.
- 3 schedule windows/day with natural timing distribution.
- Guardrails: max commits/day, weekend throttle, duplicate prevention.
- Useful logs (daily + weekly digest), not dummy content.
- Optional failure alerts to Discord/Telegram.

## Quick Start

1. Use this repository as template (or fork).
2. Run **Actions > Setup Wizard > Run workflow**.
3. (Optional) Set secrets:
   - `DISCORD_WEBHOOK_URL`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `TARGET_REPO_TOKEN` (only for cross-repo target)
4. Let **Daily Signal** run on schedule or trigger manually.

## Workflows

- `.github/workflows/setup.yml` — configure repo behavior.
- `.github/workflows/heartbeat.yml` — core automation engine.
- `.github/workflows/healthcheck.yml` — print latest status.

## Config

Main config: `.daily-signal/config.yml`

Key controls:
- target mode (`self|profile|custom`)
- timezone
- commit/day caps
- weekend throttle
- modules on/off

## Output

- `logs/daily/YYYY-MM.md`
- `logs/weekly/YYYY-WW.md`
- `logs/meta/status.json`