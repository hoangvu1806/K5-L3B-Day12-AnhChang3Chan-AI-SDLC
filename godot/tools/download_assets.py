#!/usr/bin/env python3
"""Download GLB files FROM their original publishers, directly to your local Godot project.
Does not redistribute restricted third-party raw assets in this archive.
Run: python3 tools/download_assets.py --all
     python3 tools/download_assets.py --cc0
"""
from pathlib import Path
import argparse, json, os, re, sys, tempfile
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

HERE = Path(__file__).resolve().parent.parent
ITEMS = json.loads((HERE/'tools/assets.json').read_text(encoding='utf-8'))['items']

def fetch(url):
    req = Request(url, headers={'User-Agent':'Mozilla/5.0 (asset downloader for local Godot learning project)','Accept':'*/*'})
    with urlopen(req, timeout=35) as r: return r.read()

def resolve(item):
    if item.get('url'): return item['url']
    html = fetch(item['page']).decode('utf-8', 'replace')
    html = html.replace('\\/','/')
    m = re.search(r'https://assets\.stoicsoft\.com/1designtool/3d/models/[^"\s<>]+?/model\.glb',html)
    if not m: raise ValueError('Không thấy link GLB trên trang nhà phát hành; tải thủ công: '+item['page'])
    return m.group(0)

def run():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group()
    g.add_argument('--all', action='store_true', help='CC0 + các file 1DesignTool được phép dùng trong game')
    g.add_argument('--cc0', action='store_true', help='Chỉ tải model CC0')
    a = p.parse_args()
    wanted = [x for x in ITEMS if a.all or x['license']=='CC0']
    done, errors = [],[]
    for item in wanted:
        output = HERE/'assets/external'/item['family']/(item['id']+'.glb')
        output.parent.mkdir(parents=True,exist_ok=True)
        if output.exists() and output.stat().st_size > 128:
            print('SKIP', output.relative_to(HERE)); done.append(item['id']); continue
        try:
            url = resolve(item)
            blob = fetch(url)
            if len(blob)<12 or blob[:4]!=b'glTF':
                raise ValueError('Phản hồi không phải GLB hợp lệ')
            tmp = output.with_suffix('.part')
            tmp.write_bytes(blob); os.replace(tmp, output)
            print('OK  ',item['id'],len(blob)//1024,'KB'); done.append(item['id'])
        except Exception as e:
            print('FAIL',item['id'],str(e),file=sys.stderr)
            errors.append((item['id'],str(e)))
    print(f'Đã tải được {len(done)}/{len(wanted)} asset; lỗi {len(errors)}')
    if errors:
        print('Bạn có thể tải thủ công theo docs/SOURCES.md và đặt tên file ở assets/external/<family>/<id>.glb')
    return 1 if errors else 0

if __name__=='__main__': sys.exit(run())
