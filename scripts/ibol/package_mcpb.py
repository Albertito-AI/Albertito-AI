#!/usr/bin/env python3
"""Build the deliberately scoped IBOL MCP bundle and registry metadata."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'mcp/ibol'
NAME = 'io.github.Albertito-AI/ibol-open-learning'
REPOSITORY = 'Albertito-AI/Albertito-AI'
SOURCES = {
    **{f'scripts/{name}': f'scripts/ibol/{name}' for name in ('catalog.py', 'cli.py', 'mcp_server.py', 'fetch_book.py', 'requirements.txt')},
    **{f'data/{name}.json': f'site/ibol/data/{name}.json' for name in ('book', 'lessons', 'quiz', 'cases', 'sorter')},
    **{name:f'site/ibol/{name}' for name in ('RIGHTS.md','LICENSE-CODE.txt')},
    **{name:f'mcp/ibol/{name}' for name in ('manifest.json','pyproject.toml','uv.lock','README.md')},
}


def source_digest(root: Path = ROOT) -> str:
    """Bind exact distribution inputs, including their names, without a self-hash."""
    records = [{'path': source, 'sha256': hashlib.sha256((root/source).read_bytes()).hexdigest()}
               for source in sorted([*SOURCES.values(), 'scripts/ibol/package_mcpb.py',
                    'scripts/ibol/publish_mcpb_release.py', 'scripts/ibol/check_registry.py',
                    '.github/workflows/ibol-registry.yml'])]
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_request(root: Path = ROOT) -> dict:
    request = json.loads((root/'mcp/ibol/release-request.json').read_text())
    manifest = json.loads((root/'mcp/ibol/manifest.json').read_text())
    version = request['version']
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Release version must be numeric major.minor.patch')
    if version != manifest['version']:
        raise ValueError('Release request and bundle versions differ')
    if request.get('source_sha256') != source_digest(root):
        raise ValueError('Release source digest differs from the reviewed request')
    if request.get('registry_name') != NAME:
        raise ValueError('Release namespace differs from the fixed owner namespace')
    return request


def build(output: Path, root: Path = ROOT) -> dict:
    request = validate_request(root)
    output.mkdir(parents=True, exist_ok=True)
    version = request['version']; tag = 'ibol-mcp-v' + version
    filename = 'ibol-open-learning-' + version + '.mcpb'
    artifact = output / filename
    with zipfile.ZipFile(artifact, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, source in sorted(SOURCES.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (root/source).read_bytes())
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    url = f'https://github.com/{REPOSITORY}/releases/download/{tag}/{filename}'
    server = {
        '$schema':'https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json',
        'name':NAME, 'title':'IBOL Open Learning: Albert Tan Sin Hon',
        'description':'Citation and teaching tools for Insurance-Backed Offshore Liquidity by Albert Tan Sin Hon.',
        'repository':{'url':f'https://github.com/{REPOSITORY}', 'source':'github', 'subfolder':'scripts/ibol'},
        'version':version, 'websiteUrl':'https://www.alberttansinhon.com/ibol/',
        'packages':[{'registryType':'mcpb','identifier':url,'fileSha256':digest,'transport':{'type':'stdio'}}],
    }
    (output/'server.json').write_text(json.dumps(server, indent=2)+'\n')
    receipt = {'version':version,'registry_name':NAME,'tag':tag,'filename':filename,
               'bundle_sha256':digest,'source_sha256':request['source_sha256'],
               'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()}
    (output/'build-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    (output/'SHA256SUMS').write_text(f'{digest}  {filename}\n')
    (output/'release-notes.md').write_text(
        f'IBOL Open Learning MCP bundle {version}\n\n'
        'Author-commissioned, AI-assisted companion to Insurance-Backed Offshore Liquidity '
        '(University of Groningen Press, DOI 10.21827/6ac3948159a9e). Six read-only tools provide '
        'citations, seminar guides and formative questions. Optional full-book search needs the '
        'separately installed verified publisher-PDF cache.\n\n'
        'MCPB 0.4 UV runtime required. Python dependencies are locked; the bundle omits the book PDF. '
        'Code: MIT. Original teaching data: CC BY 4.0. Book: CC BY-NC-ND 4.0. '
        'Legal cut-off: 1 August 2026. No universal host or adoption claim.\n\n'
        f'Source commit: {receipt["source_commit"]}\nSource-input SHA-256: {receipt["source_sha256"]}\n'
        f'Bundle SHA-256: {digest}\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
