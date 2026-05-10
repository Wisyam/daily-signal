import argparse
import json
import os
import random
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

CONFIG_PATH = Path('.daily-signal/config.yml')
STATUS_PATH = Path('logs/meta/status.json')
RUNTIME_DIR = Path('runtime_target')
OUTPUT_DIR = RUNTIME_DIR / 'output'
SUMMARY_PATH = RUNTIME_DIR / 'summary.json'

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

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

def now_tz(tz):
    return datetime.now(ZoneInfo(tz))

def is_weekend(dt):
    return dt.weekday() >= 5

def parse_utc_hhmm(base_utc):
    h, m = base_utc.split(':')
    return int(h), int(m)

def detect_slot_by_config(dt_utc, slots):
    # Pick nearest configured slot to current UTC minute
    now_min = dt_utc.hour * 60 + dt_utc.minute
    best = None
    best_diff = 10**9
    for slot in slots:
        h, m = parse_utc_hhmm(slot['base_utc'])
        slot_min = h * 60 + m
        diff = min(abs(now_min - slot_min), 1440 - abs(now_min - slot_min))
        if diff < best_diff:
            best_diff = diff
            best = slot
    return best or slots[0]

def should_skip(cfg, status, dt, force):
    if force:
        return False, 'force-run'
    max_day = cfg['policy']['max_commits_per_day']
    if cfg['policy'].get('weekend_mode', True) and is_weekend(dt):
        max_day = min(max_day, cfg['policy'].get('weekend_max_commits', 1))

    last_attempt = status.get('last_attempt', '')
    today = f'{dt:%Y-%m-%d}'
    if not last_attempt.startswith(today):
        status['today_count'] = 0

    if int(status.get('today_count', 0)) >= max_day:
        return True, 'max-commits-reached'

    # min gap guard
    gap_hours = int(cfg['policy'].get('min_gap_hours', 0))
    last_success = status.get('last_success', '')
    if last_success and gap_hours > 0:
        try:
            prev = datetime.fromisoformat(last_success)
            if dt - prev < timedelta(hours=gap_hours):
                return True, 'min-gap-not-met'
        except Exception:
            pass
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

def append_daily(base_dir, dt, zone_label, slot_name, include_learning):
    p = base_dir / f'daily/{dt:%Y-%m}.md'
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(f'# Daily Logs {dt:%Y-%m}\n\n', encoding='utf-8')
    content = p.read_text(encoding='utf-8')
    date_key = f'{dt:%Y-%m-%d}'
    if f'[{slot_name}] {date_key}' in content:
        return False, 'duplicate-slot-entry', None
    line = f'- [{slot_name}] {date_key} {dt:%H:%M} {zone_label} | {random.choice(PULSE_LINES)}\n'
    if include_learning:
        line += f'  - {random.choice(LEARN_LINES)}\n'
    p.write_text(content + line, encoding='utf-8')
    return True, 'written', str(p)

def append_weekly(base_dir, dt):
    week = dt.isocalendar().week
    p = base_dir / f'weekly/{dt:%Y}-W{week:02d}.md'
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        return False, 'weekly-exists', None
    text = f"# Weekly Digest {dt:%Y}-W{week:02d}\n\n- Focus: delivery consistency\n- Reliability: automation healthy\n- Next: improve quality signals\n"
    p.write_text(text, encoding='utf-8')
    return True, 'weekly-written', str(p)

def write_health(base_dir, status):
    p = base_dir / 'meta/status.json'
    save_json(p, status)
    return str(p)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='pulse')
    ap.add_argument('--force-run', default='false')
    args = ap.parse_args()

    cfg = load_config()
    status = load_status()
    tz_name = cfg.get('timezone', 'Asia/Jakarta')
    dt = now_tz(tz_name)
    dt_utc = dt.astimezone(ZoneInfo('UTC'))
    zone_label = dt.tzname() or tz_name
    force = str(args.force_run).lower() == 'true'

    mode, repo, branch = resolve_target(cfg)

    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    slot_cfg = detect_slot_by_config(dt_utc, cfg['schedule']['slots'])
    slot_name = slot_cfg['name']
    jitter_min = int(slot_cfg.get('jitter_min', 0))

    summary = {
        'timestamp': dt.isoformat(),
        'timezone': tz_name,
        'timezone_label': zone_label,
        'run_mode': args.mode,
        'target_mode': mode,
        'target_repo': repo,
        'target_branch': branch,
        'slot': slot_name,
        'slot_base_utc': slot_cfg.get('base_utc', ''),
        'jitter_min': jitter_min,
        'skipped': False,
        'skip_reason': '',
        'files_generated': [],
        'actions': []
    }

    status['last_attempt'] = dt.isoformat()
    skip, reason = should_skip(cfg, status, dt, force)
    if skip:
        status['last_reason'] = reason
        summary['skipped'] = True
        summary['skip_reason'] = reason
        summary['actions'].append('guard-skip')
        save_json(STATUS_PATH, status)
        if cfg['modules'].get('health_report', True):
            write_health(OUTPUT_DIR, status)
        save_json(SUMMARY_PATH, summary)
        print(f'Skipped: {reason}')
        return

    jitter_sec = random.randint(0, jitter_min * 60) if jitter_min > 0 else 0
    if jitter_sec:
        time.sleep(jitter_sec)
    summary['actions'].append(f'jitter-sleep-{jitter_sec}s')

    changed = False

    if cfg['modules'].get('pulse', True) and args.mode in ('pulse', 'healthcheck'):
        ok, why, path = append_daily(
            OUTPUT_DIR,
            dt,
            zone_label,
            slot_name,
            cfg['modules'].get('learning_note', True)
        )
        changed = changed or ok
        status['last_reason'] = why
        summary['actions'].append('daily-pulse')
        if path:
            summary['files_generated'].append(path)

    if cfg['modules'].get('weekly_digest', True) and args.mode in ('summary', 'pulse') and dt.weekday() == 6:
        ok, _, path = append_weekly(OUTPUT_DIR, dt)
        changed = changed or ok
        summary['actions'].append('weekly-digest')
        if path:
            summary['files_generated'].append(path)

    if changed:
        status['today_count'] = int(status.get('today_count', 0)) + 1
        status['last_success'] = dt.isoformat()
        status['consecutive_failures'] = 0
        status['last_slot'] = slot_name
        summary['actions'].append('content-generated')
    else:
        summary['actions'].append('no-change')
        status['last_reason'] = status.get('last_reason', 'no-change')

    if cfg['modules'].get('health_report', True):
        health_path = write_health(OUTPUT_DIR, status)
        summary['files_generated'].append(str(health_path))
        summary['actions'].append('health-report')

    save_json(STATUS_PATH, status)
    save_json(SUMMARY_PATH, summary)

    (RUNTIME_DIR / 'mode.txt').write_text(mode, encoding='utf-8')
    (RUNTIME_DIR / 'repo.txt').write_text(repo, encoding='utf-8')
    (RUNTIME_DIR / 'branch.txt').write_text(branch, encoding='utf-8')
    (RUNTIME_DIR / 'run_mode.txt').write_text(args.mode, encoding='utf-8')
    (RUNTIME_DIR / 'slot.txt').write_text(slot_name, encoding='utf-8')

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

    print(f'Runner completed. mode={mode} repo={repo} slot={slot_name}')

if __name__ == '__main__':
    main()