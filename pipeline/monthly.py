#!/usr/bin/env python3
"""JLN Capital monthly statement post (single image with the building), published through the 'JLN Posts' autolist.

Usage: python3 pipeline/monthly.py [YYYY-MM] [--no-feed]
Default month: the previous calendar month (Madrid time). Uses pipeline/history.json.
Writes monthly/YYYY-MM/post.jpg and, unless --no-feed, replaces posts.xml with this single item.
Prints NO_MONTH and changes nothing if that month has no trading day in the history.
"""
import sys, os, json, math, datetime as dt, zoneinfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import render as r
import note
import weekly as w


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if args:
        y, m = map(int, args[0].split('-'))
    else:
        t = dt.datetime.now(zoneinfo.ZoneInfo('Europe/Madrid')).date().replace(day=1) - dt.timedelta(days=1); y, m = t.year, t.month
    H = json.load(open(os.path.join(ROOT, 'pipeline', 'history.json')))
    D = {dt.date.fromisoformat(k): v for k, v in H.items()}
    ds = [d for d in sorted(D) if (d.year, d.month) == (y, m)]
    if not ds:
        print('NO_MONTH', f'{y}-{m:02d}'); return
    comp = lambda xs: (math.prod(1 + x / 100 for x in xs) - 1) * 100
    mo = comp([D[d]['r'] for d in ds]); ytd = comp([D[d]['r'] for d in sorted(D) if d.year == y and d <= ds[-1]])
    by = w.attribution(ds, D); name = r.MON[m - 1]
    html = w.card('MONTHLY STATEMENT', [f'<div style="{r.B};font-weight:500;font-size:80px;line-height:1">{name}</div>', w.figure('MONTHLY CHANGE', mo), w.line([('YTD', ytd)]), w.building(480)], str(y), 48)
    from playwright.sync_api import sync_playwright
    from PIL import Image
    f = f'monthly/{y}-{m:02d}/post.jpg'; os.makedirs(os.path.join(ROOT, os.path.dirname(f)), exist_ok=True)
    tmp = os.path.join(ROOT, 'pipeline', '_tmp.html'); png = os.path.join(ROOT, 'pipeline', '_tmp.png')
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1350})
        open(tmp, 'w', encoding='utf-8').write(html); pg.goto('file://' + tmp); pg.wait_for_timeout(400); pg.screenshot(path=png); br.close()
    Image.open(png).convert('RGB').save(os.path.join(ROOT, f), 'JPEG', quality=93, subsampling=0, optimize=True)
    Image.open(png).save('/tmp/jln_monthly_preview.png')
    for x in (tmp, png):
        try: os.remove(x)
        except OSError: pass
    pos = sum(D[d]['r'] > 0 for d in ds); mk = ' · '.join(f'{s} {r.fp(v)}' for s, v in by)
    line = 'Month closed. Same process next month.' if mo >= 0 else 'Losing months are part of the record too.'
    text = (f"{name} {y} · {r.fp(mo)}\nYTD {r.fp(ytd)}\n\n{len(ds)} trading days, {pos} positive.\n{mk}\n\n{line}"
            f"\n\nMy own account. Not investment advice.\n\n{w.TAGS}")
    if '--no-feed' not in sys.argv:
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')
        note.write_feed([(f'monthly-{y}-{m:02d}-{stamp}', f'Monthly {y}-{m:02d}', text, f, stamp)])
    print('OK', f, f'month {r.fp(mo)}', f'ytd {r.fp(ytd)}'); print(text); print('PREVIEW /tmp/jln_monthly_preview.png')


if __name__ == '__main__':
    main()
