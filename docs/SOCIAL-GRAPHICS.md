# Saturday Lab social graphics

The social graphics generator turns the same published rankings, predictions and results used by the site into deterministic 1080 × 1350 Instagram carousels. It supports a pregame **Weekly Preview** and a postgame **Monday Recap**. It is a presentation layer: it does not fit the model, modify rankings, recalculate archived forecasts, publish the website, or call an AI service.

## Data ownership

The generator reads the existing product contract directly:

- `public/data/manifest.json` selects the latest season when `--season` is omitted.
- `public/data/<season>.json` supplies weekly ranking snapshots, team names, colors, logos, model ranks and archived predictions.
- `public/data/live-<season>.json` supplies the current season's frozen pregame probability and current status.
- `public/data/fixtures.json` supplies the complete current-season schedule.

For a current-season game, the frozen live-feed pregame record is the probability source. For an older season, the archived season prediction is used. The generator never substitutes a newly calculated probability for a published one. Games without an FBS prediction are omitted.

By default, live or completed games are removed when at least one pregame matchup remains. This keeps a midweek rerun useful for promotion. `--include-started` produces an archival board that may include them. If a historical week contains only completed games, the generator automatically uses those games.

## Automatic selection

Every eligible game receives an explainable interest score:

- 53% ranking quality, with rapidly diminishing value farther down the FBS table;
- 34% projected closeness;
- explicit bonuses for ranked-versus-ranked, Top 10 and Top 5 matchups.

This makes an elite matchup win even when the model sees a meaningful favorite, while a close game between low-ranked teams does not displace a national game. Upset Watch is scored separately from the lower-ranked team's win probability, matchup quality, closeness and ranking gap. Exact component values and selected games are saved to `manifest.json` with every run.

The system normally chooses four individual featured slides, one Upset Watch when a candidate clears the threshold, six compact More Predictions entries, an opening board and a closing website card. The count changes naturally if a week has less data.

## Local use

```sh
npm ci
npm run social:generate -- 2026 6
```

The long-form equivalent is:

```sh
node scripts/social/generate.mjs --season 2026 --week 6
```

After Week 6 is complete and the next weekly ranking snapshot has been published, generate the seven-slide recap with:

```sh
npm run social:recap -- 2026 6
```

The Monday Recap contains the new Top 25, four important final scores with HIT/MISS labels, the complete weekly model scorecard, Upset of the Week, ranking movers, six weekend statistics and the next-week preview. Its scorecard evaluates every completed FBS prediction in the chosen week. Rankings compare the snapshot available before that week with the next published snapshot; old probabilities remain frozen.

Preview PNG files, a contact sheet and the audit manifest are written to `outputs/social/2026-week-6/`; recaps use `outputs/social/2026-week-6-recap/`. Both directories are intentionally ignored by Git.

Optional controls:

```sh
node scripts/social/generate.mjs \
  --season 2026 \
  --week 6 \
  --featured 401000001,401000002 \
  --upset 401000003 \
  --featured-count 4 \
  --other-count 6 \
  --output outputs/social/custom \
  --keep-svg
```

An override only changes which published games appear. It cannot override a probability, rank, team identity or model version.

## GitHub Actions

Open **Actions → Generate social graphics → Run workflow**, choose `weekly-preview` or `monday-recap`, then enter season and week. For a recap, `week` means the week that just finished. The read-only workflow installs the locked dependencies, renders the carousel, checks the 1080 × 1350 output, and uploads a 30-day artifact. It does not commit or deploy anything.

## Template architecture

- `scripts/social/data.mjs` joins the existing published data and enforces forecast source rules.
- `scripts/social/select.mjs` contains deterministic selection and Upset Watch scoring.
- `scripts/social/templates.mjs` contains reusable SVG slide templates and visual tokens.
- `scripts/social/render.mjs` caches public team logos locally and uses Sharp to rasterize SVG to PNG.
- `scripts/social/generate.mjs` is the CLI and carousel orchestrator.
- `scripts/social/recap-data.mjs`, `recap-templates.mjs` and `generate-recap.mjs` build the postgame edition without changing the pregame generator.
- `scripts/social/test-social.mjs` protects probability parity, deterministic overrides and output dimensions.
- `scripts/social/assets/` contains bundled OFL-licensed Barlow font files so local and CI typography match.

Add a new slide type as a pure SVG template, then register it in `generate.mjs`. Keep data selection outside the template so future formats can reuse the same audited weekly board.

