"""Subscription parsing and sing-box configuration generation (no privileged side effects)."""
import base64
import json
import re
from urllib.parse import urlsplit, parse_qs, unquote
from urllib.request import Request, urlopen

SCHEMES = ('vless://', 'trojan://', 'ss://', 'vmess://')

def decode_b64(value):
    return base64.urlsafe_b64decode(value.strip() + '=' * (-len(value.strip()) % 4)).decode('utf-8')

def extract_lines(payload):
    text = payload.strip()
    if not any(s in text for s in SCHEMES):
        try:
            text = decode_b64(text)
        except (ValueError, UnicodeError, Exception):
            return []
    return list(dict.fromkeys(re.findall(r'(?:vless|trojan|ss|vmess)://[^\s<>"\']+', text)))

def read_source(source, timeout=12):
    if source.startswith('https://'):
        req = Request(source, headers={'User-Agent': 'SmartProxyLinux/0.1'})
        with urlopen(req, timeout=timeout) as response:
            if int(response.headers.get('Content-Length', '0')) > 2_000_000:
                raise ValueError('Subscription too large')
            return response.read(2_000_001).decode('utf-8', errors='replace')
    if source.startswith(('http://', 'file://')):
        raise ValueError('Use HTTPS subscriptions or a local text file')
    with open(source, encoding='utf-8') as fp:
        return fp.read(2_000_001)

def parse_uri(uri):
    p = urlsplit(uri)
    q = {k: v[-1] for k, v in parse_qs(p.query).items()}
    tag = unquote(p.fragment)[:80] or p.hostname or 'server'
    if p.scheme == 'vmess':
        data = json.loads(decode_b64(uri.split('://', 1)[1]))
        out = {'type': 'vmess', 'server': data['add'], 'server_port': int(data['port']),
               'uuid': data['id'], 'security': data.get('scy') or 'auto', 'alter_id': int(data.get('aid') or 0)}
        if data.get('tls') == 'tls':
            out['tls'] = {'enabled': True, 'server_name': data.get('sni') or data['add']}
        if data.get('net') == 'ws':
            out['transport'] = {'type': 'ws', 'path': data.get('path') or '/', 'headers': {'Host': data.get('host') or data['add']}}
        tag = data.get('ps') or tag
    elif p.scheme in ('vless', 'trojan'):
        if not p.hostname or not p.port or not p.username:
            raise ValueError('Incomplete server URI')
        out = {'type': p.scheme, 'server': p.hostname, 'server_port': p.port}
        out['uuid' if p.scheme == 'vless' else 'password'] = unquote(p.username)
        if p.scheme == 'vless' and q.get('flow'):
            out['flow'] = q['flow']
        if q.get('security') in ('tls', 'reality') or p.scheme == 'trojan':
            tls = {'enabled': True, 'server_name': q.get('sni') or p.hostname}
            if q.get('security') == 'reality':
                if not q.get('pbk'):
                    raise ValueError('Missing Reality public key')
                tls['reality'] = {'enabled': True, 'public_key': q['pbk'], 'short_id': q.get('sid', '')}
            if q.get('fp'):
                tls['utls'] = {'enabled': True, 'fingerprint': q['fp']}
            out['tls'] = tls
        typ = q.get('type')
        if typ == 'ws':
            tr = {'type': 'ws', 'path': q.get('path', '/')}
            if q.get('host'):
                tr['headers'] = {'Host': q['host']}
            out['transport'] = tr
        elif typ == 'grpc':
            out['transport'] = {'type': 'grpc', 'service_name': q.get('serviceName', '')}
        elif typ not in (None, 'tcp'):
            raise ValueError('Unsupported transport: ' + str(typ))
    elif p.scheme == 'ss':
        auth = uri.split('://', 1)[1].split('#')[0].split('?')[0]
        if '@' not in auth:
            auth = decode_b64(auth)
        else:
            user, host = auth.rsplit('@', 1)
            if ':' not in user:
                user = decode_b64(user)
            auth = user + '@' + host
        cred, host = auth.rsplit('@', 1)
        method, password = cred.split(':', 1)
        h = urlsplit('ss://x@' + host)
        out = {'type': 'shadowsocks', 'server': h.hostname, 'server_port': h.port,
               'method': unquote(method), 'password': unquote(password)}
    else:
        raise ValueError('Unsupported scheme')
    if not out.get('server') or not 1 <= int(out.get('server_port') or 0) <= 65535:
        raise ValueError('Invalid server')
    out['tag'] = re.sub(r'[^a-zA-Z0-9_.-]', '_', tag)[:35]
    return out

def parse_subscription(payload):
    result, seen = [], set()
    for uri in extract_lines(payload):
        try:
            item = parse_uri(uri)
            fingerprint = json.dumps({k:v for k,v in item.items() if k!='tag'}, sort_keys=True)
            if fingerprint not in seen:
                seen.add(fingerprint)
                item['tag'] = f'node-{len(result)+1}'
                result.append(item)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return result

def make_config(nodes, mode='tun'):
    if not nodes:
        raise ValueError('No supported configurations were imported')
    if mode not in ('tun', 'proxy'):
        raise ValueError('Invalid mode')
    inbounds = [{'type':'mixed', 'tag':'mixed-in', 'listen':'127.0.0.1', 'listen_port':7890}]
    if mode == 'tun':
        inbounds.insert(0, {'type':'tun', 'tag':'tun-in', 'interface_name':'smartproxy0',
                            'address':['172.19.0.1/30'], 'auto_route':True, 'auto_redirect':True})
    rules = [{'ip_is_private':True,'action':'route','outbound':'direct'},
             {'domain_suffix':['.ir'],'action':'route','outbound':'direct'}]
    rule_sets = [
        {'type':'remote','tag':tag,'format':'binary',
         'url':f'https://raw.githubusercontent.com/Chocolate4U/Iran-sing-box-rules/rule-set/{tag}.srs',
         'download_detour':'direct', 'update_interval':'1d'}
        for tag in ('geosite-ir','geoip-ir')]
    rules.append({'rule_set':['geosite-ir','geoip-ir'],'action':'route','outbound':'direct'})
    return {'log':{'level':'warn'}, 'dns':{'servers':[{'type':'https','tag':'remote-dns','server':'1.1.1.1'},
                {'type':'local','tag':'local-dns'}],
                'rules':[{'domain_suffix':['.ir'],'action':'route','server':'local-dns'},
                         {'rule_set':['geosite-ir'],'action':'route','server':'local-dns'}],
                'final':'remote-dns'},
            'inbounds':inbounds,
            'outbounds':nodes + [{'type':'direct','tag':'direct'},
             {'type':'urltest','tag':'auto','outbounds':[x['tag'] for x in nodes], 'url':'https://www.gstatic.com/generate_204', 'interval':'3m', 'tolerance':100}],
            'route':{'auto_detect_interface':True, 'rules':rules, 'rule_set':rule_sets, 'final':'auto'}, 'experimental':{'cache_file':{'enabled':True}}}
