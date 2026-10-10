#!/usr/bin/env python3
"""JLN Capital note post renderer.

Usage: python3 pipeline/note.py NOTE.json [--no-feed]

NOTE.json = {"line1": "...", "line2": "...", "caption": "...", "topic": "...", "sources": ["..."]}
  line1  : main sentence shown on the image (required, max ~70 characters)
  line2  : optional second sentence shown in grey (max ~50 characters)
  caption: body text of the Instagram caption (3-4 sober sentences, plain text, no hashtags)
Writes notes/NNN.jpg, appends to notes/log.json and replaces posts.xml with this single item.
"""
import sys, os, json, html, datetime as dt, email.utils
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import render as r

SERIES = 'NOTES'
TAGS = '#algorithmictrading #quantitativetrading #riskmanagement'


def page(no, l1, l2):
    n = len(l1) + len(l2)
    fs = 74 if n <= 75 else 66 if n <= 100 else 58 if n <= 130 else 50
    l2h = f'<br><span style="color:{r.MU}">{html.escape(l2)}</span>' if l2 else ''
    return f'''<html><head><meta charset="utf-8"><style>{r.FF}body{{margin:0}}</style></head><body><div style="position:relative;width:1080px;height:1350px;background:{r.BG};color:{r.FG};overflow:hidden">
<div style="position:absolute;left:0;right:0;top:92px;text-align:center"><div style="{r.B};font-weight:500;font-size:30px;letter-spacing:11px;margin-right:-11px">JLN CAPITAL</div><div style="width:56px;height:1.5px;background:{r.FG};margin:18px auto 16px"></div><div style="{r.L};font-size:19px;letter-spacing:5px;color:{r.MU}">{SERIES} &nbsp;·&nbsp; No. {no}</div></div>
<div style="position:absolute;left:130px;right:130px;top:455px;height:1.5px;background:{r.FG}"></div>
<div style="position:absolute;left:130px;right:130px;top:456px;height:499px;display:flex;align-items:center;justify-content:center"><div style="text-align:center;{r.B};font-weight:500;font-size:{fs}px;line-height:1.22;letter-spacing:-0.5px">{html.escape(l1)}{l2h}</div></div>
<div style="position:absolute;left:130px;right:130px;top:955px;height:1.5px;background:{r.FG}"></div>
</div></body></html>'''


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    note = json.load(open(args[0], encoding='utf-8'))
    l1 = note['line1'].strip(); l2 = note.get('line2', '').strip(); cap = note['caption'].strip()
    if not l1 or len(l1) > 110 or len(l2) > 80 or len(cap) < 80 or len(cap) > 900:
        print('VALIDATION FAILED: text lengths out of range'); sys.exit(2)
    os.makedirs(os.path.join(ROOT, 'notes'), exist_ok=True)
    log_path = os.path.join(ROOT, 'notes', 'log.json')
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
    if any(e['line1'].lower() == l1.lower() for e in log):
        print('VALIDATION FAILED: this note was already published'); sys.exit(2)
    no = len(log) + 1
    from playwright.sync_api import sync_playwright
    from PIL import Image
    tmp = os.path.join(ROOT, 'pipeline', '_tmp.html'); png = os.path.join(ROOT, 'pipeline', '_tmp.png')
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1350})
        open(tmp, 'w', encoding='utf-8').write(page(no, l1, l2)); pg.goto('file://' + tmp); pg.wait_for_timeout(400); pg.screenshot(path=png); br.close()
    f = f'notes/{no:03d}.jpg'
    Image.open(png).convert('RGB').save(os.path.join(ROOT, f), 'JPEG', quality=93, subsampling=0, optimize=True)
    Image.open(png).save('/tmp/jln_note_preview.png')
    for x in (tmp, png):
        try: os.remove(x)
        except OSError: pass
    text = f"{SERIES.title()} No. {no}\n\n{l1}{(' ' + l2) if l2 else ''}\n\n{cap}\n\nNot investment advice.\n\n{TAGS}"
    now = dt.datetime.now(dt.timezone.utc); stamp = now.strftime('%Y%m%d%H%M%S')
    log.append(dict(no=no, date=now.date().isoformat(), line1=l1, line2=l2, caption=cap, topic=note.get('topic', ''), sources=note.get('sources', [])))
    json.dump(log, open(log_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if '--no-feed' not in sys.argv:
        write_feed([(f"note-{no}-{stamp}", f"Note {no}", text, f, stamp)])
    print('OK', f, '| caption:', len(text), 'chars'); print('PREVIEW /tmp/jln_note_preview.png')


def write_feed(items, name='posts.xml', title='Posts'):
    """items: (guid, title, text, image path, stamp). Replaces the feed file: posts.xml for the 'JLN Posts' autolist
    (notes) or weekly.xml for the 'JLN Weekly' autolist."""
    now = dt.datetime.now(dt.timezone.utc); out = ''
    for i, (guid, title, text, f, stamp) in enumerate(items):
        size = os.path.getsize(os.path.join(ROOT, f)); d = email.utils.format_datetime(now - dt.timedelta(seconds=i))
        out += f'<item><title>{html.escape(title)}</title><link></link><guid isPermaLink="false">jln-{guid}</guid><pubDate>{d}</pubDate><description><![CDATA[{text}]]></description><enclosure url="{r.BASE}/{f}?v={stamp}" type="image/jpeg" length="{size}"/><media:content url="{r.BASE}/{f}?v={stamp}" medium="image" type="image/jpeg"/></item>\n'
    open(os.path.join(ROOT, name), 'w', encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>JLN Capital · {title}</title><link>{r.BASE}/</link><description>JLN Capital posts</description><language>en</language><atom:link href="{r.BASE}/{name}" rel="self" type="application/rss+xml"/>
{out}</channel></rss>
''')


if __name__ == '__main__':
    main()
