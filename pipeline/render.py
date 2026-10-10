#!/usr/bin/env python3
"""JLN Capital daily statement renderer.

Usage: python3 pipeline/render.py REPORT.txt [--allow-test] [--no-feed]

REPORT.txt = body text of the JLN-DAILY e-mail(s), all parts concatenated in order.
Writes daily/YYYY-MM-DD/*.jpg, updates pipeline/history.json and feed.xml.
Exit codes: 0 ok / no trades, 2 validation failed (nothing written), 3 test report refused.
"""
import sys, os, re, json, math, datetime as dt, email.utils, calendar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPE = os.path.join(ROOT, 'pipeline')
sys.path.insert(0, PIPE)
from zerk import building as _building

BASE = 'https://jln-capital.github.io/jln-capital-media'
BG = '#EFEBDD'; FG = '#141414'; MU = '#6F6B62'; LN = '#CFC9BA'; CG = '#A39E90'; GR = '#2F6B4F'; RD = '#9B2C3A'
MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
TFS = {'M1': 60, 'M5': 300, 'M15': 900}
MAX_CANDLES = 100
MARGIN = 5
B = "font-family:'Bodoni Moda'"; L = "font-family:Lab"
FF = ''.join(
    f"@font-face{{font-family:'{n}';font-weight:{w};src:url('file://{PIPE}/fonts/{p}-latin-{w}-normal.woff2')}}"
    for n, p, w in (('Bodoni Moda', 'bodoni-moda', 500), ('Bodoni Moda', 'bodoni-moda', 400), ('Lab', 'libre-franklin', 400), ('Lab', 'libre-franklin', 500)))


def building(*a, **k):
    return re.sub(r'<line x1="[^"]*" y1="(206|211)"[^>]*></line>', '', _building(*a, **k))


def fp(v, d=2):
    return ('+' if v > 0 else '−' if v < 0 else '') + f'{abs(v):.{d}f}%'


def ts(s):
    """server time string -> seconds (naive, same axis as candle timestamps)"""
    return calendar.timegm(dt.datetime.strptime(s.strip(), '%Y.%m.%d %H:%M:%S').timetuple())


# ---------------------------------------------------------------- parse
def parse(text):
    head = {}; trades = []; blocks = []; cur = None; tf = None; section = 'head'
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith('part='):
            continue
        if ln.startswith('[TRADES]'):
            section = 'trades'; continue
        if ln.startswith('[CANDLES]'):
            kv = dict(re.findall(r'(\w+)=(\S+(?: \d\d:\d\d:\d\d)?)', ln))
            cur = dict(symbol=kv['symbol'], digits=int(kv.get('digits', 2)), tfs={},
                       t0=ts(kv['from']) if 'from' in kv else None, t1=ts(kv['to']) if 'to' in kv else None)
            blocks.append(cur); section = 'candles'; tf = None; continue
        if ln.startswith('[END]'):
            break
        m = re.match(r'\[(M1|M5|M15)\]', ln)
        if m and cur is not None:
            tf = m.group(1); cur['tfs'][tf] = []; continue
        if section == 'head' and '=' in ln:
            k, v = ln.split('=', 1); head[k.strip()] = v.strip(); continue
        if section == 'trades' and ln.startswith('T;'):
            f = ln.split(';')
            trades.append(dict(pos=f[1], sym=f[2], side=f[3], vol=float(f[4]), t0=ts(f[5]), e=float(f[6]),
                               t1=ts(f[7]), x=float(f[8]), pnl=float(f[9]), magic=int(f[10]) if f[10].lstrip('-').isdigit() else 0))
            continue
        if section == 'candles' and tf and re.match(r'^\d{9,11},', ln):
            f = ln.split(',')
            if len(f) == 5:
                cur['tfs'][tf].append((int(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[4])))
    return head, trades, blocks


# ---------------------------------------------------------------- chart
def chart(groups, C, tf, lt, pct, W=900, H=940):
    """groups: visible trade groups, C: candles (t,o,h,l,c), tf seconds, lt: offset to local time (s)"""
    snap = lambda t: math.floor(t / tf) * tf + tf / 2
    ps = [p for g in groups for p in g['parts']]
    x0 = max(C[0][0] - tf, min(p['t0'] for p in ps) - MARGIN * tf - tf / 2)
    x1 = min(C[-1][0] + tf, max(p['t1'] for p in ps) + (MARGIN + 1) * tf)
    C = [c for c in C if x0 - tf <= c[0] <= x1]
    x1 += (x1 - x0) * 0.12
    hs = sorted(c[2] for c in C); cap = hs[int(len(hs) * 0.98)] + (hs[-1] - hs[0]) * 0.02
    ys = [min(c[3] for c in C), min(max(c[2] for c in C), cap)] + [g['e'] for g in groups] + [p['x'] for p in ps]
    lo, hi = min(ys), max(ys); pad = (hi - lo) * 0.14 or 1; lo -= pad; hi += pad
    PW = W - 70
    X = lambda t: round((t - x0) / (x1 - x0) * PW, 1)
    Y = lambda v: round(H - (min(max(v, lo), hi) - lo) / (hi - lo) * H, 1)
    s = f'<svg width="{W}" height="{H + 40}" viewBox="0 0 {W} {H + 40}">'
    step = 10 ** math.floor(math.log10((hi - lo) / 4)); step = next(q * step for q in (1, 2, 2.5, 5, 10) if (hi - lo) / (q * step) <= 5)
    v = math.ceil(lo / step) * step
    dec = 0 if step >= 1 else (1 if step >= 0.1 else 2)
    while v < hi:
        s += f'<line x1="0" y1="{Y(v)}" x2="{PW}" y2="{Y(v)}" stroke="{LN}" stroke-width="1"/><text x="{PW + 10}" y="{Y(v) + 5}" font-family="Lab" font-size="15" fill="{MU}">{v:,.{dec}f}</text>'
        v += step
    xe = C[-1][0] + tf
    tstep = next((q for q in (60, 120, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200) if (xe - x0) / q <= 7), 43200)
    b = math.ceil((x0 + lt) / tstep) * tstep - lt
    while b <= xe:
        hm = dt.datetime.fromtimestamp(b + lt, dt.timezone.utc).strftime('%H:%M')
        s += f'<text x="{X(b)}" y="{H + 28}" text-anchor="middle" font-family="Lab" font-size="15" fill="{MU}">{hm}</text>'
        b += tstep
    cw = max(1.6, min(18, PW / ((x1 - x0) / tf) * 0.62))
    for t, o, h, l, c in C:
        x = X(t + tf / 2)
        s += f'<line x1="{x}" y1="{Y(h)}" x2="{x}" y2="{Y(l)}" stroke="{CG}" stroke-width="1"/><rect x="{round(x - cw / 2, 1)}" y="{Y(max(o, c))}" width="{round(cw, 1)}" height="{max(1.2, round(abs(Y(o) - Y(c)), 1))}" fill="{BG if c >= o else CG}" stroke="{CG}" stroke-width="1"/>'
    M = []; lines = ''; marks = ''; tags = ''
    for g in groups:
        a = X(snap(g['t0'])); ye = Y(g['e']); k = GR if g['pnl'] > 0 else RD; d = 1 if g['side'] == 'buy' else -1
        ex = []
        for p in sorted(g['parts'], key=lambda p: p['t1']):
            if ex and p['t1'] - ex[-1]['t1'] < 60: ex[-1]['ps'].append(p)
            else: ex.append(dict(t1=p['t1'], ps=[p]))
        for e in ex:
            w = sum(p['vol'] for p in e['ps']); e['x'] = sum(p['x'] * p['vol'] for p in e['ps']) / w; e['pnl'] = sum(p['pnl'] for p in e['ps'])
            e['bx'] = X(snap(e['t1'])); e['by'] = Y(e['x']); e['k'] = GR if e['pnl'] > 0 else RD
            lines += f'<line x1="{a}" y1="{ye}" x2="{e["bx"]}" y2="{e["by"]}" stroke="{e["k"]}" stroke-width="3" stroke-dasharray="7 6"/>'
            marks += f'<line x1="{e["bx"] - 9}" y1="{e["by"] - 9}" x2="{e["bx"] + 9}" y2="{e["by"] + 9}" stroke="{e["k"]}" stroke-width="4.5"/><line x1="{e["bx"] - 9}" y1="{e["by"] + 9}" x2="{e["bx"] + 9}" y2="{e["by"] - 9}" stroke="{e["k"]}" stroke-width="4.5"/>'
            M.append((e['bx'] - 12, e['by'] - 12, 24, 24))
        g['_'] = (a, ye, k, d, ex)
        marks += f'<polygon points="{a},{ye + d * 6} {a - 13},{ye + d * 30} {a + 13},{ye + d * 30}" fill="{k}" stroke="{BG}" stroke-width="2"/><circle cx="{a}" cy="{ye}" r="4" fill="{k}"/>'
        M.append((a - 15, min(ye, ye + d * 32) - 2, 30, 36))
    placed = list(M)

    def hit(r):
        x, y, w, h = r
        return x < 2 or y < 2 or x + w > PW - 2 or y + h > H - 2 or any(not (x + w < a_ or x > a_ + c_ or y + h < b_ or y > b_ + d_) for a_, b_, c_, d_ in placed)

    def tag(px, py, t, bg, fg, order):
        w = len(t) * 9.3 + 20; h = 28
        cand = {'L': (px - 18 - w, py - h / 2), 'R': (px + 18, py - h / 2), 'U': (px - w / 2, py - 22 - h), 'D': (px - w / 2, py + 22),
                'LU': (px - 12 - w, py - h - 10), 'LD': (px - 12 - w, py + 10), 'RU': (px + 12, py - h - 10), 'RD': (px + 12, py + 10)}
        r = None
        for o in order:
            x, y = cand[o]
            if not hit((x, y, w, h)): r = (x, y, w, h); break
        if not r:
            for k_ in range(1, 16):
                for o in ('L', 'R'):
                    x, y = cand[o]; y += ((k_ + 1) // 2) * (h + 4) * (1 if k_ % 2 else -1)
                    if not hit((x, y, w, h)): r = (x, y, w, h); break
                if r: break
        if not r:
            x, y = cand[order[0]]; r = (min(max(x, 2), PW - w - 2), min(max(y, 2), H - h - 2), w, h)
        placed.append(r); x, y, w, h = r; lead = ''
        cy = y + h / 2
        if abs(cy - py) > h or min(abs(x - px), abs(x + w - px)) > 30:
            lead = f'<line x1="{px}" y1="{py}" x2="{min(max(px, x), x + w)}" y2="{cy}" stroke="{FG}" stroke-width="1"/>'
        return lead + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{bg}"/><text x="{x + 10}" y="{y + h / 2 + 5}" font-family="Lab" font-weight="500" font-size="14" letter-spacing="0.8" fill="{fg}">{t}</text>'

    numf = lambda v: f"{v:,.1f}"
    for g in groups:
        a, ye, k, d, ex = g['_']; sd = 'BUY' if g['side'] == 'buy' else 'SELL'
        tags += tag(a, ye + d * 16, f"{g['n']} · {sd} {numf(g['e'])}", FG, BG, ('L', 'LU', 'LD', 'R', 'RD', 'RU') if d == 1 else ('L', 'LD', 'LU', 'R', 'RU', 'RD'))
    for g in groups:
        for e in g['_'][4]:
            tags += tag(e['bx'], e['by'], f"{g['n']} · {fp(pct(e['pnl']))}", e['k'], BG, ('R', 'RU', 'RD', 'U', 'D', 'L', 'LU', 'LD'))
    return s + lines + marks + tags + '</svg>'


# ---------------------------------------------------------------- pages
def story(label, inner, datestr):
    return f'''<html><head><meta charset="utf-8"><style>{FF}body{{margin:0}}</style></head><body><div style="position:relative;width:1080px;height:1920px;box-sizing:border-box;background:{BG};color:{FG};padding:230px 90px 250px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden">
<div style="text-align:center"><div style="{B};font-weight:500;font-size:34px;letter-spacing:12px;margin-right:-12px">JLN CAPITAL</div><div style="width:64px;height:1.5px;background:{FG};margin:20px auto 18px"></div><div style="{L};font-size:19px;letter-spacing:6px;color:{MU}">{label}</div></div>{inner}
<div style="text-align:center"><div style="{B};font-size:26px;letter-spacing:4px">{datestr.upper()}</div><div style="{L};font-size:15px;letter-spacing:3px;color:{MU};margin-top:22px">NOT INVESTMENT ADVICE</div></div></div></body></html>'''


def cover(day_pct, mtd, datestr):
    bw = 560; bh = round(bw * 172 / 532)
    return story('DAILY STATEMENT', f'''<div style="position:relative;height:620px"><div style="position:absolute;left:0;right:0;top:0;text-align:center;{B};font-weight:500;font-size:176px;line-height:1;letter-spacing:-3px;color:{FG if day_pct >= 0 else MU}">{fp(day_pct)}</div>
<svg width="{bw}" height="{bh}" viewBox="8 28 532 172" style="position:absolute;right:60px;top:150px;opacity:0.42">{building(FG, 1.3, 0)}</svg><div style="position:absolute;right:40px;top:{150 + bh - 1}px;width:{bw + 40}px;height:1.5px;background:{FG};opacity:0.42"></div>
<div style="position:absolute;left:0;right:0;top:{150 + bh + 90}px;text-align:center;{L};font-size:24px;letter-spacing:6px;color:{MU}">MTD <span style="{B};font-size:44px;letter-spacing:1px;color:{FG};margin-left:12px">{fp(mtd)}</span></div></div>''', datestr)


def frame(sym, sym_pct, label, svg, datestr):
    ttl = f'<div style="display:flex;justify-content:space-between;align-items:baseline"><div style="{B};font-weight:500;font-size:76px;line-height:1">{sym}</div><div style="{B};font-weight:500;font-size:76px;line-height:1;color:{FG if sym_pct >= 0 else MU}">{fp(sym_pct)}</div></div>'
    key = f'<div style="display:flex;justify-content:center;gap:40px;{L};font-size:15px;letter-spacing:3px;color:{MU}"><span><span style="display:inline-block;width:14px;height:14px;background:{GR};margin-right:10px;vertical-align:-2px"></span>PROFIT</span><span><span style="display:inline-block;width:14px;height:14px;background:{RD};margin-right:10px;vertical-align:-2px"></span>LOSS</span></div>'
    return story(label, f'<div>{ttl}<div style="height:60px"></div>{svg}<div style="height:36px"></div>{key}</div>', datestr)


# ---------------------------------------------------------------- main
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    allow_test = '--allow-test' in sys.argv; no_feed = '--no-feed' in sys.argv
    head, trades, blocks = parse(open(args[0], encoding='utf-8').read())
    cfg = json.load(open(os.path.join(PIPE, 'config.json')))
    hist_path = os.path.join(PIPE, 'history.json'); hist = json.load(open(hist_path))

    if head.get('test') == '1' and not allow_test:
        print('REFUSED: test report'); sys.exit(3)
    day = dt.datetime.strptime(head['date'], '%Y.%m.%d').date()
    datestr = f"{day.day} {MON[day.month - 1]} {day.year}"
    if int(head.get('trades', len(trades))) == 0 or not trades:
        print('NO_TRADES', day); sys.exit(0)

    start = float(head['balance_start']); net = float(head['day_net'])
    so = int(head.get('server_gmt_offset', 3)); mo = int(head.get('madrid_gmt_offset', 2)); lt = (mo - so) * 3600
    # ---- validation
    errs = []
    if len(trades) != int(head.get('trades', len(trades))): errs.append(f"trade count {len(trades)} != header {head.get('trades')}")
    if abs(sum(t['pnl'] for t in trades) - net) > 1.0: errs.append(f"sum of trades {sum(t['pnl'] for t in trades):.2f} != day_net {net:.2f}")
    if start <= 0: errs.append('balance_start <= 0')
    if abs(float(head.get('balance_end', start + net)) - (start + net + float(head.get('day_deposits', 0)) + float(head.get('day_other', 0)))) > 1.0: errs.append('balance_end mismatch')
    for b in blocks:
        for name, rows in b['tfs'].items():
            if any(not (r[3] <= min(r[1], r[4]) and r[2] >= max(r[1], r[4])) for r in rows): errs.append(f"bad candle in {b['symbol']} {name}")
            d = {y[0] - x[0] for x, y in zip(rows, rows[1:])}
            if any(x <= 0 or x % TFS[name] for x in d): errs.append(f"bad candle spacing in {b['symbol']} {name}")
    pct = lambda v: v / start * 100
    day_pct = pct(net)

    # ---- groups (entries of same symbol/side within 60 s), test strategies hidden from charts
    test = set(cfg.get('test_magics', []))
    syms = sorted({t['sym'] for t in trades}, key=lambda s: min(t['t0'] for t in trades if t['sym'] == s))
    sym_pct = {s: pct(sum(t['pnl'] for t in trades if t['sym'] == s)) for s in syms}
    frames = []
    for s in syms:
        vis = sorted([t for t in trades if t['sym'] == s and t['magic'] not in test], key=lambda t: (t['t0'], t['pos']))
        G = []
        for t in vis:
            g = next((g for g in G if g['side'] == t['side'] and abs(t['t0'] - g['t0']) < 60), None)
            if g: g['parts'].append(t)
            else: G.append(dict(side=t['side'], t0=t['t0'], parts=[t]))
        for n, g in enumerate(G):
            w = sum(p['vol'] for p in g['parts']); g['e'] = sum(p['e'] * p['vol'] for p in g['parts']) / w
            g['pnl'] = sum(p['pnl'] for p in g['parts']); g['t1'] = max(p['t1'] for p in g['parts']); g['n'] = n + 1
        bl = [b for b in blocks if b['symbol'] == s]
        if not G: continue
        if not bl: errs.append(f'no candles for {s}'); continue
        used = set()
        for bi, b in enumerate(bl):
            gs = [g for i, g in enumerate(G) if i not in used and (b['t0'] is None or (b['t0'] - 90 <= g['t0'] <= (b['t1'] or 9e18) + 90) or len(bl) == 1)]
            for i, g in enumerate(G):
                if g in gs: used.add(i)
            if not gs: continue
            t0 = min(g['t0'] for g in gs); t1 = max(g['t1'] for g in gs)
            choice = None
            for name in ('M1', 'M5', 'M15'):
                rows = b['tfs'].get(name)
                if not rows: continue
                n = (t1 - t0) / TFS[name] + 2 * MARGIN + 2
                choice = (name, rows)
                if n <= MAX_CANDLES: break
            if not choice: errs.append(f'no candle data for {s} block {bi + 1}'); continue
            name, rows = choice
            if rows[0][0] > t0 or rows[-1][0] + TFS[name] < t1: errs.append(f'candles do not cover trades for {s} block {bi + 1} ({name})')
            lab = f"{s} &nbsp;·&nbsp; {TFS[name] // 60} MIN" + (f" &nbsp;·&nbsp; {bi + 1}/{len(bl)}" if len(bl) > 1 else '')
            frames.append((s, lab, gs, rows, TFS[name]))
        if len(used) != len(G): errs.append(f'{len(G) - len(used)} trade(s) of {s} outside candle blocks')
    if errs:
        print('VALIDATION FAILED'); [print(' -', e) for e in errs]; sys.exit(2)

    # ---- history / MTD
    key = day.isoformat()
    hist[key] = dict(r=round(day_pct, 4), by={s: round(v, 4) for s, v in sym_pct.items()})
    comp = lambda xs: (math.prod(1 + x / 100 for x in xs) - 1) * 100
    mtd = comp([v['r'] for k, v in hist.items() if k[:7] == key[:7] and k <= key])

    # ---- render
    pages = [('1_cover', cover(day_pct, mtd, datestr))]
    for i, (s, lab, gs, rows, tf) in enumerate(frames):
        pages.append((f'{i + 2}_{s}', frame(s, sym_pct[s], lab, chart(gs, rows, tf, lt, pct), datestr)))
    from playwright.sync_api import sync_playwright
    from PIL import Image
    out_dir = os.path.join(ROOT, 'daily', key); os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith('.jpg'): os.remove(os.path.join(out_dir, f))
    tmp = os.path.join(PIPE, '_tmp.html'); files = []
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1920})
        for name, html in pages:
            open(tmp, 'w', encoding='utf-8').write(html); pg.goto('file://' + tmp); pg.wait_for_timeout(400)
            png = os.path.join(PIPE, '_tmp.png'); pg.screenshot(path=png)
            Image.open(png).convert('RGB').save(os.path.join(out_dir, name + '.jpg'), 'JPEG', quality=93, subsampling=0, optimize=True)
            files.append(f'daily/{key}/{name}.jpg')
        br.close()
    for f in ('_tmp.html', '_tmp.png'):
        try: os.remove(os.path.join(PIPE, f))
        except OSError: pass
    # contact sheet for review (not committed)
    sh = Image.new('RGB', (len(files) * 440 + 40, 827), '#1a1a1a')
    for i, f in enumerate(files): sh.paste(Image.open(os.path.join(ROOT, f)).resize((420, 747)), (30 + i * 440, 40))
    sh.save('/tmp/jln_daily_preview.png')

    json.dump(dict(sorted(hist.items())), open(hist_path, 'w'), indent=0)
    # ---- feed: only today's items, cover first; empty link + empty description (stories carry no text)
    if not no_feed:
        now = dt.datetime.now(dt.timezone.utc); stamp = now.strftime('%Y%m%d%H%M%S'); items = ''
        for i, f in enumerate(files):
            d = email.utils.format_datetime(now - dt.timedelta(seconds=i))
            size = os.path.getsize(os.path.join(ROOT, f))
            items += f'<item><title>Daily {key} {i + 1}/{len(files)}</title><link></link><guid isPermaLink="false">jln-daily-{key}-{i + 1}-{stamp}</guid><pubDate>{d}</pubDate><description></description><enclosure url="{BASE}/{f}?v={stamp}" type="image/jpeg" length="{size}"/><media:content url="{BASE}/{f}?v={stamp}" medium="image" type="image/jpeg"/></item>\n'
        open(os.path.join(ROOT, 'feed.xml'), 'w', encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>JLN Capital · Daily</title><link>{BASE}/</link><description>JLN Capital daily statements</description><language>en</language><atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
{items}</channel></rss>
''')
    print('OK', key, f'day {fp(day_pct)}', f'mtd {fp(mtd)}', ' '.join(f'{s} {fp(v)}' for s, v in sym_pct.items()))
    print('FILES', ' '.join(files))
    print('PREVIEW /tmp/jln_daily_preview.png')


if __name__ == '__main__':
    main()
