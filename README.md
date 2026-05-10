<h1 align="center">daily-signal</h1>
<p align="center"><strong>Reusable GitHub Actions template</strong> for meaningful contribution signals (not dummy commits).</p>

<p align="center">
  <img src="https://img.shields.io/badge/automation-github_actions-181717?style=for-the-badge&logo=githubactions&logoColor=white" />
  <img src="https://img.shields.io/badge/language-python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/notifications-discord%20%2B%20telegram-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  <img src="https://img.shields.io/badge/mode-template_ready-00C853?style=for-the-badge" />
</p>

---

## ✨ Why this exists

`daily-signal` keeps your contribution flow active with **useful logs**:
- Daily engineering pulse
- Learning notes
- Weekly digest
- Health metadata

No random spam text. Everything is structured and auditable.

---

## 🧭 System Flow (How it works)

```mermaid
flowchart TD
  A[Schedule / Manual Trigger] --> B[Load config.yml]
  B --> C[Apply Guardrails<br/>max/day, weekend throttle, duplicate slot]
  C -->|skip| D[Write status: skipped + reason]
  C -->|pass| E[Generate useful content<br/>daily pulse / learning / weekly digest]
  E --> F[Resolve target repo<br/>self / profile / custom]
  F --> G[Commit + Push]
  G --> H[Generate run summary JSON]
  H --> I[Send Discord embed<br/>success or failure]
  H --> J[Send Telegram<br/>failure optional]
```

---

## ⚙️ Setup Flow (for users who fork/template)

```mermaid
flowchart LR
  A[Use Template / Fork] --> B[Actions: Setup Wizard]
  B --> C[Choose target mode + timezone + limits]
  C --> D[Auto-write .daily-signal/config.yml]
  D --> E[Optional: set secrets]
  E --> F[Run Heartbeat manually once]
  F --> G[Scheduler runs 24/7 by cron windows]
```

---

## 🚀 Quick Start

1. Click **Use this template**.
2. Go to **Actions → Setup Wizard → Run workflow**.
3. Choose configuration:
   - `target_mode`: `self | profile | custom`
   - timezone
   - commits/day policy
4. Optional secrets:
   - `DISCORD_WEBHOOK_URL` (success+failure embed)
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (failure alert)
   - `TARGET_REPO_TOKEN` (required for cross-repo push)
5. Run **Daily Signal** manually once to validate.

---

## 🧩 Target Modes

- `self` → writes to same repo (default)
- `profile` → writes to `username/username` profile repo
- `custom` → writes to repo specified in config

---

## 📦 Repo Structure

- `.github/workflows/setup.yml` → setup wizard
- `.github/workflows/heartbeat.yml` → main engine
- `.github/workflows/healthcheck.yml` → status check
- `.daily-signal/config.yml` → runtime config
- `scripts/runner.py` → generation engine
- `scripts/setup.py` → setup writer
- `logs/` → generated outputs

---

## 🔔 Discord Report Content (Embed)

Each run sends rich details:
- status (success/failure)
- source repo + run URL
- target mode/repo/branch
- slot + skip reason
- actions executed
- files generated

---

## 🛡️ Reliability Notes

- Scheduled windows run automatically (event-driven, not daemon process).
- Concurrency lock prevents overlap.
- Guardrails prevent noisy/duplicate commits.
- Works continuously as long as GitHub Actions is enabled.

---

## 📝 License / Usage

Free to use as your own template. Recommended: keep commit content meaningful.