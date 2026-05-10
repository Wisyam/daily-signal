<h1 align="center">daily-signal</h1>
<p align ="center"><strong>Reusable GitHub Actions tem plate</strong> for meaningful contribution si gnals (not dummy commits).</p>

<p align="cen ter">
  <img src="https://img.shields.io/badg e/automation-github_actions-181717?style=for- the-badge&logo=githubactions&logoColor=white"  />
  <img src="https://img.shields.io/badge/ language-python-3776AB?style=for-the-badge&lo go=python&logoColor=white" />
  <img src="htt ps://img.shields.io/badge/notifications-disco rd%20%2B%20telegram-5865F2?style=for-the-badg e&logo=discord&logoColor=white" />
  <img src ="https://img.shields.io/badge/mode-template_ ready-00C853?style=for-the-badge" />
</p>

-- -

## ✨ Why this exists

`daily-signal` kee ps your contribution flow active with **usefu l logs**:
- Daily engineering pulse
- Learnin g notes
- Weekly digest
- Health metadata

No  random spam text. Everything is structured a nd auditable.

---

## 🧭 System Flow (How  it works)

```mermaid
flowchart TD
  A[Schedu le / Manual Trigger] --> B[Load config.yml]
   B --> C[Apply Guardrails<br/>max/day, weeken d throttle, duplicate slot]
  C -->|skip| D[W rite status: skipped + reason]
  C -->|pass|  E[Generate useful content<br/>daily pulse / l earning / weekly digest]
  E --> F[Resolve ta rget repo<br/>self / profile / custom]
  F -- > G[Commit + Push]
  G --> H[Generate run sum mary JSON]
  H --> I[Send Discord embed<br/>s uccess or failure]
  H --> J[Send Telegram<br />failure optional]
```

---

## ⚙️ Setup  Flow (for users who fork/template)

```merma id
flowchart LR
  A[Use Template / Fork] -->  B[Actions: Setup Wizard]
  B --> C[Choose tar get mode + timezone + limits]
  C --> D[Auto- write .daily-signal/config.yml]
  D --> E[Opt ional: set secrets]
  E --> F[Run Heartbeat m anually once]
  F --> G[Scheduler runs 24/7 b y cron windows]
```

---

## 🚀 Quick Start 

1. Click **Use this template**.
2. Go to ** Actions → Setup Wizard → Run workflow**.
 3. Choose configuration:
   - `target_mode`:  `self | profile | custom`
   - timezone
   -  commits/day policy
4. Optional secrets:
   -  `DISCORD_WEBHOOK_URL` (success+failure embed) 
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID ` (failure alert)
   - `TARGET_REPO_TOKEN` (r equired for cross-repo push)
5. Run **Daily S ignal** manually once to validate.

---

## � ��� Target Modes

- `self` → writes to same  repo (default)
- `profile` → writes to `us ername/username` profile repo
- `custom` →  writes to repo specified in config

---

## � ��� Repo Structure

- `.github/workflows/setu p.yml` → setup wizard
- `.github/workflows/ heartbeat.yml` → main engine
- `.github/wor kflows/healthcheck.yml` → status check
- `. daily-signal/config.yml` → runtime config
-  `scripts/runner.py` → generation engine
-  `scripts/setup.py` → setup writer
- `logs/`  → generated outputs

---

## 🔔 Discord  Report Content (Embed)

Each run sends rich d etails:
- status (success/failure)
- source r epo + run URL
- target mode/repo/branch
- slo t + skip reason
- actions executed
- files ge nerated

---

## 🛡️ Reliability Notes

-  Scheduled windows run automatically (event-d riven, not daemon process).
- Concurrency loc k prevents overlap.
- Guardrails prevent nois y/duplicate commits.
- Works continuously as  long as GitHub Actions is enabled.

---

## � ��� License / Usage

Free to use as your own  template. Recommended: keep commit content me aningful.  \n\n## ✅ Quality Gates\n\n- CI workflow runs `ruff` + `pytest` on push/PR.\n- Config schema now validates nested runtime fields used by engine.\n- Runtime slot selection now uses `.daily-signal/config.yml` `schedule.slots` as source of truth.\n