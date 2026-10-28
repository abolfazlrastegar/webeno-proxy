"""Source management. Store only user-chosen subscriptions; default website is a reference."""
import json
from pathlib import Path
from .core import parse_subscription, read_source, make_config

DEFAULT_PAGE = 'https://yamyamproxyy.github.io/Yamyamproxy/'

def load(path):
    path = Path(path)
    if not path.exists():
        return {'default_page': DEFAULT_PAGE, 'sources':[], 'manual':[], 'priority':'personal'}
    return json.loads(path.read_text(encoding='utf8'))

def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf8')
    path.chmod(0o600)

def add_source(data, source):
    if not source.startswith('https://'):
        raise ValueError('Subscription must use HTTPS')
    if source not in data['sources']:
        data['sources'].append(source)

def add_manual(data, uri):
    from .core import parse_uri
    parse_uri(uri)
    if uri not in data['manual']:
        data['manual'].append(uri)

def collect(data, fetch=read_source):
    combined = []
    problems = []
    personal = list(data.get('manual',[]))
    remote = []
    for src in data.get('sources',[]):
        try:
            remote.extend([node for node in parse_subscription(fetch(src))])
        except Exception as ex:
            problems.append(f'{src}: {type(ex).__name__}: {ex}')
    from .core import parse_uri
    manual_nodes = []
    for uri in personal:
        try:
            manual_nodes.append(parse_uri(uri))
        except Exception as ex:
            problems.append(f'manual: {type(ex).__name__}: {ex}')
    ordered = (manual_nodes+remote if data.get('priority')=='personal' else remote+manual_nodes)
    seen = set()
    for node in ordered:
        fingerprint = json.dumps({k:v for k,v in node.items() if k!='tag'}, sort_keys=True)
        if fingerprint in seen: continue
        seen.add(fingerprint)
        node = dict(node)
        node['tag'] = f'node-{len(combined)+1}'
        combined.append(node)
    return combined, problems
