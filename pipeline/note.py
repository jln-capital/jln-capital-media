#!/usr/bin/env python3
"""JLN Capital note post renderer (15 layouts). Full specification: pipeline/NOTES.md

Usage: python3 pipeline/note.py NOTE.json [--dry-run] [--no-feed]

  --dry-run : only render /tmp/jln_note_preview.png (no file in notes/, no log, no feed)
  --no-feed : write notes/NNN.jpg and notes/log.json but leave posts.xml untouched

Without flags: writes notes/NNN.jpg, appends notes/log.json and replaces posts.xml with this single item
(read by the Metricool autolist 'JLN Posts').
Prints 'OK ...' or 'VALIDATION FAILED: reason' (exit 2, nothing written).
"""
import sys, os, re, json, html, math, datetime as dt, email.utils
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import render as r

SERIES = 'NOTES'
TAGS = '#algorithmictrading #quantitativetrading #riskmanagement'
B, L, FG, MU, LN, BG, CG = r.B, r.L, r.FG, r.MU, r.LN, r.BG, r.CG
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI']


class Bad(Exception):
    pass


def e(s):
    return html.escape(str(s).strip())


def need(n, key, lo, hi, optional=False):
    """Return a checked string field."""
    v = n.get(key, '')
    if not isinstance(v, str):
        raise Bad(f'"{key}" must be text')
    v = v.strip()
    if not v and optional:
        return ''
    if not lo <= len(v) <= hi:
        raise Bad(f'"{key}" must have {lo}-{hi} characters (has {len(v)})')
    return v


def need_list(n, key, lo, hi):
    v = n.get(key)
    if not isinstance(v, list) or not lo <= len(v) <= hi:
        raise Bad(f'"{key}" must be a list of {lo}-{hi} items')
    return v


def size(n, steps, last):
    for limit, s in steps:
        if n <= limit:
            return s
    return last


def lab(t, s=17, c=None):
    return f'<div style="{L};font-size:{s}px;letter-spacing:5px;color:{c or MU};text-transform:uppercase">{e(t)}</div>'


def tail(l1, l2='', s=50, top=64):
    """Closing sentence(s) under a figure: l1 in black, l2 in grey."""
    if not l1 and not l2:
        return ''
    a = f'<span>{e(l1)}</span>' if l1 else ''
    b = f'<span style="color:{MU}">{e(l2)}</span>' if l2 else ''
    return f'<div style="{B};font-weight:500;font-size:{s}px;line-height:1.25;margin-top:{top}px;text-align:center">{a}{"<br>" if a and b else ""}{b}</div>'


def grey_tail(t, top=64):
    return f'<div style="{B};font-size:38px;line-height:1.3;color:{MU};margin-top:{top}px;text-align:center">{e(t)}</div>' if t else ''


# ------------------------------------------------------------------ formats
def f_statement(n):
    l1 = need(n, 'line1', 10, 110); l2 = need(n, 'line2', 3, 80, True)
    fs = size(len(l1) + len(l2), ((75, 74), (100, 66), (130, 58)), 50)
    l2h = f'<br><span style="color:{MU}">{e(l2)}</span>' if l2 else ''
    return (f'<div style="width:100%;min-height:500px;box-sizing:border-box;border-top:1.5px solid {FG};border-bottom:1.5px solid {FG};display:flex;align-items:center;justify-content:center;padding:50px 0">'
            f'<div style="{B};font-weight:500;font-size:{fs}px;line-height:1.22;letter-spacing:-0.5px;text-align:center">{e(l1)}{l2h}</div></div>'), f'{l1} {l2}'.strip()


def f_quote(n):
    q = need(n, 'quote', 15, 230); a = need(n, 'author', 3, 40); s = need(n, 'source', 4, 80)
    if len(q.split()) > 35:
        raise Bad('"quote" must be 35 words or fewer')
    q = q.strip('"“”')
    fs = size(len(q), ((60, 68), (110, 58), (170, 50)), 44)
    return (f'<div style="text-align:center"><div style="{B};font-size:150px;line-height:0.6;height:70px;color:{MU}">“</div>'
            f'<div style="{B};font-weight:500;font-size:{fs}px;line-height:1.25;margin-top:30px">{e(q)}</div>'
            f'<div style="width:56px;height:1.5px;background:{FG};margin:54px auto 30px"></div>'
            f'<div style="{L};font-size:21px;letter-spacing:6px;text-transform:uppercase">{e(a)}</div>'
            f'<div style="{L};font-size:16px;letter-spacing:3px;color:{MU};margin-top:14px">{e(s)}</div></div>'), f'“{q}” — {a}, {s}'


def f_number(n):
    lb = need(n, 'label', 3, 60); num = need(n, 'number', 1, 12); l1 = need(n, 'line1', 5, 90); l2 = need(n, 'line2', 3, 70, True)
    fs = size(len(num), ((4, 300), (6, 250), (8, 190)), 150)
    return (f'<div style="text-align:center">{lab(lb)}<div style="{B};font-weight:500;font-size:{fs}px;line-height:1;letter-spacing:-0.02em;margin:40px 0 0;white-space:nowrap">{e(num)}</div></div>'
            + (f'<div style="{B};font-size:40px;line-height:1.3;margin-top:46px;text-align:center">{e(l1)}' + (f'<br><span style="color:{MU}">{e(l2)}</span>' if l2 else '') + '</div>')), f'{lb}: {num}. {l1} {l2}'.strip()


def f_formula(n):
    lb = need(n, 'label', 3, 40); fm = need(n, 'formula', 3, 60); l1 = need(n, 'line1', 5, 80); l2 = need(n, 'line2', 3, 80, True)
    fs = size(len(fm), ((28, 56), (40, 46)), 38)
    fh = re.sub(r'_\{?([A-Za-z0-9]+)\}?', lambda m: f'<sub style="font-size:0.52em">{m.group(1)}</sub>', e(fm))
    return (f'<div style="text-align:center;width:100%">{lab(lb)}<div style="border-top:1.5px solid {FG};border-bottom:1.5px solid {FG};margin:44px 0 0;padding:70px 0;{B};font-weight:500;font-size:{fs}px;line-height:1.5;white-space:nowrap">{fh}</div></div>'
            + (f'<div style="{B};font-size:38px;line-height:1.35;color:{MU};margin-top:44px;text-align:center">{e(l1)}' + (f'<br>{e(l2)}' if l2 else '') + '</div>')), f'{lb}: {fm}. {l1} {l2}'.strip()


def f_table(n):
    hd = need_list(n, 'head', 2, 2); rows = need_list(n, 'rows', 3, 7); ln = need(n, 'line1', 5, 80, True)
    for x in hd:
        if not isinstance(x, str) or not 2 <= len(x) <= 22: raise Bad('"head" items must have 2-22 characters')
    for row in rows:
        if not isinstance(row, list) or len(row) != 2 or any(not isinstance(x, str) or not 1 <= len(x) <= 16 for x in row):
            raise Bad('each row must be two texts of 1-16 characters')
    rh = ''.join(f'<div style="display:flex;justify-content:space-between;align-items:baseline;padding:17px 0;border-bottom:1px solid {LN}"><span style="{B};font-size:44px;color:{MU}">{e(a)}</span><span style="{B};font-weight:500;font-size:44px">{e(b)}</span></div>' for a, b in rows)
    return (f'<div style="width:660px"><div style="display:flex;justify-content:space-between;padding-bottom:16px;border-bottom:1.5px solid {FG}">{lab(hd[0], 16)}{lab(hd[1], 16)}</div>{rh}</div>' + grey_tail(ln, 70)), f'{hd[0]} / {hd[1]}. {ln}'.strip()


def f_chart(n):
    lb = need(n, 'label', 3, 60); l1 = need(n, 'line1', 5, 70); l2 = need(n, 'line2', 3, 70, True)
    ser = need_list(n, 'series', 1, 30); W, H = 820, 470
    pts_all = []
    for s in ser:
        p = s.get('points') if isinstance(s, dict) else None
        if not isinstance(p, list) or not 2 <= len(p) <= 600: raise Bad('each series needs 2-600 points [[x, y], ...]')
        for q in p:
            if not isinstance(q, list) or len(q) != 2 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in q): raise Bad('points must be finite numbers [x, y]')
        if s.get('style', 'main') not in ('main', 'muted', 'dashed'): raise Bad('series style must be main, muted or dashed')
        pts_all += p
    x0, x1 = min(p[0] for p in pts_all), max(p[0] for p in pts_all); y0, y1 = min(p[1] for p in pts_all), max(p[1] for p in pts_all)
    base = n.get('baseline')
    if base is not None:
        if not isinstance(base, (int, float)): raise Bad('"baseline" must be a number or null')
        y0, y1 = min(y0, base), max(y1, base)
    if x1 <= x0 or y1 <= y0: raise Bad('chart has no extent')
    pad = (y1 - y0) * 0.05
    X = lambda x: (x - x0) / (x1 - x0) * W; Y = lambda y: H - (y - (y0 - pad)) / ((y1 + pad) - (y0 - pad)) * H
    svg = ''
    if n.get('axis'): svg += f'<line x1="0" x2="{W}" y1="{H}" y2="{H}" stroke="{FG}" stroke-width="1.5"/>'
    if base is not None: svg += f'<line x1="0" x2="{W}" y1="{Y(base):.1f}" y2="{Y(base):.1f}" stroke="{LN}" stroke-width="1.5" stroke-dasharray="4 7"/>'
    look = {'muted': f'stroke="{CG}" stroke-width="1.3" opacity="0.75"', 'dashed': f'stroke="{CG}" stroke-width="2.4" stroke-dasharray="7 7"', 'main': f'stroke="{FG}" stroke-width="3"'}
    for st in ('muted', 'dashed', 'main'):
        for s in ser:
            if s.get('style', 'main') == st:
                svg += f'<polyline points="{" ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in s["points"])}" fill="none" stroke-linejoin="round" {look[st]}/>'
    leg = [(s.get('label'), s.get('style', 'main')) for s in ser if isinstance(s.get('label'), str) and s.get('label').strip()][:3]
    for t, _ in leg:
        if len(t) > 24: raise Bad('series labels must have 24 characters or fewer')
    lstyle = {'main': f'3px solid {FG}', 'dashed': f'2.4px dashed {CG}', 'muted': f'1.5px solid {CG}'}
    legh = ('<div style="display:flex;justify-content:center;gap:56px;margin-top:30px">' + ''.join(f'<span style="{L};font-size:16px;letter-spacing:4px;color:{MU};text-transform:uppercase"><span style="display:inline-block;width:44px;border-top:{lstyle[st]};vertical-align:middle;margin-right:14px"></span>{e(t)}</span>' for t, st in leg) + '</div>') if leg else ''
    return (f'<div style="text-align:center;width:100%">{lab(lb, 16)}<svg width="{W}" height="{H + 4}" style="display:block;margin-top:44px">{svg}</svg>{legh}</div>' + tail(l1, l2, 52, 56)), f'{l1} {l2}'.strip()


def f_definition(n):
    t = need(n, 'term', 3, 34); k = need(n, 'kind', 3, 40); tx = need(n, 'text', 30, 200); l2 = need(n, 'line2', 3, 80, True)
    fs = size(len(t), ((18, 92), (26, 76)), 62)
    return (f'<div style="width:780px;text-align:left"><div style="{B};font-weight:500;font-size:{fs}px;line-height:1.05">{e(t)}</div><div style="margin:30px 0 40px">{lab(k, 19)}</div><div style="height:1.5px;background:{FG}"></div>'
            f'<div style="{B};font-size:44px;line-height:1.38;margin-top:44px">{e(tx)}' + (f'<br><span style="color:{MU}">{e(l2)}</span>' if l2 else '') + '</div></div>'), f'{t}: {tx} {l2}'.strip()


def f_long(n):
    lb = need(n, 'label', 3, 40); ps = need_list(n, 'paragraphs', 1, 3)
    if any(not isinstance(p, str) or len(p.strip()) < 20 for p in ps) or not 120 <= sum(len(p) for p in ps) <= 460:
        raise Bad('"paragraphs" must be 1-3 texts with 120-460 characters in total')
    body = '<br><br>'.join(e(p) for p in ps)
    return (f'<div style="width:780px;text-align:left">{lab(lb)}<div style="width:56px;height:1.5px;background:{FG};margin:30px 0 44px"></div><div style="{B};font-size:41px;line-height:1.5">{body}</div></div>'), f'{lb}. {ps[0]}'


def f_comparison(n):
    cols = []
    for side, c in (('left', MU), ('right', FG)):
        d = n.get(side)
        if not isinstance(d, dict): raise Bad(f'"{side}" must be an object with head and items')
        hd = need(d, 'head', 2, 20); it = need_list(d, 'items', 3, 4)
        if any(not isinstance(x, str) or not 3 <= len(x.strip()) <= 26 for x in it): raise Bad('comparison items must have 3-26 characters')
        cols.append((hd, it, c))
    if len(cols[0][1]) != len(cols[1][1]): raise Bad('both comparison columns need the same number of items')
    ln = need(n, 'line1', 5, 80, True)
    col = lambda hd, it, c: f'<div style="flex:1;padding:0 34px;text-align:left">{lab(hd, 17, FG)}<div style="width:40px;height:1.5px;background:{FG};margin:22px 0 34px"></div>' + ''.join(f'<div style="{B};font-size:40px;line-height:1.25;color:{c};padding:18px 0;border-bottom:1px solid {LN}">{e(x)}</div>' for x in it) + '</div>'
    return (f'<div style="display:flex;width:888px;margin:0 -34px">{col(*cols[0])}<div style="width:1.5px;background:{FG}"></div>{col(*cols[1])}</div>' + grey_tail(ln, 76)), f'{cols[0][0]} / {cols[1][0]}. {ln}'.strip()


def f_question(n):
    q = need(n, 'question', 15, 130)
    if not q.endswith('?'): raise Bad('"question" must end with a question mark')
    fs = size(len(q), ((50, 76), (80, 68), (105, 60)), 54)
    return (f'<div style="text-align:center"><div style="{B};font-size:210px;line-height:0.8;color:{LN}">?</div><div style="{B};font-weight:500;font-size:{fs}px;line-height:1.2;margin-top:50px">{e(q)}</div>'
            f'<div style="width:56px;height:1.5px;background:{FG};margin:54px auto 30px"></div>{lab("Answer in the caption")}</div>'), q


def f_arithmetic(n):
    st = need_list(n, 'steps', 2, 4); res = need_list(n, 'result', 2, 2); l1 = need(n, 'line1', 5, 60); l2 = need(n, 'line2', 3, 60, True)
    for row in st + [res]:
        if not isinstance(row, list) or len(row) != 2 or not isinstance(row[0], str) or not isinstance(row[1], str) or not 2 <= len(row[0]) <= 26 or not 1 <= len(row[1]) <= 9:
            raise Bad('steps and result must be [label (2-26 chars), value (1-9 chars)]')
    rows = ''.join(f'<div style="display:flex;justify-content:space-between;align-items:baseline;padding:20px 0;border-bottom:1px solid {LN}"><span style="{L};font-size:18px;letter-spacing:5px;color:{MU};text-transform:uppercase">{e(a)}</span><span style="{B};font-weight:500;font-size:60px;color:{MU if b.strip().startswith(("−", "-")) else FG}">{e(b)}</span></div>' for a, b in st)
    rows += f'<div style="display:flex;justify-content:space-between;align-items:baseline;padding:26px 0;border-bottom:1.5px solid {FG}"><span style="{L};font-size:18px;letter-spacing:5px;text-transform:uppercase">{e(res[0])}</span><span style="{B};font-weight:500;font-size:60px">{e(res[1])}</span></div>'
    return (f'<div style="width:680px;border-top:1.5px solid {FG}">{rows}</div>' + tail(l1, l2, 50, 70)), f'{l1} {l2}'.strip()


def f_matrix(n):
    cols = need_list(n, 'cols', 2, 2); rws = need_list(n, 'rows', 2, 2); cells = need_list(n, 'cells', 4, 4); l1 = need(n, 'line1', 5, 70); l2 = need(n, 'line2', 3, 70, True)
    for x in cols + rws:
        if not isinstance(x, str) or not 2 <= len(x) <= 18: raise Bad('matrix cols/rows labels must have 2-18 characters')
    for c in cells:
        if not isinstance(c, list) or len(c) != 2 or not isinstance(c[0], str) or not isinstance(c[1], str) or not 2 <= len(c[0]) <= 14 or len(c[1]) > 20: raise Bad('each cell must be [title (2-14 chars), subtitle (0-20 chars)]')
    cell = lambda i: f'<div style="height:240px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;{"border-right:1px solid " + LN + ";" if i % 2 == 0 else ""}{"border-bottom:1px solid " + LN + ";" if i < 2 else ""}"><div style="{B};font-weight:500;font-size:44px">{e(cells[i][0])}</div><div style="margin-top:16px">{lab(cells[i][1], 15)}</div></div>'
    side = lambda t: f'<div style="height:240px;display:flex;align-items:center;justify-content:flex-end;text-align:right;padding-right:22px"><div style="{L};font-size:16px;letter-spacing:4px;line-height:1.5;color:{MU};text-transform:uppercase;width:120px">{e(t)}</div></div>'
    return (f'<div style="display:flex;width:820px"><div style="width:150px;padding-top:54px">{side(rws[0])}{side(rws[1])}</div><div style="flex:1"><div style="display:flex;justify-content:space-around;height:54px">{lab(cols[0], 16)}{lab(cols[1], 16)}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;border:1.5px solid {FG}">{"".join(cell(i) for i in range(4))}</div></div></div>' + tail(l1, l2, 50, 70)), f'{l1} {l2}'.strip()


def f_history(n):
    d = need(n, 'date', 4, 30); num = need(n, 'number', 1, 12); tx = need(n, 'text', 10, 110); l2 = need(n, 'line2', 3, 80, True)
    fs = size(len(num), ((4, 300), (6, 250), (8, 190)), 150)
    return (f'<div style="text-align:center">{lab(d)}<div style="{B};font-weight:500;font-size:{fs}px;line-height:1;letter-spacing:-0.02em;margin:36px 0 40px;white-space:nowrap">{e(num)}</div>'
            f'<div style="{B};font-size:42px;line-height:1.35">{e(tx)}' + (f'<br><span style="color:{MU}">{e(l2)}</span>' if l2 else '') + '</div></div>'), f'{d}: {num}. {tx} {l2}'.strip()


def f_myth(n):
    m = need(n, 'myth', 10, 90); f = need(n, 'fact', 10, 120)
    return (f'<div style="width:780px;text-align:left">{lab("Myth")}<div style="{B};font-size:56px;line-height:1.25;color:{MU};margin-top:26px;text-decoration:line-through;text-decoration-thickness:2px">{e(m)}</div>'
            f'<div style="height:1.5px;background:{FG};margin:64px 0 60px"></div>{lab("Fact", 17, FG)}<div style="{B};font-weight:500;font-size:56px;line-height:1.25;margin-top:26px">{e(f)}</div></div>'), f'Myth: {m} Fact: {f}'


def f_list(n):
    lb = need(n, 'label', 3, 44); it = need_list(n, 'items', 3, 5)
    if any(not isinstance(x, str) or not 8 <= len(x.strip()) <= 62 for x in it): raise Bad('list items must have 8-62 characters')
    rows = ''.join(f'<div style="display:flex;align-items:baseline;gap:34px;padding:24px 0;border-bottom:1px solid {LN}"><span style="{B};font-size:34px;color:{MU};width:44px;flex:none">{ROMAN[i]}</span><span style="{B};font-weight:500;font-size:44px;line-height:1.2">{e(x)}</span></div>' for i, x in enumerate(it))
    return (f'<div style="width:780px;text-align:left">{lab(lb)}<div style="height:1.5px;background:{FG};margin-top:28px"></div>{rows}</div>'), f'{lb}: ' + ' '.join(x.strip() for x in it)


FORMATS = dict(statement=f_statement, quote=f_quote, number=f_number, formula=f_formula, table=f_table, chart=f_chart, definition=f_definition, long=f_long,
               comparison=f_comparison, question=f_question, arithmetic=f_arithmetic, matrix=f_matrix, history=f_history, myth=f_myth, list=f_list)


def page(no, inner):
    return f'''<html><head><meta charset="utf-8"><style>{r.FF}body{{margin:0}}</style></head><body><div style="position:relative;width:1080px;height:1350px;background:{BG};color:{FG};overflow:hidden">
<div style="position:absolute;left:0;right:0;top:92px;text-align:center"><div style="{B};font-weight:500;font-size:30px;letter-spacing:11px;margin-right:-11px">JLN CAPITAL</div><div style="width:56px;height:1.5px;background:{FG};margin:18px auto 16px"></div><div style="{L};font-size:19px;letter-spacing:5px;color:{MU}">{SERIES} &nbsp;·&nbsp; No. {no}</div></div>
<div id="box" style="position:absolute;left:130px;width:820px;top:285px;height:930px;display:flex;align-items:center;justify-content:center"><div id="in" style="width:100%;display:flex;flex-direction:column;align-items:center">{inner}</div></div>
</div><script>
const box=document.getElementById('box'), inn=document.getElementById('in');
function over(){{const b=box.getBoundingClientRect(); if(inn.getBoundingClientRect().height>b.height+1) return true;
  for(const el of inn.querySelectorAll('*')){{const q=el.getBoundingClientRect(); if(q.width&&(q.right>b.right+36||q.left<b.left-36)) return true;}} return false;}}
let z=1; while(over()&&z>0.62){{z-=0.02; inn.style.zoom=z;}}
window.FIT={{zoom:z, over:over()}};
</script></body></html>'''


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    try:
        note = json.load(open(args[0], encoding='utf-8'))
        fmt = note.get('format', 'statement')
        if fmt not in FORMATS: raise Bad(f'unknown format "{fmt}"; use one of: {", ".join(FORMATS)}')
        cap = need(note, 'caption', 120, 900)
        if '#' in cap or '\n' in cap or 'http' in cap: raise Bad('"caption" must be plain text without hashtags, links or line breaks')
        inner, headline = FORMATS[fmt](note)
    except Bad as x:
        print('VALIDATION FAILED:', x); sys.exit(2)
    os.makedirs(os.path.join(ROOT, 'notes'), exist_ok=True)
    log_path = os.path.join(ROOT, 'notes', 'log.json')
    log = json.load(open(log_path, encoding='utf-8')) if os.path.exists(log_path) else []
    key = re.sub(r'\W+', ' ', headline.lower()).strip()
    if any(re.sub(r'\W+', ' ', x.get('headline', x.get('line1', '')).lower()).strip() == key for x in log):
        print('VALIDATION FAILED: this note was already published'); sys.exit(2)
    no = len(log) + 1
    from playwright.sync_api import sync_playwright
    from PIL import Image
    tmp = os.path.join(ROOT, 'pipeline', '_tmp.html'); png = os.path.join(ROOT, 'pipeline', '_tmp.png')
    try:
        with sync_playwright() as p:
            br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1350})
            open(tmp, 'w', encoding='utf-8').write(page(no, inner)); pg.goto('file://' + tmp); pg.wait_for_timeout(500)
            fit = pg.evaluate('window.FIT'); pg.screenshot(path=png); br.close()
        if fit['over']:
            print('VALIDATION FAILED: the content does not fit in the image; shorten the texts'); sys.exit(2)
        Image.open(png).save('/tmp/jln_note_preview.png')
        if dry:
            print(f'DRY RUN OK | format {fmt} | zoom {fit["zoom"]:.2f}'); print('PREVIEW /tmp/jln_note_preview.png'); return
        f = f'notes/{no:03d}.jpg'
        Image.open(png).convert('RGB').save(os.path.join(ROOT, f), 'JPEG', quality=93, subsampling=0, optimize=True)
    finally:
        for x in (tmp, png):
            try: os.remove(x)
            except OSError: pass
    text = f"{SERIES.title()} No. {no}\n\n{headline}\n\n{cap}\n\nNot investment advice.\n\n{TAGS}"
    now = dt.datetime.now(dt.timezone.utc); stamp = now.strftime('%Y%m%d%H%M%S')
    entry = dict(no=no, date=now.date().isoformat(), format=fmt, headline=headline, topic=note.get('topic', ''), sources=note.get('sources', []), note=note)
    log.append(entry)
    json.dump(log, open(log_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if '--no-feed' not in sys.argv:
        write_feed([(f"note-{no}-{stamp}", f"Note {no}", text, f, stamp)])
    print('OK', f, '| format', fmt, '| zoom', f'{fit["zoom"]:.2f}', '| caption:', len(text), 'chars'); print('PREVIEW /tmp/jln_note_preview.png')


def write_feed(items, name='posts.xml', title='Posts'):
    """items: (guid, title, text, image path, stamp). Replaces the feed file: posts.xml for the 'JLN Posts' autolist
    (notes) or weekly.xml for the 'JLN Weekly' autolist."""
    now = dt.datetime.now(dt.timezone.utc); out = ''
    for i, (guid, title_, text, f, stamp) in enumerate(items):
        size_ = os.path.getsize(os.path.join(ROOT, f)); d = email.utils.format_datetime(now - dt.timedelta(seconds=i))
        text = text.replace(']]>', ']] >')
        out += f'<item><title>{html.escape(title_)}</title><link></link><guid isPermaLink="false">jln-{guid}</guid><pubDate>{d}</pubDate><description><![CDATA[{text}]]></description><enclosure url="{r.BASE}/{f}?v={stamp}" type="image/jpeg" length="{size_}"/><media:content url="{r.BASE}/{f}?v={stamp}" medium="image" type="image/jpeg"/></item>\n'
    open(os.path.join(ROOT, name), 'w', encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>JLN Capital · {title}</title><link>{r.BASE}/</link><description>JLN Capital posts</description><language>en</language><atom:link href="{r.BASE}/{name}" rel="self" type="application/rss+xml"/>
{out}</channel></rss>
''')


if __name__ == '__main__':
    main()
