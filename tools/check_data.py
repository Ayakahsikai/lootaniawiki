#!/usr/bin/env python3
"""檢查 wiki/data 的資料，並產生 versions.json（給天賦模擬讀取）。
   GitHub Actions 部署前會執行；本機也可以執行：python tools/check_data.py
   有錯誤時結束碼為 1（停止部署）。"""
import json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wiki')
D = os.path.join(ROOT, 'data')
errs, warns = [], []
def rel(p): return os.path.relpath(p, os.path.join(ROOT, '..')).replace('\\', '/')
def load_js(path, var, required=True):
    if not os.path.exists(path):
        (errs if required else warns).append(f'找不到 {rel(path)}'); return None
    t = open(path, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', t)
    if not m: errs.append(f'{rel(path)}: 找不到 window.{var} =（檔案格式不對，請用編輯器重新存檔）'); return None
    try: return json.loads(t[m.end():].rstrip().rstrip(';'))
    except Exception as e: errs.append(f'{rel(path)}: 內容不是正確的 JSON（{e}）'); return None
def check_list(d, path, key, vdir):
    if d is None: return
    items = d.get(key)
    if not isinstance(items, list): errs.append(f'{rel(path)}: 找不到 {key} 陣列'); return
    ids = [x.get('id') for x in items]
    dup = sorted({str(i) for i in ids if ids.count(i) > 1})
    if dup: errs.append(f'{rel(path)}: 編號重複 {", ".join(dup)}')
    for x in items:
        if not x.get('name'): errs.append(f'{rel(path)}: {x.get("id")} 沒有名稱')
    sh = d.get('iconSheet')
    if sh:
        if not os.path.exists(os.path.join(vdir, sh.get('file', ''))): errs.append(f'{rel(path)}: 找不到圖示表 {rel(os.path.join(vdir, sh.get("file", "")))}')
        bad = [x['id'] for x in items if isinstance(x.get('icon'), int) and not (0 <= x['icon'] < sh.get('count', 0))]
        if bad: errs.append(f'{rel(path)}: 圖示編號超出圖示表範圍 {", ".join(bad)}')
    print(f'  {rel(path)}: {len(items)} 筆')

V = load_js(os.path.join(D, 'versions.js'), 'LOOTANIA_VERSIONS')
if V is not None:
    vs = V.get('versions') if isinstance(V.get('versions'), list) else []
    if not vs: errs.append('versions.js: versions 沒有任何版本')
    names = [v.get('version') for v in vs]; dirs = [v.get('dir') for v in vs]
    for k, arr in (('version', names), ('dir', dirs)):
        dup = sorted({str(x) for x in arr if arr.count(x) > 1})
        if dup: errs.append(f'versions.js: {k} 重複 {", ".join(dup)}')
    if vs and V.get('latest') not in names: errs.append(f'versions.js: latest「{V.get("latest")}」不在 versions 清單裡')
    for v in vs:
        name, d = v.get('version'), v.get('dir')
        if not name or not d: errs.append(f'versions.js: 每一筆都要有 version 和 dir（{v}）'); continue
        if not re.fullmatch(r'[\w.-]+', d): errs.append(f'versions.js: dir「{d}」只能用英數字、點、底線、減號'); continue
        vdir = os.path.join(D, d)
        print(f'版本 {name}（data/{d}/）')
        if not os.path.isdir(vdir): errs.append(f'找不到資料夾 {rel(vdir)}（versions.js 的 {name}）'); continue
        for js, var, key, jn in (('skills.js', 'LOOTANIA_SKILLS', 'skills', 'skills.json'), ('runes.js', 'LOOTANIA_RUNES', 'runes', 'runes.json')):
            p = os.path.join(vdir, js); data = load_js(p, var); check_list(data, p, key, vdir)
            if data is None: continue
            if data.get('gameVersion') and data['gameVersion'] != name:
                warns.append(f'{rel(p)}: 檔內 gameVersion「{data["gameVersion"]}」和 versions.js 的「{name}」不同（請確認放對資料夾）')
            pj = os.path.join(vdir, jn)
            if not os.path.exists(pj): warns.append(f'找不到 {rel(pj)}（網站可正常顯示，但天賦模擬讀不到這份資料）')
            else:
                try:
                    if json.load(open(pj, encoding='utf-8')) != data: errs.append(f'{rel(pj)} 和 {js} 內容不一致，請兩個檔案一起更新')
                except Exception as e: errs.append(f'{rel(pj)}: 無法讀取（{e}）')
h = load_js(os.path.join(D, 'home.js'), 'LOOTANIA_HOME', required=False)
if h is not None:
    for k in ('start', 'end'):
        if h.get(k) and not re.fullmatch(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?', h[k]): errs.append(f'home.js: {k} 格式應為 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM')
    if h.get('start') and h.get('end'):
        st = h['start'] if 'T' in h['start'] else h['start'] + 'T00:00'
        en = h['end'] if 'T' in h['end'] else h['end'] + 'T23:59'
        if en < st: errs.append('home.js: 結束時間早於開始時間')
gh = os.environ.get('GITHUB_ACTIONS') == 'true'
for w in warns: print(f'::warning::{w}' if gh else f'警告：{w}')
for e in errs: print(f'::error::{e}' if gh else f'錯誤：{e}')
if errs: sys.exit(1)
# 產生 versions.json（給天賦模擬：找同名版本，找不到用 latest）
out = sys.argv[1] if len(sys.argv) > 1 else None
if out and V is not None:
    os.makedirs(out, exist_ok=True)
    json.dump({'latest': V['latest'], 'versions': [{'version': v['version'], 'dir': v['dir'], **({'note': v['note']} if v.get('note') else {})} for v in V['versions']]},
              open(os.path.join(out, 'versions.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'已產生 {os.path.join(out, "versions.json")}')
print('檢查通過')
