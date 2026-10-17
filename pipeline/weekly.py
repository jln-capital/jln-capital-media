#!/usr/bin/env python3
"""JLN Capital weekly statement post (single image) for the 'JLN Weekly' autolist.

Usage: python3 pipeline/weekly.py [YYYY-MM-DD] [--no-feed] [--post-only]
The date is any day of the week to report (default: today in Madrid). Uses pipeline/history.json.
Writes weekly/<monday>/post.jpg (feed post, replaces weekly.xml, read by the 'JLN Weekly' autolist) and two story frames\n(By Day, By Market) that are appended to feed.xml after today's daily stories.
Prints NO_WEEK and changes nothing if that week has no trading day in the history.
"""
import sys, os, json, math, datetime as dt, zoneinfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import render as r
import note

DN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']


def attribution(days, D):
    """Exact contribution of each market to the compounded return of a period: every daily contribution is
    weighted by the equity at the start of that day, so the figures add up to the period return."""
    e = 1.0; out = {}
    for d in days:
        v = D[d]; tot = sum(v.get('by', {}).values()); k = v['r'] / tot if abs(tot) > 1e-9 else 1
        for s, c in v.get('by', {}).items(): out[s] = out.get(s, 0) + c * k * e
        e *= 1 + v['r'] / 100
    return sorted(out.items(), key=lambda x: -x[1])


def col(v):
    return r.FG if v >= 0 else r.MU


def figure(label, v, size=104):
    """Main figure of a statement card: small label and the number."""
    return f'<div style="display:flex;flex-direction:column;align-items:center;gap:{round(size * 0.22)}px"><div style="{r.L};font-size:17px;letter-spacing:7px;color:{r.MU}">{label}</div><div style="{r.B};font-weight:500;font-size:{size}px;line-height:1;letter-spacing:-0.02em;color:{col(v)}">{r.fp(v)}</div></div>'


def line(items):
    """Secondary line: [(label, value), ...] in small type."""
    return '<div style="display:flex;gap:54px;align-items:baseline">' + ''.join(f'<div style="{r.L};font-size:17px;letter-spacing:6px;color:{r.MU}">{a} &nbsp;<span style="{r.B};font-weight:500;font-size:36px;letter-spacing:0;color:{col(v)};vertical-align:-4px">{r.fp(v)}</span></div>' for a, v in items) + '</div>'


TAGS = '#algotrading #algorithmictrading #tradingstrategy #daytrading #trading'


def caption(rng_txt, wk, mtd, ytd, days, mk):
    line = 'A good week. Same rules as a bad one.' if wk >= 0 else 'A losing week. Same rules as a winning one.'
    return (f"Week of {rng_txt}.\n\n{r.fp(wk)} this week · MTD {r.fp(mtd)} · YTD {r.fp(ytd)}\n\n{days}\n{mk}\n\n{line}"
            f"\n\nMy own account. Not investment advice.\n\n{TAGS}")


def building(bw=480):
    bh = round(bw * 172 / 532)
    return f'<div style="opacity:0.5;width:{bw + 80}px;display:flex;flex-direction:column;align-items:center"><svg width="{bw}" height="{bh}" viewBox="8 28 532 172">{r.building(r.FG, 1.3, 0)}</svg><div style="width:{bw + 80}px;height:1.5px;background:{r.FG};margin-top:-1px"></div></div>'


def card(label, blocks, foot, gap=50):
    """1080x1350 statement card: header, vertically centred blocks, footer."""
    return f'''<html><head><meta charset="utf-8"><style>{r.FF}body{{margin:0}}</style></head><body><div style="position:relative;width:1080px;height:1350px;background:{r.BG};color:{r.FG};overflow:hidden">
<div style="position:absolute;left:0;right:0;top:92px;text-align:center"><div style="{r.B};font-weight:500;font-size:30px;letter-spacing:11px;margin-right:-11px">JLN CAPITAL</div><div style="width:56px;height:1.5px;background:{r.FG};margin:18px auto 16px"></div><div style="{r.L};font-size:19px;letter-spacing:5px;color:{r.MU}">{label}</div></div>
<div style="position:absolute;left:0;right:0;top:250px;height:900px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{gap}px">{"".join(blocks)}</div>
<div style="position:absolute;left:0;right:0;bottom:104px;text-align:center;{r.B};font-size:26px;letter-spacing:4px">{foot}</div></div></body></html>'''


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
    last = ds[-1]; mtd = comp([D[d]['r'] for d in sorted(D) if (d.year, d.month) == (last.year, last.month) and d <= last])
    by = attribution(ds, D)
    MU_, M3 = [m.upper() for m in r.MON], [m[:3].upper() for m in r.MON]
    rng = f'{mon.day} – {fri.day} {MU_[fri.month - 1]} {fri.year}' if mon.month == fri.month else f'{mon.day} {M3[mon.month - 1]} – {fri.day} {M3[fri.month - 1]} {fri.year}'
    rng_txt = f'{mon.day} – {fri.day} {r.MON[fri.month - 1]} {fri.year}' if mon.month == fri.month else f'{mon.day} {r.MON[mon.month - 1][:3]} – {fri.day} {r.MON[fri.month - 1][:3]} {fri.year}'
    c = lambda v: r.FG if v >= 0 else r.MU
    html = card('WEEKLY STATEMENT', [figure('WEEKLY CHANGE', wk), line([('MTD', mtd), ('YTD', ytd)])], rng)
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
    if '--post-only' in sys.argv:   # backfill: only the post image, no stories, no feeds
        days = ' · '.join(f"{DN[d.weekday()]} {r.fp(D[d]['r'])}" for d in ds); mk = ' · '.join(f'{s} {r.fp(v)}' for s, v in by)
        print('OK', f, f'week {r.fp(wk)}', f'mtd {r.fp(mtd)}', f'ytd {r.fp(ytd)}'); print('CAPTION-BEGIN'); print(caption(rng_txt, wk, mtd, ytd, days, mk)); print('CAPTION-END'); return
    # ---- story frames (By Day, By Market) for the 'JLN Daily' stories autolist
    def rows(items, tot):
        mx = max([abs(v) for _, v in items if v is not None] or [1]) or 1
        h = f'<div style="border-top:1.5px solid {r.FG}">'
        for kk, v in items:
            if v is None:
                bar = '<div style="width:330px"></div>'; val = f'<div style="width:220px;text-align:right;{r.B};font-size:50px;color:{r.MU}">—</div>'
            else:
                w = abs(v) / mx * 155
                bar = f'<div style="width:330px;height:18px;position:relative"><div style="position:absolute;left:165px;top:-9px;width:1px;height:36px;background:{r.LN}"></div><div style="position:absolute;top:0;height:18px;width:{w}px;{"left:165px" if v >= 0 else f"left:{165 - w}px"};background:{r.GR if v >= 0 else r.RD}"></div></div>'
                val = f'<div style="width:220px;text-align:right;{r.B};font-size:50px;color:{c(v)}">{r.fp(v)}</div>'
            h += f'<div style="display:flex;align-items:center;justify-content:space-between;padding:38px 0;border-bottom:1px solid {r.LN}"><div style="width:250px;{r.L};font-size:24px;letter-spacing:4px">{kk}</div>{bar}{val}</div>'
        h += f'<div style="display:flex;align-items:center;justify-content:space-between;padding:38px 0;border-bottom:1.5px solid {r.FG}"><div style="{r.L};font-size:24px;letter-spacing:4px;font-weight:500">{tot[0]}</div><div style="{r.B};font-weight:500;font-size:54px">{r.fp(tot[1])}</div></div>'
        return h + '</div>'
    ttl = lambda t: f'<div style="display:flex;justify-content:space-between;align-items:baseline"><div style="{r.B};font-weight:500;font-size:76px;line-height:1">{t}</div><div style="{r.B};font-weight:500;font-size:76px;line-height:1;color:{c(wk)}">{r.fp(wk)}</div></div>'
    wd = [mon + dt.timedelta(days=i) for i in range(5)]
    s_day = r.story('WEEKLY STATEMENT &nbsp;·&nbsp; BY DAY', f'<div>{ttl("By Day")}<div style="height:70px"></div>{rows([(f"{DN[d.weekday()].upper()} {d.day} {M3[d.month - 1]}", D[d]["r"] if d in D else None) for d in wd], ("WEEK", wk))}</div>', rng_txt)
    s_mkt = r.story('WEEKLY STATEMENT &nbsp;·&nbsp; BY MARKET', f'<div>{ttl("By Market")}<div style="height:70px"></div>{rows(by, ("WEEK", wk))}</div>', rng_txt)
    sfiles = []
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1920})
        for nm, h_ in (('story_1_by_day', s_day), ('story_2_by_market', s_mkt)):
            open(tmp, 'w', encoding='utf-8').write(h_); pg.goto('file://' + tmp); pg.wait_for_timeout(400); pg.screenshot(path=png)
            sf = f'weekly/{mon.isoformat()}/{nm}.jpg'; Image.open(png).convert('RGB').save(os.path.join(ROOT, sf), 'JPEG', quality=93, subsampling=0, optimize=True); sfiles.append(sf)
        br.close()
    sh = Image.new('RGB', (2 * 440 + 40, 827), '#1a1a1a')
    for i, sf in enumerate(sfiles): sh.paste(Image.open(os.path.join(ROOT, sf)).resize((420, 747)), (30 + i * 440, 40))
    sh.save('/tmp/jln_weekly_stories_preview.png')
    for x in (tmp, png):
        try: os.remove(x)
        except OSError: pass
    days = ' · '.join(f"{DN[d.weekday()]} {r.fp(D[d]['r'])}" for d in ds)
    mk = ' · '.join(f'{s} {r.fp(v)}' for s, v in by)
    text = caption(rng_txt, wk, mtd, ytd, days, mk)
    if '--no-feed' not in sys.argv:
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')
        note.write_feed([(f'weekly-{mon.isoformat()}-{stamp}', f'Weekly {mon.isoformat()}', text, f, stamp)], 'weekly.xml', 'Weekly')
        # stories feed: keep today's daily items (if any), then the two weekly frames
        import re, email.utils
        fp_ = os.path.join(ROOT, 'feed.xml'); feed = open(fp_, encoding='utf-8').read()
        today = dt.datetime.now(zoneinfo.ZoneInfo('Europe/Madrid')).date().isoformat()
        keep = [it for it in re.findall(r'<item>.*?</item>', feed, flags=re.S) if f'jln-daily-{today}-' in it]
        now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0); extra = []
        # weekly frames go after the daily ones: each one minute older than the oldest daily item (Metricool compares to the minute)
        ds_ = [email.utils.parsedate_to_datetime(x) for it in keep for x in re.findall(r'<pubDate>(.*?)</pubDate>', it)]
        base_ = min(ds_) - dt.timedelta(minutes=1) if ds_ else now
        for i, sf in enumerate(sfiles):
            d_ = email.utils.format_datetime(base_ - dt.timedelta(minutes=i)); size = os.path.getsize(os.path.join(ROOT, sf))
            extra.append(f'<item><title>Weekly {mon.isoformat()} story {i + 1}/2</title><link></link><guid isPermaLink="false">jln-weekly-story-{mon.isoformat()}-{i + 1}-{stamp}</guid><pubDate>{d_}</pubDate><description></description><enclosure url="{r.BASE}/{sf}?v={stamp}" type="image/jpeg" length="{size}"/><media:content url="{r.BASE}/{sf}?v={stamp}" medium="image" type="image/jpeg"/></item>')
        head_ = feed.split('<item>')[0].split('</channel>')[0].rstrip()
        open(fp_, 'w', encoding='utf-8').write(head_ + '\n' + '\n'.join(keep + extra) + '\n</channel></rss>\n')
    print('OK', f, f'week {r.fp(wk)}', f'ytd {r.fp(ytd)}'); print(text); print('PREVIEW /tmp/jln_weekly_preview.png /tmp/jln_weekly_stories_preview.png')


if __name__ == '__main__':
    main()
