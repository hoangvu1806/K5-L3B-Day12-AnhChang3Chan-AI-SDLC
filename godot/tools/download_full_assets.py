#!/usr/bin/env python3
"""Tải asset game 3D Tây Nam Bộ cho máy người dùng, trực tiếp từ nhà phát hành.

python3 tools/download_full_assets.py --all
python3 tools/download_full_assets.py --core
python3 tools/download_full_assets.py --list

Không phân phối lại model của River Delta. Script hợp lệ chỉ lấy cho project local.
Dựa trên file API của 3dassets.dev (không đoán đường dẫn CDN).
"""
import argparse, io, json, os, re, sys, time, zipfile
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent.parent
GLB_MAGIC=b'glTF'
SOURCES=BASE/'tools'/'sources.json'


def get(url, attempts=2):
    exc=None
    for i in range(attempts):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (Godot Asset Kit; educational project)','Accept':'application/json,application/octet-stream,*/*'}),timeout=45) as f:
                return f.read()
        except Exception as e:
            exc=e
            if i+1<attempts: time.sleep(1)
    raise exc

def save_glb(url, path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size>=32:
        with path.open('rb') as f:
            if f.read(4)==GLB_MAGIC:
                return 'cached'
    blob=get(url)
    if len(blob)<20 or blob[:4]!=GLB_MAGIC:
        raise RuntimeError('Nội dung tải không phải GLB: '+url)
    part=path.with_suffix('.part')
    part.write_bytes(blob)
    os.replace(part,path)
    return str(len(blob))

def slug(s):
    return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')[:95]

def download_pack(slug_name):
    api='https://3dassets.dev/api/v1/packs/'+slug_name
    obj=json.loads(get(api))
    data=obj.get('data',obj)
    assets=data.get('assets',[])
    if not assets:
        raise RuntimeError('Pack không có assets: '+slug_name)
    folder=BASE/'assets'/'downloaded_packs'/slug_name
    folder.mkdir(parents=True,exist_ok=True)
    index=[]; errors=[]
    for n,a in enumerate(assets):
        url=a.get('cdnUrl') or a.get('modelUrl')
        if not url:
            errors.append(str(a.get('title',n))+' no url'); continue
        file_id=str(a.get('id',n))
        fn=slug(str(a.get('title') or a.get('slug') or file_id))+'_'+file_id+'.glb'
        try:
            state=save_glb(url,folder/fn)
            index.append({'id':file_id,'title':a.get('title',''), 'file':fn,'source':a.get('url',''),'cdnUrl':url})
        except Exception as e:
            errors.append(fn+': '+str(e))
    starter=data.get('starterScene') or {}
    if starter.get('cdnUrl'):
        try: save_glb(starter['cdnUrl'],folder/'starter_scene.glb')
        except Exception as e: errors.append('starter: '+str(e))
    (folder/'index.json').write_text(json.dumps({'source':api,'license':'CC0 1.0','assets':index,'errors':errors},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Map names to the canonical names used by the 3D showcase, without guessing CDN ids.
    aliases={
        'tropical-island-ecology':{
            'coconut_tall':'tall coconut palm',
            'coconut_lean':'leaning coconut palm',
            'nipa_palm':'nipa palm',
            'banana_clump':'banana',
            'mangrove_small':'small red mangrove',
            'mangrove_large':'large red mangrove',
            'taro':'taro',
        },
        'swamp-and-mangrove':{
            'mangrove_red':'mangrove',
        }
    }
    from shutil import copyfile
    family='tropical' if slug_name=='tropical-island-ecology' else 'swamp' if slug_name=='swamp-and-mangrove' else 'quiet_lake'
    for alias,search_title in aliases.get(slug_name,{}).items():
        found=next((row for row in index if search_title in row['title'].lower()),None)
        if not found:
            print(f'  Cảnh báo: không thấy model {search_title} trong pack');continue
        target=BASE/'assets'/'external'/('tropical' if family=='tropical' else 'swamp')/(alias+'.glb')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():copyfile(folder/found['file'],target)
    print(f'[3DAssets] {slug_name}: {len(index)}/{len(assets)} GLBs, {len(errors)} lỗi')
    return len(errors)

def download_github_zip(repo, folder):
    url='https://codeload.github.com/KayKit-Game-Assets/'+repo+'/zip/refs/heads/main'
    raw=get(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        extracted=0
        for entry in z.infolist():
            if entry.is_dir(): continue
            parts=Path(entry.filename).parts
            if len(parts)<2: continue
            relative=Path(*parts[1:])
            if '..' in relative.parts or relative.is_absolute(): continue
            if entry.file_size>70_000_000: continue
            target=BASE/'assets'/'downloaded_packs'/folder/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():
                target.write_bytes(z.read(entry))
            extracted+=1
    print(f'[KayKit] {repo}: {extracted} file (đã giữ nguyên texture và thư mục gốc)')
    return 0

def download_gobkit():
    obj=json.loads(get('https://gobkit.com/api/free'))
    urls=obj.get('glbs',[])
    targets=('officelady','grandmashopper','cashier','foodcourier','stockclerk','storemanager','schoolkid')
    found=[]
    for token in targets:
        match=next((u for u in urls if slug(u.rsplit('/',1)[-1].rsplit('.',1)[0]).replace('_','')==token),None)
        if match: found.append(match)
    # safe fallback if the exact repo filenames changed
    if not found:
        found=[u for u in urls if re.search(r'(office|grandma|cashier|courier|school)',u,re.I)][:6]
    if not found:
        print('[Gobkit] Không tìm thấy NPC phù hợp trong manifest; xem https://gobkit.com/freebies')
        return 1
    errs=0
    for u in found:
        try: save_glb(u,BASE/'assets'/'downloaded_packs'/'gobkit_characters'/u.rsplit('/',1)[-1])
        except Exception as e:
            print('[Gobkit] FAIL',u,e); errs+=1
    print(f'[Gobkit] {len(found)-errs}/{len(found)} characters')
    return errs

def download_river():
    # URLs từ trang tác giả hoặc từ file assets.json cũ; KHÔNG đưa vào zip phát tán
    raw=json.loads((BASE/'tools'/'assets.json').read_text(encoding='utf8'))
    items=[a for a in raw['items'] if a.get('family')=='river_delta']
    ok=0; err=0
    for item in items:
        path=BASE/'assets'/'external'/'river_delta'/(item['id']+'.glb')
        try:
            url=item.get('url')
            if item.get('page'):
                html=get(item['page']).decode('utf-8','replace').replace('\\/','/')
                m=re.search(r'https://assets\.stoicsoft\.com/1designtool/3d/models/[^"\s<>]+?/model\.glb',html)
                if m: url=m.group(0)
            if not url: raise RuntimeError('Cần tải thủ công qua '+str(item.get('page')))
            save_glb(url,path); ok+=1
        except Exception as e:
            print('[River Delta] FAIL',item['id'],e);err+=1
    print(f'[River Delta] {ok}/{len(items)} GLB; không nằm trong zip gốc')
    return err

def main():
    ap=argparse.ArgumentParser(description='Cài bộ asset Quán Ăn Chợ Nổi: dùng internet của máy bạn')
    group=ap.add_mutually_exclusive_group(required=True)
    for mode in ['all','core','river-delta','list']:
        group.add_argument('--'+mode,action='store_true')
    args=ap.parse_args()
    if args.list:
        for category,rows in json.loads(SOURCES.read_text(encoding='utf8')).items():
            print('\n'+category)
            for r in rows:print('•',r[0],r[1])
        return 0
    fails=0
    if args.all or args.core:
        for pack in ['tropical-island-ecology','swamp-and-mangrove','quiet-lake-fishing']:
            try: fails+=download_pack(pack)
            except Exception as e:print('FAIL pack',pack,e);fails+=1
        for repo,folder in [('KayKit-Restaurant-Bits-1.0','kaykit_restaurant'),('KayKit-Furniture-Bits-1.0','kaykit_furniture')]:
            try: fails+=download_github_zip(repo,folder)
            except Exception as e:print('FAIL repo',repo,e);fails+=1
        try: fails+=download_gobkit()
        except Exception as e:print('FAIL Gobkit',e);fails+=1
        # relative .glb files required by the existing perspective 3D scene
        manifest=json.loads((BASE/'tools'/'assets.json').read_text(encoding='utf8'))['items']
        for a in manifest:
            if a['license']!='CC0': continue
            path=BASE/'assets'/'external'/a['family']/(a['id']+'.glb')
            try:
                if not a.get('url'): continue
                save_glb(a['url'],path)
            except Exception as e:
                print('FAIL core glb',a['id'],e);fails+=1
    if args.all or args.river_delta:
        fails+=download_river()
    print('\nKết quả: ', 'TẢI XONG' if fails==0 else f'Có {fails} lỗi mạng / link. Mở docs/SOURCES_FULL.md để tải thủ công.')
    return 0 if fails==0 else 1

if __name__=='__main__':sys.exit(main())
