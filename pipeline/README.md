# JLN Capital daily pipeline

Turns the JLN-DAILY e-mail report into Instagram story images and updates the feed that the Metricool autolist "JLN Daily" reads.

## Run

1. Save the body text of the report e-mail(s) for the day to a file, all parts in order (`part=1/N`, `part=2/N`, ...), copied exactly.
   For each `[CANDLES]` block only ONE timeframe is needed: the smallest of M1/M5/M15 whose rows count is 110 or fewer
   (if none, the largest timeframe). The other timeframe sections of that block may be left out.
2. `python3 pipeline/render.py /path/to/report.txt`
   - `OK ...` : images written to `daily/YYYY-MM-DD/`, `pipeline/history.json` and `feed.xml` updated. Look at `/tmp/jln_daily_preview.png`.
   - `NO_TRADES` : nothing to publish, nothing changed.
   - `VALIDATION FAILED` (exit 2) : nothing changed. Do not publish. Report the listed reasons.
   - `REFUSED: test report` (exit 3) : the e-mail has `test=1`; only use `--allow-test` when explicitly asked to run a test.
3. Commit and push to `main`. GitHub Pages serves `feed.xml`; Metricool picks up new items within about 10 minutes and the
   autolist publishes them as stories, one per scheduled minute, in feed order (cover first).

Requirements: Python 3 with `playwright` (Chromium) and `Pillow`. Fonts are in `pipeline/fonts`.

## Files

- `render.py` : parser, validation, charts, pages, feed.
- `config.json` : `test_magics` = magic numbers of test strategies (hidden from charts, still counted in results).
- `history.json` : daily result in percent since inception, used for MTD/YTD.

## Weekly, monthly and notes

- `weekly.py` : weekly statement post (WEEKLY CHANGE with a small MTD / YTD line) -> `weekly.xml` ('JLN Weekly' autolist), plus two
  story frames appended to `feed.xml`. Run on Fridays by the daily job. `--post-only` renders only the image (backfill).
- `monthly.py` : monthly statement post (month, MONTHLY CHANGE, YTD line, building) -> `posts.xml` ('JLN Posts' autolist).
  Run by the notes job on its first run of a month, in place of that day's note, when `monthly/YYYY-MM/post.jpg` of the
  previous month does not exist yet.
- `note.py` + `NOTES.md` : the notes series -> `posts.xml`.
