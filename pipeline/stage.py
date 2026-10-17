"""Two-batch stories feed, so the cover is always the first story.

When the whole day lands in feed.xml at once, Metricool's "JLN Daily" autolist does not keep the feed order (the cover has
come out second). So the cover goes out alone first and the rest of the stories follow in a second push:

  split    after render.py (and weekly.py on Fridays): feed.xml keeps only the cover, every other item moves to
           pipeline/feed_pending.xml. Commit and push.
  wait     sleeps (at most 9 minutes per call) until the release is allowed; prints READY or WAIT <seconds>.
  release  allowed from 22:02 Madrid and at least 12 minutes after split: puts the pending items back into feed.xml
           after the cover, with fresh pubDates (one minute apart, in order), and deletes the pending file.
           Commit and push again.
"""
import datetime as dt, email.utils, os, re, sys, time, zoneinfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, 'feed.xml')
PENDING = os.path.join(ROOT, 'pipeline', 'feed_pending.xml')
MAD = zoneinfo.ZoneInfo('Europe/Madrid')
RELEASE_AT = dt.time(22, 2)
MIN_GAP = dt.timedelta(minutes=12)


def items_of(text):
    return re.findall(r'<item>.*?</item>', text, flags=re.S)


def write_feed(head, items):
    open(FEED, 'w', encoding='utf-8').write(head + '\n' + '\n'.join(items) + '\n</channel></rss>\n')


def feed_head(text):
    return text.split('<item>')[0].split('</channel>')[0].rstrip()


def read_pending():
    if not os.path.exists(PENDING):
        return None
    t = open(PENDING, encoding='utf-8').read()
    day = re.search(r'<!-- day=(\S+) split=(\S+) -->', t)
    return day.group(1), dt.datetime.fromisoformat(day.group(2)), items_of(t)


def release_time(split_at):
    now = dt.datetime.now(MAD)
    return max(dt.datetime.combine(now.date(), RELEASE_AT, MAD), split_at.astimezone(MAD) + MIN_GAP)


def split():
    feed = open(FEED, encoding='utf-8').read(); its = items_of(feed)
    if not its or not re.search(r'<title>Daily \S+ 1/\d+</title>', its[0]):
        print('NOTHING: feed.xml does not start with a daily cover'); return
    if len(its) == 1:
        print('NOTHING: only the cover'); return
    now = dt.datetime.now(MAD).replace(microsecond=0)
    write_feed(feed_head(feed), its[:1])
    open(PENDING, 'w', encoding='utf-8').write(f'<!-- day={now.date().isoformat()} split={now.isoformat()} -->\n' + '\n'.join(its[1:]) + '\n')
    print(f'SPLIT cover alone in feed.xml, {len(its) - 1} items pending; release from {release_time(now).strftime("%H:%M")} Madrid')


def wait():
    p = read_pending()
    if not p:
        print('NOTHING: no pending items'); return
    left = (release_time(p[1]) - dt.datetime.now(MAD)).total_seconds()
    if left > 0:
        time.sleep(min(left + 2, 540)); left = (release_time(p[1]) - dt.datetime.now(MAD)).total_seconds()
    print('READY' if left <= 0 else f'WAIT {int(left)}')


def release():
    p = read_pending()
    if not p:
        print('NOTHING: no pending items'); return
    day, split_at, pend = p
    now = dt.datetime.now(MAD)
    if day != now.date().isoformat():
        os.remove(PENDING); print(f'DISCARDED stale pending items from {day}'); return
    if now < release_time(split_at) and '--now' not in sys.argv:
        print(f'TOO EARLY: release from {release_time(split_at).strftime("%H:%M:%S")} Madrid'); sys.exit(4)
    feed = open(FEED, encoding='utf-8').read(); its = items_of(feed)
    base = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    out = []
    for i, it in enumerate(pend):  # first pending item newest, one minute apart (Metricool compares to the minute)
        d = email.utils.format_datetime(base - dt.timedelta(minutes=i))
        out.append(re.sub(r'<pubDate>.*?</pubDate>', f'<pubDate>{d}</pubDate>', it))
    write_feed(feed_head(feed), its + out)
    os.remove(PENDING)
    print(f'RELEASED {len(out)} items')


if __name__ == '__main__':
    {'split': split, 'wait': wait, 'release': release}[sys.argv[1] if len(sys.argv) > 1 else '']()
