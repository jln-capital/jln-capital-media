# JLN Capital · Notes series

Short posts (one image, 1080×1350) on trading, markets, mathematics, statistics and trading philosophy.
Published without human review by the Metricool autolist "JLN Posts", which reads `posts.xml`.
One note per run. Skipping a run is always better than publishing a doubtful note.

## Voice

English. A discreet private trading firm: calm, precise, impersonal, no hype. Own words (except in the `quote` format).

## Hard rules (no exceptions)

- Every fact, date, figure and formula must be TRUE and checked in at least two reliable sources that agree
  (textbooks, academic papers, university material, exchange / index-provider / central-bank pages, established reference works).
  Not forums, not sales pages, not quote-collection sites. Compute every number yourself as well.
- No investment advice and no instructions to the reader ("you should", "buy", "sell"). No predictions or opinions on any
  asset or market direction. No promises or hints about returns.
- Nothing about JLN Capital itself: not its results, strategies, systems, markets, set-up or people.
- No politics, no current news, no jokes, no exclamation marks, no emojis, no hashtags or links in the texts.
- Real people, firms and books may be named ONLY in the formats `quote` and `history`, and in topics "classic papers"
  and "word origins", and only for verified facts. Never put words in anyone's mouth. Never criticise a living person or a firm.
- `quote` format: only a quotation whose exact wording you have found in its PRIMARY source (the author's own book, letter,
  paper, speech transcript or recorded interview) or in a reliable source that cites that primary source precisely.
  At most 35 words, copied exactly, with the author and the source and year shown. If the wording differs between
  sources, or you only find it on quote sites or social media, it is NOT verified: use another format instead.
- Never repeat or closely paraphrase a note in `notes/log.json`.

## Rotation

Read `notes/log.json` (it may not exist yet). For the new note:
- the format must differ from the formats of the last 4 notes; prefer the formats used least so far;
- the topic area must differ from the topic areas of the last 2 notes; prefer the areas used least so far;
- mix lengths: short notes (statement, number, question, myth) and longer ones (long, list, comparison, definition).

## Topic areas

1. **Risk and position sizing** — risk per trade, risk of ruin versus size, drawdown depth and duration, leverage arithmetic.
2. **Probability and statistics** — sample size, variance, expectancy, distributions and fat tails, regression to the mean,
   base rates, law of large numbers, correlation versus causation.
3. **Mathematics of returns** — compounding, drawdown recovery, volatility drag, geometric versus arithmetic mean, Kelly criterion, Sharpe ratio.
4. **Research method** — overfitting, out-of-sample testing, data snooping, survivorship bias, look-ahead bias, transaction costs.
5. **How markets work** — anatomy of an order, bid/ask spread and slippage, order types, the trading sessions of the day and
   their overlaps, what an index measures and how it is weighted, the cost of trading and its effect on expectancy.
6. **Market history** — episodes with their figure (1929, 1987, 2000, 2008, the 2010 flash crash, March 2020 and others),
   "on this day" anniversaries (only when the exact date is verified), long-run facts about indices.
7. **Classic papers and ideas** — the central idea of a founding work in two sentences, with author and year
   (diversification, Kelly, option pricing, efficient markets, prospect theory and others).
8. **Word origins** — where market words come from (bull, bear, blue chip, spread, hedge, margin ...), only when the
   etymology is well documented; if sources disagree, say that the origin is uncertain or choose another word.
9. **Long-run data** — share of positive years of an index, typical length of declines, clustering of best and worst days,
   depth versus duration of drawdowns. State the index, the period and the source in the caption.
10. **Behaviour and psychology** — one bias per note (loss aversion, gambler's fallacy, hindsight bias, recency, anchoring,
    confirmation, disposition effect, overconfidence, sunk cost).
11. **Probability puzzles** — Monty Hall, birthday paradox, streaks in coin flips, St Petersburg, base-rate puzzles.
    Usually in the `question` format with the full answer in the caption.
12. **Systematic trading philosophy** — process over outcome, rules versus discretion, discipline, simplicity.

## NOTE.json

Common fields for every format:

```
"format":  one of the 15 formats below
"caption": 120-900 characters, 3-5 sober sentences that explain the idea (for `question`: the full answer).
           Plain text: no hashtags, no links, no line breaks. For topics 6 and 9 name the index, period and source.
"topic":   "area / subject", e.g. "statistics / sample size"
"sources": ["url", ...] the pages you checked
```

Keep texts short; the renderer shrinks content slightly if needed and refuses (VALIDATION FAILED) when it cannot fit.
Use the real minus sign "−" for negative numbers and "×" for multiplication.

| format | fields (limits in characters) |
|---|---|
| `statement` | `line1` (10-110), `line2` optional grey (≤80) |
| `quote` | `quote` (≤35 words, exact), `author`, `source` (e.g. "The Intelligent Investor, 1949") |
| `number` | `label` (≤60), `number` (≤12, e.g. "100%"), `line1` (≤90), `line2` optional |
| `formula` | `label` (≤40), `formula` (≤60; `_x` makes a subscript: `P_win`), `line1` (≤80), `line2` optional |
| `table` | `head` [left, right], `rows` 3-7 × [left, right] (each ≤16), `line1` optional |
| `chart` | `label` (≤60), `series` (see below), `baseline` number or null, `axis` true/false, `line1` (≤70), `line2` optional |
| `definition` | `term` (≤34), `kind` (e.g. "Noun · Statistics"), `text` (30-200), `line2` optional |
| `long` | `label` (≤40), `paragraphs` 1-3 texts, 120-460 characters in total |
| `comparison` | `left` {`head`, `items` 3-4 (each ≤26)}, `right` {same number of items}, `line1` optional |
| `question` | `question` (15-130, ends with "?"); the answer goes in `caption` |
| `arithmetic` | `steps` 2-4 × [label (≤26), value (≤9)], `result` [label, value], `line1` (≤60), `line2` optional |
| `matrix` | `cols` [a, b], `rows` [a, b] (each ≤18), `cells` 4 × [title (≤14), subtitle (≤20)] in reading order, `line1` (≤70), `line2` optional |
| `history` | `date` (e.g. "19 October 1987"), `number` (≤12), `text` (10-110), `line2` optional |
| `myth` | `myth` (10-90), `fact` (10-120) |
| `list` | `label` (≤44), `items` 3-5 (each 8-62) |

### chart

`series` is a list of 1-30 lines: `{"points": [[x, y], ...], "style": "main" | "muted" | "dashed", "label": "optional legend text"}`
with 2-600 points each. `main` is the black line, `muted` thin grey lines (e.g. many simulated paths), `dashed` a grey
reference curve. `baseline` draws a dotted horizontal line at that y (e.g. 0); `axis: true` draws the bottom line.
The chart has no axis numbers, so it must show a SHAPE, not values to be read: simulated equity paths, a distribution
against the normal curve, compounding curves, drawdown and recovery, risk of ruin against position size.
Generate the points with a short Python script (fixed random seed for simulations; exact formulas for curves) and
make sure the picture really shows what the sentence says. Never draw real market prices or anything presented as real data.

## Run

```
python3 pipeline/note.py /tmp/note.json --dry-run   # renders /tmp/jln_note_preview.png only
python3 pipeline/note.py /tmp/note.json             # writes notes/NNN.jpg, notes/log.json and posts.xml
```

Always dry-run first and LOOK at the preview: everything visible, nothing cut, balanced, no single word alone on the
last line when it can be avoided. Then re-read every text once more against the hard rules before the real run.
