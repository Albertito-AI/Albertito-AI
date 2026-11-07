#!/usr/bin/env python3
"""Notify IndexNow of reviewed changes on the author's two owned publication routes.

Dry-run by default. A receipt establishes request delivery, never indexing/ranking.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ENDPOINT = 'https://api.indexnow.org/indexnow'
CONFIG = Path(__file__).resolve().parents[2] / 'config/ibol-indexnow.json'
SCOPES = {'www.alberttansinhon.com': '/', 'albertito-ai.github.io': '/Albertito-AI/'}


def validate(payload: dict) -> dict:
    host, key = payload.get('host'), payload.get('key')
    if host not in SCOPES or not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{32}', key):
        raise ValueError('Use a configured owned host and a 32-character hexadecimal proof key')
    prefix = SCOPES[host]
    expected_key = 'https://' + host + prefix + key + '.txt'
    if payload.get('keyLocation') != expected_key:
        raise ValueError('Proof file must be at the configured ownership boundary')
    urls = payload.get('urlList')
    if not isinstance(urls, list) or not 1 <= len(urls) <= 10 or len(set(urls)) != len(urls):
        raise ValueError('Submit one to ten unique reviewed URLs')
    for url in urls:
        p = urlsplit(url)
        if (p.scheme != 'https' or p.netloc != host or p.query or p.fragment
                or p.path not in {prefix + 'ibol/', prefix + 'ibol/slides.html', *[prefix + f'ibol/lessons/{n:02d}.html' for n in range(1, 9)]}):
            raise ValueError('Only the published book hub, lecture and eight seminar routes are authorised')
    return payload


def notify(payload: dict, submit: bool = False, opener=urlopen) -> dict:
    validate(payload)
    encoded = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    receipt = {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
               'endpoint': ENDPOINT, 'host': payload['host'], 'urls': payload['urlList'],
               'payload_sha256': hashlib.sha256(encoded).hexdigest(),
               'submitted': False, 'received': False,
               'meaning': 'No evidence of crawling, indexing, ranking or readership.'}
    if not submit:
        return {**receipt, 'state': 'dry_run'}
    try:
        with opener(Request(payload['keyLocation']), timeout=15) as response:
            if response.status != 200 or response.geturl() != payload['keyLocation']:
                raise ValueError('The public proof URL must return 200 without redirection')
            if response.read(1024).decode('utf-8') != payload['key']:
                raise ValueError('The public proof file does not contain the exact key')
    except (HTTPError, URLError, OSError, ValueError, UnicodeError) as error:
        return {**receipt, 'state': 'proof_unverified', 'error': str(error)}
    request = Request(ENDPOINT, data=encoded, headers={'Content-Type': 'application/json; charset=utf-8'}, method='POST')
    receipt['submitted'] = True
    try:
        with opener(request, timeout=20) as response:
            if response.geturl() != ENDPOINT:
                return {**receipt, 'state': 'delivery_unknown', 'error': 'Notification endpoint redirected; receipt not established'}
            status = response.status
            body = response.read(2000).decode('utf-8', 'replace')
    except HTTPError as error:
        status = error.code
        body = error.read(2000).decode('utf-8', 'replace')
    except (URLError, OSError) as error:
        return {**receipt, 'state': 'delivery_unknown', 'error': str(error)}
    state = {200: 'received', 202: 'received_key_validation_pending'}.get(status, 'not_accepted')
    return {**receipt, 'state': state, 'http_status': status, 'received': status in (200, 202), 'response_body': body}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['official', 'github'], required=True)
    parser.add_argument('--submit', action='store_true', help='Make one notification after verifying the live proof file')
    parser.add_argument('--receipt', type=Path, help='Write the dated receipt to this explicit destination')
    args = parser.parse_args()
    payload = json.loads(CONFIG.read_text())['targets'][args.target]
    result = notify(payload, submit=args.submit)
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(output)
    print(output, end='')
    return 0 if result['state'] in {'dry_run', 'received', 'received_key_validation_pending'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
