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
    body = t[m.end():].rstrip().rstrip(';')
    try: return json.loads(body)
    except Exception: pass
    try: return json.loads(relax(body))   # 手動編輯的檔案（credits.js、home.js）：容許註解與最後一項後面的逗號
    except Exception as e:
        ln = body[:getattr(e, 'pos', 0) or 0].count('\n') + t[:m.end()].count('\n') + 1
        errs.append(f'{rel(path)}: 第 {ln} 行附近格式不對（{e}）。名字要用雙引號 " 包起來，項目之間用逗號分隔'); return None
def relax(s):
    """去掉字串以外的 // 、/* */ 註解，以及 ] 或 } 前面多出來的逗號（瀏覽器可以，JSON 不行）。"""
    out, i, n, q = [], 0, len(s), None
    while i < n:
        c = s[i]
        if q:
            out.append(c)
            if c == '\\' and i + 1 < n: out.append(s[i + 1]); i += 2; continue
            if c == q: q = None
            i += 1; continue
        if c in '"\'': q = c; out.append(c); i += 1; continue
        if s.startswith('//', i): j = s.find('\n', i); i = n if j < 0 else j; continue
        if s.startswith('/*', i): j = s.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        if c == ',':
            j = i + 1
            while j < n and s[j] in ' \t\r\n': j += 1
            if j < n and s[j] in ']}': i += 1; continue
        out.append(c); i += 1
    return ''.join(out)
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
# 裝備、通貨（選用）：以 json 為準，js 不存在或內容不同時自動產生
def check_items(vdir, name, outdir, base, var):
    pj = os.path.join(vdir, base + '.json')
    if not os.path.exists(pj): return
    try: d = json.load(open(pj, encoding='utf-8'))
    except Exception as e: errs.append(f'{rel(pj)}: 無法讀取（{e}）'); return
    items = d.get('items')
    if not isinstance(items, list): errs.append(f'{rel(pj)}: 找不到 items 陣列'); return
    ids = [x.get('id') for x in items]
    dup = sorted({str(i) for i in ids if ids.count(i) > 1})
    if dup: errs.append(f'{rel(pj)}: 編號重複 {", ".join(dup)}')
    for x in items:
        if not x.get('name'): errs.append(f'{rel(pj)}: {x.get("id")} 沒有名稱')
    if d.get('gameVersion') and d['gameVersion'] != name:
        warns.append(f'{rel(pj)}: 檔內 gameVersion「{d["gameVersion"]}」和 versions.js 的「{name}」不同（請確認放對資料夾）')
    sheet = (d.get('iconSheet') or {}).get('file') or base + '-icons.png'
    if any(isinstance(x.get('iconIndex'), int) for x in items) and not os.path.exists(os.path.join(vdir, sheet)):
        warns.append(f'找不到 {rel(os.path.join(vdir, sheet))}（圖示不會顯示）')
    js = f'/* 內容同 {base}.json（tools/check_data.py 自動產生），請勿手動修改 */\nwindow.{var} = ' + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ';\n'
    target = os.path.join(outdir, os.path.basename(vdir)) if outdir else vdir
    pjs = os.path.join(target, base + '.js')
    cur = open(pjs, encoding='utf-8').read() if os.path.exists(pjs) else None
    if cur != js:
        os.makedirs(target, exist_ok=True); open(pjs, 'w', encoding='utf-8').write(js); print(f'  已產生 {pjs}')
    print(f'  {rel(pj)}: {len(items)} 筆')
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else None
if V is not None:
    for v in V.get('versions') or []:
        if v.get('dir') and os.path.isdir(os.path.join(D, v['dir'])): 
            for base, var in (('equipment', 'LOOTANIA_EQUIPMENT'), ('currency', 'LOOTANIA_CURRENCY')): check_items(os.path.join(D, v['dir']), v.get('version'), OUT_DIR, base, var)
h = load_js(os.path.join(D, 'home.js'), 'LOOTANIA_HOME', required=False)
if h is not None:
    for k in ('start', 'end'):
        if h.get(k) and not re.fullmatch(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?', h[k]): errs.append(f'home.js: {k} 格式應為 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM')
    if h.get('start') and h.get('end'):
        st = h['start'] if 'T' in h['start'] else h['start'] + 'T00:00'
        en = h['end'] if 'T' in h['end'] else h['end'] + 'T23:59'
        if en < st: errs.append('home.js: 結束時間早於開始時間')
cr = load_js(os.path.join(D, 'credits.js'), 'LOOTANIA_CREDITS', required=False)   # 頁尾感謝名單（選用）
if cr is not None:
    gs = cr.get('groups')
    if gs is not None and not isinstance(gs, list): errs.append('credits.js: groups 應為陣列')
    for g in gs or []:
        if not isinstance(g, dict) or not isinstance(g.get('names', []), list): errs.append(f'credits.js: 分組格式不對（{g}）'); continue
        for n in g.get('names', []):
            if not (isinstance(n, str) or (isinstance(n, dict) and n.get('name'))): errs.append(f'credits.js: 「{g.get("label")}」裡有無法辨識的名字（{n}）')
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
