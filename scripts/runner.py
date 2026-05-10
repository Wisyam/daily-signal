import argparse
import json
import os
import random
import shutil
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

CONFIG_PATH = Path('.daily-signal/config.yml')
STATUS_PATH = Path('logs/meta/status.json')
RUNTIME_DIR = Path('runtime_target')
OUTPUT_DIR = RUNTIME_DIR / 'output'

PULSE_LINES = [
    'Reviewed architecture trade-offs for maintainability.',
    'Improved build/release reliability checklist.',
    'Captured debugging insights for recurring issues.',
    'Documented implementation decisions for future reference.'
]
LEARN_LINES = [
    'Learned: prefer config-driven workflows for reusability.',
    'Learned: concurrency locks prevent overlapping automation runs.',
    'Learned: guardrails reduce noisy commits while preserving signal.',
    'Learned: failure notifications should be actionable, not noisy.'
]

def load_config():
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_status():
    if not STATUS_PATH.exists():
        return {"last_success":"","last_attempt":"","today_count":0,"last_slot":"","last_reason":"init","consecutive_failures":0}
    return json.loads(STATUS_PATH.read_text(encoding='utf-8'))

def save_status(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

def now_tz(tz):
    return datetime.now(ZoneInfo(tz))

def is_weekend(dt):
    return dt.weekday() >= 5

def detect_slot(hour):
    if 8 <= hour <= 11:
        return 'morning'
    if 12 <= hour <= 17:
        return 'afternoon'
    return 'night'

def append_daily_log(base_dir, dt, slot):
    p = base_dir / f'daily/{dt:%Y-%m}.md'
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(f'# Daily Logs {dt:%Y-%m}\n\n', encoding='utf-8')
    content = p.read_text(encoding='utf-8')
    date_key = f'{dt:%Y-%m-%d}'
    if f'[{slot}] {date_key}' in content:
        return False, 'duplicate-slot-entry'
    line = f'- [{slot}] {date_key} {dt:%H:%M} WIB | {random.choice(PULSE_LINES)}\n'
    line += f'  - {random.choice(LEARN_LINES)}\n'
    p.write_text(content + line, encoding='utf-8')
    return True, 'written'

def append_weekly_digest(base_dir, dt):
    week = dt.isocalendar().week
    p = base_dir / f'weekly/{dt:%Y}-W{week:02d}.md'
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        return False, 'weekly-exists'
    text = f"# Weekly Digest {dt:%Y}-W{week:02d}\n\n- Focus: delivery consistency\n- Reliability: automation healthy\n- Next: improve quality signals\n"
    p.write_text(text, encoding='utf-8')
    return True, 'weekly-written'

def should_skip(cfg, status, dt, force):
    if force:
        return False, 'force-run'
    max_day = cfg['policy']['max_commits_per_day']
    if cfg['policy'].get('weekend_mode', True) and is_weekend(dt):
        max_day = min(max_day, cfg['policy'].get('weekend_max_commits', 1))
    last_attempt = status.get('last_attempt', '')
    if last_attempt.startswith(f'{dt:%Y-%m-%d}') and status.get('today_count', 0) >= max_day:
        return True, 'max-commits-reached'
    return False, 'ok'

def resolve_target(cfg):
    mode = cfg['target'].get('mode', 'self')
    branch = cfg['target'].get('branch', 'main')
    repo = cfg['target'].get('repo', '').strip()
    current_repo = os.getenv('GITHUB_REPOSITORY', '').strip()
    actor = os.getenv('GITHUB_ACTOR', '').strip()

    if mode == 'self':
        return mode, current_repo, branch
    if mode == 'profile':
        if repo:
            return mode, repo, branch
        return mode, f'{actor}/{actor}', branch
    if mode == 'custom':
        if not repo:
            raise RuntimeError('custom mode requires target.repo')
        return mode, repo, branch
    raise RuntimeError(f'Unknown target mode: {mode}')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='pulse')
    ap.add_argument('--force-run', default='false')
    args = ap.parse_args()

    cfg = load_config()
    status = load_status()
    dt = now_tz(cfg.get('timezone', 'Asia/Jakarta'))
    force = str(args.force_run).lower() == 'true'

    mode, repo, branch = resolve_target(cfg)

    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    (RUNTIME_DIR / 'mode.txt').write_text(mode, encoding='utf-8')
    (RUNTIME_DIR / 'repo.txt').write_text(repo, encoding='utf-8')
    (RUNTIME_DIR / 'branch.txt').write_text(branch, encoding='utf-8')
    (RUNTIME_DIR / 'run_mode.txt').write_text(args.mode, encoding='utf-8')

    status['last_attempt'] = dt.isoformat()

    skip, reason = should_skip(cfg, status, dt, force)
    if skip:
        status['last_reason'] = reason
        save_status(STATUS_PATH, status)
        save_status(OUTPUT_DIR / 'meta/status.json', status)
        print(f'Skipped: {reason}')
        return

    slot = detect_slot(dt.hour)
    (RUNTIME_DIR / 'slot.txt').write_text(slot, encoding='utf-8')
    random.seed(f"{dt:%Y-%m-%d}-{slot}")
    time.sleep(random.randint(0, 20))

    changed = False
    if args.mode in ('pulse', 'healthcheck') and cfg['modules'].get('pulse', True):
        ok, why = append_daily_log(OUTPUT_DIR, dt, slot)
        changed = changed or ok
        status['last_reason'] = why

    if args.mode in ('summary', 'pulse') and cfg['modules'].get('weekly_digest', True) and dt.weekday() == 6:
        ok, _ = append_weekly_digest(OUTPUT_DIR, dt)
        changed = changed or ok

    if changed:
        status['today_count'] = int(status.get('today_count', 0)) + 1
        status['last_success'] = dt.isoformat()
        status['consecutive_failures'] = 0
        status['last_slot'] = slot
    else:
        status['last_reason'] = status.get('last_reason', 'no-change')

    save_status(STATUS_PATH, status)
    save_status(OUTPUT_DIR / 'meta/status.json', status)

    if mode == 'self':
        local_logs = Path('logs')
        local_logs.mkdir(parents=True, exist_ok=True)
        for child in OUTPUT_DIR.iterdir():
            target = local_logs / child.name
            if child.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)

    print(f'Runner completed. mode={mode} repo={repo}')

if __name__ == '__main__':
    main()