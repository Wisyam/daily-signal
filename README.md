<h1 align="center">daily-signal</h1>
<p align="center"><strong>Reusable GitHub Actions template</strong> for meaningful contribution signals (not dummy commits).</p>

<p align="center">
  <img src="https://img.shields.io/badge/automation-github_actions-181717?style=for-the-badge&logo=githubactions&logoColor=white" />
  <img src="https://img.shields.io/badge/language-python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/notifications-discord%20%2B%20telegram-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  <img src="https://img.shields.io/badge/mode-template_ready-00C853?style=for-the-badge" />
</p>

---

## Why this exists

`daily-signal` keeps your contribution flow active with useful, auditable logs:
- Daily engineering pulse
- Learning notes
- Weekly digest
- Health metadata

No random spam text. All outputs are structured and reviewable.

---

## System Flow

```mermaid
flowchart TD
  A[Schedule / Manual Trigger] --> B[Load config.yml]
  B --> C[Apply guardrails max/day weekend throttle duplicate slot]
  C -->|skip| D[Write status skipped with reason]
  C -->|pass| E[Generate useful content pulse learning weekly]
  E --> F[Resolve target repo self profile custom]
  F --> G[Commit and push]
  G --> H[Generate run summary JSON]
  H --> I[Send Discord embed success/failure]
  H --> J[Send Telegram failure optional]
```

---

## Setup Flow

```mermaid
flowchart LR
  A[Use Template or Fork] --> B[Run Setup Wizard workflow]
  B --> C[Choose target mode timezone and limits]
  C --> D[Auto-write config.yml]
  D --> E[Optional set secrets]
  E --> F[Run Daily Signal once manually]
  F --> G[Scheduled automation continues]
```

---

## Quick Start

1. Click **Use this template**.
2. Go to **Actions -> Setup Wizard -> Run workflow**.
3. Choose configuration:
   - `target_mode`: `self | profile | custom`
   - timezone
   - commits/day policy
4. Optional secrets:
   - `DISCORD_WEBHOOK_URL` (success + failure embed)
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (failure alert)
   - `TARGET_REPO_TOKEN` (required for cross-repo push)
5. Run **Daily Signal** once manually to validate.

---

## Target Modes

- `self` -> writes to same repo (default)
- `profile` -> writes to `username/username` profile repo
- `custom` -> writes to repo defined in config

---

## Repo Structure

- `.github/workflows/setup.yml` -> setup wizard
- `.github/workflows/heartbeat.yml` -> main engine
- `.github/workflows/healthcheck.yml` -> status check
- `.github/workflows/ci.yml` -> lint and test gate
- `.daily-signal/config.yml` -> runtime config
- `.daily-signal/config.schema.json` -> config schema
- `scripts/runner.py` -> generation engine
- `scripts/setup.py` -> setup writer
- `tests/test_runner.py` -> unit tests
- `logs/` -> generated outputs

---

## Discord Report Details

Each run sends a detailed embed with:
- execution status
- source repo + run URL
- target mode/repo/branch
- schedule window info
- actions executed
- generated files
- skip reason (if any)

---

## Reliability Notes

- Scheduled windows run automatically (event-driven, not daemon process).
- Concurrency lock prevents overlap.
- Guardrails prevent noisy/duplicate commits.
- Works continuously as long as GitHub Actions is enabled.

---

## Quality Gates

- CI runs `ruff` + `pytest` on push/PR.
- Config schema validates nested runtime fields.
- Runtime slot selection uses `schedule.slots` as source of truth.

---

## License / Usage

Free to use as your own template. Recommended: keep commit content meaningful.