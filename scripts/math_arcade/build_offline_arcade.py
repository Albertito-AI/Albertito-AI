#!/usr/bin/env python3
"""Build Maths_Arcade_Offline.zip with Python 3.10+, using only the standard library.

From this profile repository, with atlas-open-mathematics cloned alongside it, run:
  python3 scripts/math_arcade/build_offline_arcade.py --fetch-public --math-repo ../atlas-open-mathematics --output Maths_Arcade_Offline.zip

With a local site checkout, pass --arcade-dir /path/to/dist/math-arcade instead.
--math-repo defaults to the working directory and supplies LICENSE and LICENSE-CONTENT.md.
Copy unmodified PDFs into the site's teaching/ directory when building a local edition.
Rebuilding with the same bytes and Python/zlib versions produces the same archive.
Source hashes are recorded in SOURCE-SHA256.txt in each release.
"""
import argparse
import base64
import hashlib
import html
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import zipfile

SITE = 'https://alberttansinhon.com/math-arcade/'
REPOSITORY = 'https://github.com/Albertito-AI/atlas-open-mathematics'
GUIDE = 'Maths_Arcade_Teaching_Guide.pdf'
SHEETS = 'Maths_Arcade_Player_Sheets.pdf'
GAMES = (
    ('Sudoku', 'sudoku', '0/0', '1/8'),
    ('Lattice Dash', 'lattice', '0/2', '1/55'),
    ('Target Forge', 'forge', '0/2', '2/1'),
    ('Parity Lights', 'parity', '0/7', '0/4'),
    ('Nim Lab', 'nim', '0/7', '1/2'),
    ('Reversi Endgame Lab', 'reversi', '0/7', '0/14'),
)
README = """ATLAS MATHS ARCADE | OFFLINE
Albert Tan Sin Hon and Atlas Open Mathematics

English
1. Extract the whole ZIP into one folder. Double-click Maths_Arcade.html and open it in a current desktop browser with JavaScript enabled. There is no installation or server to start.
2. Play a solo game, play a match against the local computer opponent, try the daily challenge, or choose a fixed opening under “Practise with the player sheets”. All six games run locally. Teaching guide and player sheets open the two PDF files in this folder. The game interface and PDFs are in English.
3. On phones or managed devices that cannot open local HTML games, use the two PDFs directly. The printed QR codes and online puzzle links need internet access. For the same task offline, choose its opening or transfer link in the HTML.
4. Daily challenges use the device clock and the Singapore calendar date. Browser privacy settings and moving the file can affect saved progress. If storage is unavailable the current visit remains playable. The international website and research papers are optional online references.

简体中文
1. 将整个 ZIP 压缩包解压到同一个文件夹。在电脑上双击 Maths_Arcade.html，用已启用 JavaScript 的新版浏览器打开。无需安装，也无需启动服务器。
2. 选择单人游戏、与本机电脑对战、每日挑战或“Practise with the player sheets”中的指定题目。全部游戏均可离线运行。教学指南和练习单是同一文件夹中的两份 PDF。游戏界面和 PDF 使用英语。
3. 若手机或受管理的设备无法打开本地 HTML 游戏，可直接打开两份 PDF。纸上的二维码和在线题目链接需要联网。离线时，请在 HTML 内选择对应的起始题（Opening）或迁移题（Transfer）。
4. 每日挑战按设备时钟和新加坡日期更新。浏览器的隐私设置或文件位置变动可能影响进度保存。无法保存时，仍可在本次打开期间继续游戏。

繁體中文
1. 將整個 ZIP 壓縮檔解壓縮到同一個資料夾。在電腦上按兩下 Maths_Arcade.html，以已啟用 JavaScript 的新版瀏覽器開啟。毋須安裝，亦毋須啟動伺服器。
2. 選擇單人遊戲、與本機電腦對戰、每日挑戰，或「Practise with the player sheets」內的指定題目。全部遊戲均可離線運作。教學指南和練習紙是同一個資料夾內的兩份 PDF。遊戲介面和 PDF 使用英文。
3. 如手機或受管理的裝置無法開啟本機 HTML 遊戲，可直接開啟兩份 PDF。紙上的二維碼和網上題目連結需要連線。離線時，請在 HTML 內選擇對應的起始題（Opening）或遷移題（Transfer）。
4. 每日挑戰按裝置時間及新加坡日期更新。瀏覽器的私隱設定或檔案位置改變可能影響進度儲存。無法儲存時，仍可在本次開啟期間繼續遊戲。

Online source and attribution
Project: Atlas Open Mathematics, directed by Albert Tan Sin Hon.
Teaching and play: https://alberttansinhon.com/math-arcade/teaching/
Source and research: https://github.com/Albertito-AI/atlas-open-mathematics
The downloadable code carries the MIT licence. See LICENSE-CODE.txt.
Original educational prose and diagrams use CC BY 4.0. See LICENSE-CONTENT.txt.
The bundled Bricolage Grotesque font carries the SIL Open Font License. See LICENSE-FONT.txt.
This offline adaptation embeds the game assets, provides local teaching links and keeps shared puzzle links pointed at the public site. The two PDFs are unmodified.
"""

class Sources:
    def __init__(self, root, remote):
        self.root = root
        self.remote = remote
        self.hashes = {}

    def get(self, name):
        if '://' in name or '..' in Path(name).parts or name.startswith('/'):
            raise ValueError(f'Expected a site-relative asset: {name}')
        src = self.root / name
        if self.remote and not src.exists():
            url = SITE + ('' if name == 'index.html' else name)
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Atlas Open Mathematics offline edition builder)'})
            with urlopen(req, timeout=30) as response:
                data = response.read()
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_bytes(data)
        data = src.read_bytes()
        self.hashes[name] = hashlib.sha256(data).hexdigest()
        return data

def as_data(mime, content):
    return 'data:' + mime + ';base64,' + base64.b64encode(content).decode('ascii')

def change_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Expected one source match: {old[:80]}')
    return text.replace(old, new, 1)

def build(src, repo, output):
    text = src.get('index.html').decode()
    modules = {}
    computing = set()
    def module(name):
        if name in modules:
            return modules[name]
        if name in computing:
            raise ValueError(f'Cyclic import: {name}. Use a full module bundler for this edition.')
        computing.add(name)
        code = src.get(name).decode()
        if name == 'arcade.mjs' and 'new URL(location.href)' in code:
            code = change_once(code, 'new URL(location.href)', "new URL('" + SITE + "')")
        # Preserve ES module scopes and the original lazy imports. Repeated references
        # use the identical data URL, so the browser creates one instance per module.
        def dep(m):
            return m[1] + m[2] + module(m[3]) + m[2]
        spec = r"""(\bfrom\s+|\bimport\s*\(\s*)(['"])\./([\w-]+\.mjs)(?:\?[^'"]*)?\2"""
        code = re.sub(spec, dep, code)
        if re.search(r"""\b(?:import\s+(?:[^;]*?)from\s+|import\(\s*)['"](?!data:)""", code):
            raise ValueError(f'Unbundled import in {name}')
        computing.remove(name)
        modules[name] = as_data('text/javascript', code.encode())
        return modules[name]

    def style(match):
        name = urlsplit(match[1]).path
        css = src.get(name).decode()
        def asset(m):
            name = m[2]
            if not name.endswith('.woff2'):
                raise ValueError(f'Unexpected CSS asset: {name}')
            return 'url("' + as_data('font/woff2', src.get(name)) + '")'
        css = re.sub(r"""url\((['"]?)([^()'"]+)\1\)""", asset, css)
        return '<style>\n' + css + '\n</style>'
    text = re.sub(r'<link rel="stylesheet" href="([^"]+)">', style, text)
    text = re.sub(r'<link rel="(?:canonical|alternate|icon)"[^>]+>', '', text)
    text = re.sub(r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>', '', text)
    text = re.sub(r'<script type="application/ld\+json">.*?</script>', '', text, flags=re.S)
    text = re.sub(r'src="(art/[\w-]+\.webp)"', lambda m: 'src="'+as_data('image/webp',src.get(m[1]))+'"', text)
    text = re.sub(r'<script type="module" src="arcade\.mjs(?:\?[^"]*)?"></script>',
                  lambda _: '<script type="module" src="'+module('arcade.mjs')+'"></script>', text, count=1)
    if 'arcade.mjs' not in modules or not all(slug+'.mjs' in modules for _,slug,_,_ in GAMES):
        raise ValueError('One or more of the six games was absent from the built modules')
    if 'id="match-room"' in text:
        expected = {'match-room.mjs', *(f'match-{slug}.mjs' for _, slug, _, _ in GAMES)}
        if missing := expected.difference(modules):
            raise ValueError('Missing match modules: ' + ', '.join(sorted(missing)))
        text = change_once(text, 'href="teaching/">Teaching guide</a>',
                           'href="' + GUIDE + '">Teaching guide (PDF)</a>')
    text = text.replace('href="/"', 'href="https://alberttansinhon.com/"')
    text = change_once(text, '>Copy puzzle link</button>', '>Copy online puzzle link</button>')
    text = change_once(text, '<title>Maths Arcade |', '<title>Offline Maths Arcade |')
    links = '<a href="'+GUIDE+'">Teaching guide (PDF)</a> · <a href="'+SHEETS+'">Player sheets (PDF)</a>'
    rows = ''.join('<li><strong>'+title+'</strong> · <a href="#play/'+slug+'/'+op+'">Opening</a> · <a href="#play/'+slug+'/'+tr+'">Transfer</a></li>' for title,slug,op,tr in GAMES)
    panel = '<section class="offline-teaching" aria-labelledby="offline-teaching-title"><h2 id="offline-teaching-title">Practise with the player sheets</h2><p>'+links+'</p><p>Open the same boards as the printed sheets. These links work offline.</p><ul>'+rows+'</ul></section>'
    text, n = re.subn(r'<section class="boardroom-feature".*?</section>\s*<p class="notes-link">.*?</p>', lambda _: panel, text, count=1,flags=re.S)
    if n!=1:
        raise ValueError('Could not place the offline resources in the library')
    text,n=re.subn(r'<p class="notes-link"><a href="teaching/">Teach this game.*?</p>',lambda _:'<p class="notes-link">'+links+'</p>',text,count=1,flags=re.S)
    if n!=1:
        raise ValueError('Missing teaching links in game routes')
    text = text.replace('<head>', '<head>\n<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src data:; style-src \'unsafe-inline\'; img-src data:; font-src data:; connect-src \'none\'; base-uri \'none\'; form-action \'none\'">', 1)
    extra = '<style>.offline-teaching{margin:2.5rem 0;padding:clamp(1rem,4vw,2.2rem);border:1px solid var(--line);border-radius:1rem;background:var(--panel)}.offline-teaching h2{font-size:clamp(1.5rem,4vw,2.3rem)}.offline-teaching a,.notes-link a{color:var(--mint);text-decoration:underline}.offline-teaching ul{padding-left:1.3rem}.offline-teaching li{margin:.65rem 0}</style>'
    text = change_once(text, '</head>', extra+'\n</head>')
    data = {'Maths_Arcade.html':text.encode(), GUIDE:src.get('teaching/'+GUIDE), SHEETS:src.get('teaching/'+SHEETS),
            'README.txt':README.encode(),'LICENSE-FONT.txt':src.get('fonts/OFL.txt')}
    for fn in (GUIDE,SHEETS):
        if not data[fn].startswith(b'%PDF-'):
            raise ValueError(f'{fn} is not a PDF')
    for name,target in (('LICENSE','LICENSE-CODE.txt'),('LICENSE-CONTENT.md','LICENSE-CONTENT.txt')):
        data[target]=(repo/name).read_bytes()
        src.hashes['atlas-open-mathematics/'+name]=hashlib.sha256(data[target]).hexdigest()
    data['SOURCE-SHA256.txt']=''.join(f'{digest}  {name}\n' for name,digest in sorted(src.hashes.items())).encode()
    with zipfile.ZipFile(output, 'w') as target:
        for name,content in data.items():
            entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
            entry.create_system=3
            entry.external_attr=0o100644 << 16
            target.writestr(entry,content,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--arcade-dir', type=Path)
    source.add_argument('--fetch-public',action='store_true')
    parser.add_argument('--math-repo',type=Path,default=Path.cwd())
    parser.add_argument('--output',type=Path,default=Path('Maths_Arcade_Offline.zip'))
    args=parser.parse_args()
    with TemporaryDirectory() as work:
        build(Sources(args.arcade_dir or Path(work),args.fetch_public),args.math_repo,args.output)
    print(f'{args.output}: {args.output.stat().st_size:,} bytes; SHA-256 {hashlib.sha256(args.output.read_bytes()).hexdigest()}')
if __name__=='__main__':
    main()
