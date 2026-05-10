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


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))


def load_status() -> dict:
    if not STATUS_PATH.exists():
        return {
            'last_success': '',
            'last_attempt': '',
            'today_count': 0,
            'last_slot': '',
            'last_reason': 'init',
            'consecutive_failures': 0,
        }
    return json.loads(STATUS_PATH.read_text(encoding='utf-8'))


def parse_hhmm_utc(value: str) -> tuple[int, int]:
    hour, minute = value.split(':')
    return int(hour), int(minute)


def nearest_slot(now_utc: datetime, slots: list[dict]) -> dict:
    now_min = now_utc.hour * 60 + now_utc.minute
    best = slots[0]
    best_diff = 10**9
    for slot in slots:
        h, m = parse_hhmm_utc(slot['base_utc'])
        slot_min = h * 60 + m
        diff = min(abs(now_min - slot_min), 1440 - abs(now_min - slot_min))
        if diff < best_diff:
            best_diff = diff
            best = slot
    return best


def resolve_target(cfg: dict) -> tuple[str, str, str]:
    mode = cfg['target'].get('mode', 'self')
    branch = cfg['target'].get('branch', 'main')
    repo = cfg['target'].get('repo', '').strip()
    current_repo = os.getenv('GITHUB_REPOSITORY', '').strip()
    actor = os.getenv('GITHUB_ACTOR', '').strip()

    if mode == 'self':
        return mode, current_repo, branch
    if mode == 'profile':
        return mode, (repo or f'{actor}/{actor}'), branch
    if mode == 'custom':
        if not repo:
            raise RuntimeError('custom mode requires target.repo')
        return mode, repo, branch
    raise RuntimeError(f'Unknown target mode: {mode}')


def append_daily(base_dir: Path, dt: datetime, zone_label: str, slot_name: str, include_learning: bool):
    path = base_dir / f'daily/{dt:%Y-%m}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f'# Daily Logs {dt:%Y-%m}\n\n', encoding='utf-8')

    text = path.read_text(encoding='utf-8')
    key = f'{dt:%Y-%m-%d}'
    if f'[{slot_name}] {key}' in text:
        return False, 'duplicate-slot-entry', None

    line = f'- [{slot_name}] {key} {dt:%H:%M} {zone_label} | {random.choice(PULSE_LINES)}\n'
    if include_learning:
        line += f'  - {random.choice(LEARN_LINES)}\n'

    path.write_text(text + line, encoding='utf-8')
    return True, 'written', str(path)


def append_weekly(base_dir: Path, dt: datetime):
    week = dt.isocalendar().week
    path = base_dir / f'weekly/{dt:%Y}-W{week:02d}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False, 'weekly-exists', None
    body = (
        f'# Weekly Digest {dt:%Y}-W{week:02d}\n\n'
        '- Focus: delivery consistency\n'
        '- Reliability: automation healthy\n'
        '- Next: improve quality signals\n'
    )
    path.write_text(body, encoding='utf-8')
    return True, 'weekly-written', str(path)


def should_skip(cfg: dict, status: dict, dt: datetime, force: bool):
    if force:
        return False, 'force-run'

    max_day = int(cfg['policy']['max_commits_per_day'])
    if cfg['policy'].get('weekend_mode', True) and dt.weekday() >= 5:
        max_day = min(max_day, int(cfg['policy'].get('weekend_max_commits', 1)))

    today = f'{dt:%Y-%m-%d}'
    if not str(status.get('last_attempt', '')).startswith(today):
        status['today_count'] = 0

    if int(status.get('today_count', 0)) >= max_day:
        return True, 'max-commits-reached'

    min_gap = int(cfg['policy'].get('min_gap_hours', 0))
    last_success = status.get('last_success', '')
    if last_success and min_gap > 0:
        try:
            prev = datetime.fromisoformat(last_success)
            if dt - prev < timedelta(hours=min_gap):
                return True, 'min-gap-not-met'
        except Exception:
            pass

    return False, 'ok'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='pulse')
    parser.add_argument('--force-run', default='false')
    args = parser.parse_args()

    cfg = load_config()
    status = load_status()

    tz_name = cfg.get('timezone', 'Asia/Jakarta')
    now_local = datetime.now(ZoneInfo(tz_name))
    now_utc = now_local.astimezone(ZoneInfo('UTC'))
    zone_label = now_local.tzname() or tz_name
    force = str(args.force_run).lower() == 'true'

    mode, repo, branch = resolve_target(cfg)

    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    slot = nearest_slot(now_utc, cfg['schedule']['slots'])
    slot_name = slot['name']
    jitter_min = int(slot.get('jitter_min', 0))

    summary = {
        'timestamp': now_local.isoformat(),
        'timezone': tz_name,
        'timezone_label': zone_label,
        'run_mode': args.mode,
        'target_mode': mode,
        'target_repo': repo,
        'target_branch': branch,
        'slot': slot_name,
        'slot_base_utc': slot.get('base_utc', ''),
        'jitter_min': jitter_min,
        'skipped': False,
        'skip_reason': '',
        'files_generated': [],
        'actions': [],
    }

    status['last_attempt'] = now_local.isoformat()
    skip, reason = should_skip(cfg, status, now_local, force)
    if skip:
        status['last_reason'] = reason
        summary['skipped'] = True
        summary['skip_reason'] = reason
        summary['actions'].append('guard-skip')
        save_json(STATUS_PATH, status)
        if cfg['modules'].get('health_report', True):
            save_json(OUTPUT_DIR / 'meta/status.json', status)
        save_json(SUMMARY_PATH, summary)
        print(f'Skipped: {reason}')
        return

    max_jitter = jitter_min * 60
    if os.getenv('GITHUB_EVENT_NAME', '') == 'workflow_dispatch':
        max_jitter = min(max_jitter, 5)
    jitter = random.randint(0, max_jitter) if max_jitter > 0 else 0
    if jitter:
        time.sleep(jitter)
    summary['actions'].append(f'jitter-sleep-{jitter}s')

    changed = False

    if cfg['modules'].get('pulse', True) and args.mode in ('pulse', 'healthcheck'):
        ok, why, path = append_daily(
            OUTPUT_DIR,
            now_local,
            zone_label,
            slot_name,
            cfg['modules'].get('learning_note', True),
        )
        changed = changed or ok
        status['last_reason'] = why
        summary['actions'].append('daily-pulse')
        if path:
            summary['files_generated'].append(path)

    if cfg['modules'].get('weekly_digest', True) and args.mode in ('summary', 'pulse') and now_local.weekday() == 6:
        ok, _, path = append_weekly(OUTPUT_DIR, now_local)
        changed = changed or ok
        summary['actions'].append('weekly-digest')
        if path:
            summary['files_generated'].append(path)

    if changed:
        status['today_count'] = int(status.get('today_count', 0)) + 1
        status['last_success'] = now_local.isoformat()
        status['consecutive_failures'] = 0
        status['last_slot'] = slot_name
        summary['actions'].append('content-generated')
    else:
        status['last_reason'] = status.get('last_reason', 'no-change')
        summary['actions'].append('no-change')

    if cfg['modules'].get('health_report', True):
        save_json(OUTPUT_DIR / 'meta/status.json', status)
        summary['actions'].append('health-report')
        summary['files_generated'].append('runtime_target/output/meta/status.json')

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