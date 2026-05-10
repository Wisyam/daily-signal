import argparse
import json
import os
import   random
import shutil
import time
from dateti m e import datetime, timedelta
from pathlib i mp ort Path
from zoneinfo import ZoneInfo
imp ort  yaml

CONFIG_PATH = Path('.daily-signal/ conf ig.yml')
STATUS_PATH = Path('logs/meta/s tatus .json')
RUNTIME_DIR = Path('runtime_tar get')
 OUTPUT_DIR = RUNTIME_DIR / 'output'
SU MMARY_P ATH = RUNTIME_DIR / 'summary.json'

P ULSE_LIN ES = [
    'Reviewed architecture tr ade-offs  for maintainability.',
    'Improve d build/re lease reliability checklist.',
     'Captured  debugging insights for recurring  issues.',
     'Documented implementation dec isions for fu ture reference.'
]
LEARN_LINES  = [
    'Learn ed: prefer config-driven workf lows for reusab ility.',
    'Learned: concur rency locks prev ent overlapping automation r uns.',
    'Learn ed: guardrails reduce noisy  commits while pre serving signal.',
    'Lea rned: failure notif ications should be action able, not noisy.'
]
 
def load_config():
     with CONFIG_PATH.open ('r', encoding='utf-8')  as f:
        return  yaml.safe_load(f)

def  load_status():
    if  not STATUS_PATH.exist s():
        return {"la st_success":"","last _attempt":"","today_count ":0,"last_slot":"", "last_reason":"init","cons ecutive_failures": 0}
    return json.loads(ST ATUS_PATH.read_te xt(encoding='utf-8'))

def s ave_json(path, d ata):
    path.parent.mkdir(p arents=True, ex ist_ok=True)
    path.write_te xt(json.dumps( data, indent=2), encoding='utf- 8')

def now_ tz(tz):
    return datetime.now( ZoneInfo(tz) )

def is_weekend(dt):
    return  dt.weekday () >= 5

def parse_utc_hhmm(base_u tc):
    h , m = base_utc.split(':')
    retur n int(h),  int(m)

def detect_slot_by_config(d t_utc, s lots):
    # Pick nearest configured  slot to  current UTC minute
    now_min = dt_u tc.hou r * 60 + dt_utc.minute
    best = None
     b est_diff = 10**9
    for slot in slots:
          h, m = parse_utc_hhmm(slot['base_utc' ])
         slot_min = h * 60 + m
        diff  =  min(abs(now_min - slot_min), 1440 - abs(no w _min - slot_min))
        if diff < best_dif  f:
            best_diff = diff
            b  est = slot
    return best or slots[0]

def  s hould_skip(cfg, status, dt, force):
    if  fo rce:
        return False, 'force-run'
     ma x_day = cfg['policy']['max_commits_per_da y']
     if cfg['policy'].get('weekend_mode',  True ) and is_weekend(dt):
        max_day =  min(m ax_day, cfg['policy'].get('weekend_max _commit s', 1))

    last_attempt = status.ge t('last_ attempt', '')
    today = f'{dt:%Y-% m-%d}'
     if not last_attempt.startswith(to day):
         status['today_count'] = 0

     if int(sta tus.get('today_count', 0)) >= max _day:
         return True, 'max-commits-reac hed'

    # m in gap guard
    gap_hours = in t(cfg['policy' ].get('min_gap_hours', 0))
     last_success =  status.get('last_success', ' ')
    if last_s uccess and gap_hours > 0:
         try:
             prev = datetime.fromi soformat(last_succ ess)
            if dt - p rev < timedelta(hou rs=gap_hours):
                 return True, ' min-gap-not-met'
         except Exception:
             pass
    retu rn False, 'ok'

def re solve_target(cfg):
     mode = cfg['target'].g et('mode', 'self')
     branch = cfg['target'] .get('branch', 'main ')
    repo = cfg['target '].get('repo', ''). strip()
    current_repo =  os.getenv('GITHUB _REPOSITORY', '').strip()
     actor = os.get env('GITHUB_ACTOR', '').stri p()

    if mode  == 'self':
        return mo de, current_rep o, branch
    if mode == 'prof ile':
         if repo:
            return mod e, repo, bran ch
        return mode, f'{actor }/{actor}',  branch
    if mode == 'custom':
         if n ot repo:
            raise Runtime Error('cus tom mode requires target.repo')
         retu rn mode, repo, branch
    raise Runt imeError (f'Unknown target mode: {mode}')

def  append _daily(base_dir, dt, zone_label, slot_ name,  include_learning):
    p = base_dir / f 'dail y/{dt:%Y-%m}.md'
    p.parent.mkdir(pare nts= True, exist_ok=True)
    if not p.exists( ):
         p.write_text(f'# Daily Logs {dt:%Y -% m}\n\n', encoding='utf-8')
    content = p. r ead_text(encoding='utf-8')
    date_key = f'  {dt:%Y-%m-%d}'
    if f'[{slot_name}] {date_k  ey}' in content:
        return False, 'dupl i cate-slot-entry', None
    line = f'- [{slo t_ name}] {date_key} {dt:%H:%M} {zone_label}  | { random.choice(PULSE_LINES)}\n'
    if inc lude _learning:
        line += f'  - {random .choi ce(LEARN_LINES)}\n'
    p.write_text(co ntent  + line, encoding='utf-8')
    return T rue, 'w ritten', str(p)

def append_weekly(ba se_dir,  dt):
    week = dt.isocalendar().wee k
    p =  base_dir / f'weekly/{dt:%Y}-W{week :02d}.md'
     p.parent.mkdir(parents=True, e xist_ok=Tru e)
    if p.exists():
        ret urn False, ' weekly-exists', None
    text =  f"# Weekly Di gest {dt:%Y}-W{week:02d}\n\n- F ocus: delivery  consistency\n- Reliability: a utomation healt hy\n- Next: improve quality s ignals\n"
    p. write_text(text, encoding='u tf-8')
    return  True, 'weekly-written', st r(p)

def write_he alth(base_dir, status):
     p = base_dir / 'm eta/status.json'
    save _json(p, status)
     return str(p)

def main ():
    ap = argparse .ArgumentParser()
    a p.add_argument('--mode ', default='pulse')
     ap.add_argument('--fo rce-run', default='fa lse')
    args = ap.pars e_args()

    cfg =  load_config()
    status  = load_status()
     tz_name = cfg.get('timezo ne', 'Asia/Jakarta ')
    dt = now_tz(tz_name) 
    dt_utc = dt. astimezone(ZoneInfo('UTC'))
     zone_label =  dt.tzname() or tz_name
    f orce = str(args .force_run).lower() == 'true'
 
    mode, rep o, branch = resolve_target(cfg) 

    if RUNT IME_DIR.exists():
        shutil .rmtree(RUNT IME_DIR)
    OUTPUT_DIR.mkdir(par ents=True,  exist_ok=True)

    slot_cfg = det ect_slot_b y_config(dt_utc, cfg['schedule']['s lots'])
     slot_name = slot_cfg['name']
     jitter_m in = int(slot_cfg.get('jitter_min', 0 ))

     summary = {
        'timestamp': dt.i soform at(),
        'timezone': tz_name,
         ' timezone_label': zone_label,
        'ru n_mo de': args.mode,
        'target_mode': mo de, 
        'target_repo': repo,
        'tar ge t_branch': branch,
        'slot': slot_nam e ,
        'slot_base_utc': slot_cfg.get('bas  e_utc', ''),
        'jitter_min': jitter_min  ,
        'skipped': False,
        'skip_re a son': '',
        'files_generated': [],
          'actions': []
    }

    status['last_ att empt'] = dt.isoformat()
    skip, reason  = sh ould_skip(cfg, status, dt, force)
    if  skip :
        status['last_reason'] = reaso n
         summary['skipped'] = True
         summary ['skip_reason'] = reason
        summ ary['act ions'].append('guard-skip')
         save_json (STATUS_PATH, status)
        if cf g['modules '].get('health_report', True):
             wr ite_health(OUTPUT_DIR, status)
         save_j son(SUMMARY_PATH, summary)
         print(f'Sk ipped: {reason}')
        retur n

    jitter_ sec = random.randint(0, jitter _min * 60) if j itter_min > 0 else 0
    if j itter_sec:
         time.sleep(jitter_sec)
     summary['action s'].append(f'jitter-sleep-{ jitter_sec}s')

     changed = False

    if  cfg['modules'].get( 'pulse', True) and args.m ode in ('pulse', 'he althcheck'):
        ok,  why, path = append_d aily(
            OUTPU T_DIR,
            dt, 
            zone_labe l,
            slot_nam e,
            cfg['m odules'].get('learning_n ote', True)
         )
        changed = chang ed or ok
        st atus['last_reason'] = why
         summary['a ctions'].append('daily-puls e')
        if pa th:
            summary['fil es_generated'].a ppend(path)

    if cfg['modu les'].get('week ly_digest', True) and args.mod e in ('summary ', 'pulse') and dt.weekday() ==  6:
        o k, _, path = append_weekly(OUTPU T_DIR, dt)
         changed = changed or ok
         summa ry['actions'].append('weekly-diges t')
         if path:
            summary['fil es_genera ted'].append(path)

    if changed:
          status['today_count'] = int(status.ge t('toda y_count', 0)) + 1
        status['last _succe ss'] = dt.isoformat()
        status['c onsec utive_failures'] = 0
        status['las t_sl ot'] = slot_name
        summary['actions ']. append('content-generated')
    else:
          summary['actions'].append('no-change')
          status['last_reason'] = status.get('las  t_reason', 'no-change')

    if cfg['modules'  ].get('health_report', True):
        health _ path = write_health(OUTPUT_DIR, status)
          summary['files_generated'].append(str(h eal th_path))
        summary['actions'].appe nd(' health-report')

    save_json(STATUS_PA TH, s tatus)
    save_json(SUMMARY_PATH, summ ary)

     (RUNTIME_DIR / 'mode.txt').write_t ext(mod e, encoding='utf-8')
    (RUNTIME_DIR  / 'repo .txt').write_text(repo, encoding='ut f-8')
     (RUNTIME_DIR / 'branch.txt').write _text(bran ch, encoding='utf-8')
    (RUNTIME _DIR / 'run _mode.txt').write_text(args.mode,  encoding='u tf-8')
    (RUNTIME_DIR / 'slot. txt').write_t ext(slot_name, encoding='utf-8' )

    if mode  == 'self':
        local_logs  = Path('logs') 
        local_logs.mkdir(par ents=True, exist _ok=True)
        for child  in OUTPUT_DIR.ite rdir():
            target  = local_logs / chi ld.name
            if chi ld.is_dir():
                 if target.exist s():
                     shutil.rmtree(targe t)
                sh util.copytree(child, ta rget)
            else :
                shut il.copy2(child, target) 

    print(f'Runner  completed. mode={mode} r epo={repo} slot={slo t_name}')

if __name__ ==  '__main__':
    ma in()  