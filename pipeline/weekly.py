#!/usr/bin/env python3
"""JLN Capital weekly statement post (single image) for the 'JLN Posts' autolist.

Usage: python3 pipeline/weekly.py [YYYY-MM-DD] [--no-feed]
The date is any day of the week to report (default: today in Madrid). Uses pipeline/history.json.
Writes weekly/<monday>/post.jpg and replaces posts.xml with this single item.
Prints NO_WEEK and changes nothing if that week has no trading day in the history.
"""
import sys, os, json, math, datetime as dt, zoneinfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import render as r
import note

DN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    day = dt.date.fromisoformat(args[0]) if args else dt.datetime.now(zoneinfo.ZoneInfo('Europe/Madrid')).date()
    H = json.load(open(os.path.join(ROOT, 'pipeline', 'history.json')))
    D = {dt.date.fromisoformat(k): v for k, v in H.items()}
    mon = day - dt.timedelta(days=day.weekday()); fri = mon + dt.timedelta(days=4)
    ds = [d for d in sorted(D) if mon <= d <= fri]
    if not ds:
        print('NO_WEEK', mon); return
    comp = lambda xs: (math.prod(1 + x / 100 for x in xs) - 1) * 100
    wk = comp([D[d]['r'] for d in ds]); ytd = comp([v['r'] for d, v in sorted(D.items()) if d.year == fri.year and d <= fri])
    by = {}
    for d in ds:
        for s, v in D[d].get('by', {}).items(): by[s] = by.get(s, 0) + v
    k = wk / sum(by.values()) if by and abs(sum(by.values())) > 1e-9 else 1
    by = sorted(((s, v * k) for s, v in by.items()), key=lambda x: -x[1])
    MU_, M3 = [m.upper() for m in r.MON], [m[:3].upper() for m in r.MON]
    rng = f'{mon.day} – {fri.day} {MU_[fri.month - 1]} {fri.year}' if mon.month == fri.month else f'{mon.day} {M3[mon.month - 1]} – {fri.day} {M3[fri.month - 1]} {fri.year}'
    rng_txt = f'{mon.day} – {fri.day} {r.MON[fri.month - 1]} {fri.year}' if mon.month == fri.month else f'{mon.day} {r.MON[mon.month - 1][:3]} – {fri.day} {r.MON[fri.month - 1][:3]} {fri.year}'
    c = lambda v: r.FG if v >= 0 else r.MU
    html = f'''<html><head><meta charset="utf-8"><style>{r.FF}body{{margin:0}}</style></head><body><div style="position:relative;width:1080px;height:1350px;background:{r.BG};color:{r.FG};overflow:hidden">
<div style="position:absolute;left:0;right:0;top:92px;text-align:center"><div style="{r.B};font-weight:500;font-size:30px;letter-spacing:11px;margin-right:-11px">JLN CAPITAL</div><div style="width:56px;height:1.5px;background:{r.FG};margin:18px auto 16px"></div><div style="{r.L};font-size:19px;letter-spacing:5px;color:{r.MU}">WEEKLY STATEMENT</div></div>
<div style="position:absolute;left:0;right:0;top:400px;display:flex;flex-direction:column;align-items:center">
<div style="{r.L};font-size:19px;letter-spacing:7px;color:{r.MU}">WEEKLY CHANGE</div><div style="{r.B};font-weight:500;font-size:118px;line-height:1;letter-spacing:-2px;color:{c(wk)};margin-top:26px">{r.fp(wk)}</div>
<div style="width:300px;height:1px;background:{r.LN};margin:62px 0 56px"></div>
<div style="{r.L};font-size:19px;letter-spacing:7px;color:{r.MU}">YTD CHANGE</div><div style="{r.B};font-weight:500;font-size:118px;line-height:1;letter-spacing:-2px;color:{c(ytd)};margin-top:26px">{r.fp(ytd)}</div></div>
<div style="position:absolute;left:0;right:0;bottom:120px;text-align:center;{r.B};font-size:26px;letter-spacing:4px">{rng}</div>
</div></body></html>'''
    from playwright.sync_api import sync_playwright
    from PIL import Image
    out_dir = os.path.join(ROOT, 'weekly', mon.isoformat()); os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(ROOT, 'pipeline', '_tmp.html'); png = os.path.join(ROOT, 'pipeline', '_tmp.png')
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1350})
        open(tmp, 'w', encoding='utf-8').write(html); pg.goto('file://' + tmp); pg.wait_for_timeout(400); pg.screenshot(path=png); br.close()
    f = f'weekly/{mon.isoformat()}/post.jpg'
    Image.open(png).convert('RGB').save(os.path.join(ROOT, f), 'JPEG', quality=93, subsampling=0, optimize=True)
    Image.open(png).save('/tmp/jln_weekly_preview.png')
    for x in (tmp, png):
        try: os.remove(x)
        except OSError: pass
    days = ' · '.join(f"{DN[d.weekday()]} {r.fp(D[d]['r'])}" for d in ds)
    mk = ' · '.join(f'{s} {r.fp(v)}' for s, v in by)
    text = f"Weekly Statement · {rng_txt}\n\nWeekly change: {r.fp(wk)}\nYTD change: {r.fp(ytd)}\n\n{days}\n\n{mk}\n\nNot investment advice.\n\n#algorithmictrading #proprietarytrading #weeklystatement"
    if '--no-feed' not in sys.argv:
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')
        note.write_feed([(f'weekly-{mon.isoformat()}-{stamp}', f'Weekly {mon.isoformat()}', text, f, stamp)])
    print('OK', f, f'week {r.fp(wk)}', f'ytd {r.fp(ytd)}'); print(text); print('PREVIEW /tmp/jln_weekly_preview.png')


if __name__ == '__main__':
    main()
