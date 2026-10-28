import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from .core import read_source, parse_subscription, make_config
from .sources import load, save, add_source, add_manual, collect, DEFAULT_PAGE

USER_DATA = Path.home() / '.config/smartproxy'
CONFIG = USER_DATA / 'config.json'
SOURCES = USER_DATA / 'sources.json'
SYSTEM_CONFIG = '/etc/smartproxy/config.json'
SERVICE = 'smartproxy.service'

def call(*args):
    p = subprocess.run(args, text=True)
    return p.returncode

def build(source, mode):
    nodes = parse_subscription(read_source(source))
    if not nodes:
        raise ValueError('No supported VLESS, VMess, Trojan or Shadowsocks nodes found')
    USER_DATA.mkdir(parents=True, exist_ok=True)
    os.chmod(USER_DATA, 0o700)
    with CONFIG.open('w') as f:
        json.dump(make_config(nodes, mode), f, indent=2)
    os.chmod(CONFIG, 0o600)
    print(f'Imported {len(nodes)} nodes into {CONFIG}')
    return len(nodes)

def main(argv=None):
    parser = argparse.ArgumentParser(prog='smartproxy')
    sub = parser.add_subparsers(dest='action', required=True)
    imp = sub.add_parser('import', help='Fetch and build a subscription')
    imp.add_argument('source', help='HTTPS subscription URL or local text file')
    imp.add_argument('--mode', choices=['tun','proxy'], default='tun')
    add = sub.add_parser('add', help='Save an HTTPS subscription URL')
    add.add_argument('url')
    manual = sub.add_parser('add-uri', help='Save one VLESS/VMess/Trojan/SS URI')
    manual.add_argument('uri')
    sub.add_parser('sources', help='List subscription sources')
    sub.add_parser('refresh', help='Rebuild config from all saved sources')
    for name in ('start','stop','restart','status','logs','check'):
        sub.add_parser(name)
    args = parser.parse_args(argv)
    try:
        if args.action in ('add','add-uri'):
            data = load(SOURCES)
            (add_source(data,args.url) if args.action=='add' else add_manual(data,args.uri))
            save(SOURCES,data)
            print('Source saved. Run smartproxy refresh to build the configuration.')
            return 0
        if args.action == 'sources':
            data=load(SOURCES)
            print('Yamyam website reference (not a validated subscription):', DEFAULT_PAGE)
            print('Subscriptions:', *data['sources'], sep='\n  ')
            print('Manual nodes:', len(data['manual']))
            return 0
        if args.action == 'refresh':
            nodes, problems = collect(load(SOURCES))
            if not nodes:
                raise ValueError('No supported nodes. Add an HTTPS subscription or URI first. ' + '; '.join(problems))
            USER_DATA.mkdir(parents=True,exist_ok=True)
            USER_DATA.chmod(0o700)
            CONFIG.write_text(json.dumps(make_config(nodes),indent=2))
            CONFIG.chmod(0o600)
            print(f'Generated {len(nodes)} nodes; failures: {len(problems)}')
            for error in problems: print('Warning:',error, file=sys.stderr)
            return 0
        if args.action == 'import':
            build(args.source, args.mode)
            print('Next: smartproxy check, then smartproxy start')
            return 0
        if args.action == 'check':
            if not CONFIG.exists():
                raise ValueError('Import a subscription first')
            if not shutil.which('sing-box'):
                raise ValueError('sing-box not installed')
            return call('sing-box', 'check', '-c', str(CONFIG))
        if args.action == 'start':
            if not CONFIG.exists():
                raise ValueError('Import a subscription first')
            if not shutil.which('pkexec'):
                raise ValueError('pkexec required for privileged service control')
            return call('pkexec', '/usr/local/libexec/smartproxy-ctl', 'start', str(CONFIG))
        if args.action in ('stop','restart'):
            return call('pkexec', '/usr/local/libexec/smartproxy-ctl', args.action)
        if args.action == 'status':
            return call('systemctl', 'is-active', SERVICE)
        if args.action == 'logs':
            return call('journalctl', '-u', SERVICE, '-n', '50', '--no-pager')
    except (OSError, ValueError) as exc:
        print('Error:', exc, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
