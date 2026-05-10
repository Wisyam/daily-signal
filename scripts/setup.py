import argparse
from pathlib import Path
import yaml

CONFIG_PATH = Path('.daily-signal/config.yml')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target-mode', required=True)
    ap.add_argument('--target-repo', default='')
    ap.add_argument('--timezone', default='Asia/Jakarta')
    ap.add_argument('--commits-per-day', type=int, default=3)
    ap.add_argument('--weekend-mode', default='true')
    args = ap.parse_args()

    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    cfg['target']['mode'] = args.target_mode
    cfg['target']['repo'] = args.target_repo.strip()
    cfg['timezone'] = args.timezone
    cfg['policy']['max_commits_per_day'] = max(1, min(args.commits_per_day, 3))
    cfg['policy']['weekend_mode'] = str(args.weekend_mode).lower() == 'true'

    CONFIG_PATH.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding='utf-8')
    print('Config updated via setup wizard.')

if __name__ == '__main__':
    main()