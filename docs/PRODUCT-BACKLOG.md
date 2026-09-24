# Saturday Lab product backlog

This document collects requested site changes before the next grouped implementation pass. Adding an item here does not change the production website.

## Workflow

1. Record each idea with its user-facing problem and desired behavior.
2. Keep related ideas together so navigation, data and responsive behavior can be designed as one system.
3. Do not implement or publish backlog items until the user asks to begin the batch.
4. Before implementation, check data availability, affected routes, mobile behavior and interactions with the production v6 model.
5. After implementation, verify locally, run model and build checks, publish, and mark completed items with the release commit.

## Pending requests

### Completed-game scoring by period

- Status: Recorded; defer until the next grouped game-page rebuild
- Priority: High
- Area: Games / Data / Mobile
- User problem: A completed game currently jumps from the matchup header to summary facts and aggregate box-score statistics. It does not show how the score developed by quarter.
- Desired behavior: Add an ESPN-style scoring summary near the top of every completed-game page. Show both teams as rows and Q1, Q2, Q3, Q4 and final score as columns. Support overtime periods when the source provides them. Place this above the broader team box score because it is a primary game fact.
- Data needed: Period-by-period scoring is not part of the current normalized `box-YYYY.json` team-stat rows. Investigate the ESPN/SportsDataverse event or summary source, archive the source provenance, normalize regulation and overtime periods, and preserve missing periods as unavailable rather than zero unless the source explicitly reports zero.
- Routes affected: Every completed `/games/{season}/{game}/` page for 2018–2026.
- Acceptance checks: Quarter totals add to the published final score; overtime games label every available overtime period; abandoned, shortened or incomplete records do not fabricate quarters; table remains readable on mobile; non-available period data has a clear fallback.
- Notes and dependencies: Implement in one batch because adding the normalized period-score dataset changes thousands of generated game pages.

### Cross-season recent meetings

- Status: Recorded; defer until the next grouped game-page rebuild
- Priority: Medium
- Area: Games / Navigation / Historical data
- User problem: “Recent meetings in the archive” currently searches only the selected season, when most college teams play each other only once per year. The section is therefore usually empty.
- Desired behavior: Search across the previous three to four seasons and show the latest meetings between the same two programs. Each meeting should include season, date, site, final score and winner. Selecting a meeting opens that historical game’s permanent Saturday Lab game-center URL.
- Data needed: Reuse the existing 2018–2026 game catalog. Match teams by stable ESPN team IDs, not display names, so renamed teams still connect correctly.
- Routes affected: All `/games/{season}/{game}/` pages and their static generation data.
- Acceptance checks: Current game is excluded; meetings are ordered newest first; both home/away orientations match; each listed result links to the correct permanent game route; no same-season-only wording remains; mobile links remain easy to select.
- Notes and dependencies: Default window should be the current season plus the previous four seasons, capped to a small number of meetings. Final window and cap can be chosen during the grouped design pass.

<!--
Use this format for new entries:

### Short title

- Status: Recorded
- Area: Rankings / Teams / Games / Matchup / Trends / Model / Navigation / Mobile / Data
- User problem:
- Desired behavior:
- Data needed:
- Routes affected:
- Acceptance checks:
- Notes and dependencies:
-->

## Completed batches

### Permanent route system and game archive

- Status: Published
- Source commit: `fba682f`
- Pages artifact: `1b1cb01ddd337a331965f4cc5fefaad363020218`
- Added permanent team, game, matchup, trend, model, methodology and legal routes.

### Team finder and richer game centers

- Status: Published
- Source commit: `77744a3`
- Pages artifact: `6a758bf34d0a08b1475e37e6728fa8ca3fb999e6`
- Added the team directory, one-decimal game probabilities, full-row schedule navigation, expanded completed-game box scores and broader future-game comparisons.
