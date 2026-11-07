#!/usr/bin/env python3
"""Read back the exact IBOL Registry version. Exit 2 only when absent (HTTP 404)."""
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen


def check(path):
    expected=json.loads(path.read_text())
    url='https://registry.modelcontextprotocol.io/v0.1/servers/'+quote(expected['name'],safe='')+'/versions/'+quote(expected['version'],safe='')
    try:
        with urlopen(url,timeout=30) as response: actual=json.load(response)
    except HTTPError as error:
        if error.code==404:return 2
        raise
    server=actual.get('server',actual)
    for field in ('name','version'):
        if server.get(field)!=expected[field]:raise ValueError('Registry '+field+' differs from tested release')
    packages=server.get('packages',[])
    if len(packages)!=1 or any(packages[0].get(key)!=value for key,value in expected['packages'][0].items()):
        raise ValueError('Registry packages differs from tested release')
    print(json.dumps({'url':url,'name':server['name'],'version':server['version'],'packages':server['packages']},indent=2))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('server',type=Path)
    raise SystemExit(check(parser.parse_args().server))
