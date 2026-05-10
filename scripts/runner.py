import argparse
import json
import os
import  random
import shutil
import time
from datetim e import datetime, timedelta
from pathlib imp ort Path
from zoneinfo import ZoneInfo
import  yaml

CONFIG_PATH = Path('.daily-signal/conf ig.yml')
STATUS_PATH = Path('logs/meta/status .json')
RUNTIME_DIR = Path('runtime_target')
 OUTPUT_DIR = RUNTIME_DIR / 'output'
SUMMARY_P ATH = RUNTIME_DIR / 'summary.json'

PULSE_LIN ES = [
    'Reviewed architecture trade-offs  for maintainability.',
    'Improved build/re lease reliability checklist.',
    'Captured  debugging insights for recurring issues.',
     'Documented implementation decisions for fu ture reference.'
]
LEARN_LINES = [
    'Learn ed: prefer config-driven workflows for reusab ility.',
    'Learned: concurrency locks prev ent overlapping automation runs.',
    'Learn ed: guardrails reduce noisy commits while pre serving signal.',
    'Learned: failure notif ications should be actionable, not noisy.'
]
 
def load_config():
    with CONFIG_PATH.open ('r', encoding='utf-8') as f:
        return  yaml.safe_load(f)

def load_status():
    if  not STATUS_PATH.exists():
        return {"la st_success":"","last_attempt":"","today_count ":0,"last_slot":"","last_reason":"init","cons ecutive_failures":0}
    return json.loads(ST ATUS_PATH.read_text(encoding='utf-8'))

def s ave_json(path, data):
    path.parent.mkdir(p arents=True, exist_ok=True)
    path.write_te xt(json.dumps(data, indent=2), encoding='utf- 8')

def now_tz(tz):
    return datetime.now( ZoneInfo(tz))

def is_weekend(dt):
    return  dt.weekday() >= 5

def parse_utc_hhmm(base_u tc):
    h, m = base_utc.split(':')
    retur n int(h), int(m)

def detect_slot_by_config(d t_utc, slots):
    # Pick nearest configured  slot to current UTC minute
    now_min = dt_u tc.hour * 60 + dt_utc.minute
    best = None
     best_diff = 10**9
    for slot in slots:
         h, m = parse_utc_hhmm(slot['base_utc' ])
        slot_min = h * 60 + m
        diff  = min(abs(now_min - slot_min), 1440 - abs(no w_min - slot_min))
        if diff < best_dif f:
            best_diff = diff
            b est = slot
    return best or slots[0]

def s hould_skip(cfg, status, dt, force):
    if fo rce:
        return False, 'force-run'
    ma x_day = cfg['policy']['max_commits_per_day']
     if cfg['policy'].get('weekend_mode', True ) and is_weekend(dt):
        max_day = min(m ax_day, cfg['policy'].get('weekend_max_commit s', 1))

    last_attempt = status.get('last_ attempt', '')
    today = f'{dt:%Y-%m-%d}'
     if not last_attempt.startswith(today):
         status['today_count'] = 0

    if int(sta tus.get('today_count', 0)) >= max_day:
         return True, 'max-commits-reached'

    # m in gap guard
    gap_hours = int(cfg['policy' ].get('min_gap_hours', 0))
    last_success =  status.get('last_success', '')
    if last_s uccess and gap_hours > 0:
        try:
             prev = datetime.fromisoformat(last_succ ess)
            if dt - prev < timedelta(hou rs=gap_hours):
                return True, ' min-gap-not-met'
        except Exception:
             pass
    return False, 'ok'

def re solve_target(cfg):
    mode = cfg['target'].g et('mode', 'self')
    branch = cfg['target'] .get('branch', 'main')
    repo = cfg['target '].get('repo', '').strip()
    current_repo =  os.getenv('GITHUB_REPOSITORY', '').strip()
     actor = os.getenv('GITHUB_ACTOR', '').stri p()

    if mode == 'self':
        return mo de, current_repo, branch
    if mode == 'prof ile':
        if repo:
            return mod e, repo, branch
        return mode, f'{actor }/{actor}', branch
    if mode == 'custom':
         if not repo:
            raise Runtime Error('custom mode requires target.repo')
         return mode, repo, branch
    raise Runt imeError(f'Unknown target mode: {mode}')

def  append_daily(base_dir, dt, zone_label, slot_ name, include_learning):
    p = base_dir / f 'daily/{dt:%Y-%m}.md'
    p.parent.mkdir(pare nts=True, exist_ok=True)
    if not p.exists( ):
        p.write_text(f'# Daily Logs {dt:%Y -%m}\n\n', encoding='utf-8')
    content = p. read_text(encoding='utf-8')
    date_key = f' {dt:%Y-%m-%d}'
    if f'[{slot_name}] {date_k ey}' in content:
        return False, 'dupli cate-slot-entry', None
    line = f'- [{slot_ name}] {date_key} {dt:%H:%M} {zone_label} | { random.choice(PULSE_LINES)}\n'
    if include _learning:
        line += f'  - {random.choi ce(LEARN_LINES)}\n'
    p.write_text(content  + line, encoding='utf-8')
    return True, 'w ritten', str(p)

def append_weekly(base_dir,  dt):
    week = dt.isocalendar().week
    p =  base_dir / f'weekly/{dt:%Y}-W{week:02d}.md'
     p.parent.mkdir(parents=True, exist_ok=Tru e)
    if p.exists():
        return False, ' weekly-exists', None
    text = f"# Weekly Di gest {dt:%Y}-W{week:02d}\n\n- Focus: delivery  consistency\n- Reliability: automation healt hy\n- Next: improve quality signals\n"
    p. write_text(text, encoding='utf-8')
    return  True, 'weekly-written', str(p)

def write_he alth(base_dir, status):
    p = base_dir / 'm eta/status.json'
    save_json(p, status)
     return str(p)

def main():
    ap = argparse .ArgumentParser()
    ap.add_argument('--mode ', default='pulse')
    ap.add_argument('--fo rce-run', default='false')
    args = ap.pars e_args()

    cfg = load_config()
    status  = load_status()
    tz_name = cfg.get('timezo ne', 'Asia/Jakarta')
    dt = now_tz(tz_name) 
    dt_utc = dt.astimezone(ZoneInfo('UTC'))
     zone_label = dt.tzname() or tz_name
    f orce = str(args.force_run).lower() == 'true'
 
    mode, repo, branch = resolve_target(cfg) 

    if RUNTIME_DIR.exists():
        shutil .rmtree(RUNTIME_DIR)
    OUTPUT_DIR.mkdir(par ents=True, exist_ok=True)

    slot_cfg = det ect_slot_by_config(dt_utc, cfg['schedule']['s lots'])
    slot_name = slot_cfg['name']
     jitter_min = int(slot_cfg.get('jitter_min', 0 ))

    summary = {
        'timestamp': dt.i soformat(),
        'timezone': tz_name,
         'timezone_label': zone_label,
        'ru n_mode': args.mode,
        'target_mode': mo de,
        'target_repo': repo,
        'tar get_branch': branch,
        'slot': slot_nam e,
        'slot_base_utc': slot_cfg.get('bas e_utc', ''),
        'jitter_min': jitter_min ,
        'skipped': False,
        'skip_rea son': '',
        'files_generated': [],
         'actions': []
    }

    status['last_att empt'] = dt.isoformat()
    skip, reason = sh ould_skip(cfg, status, dt, force)
    if skip :
        status['last_reason'] = reason
         summary['skipped'] = True
        summary ['skip_reason'] = reason
        summary['act ions'].append('guard-skip')
        save_json (STATUS_PATH, status)
        if cfg['modules '].get('health_report', True):
            wr ite_health(OUTPUT_DIR, status)
        save_j son(SUMMARY_PATH, summary)
        print(f'Sk ipped: {reason}')
        return

    jitter_ sec = random.randint(0, jitter_min * 60) if j itter_min > 0 else 0
    if jitter_sec:
         time.sleep(jitter_sec)
    summary['action s'].append(f'jitter-sleep-{jitter_sec}s')

     changed = False

    if cfg['modules'].get( 'pulse', True) and args.mode in ('pulse', 'he althcheck'):
        ok, why, path = append_d aily(
            OUTPUT_DIR,
            dt, 
            zone_label,
            slot_nam e,
            cfg['modules'].get('learning_n ote', True)
        )
        changed = chang ed or ok
        status['last_reason'] = why
         summary['actions'].append('daily-puls e')
        if path:
            summary['fil es_generated'].append(path)

    if cfg['modu les'].get('weekly_digest', True) and args.mod e in ('summary', 'pulse') and dt.weekday() ==  6:
        ok, _, path = append_weekly(OUTPU T_DIR, dt)
        changed = changed or ok
         summary['actions'].append('weekly-diges t')
        if path:
            summary['fil es_generated'].append(path)

    if changed:
         status['today_count'] = int(status.ge t('today_count', 0)) + 1
        status['last _success'] = dt.isoformat()
        status['c onsecutive_failures'] = 0
        status['las t_slot'] = slot_name
        summary['actions '].append('content-generated')
    else:
         summary['actions'].append('no-change')
         status['last_reason'] = status.get('las t_reason', 'no-change')

    if cfg['modules' ].get('health_report', True):
        health_ path = write_health(OUTPUT_DIR, status)
         summary['files_generated'].append(str(heal th_path))
        summary['actions'].append(' health-report')

    save_json(STATUS_PATH, s tatus)
    save_json(SUMMARY_PATH, summary)

     (RUNTIME_DIR / 'mode.txt').write_text(mod e, encoding='utf-8')
    (RUNTIME_DIR / 'repo .txt').write_text(repo, encoding='utf-8')
     (RUNTIME_DIR / 'branch.txt').write_text(bran ch, encoding='utf-8')
    (RUNTIME_DIR / 'run _mode.txt').write_text(args.mode, encoding='u tf-8')
    (RUNTIME_DIR / 'slot.txt').write_t ext(slot_name, encoding='utf-8')

    if mode  == 'self':
        local_logs = Path('logs') 
        local_logs.mkdir(parents=True, exist _ok=True)
        for child in OUTPUT_DIR.ite rdir():
            target = local_logs / chi ld.name
            if child.is_dir():
                 if target.exists():
                     shutil.rmtree(target)
                sh util.copytree(child, target)
            else :
                shutil.copy2(child, target) 

    print(f'Runner completed. mode={mode} r epo={repo} slot={slot_name}')

if __name__ ==  '__main__':
    main() 