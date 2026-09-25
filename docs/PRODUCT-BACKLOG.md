# Saturday Lab product backlog

This document collects requested site changes before the next grouped implementation pass. Adding an item here does not change the production website.

## Workflow

1. Record each idea with its user-facing problem and desired behavior.
2. Keep related ideas together so navigation, data and responsive behavior can be designed as one system.
3. Do not implement or publish backlog items until the user asks to begin the batch.
4. Before implementation, check data availability, affected routes, mobile behavior and interactions with the production v6 model.
5. After implementation, verify locally, run model and build checks, publish, and mark completed items with the release commit.

## Request ledger

### Completed-game box-score contrast

- Status: Recorded; include in the next grouped front-end pass
- Priority: High
- Area: Games / Accessibility / Visual design / Mobile
- User problem: In the completed-game “Scoring by quarter” table, team names are rendered with dark text on a dark navy background and are effectively invisible. The column labels are also too muted against the same background, so readers have to strain to identify the teams and periods.
- Desired behavior: Restore clear, restrained contrast for every label in the scoring table. Team names should use a light foreground with normal or medium emphasis; column headings should be brighter than the current muted blue-gray while remaining visually secondary to the scores. Preserve the existing sports-site palette rather than introducing loud accent colors.
- Scope: Audit the period-score table in light and responsive layouts, including team names, Q1–Q4, overtime labels and FINAL. Check the related completed-game tables for the same foreground/background token mismatch instead of fixing only the captured example.
- Routes affected: Every completed `/games/{season}/{game}/` page.
- Acceptance checks: Both team names are immediately legible; all period headings meet WCAG AA contrast for normal text; the winner/final emphasis still has a clear hierarchy; long team names wrap or truncate gracefully; mobile and desktop use the same readable treatment.

### Reader-facing copy restraint pass

- Status: Recorded; include in the next grouped front-end pass
- Priority: Medium
- Area: Site-wide content / Games / Teams / Rankings / Trends / Matchup / Mobile
- User problem: Several public-facing pages add explanatory sentences that repeat what a heading already says without adding context. This makes data pages feel busier and more self-conscious than a finished sports product.
- Desired behavior: Review ordinary reader-facing routes and remove or tighten copy that provides no new information. Prefer short, familiar labels: for example, consider “Score” in place of “Scoring by quarter,” remove “How the final score developed,” and remove “What each side produced in this game. Source totals and clearly labeled calculated rates.” when the surrounding heading and table already communicate that information.
- Editorial rule: Keep all data, technical definitions, source attribution, caveats, missing-data behavior and explanations that help a reader interpret a metric. Keep useful implementation notes such as how play volume, possession and missing values are calculated. Do not trim the Methodology page merely because its explanations are long; detailed explanation is that page’s purpose. Do not delete broadly or chase minimalism—the pass should target only sentences and labels that add no meaning.
- Review scope: The implementer is responsible for inspecting home/rankings, team reports, scores and schedules, completed and future game centers, team finder, trends and Matchup Lab, then making the editorial decision for each piece of copy in its page context. The user is not expected to review or approve sentences one by one. Evaluate the edited pages on desktop and mobile rather than using a global text search-and-delete rule.
- Acceptance checks: Every remaining subtitle or helper sentence answers a real reader question; headings remain understandable without redundant prose; technical and provenance information remains intact; Methodology retains its full explanatory role; no page becomes ambiguous after copy is shortened.

### Context-aware back navigation on game pages

- Status: Recorded; include in the next grouped front-end pass
- Priority: Medium
- Area: Games / Navigation / Teams / Scores / Mobile
- User problem: A reader can open a permanent game center from a team schedule, completed results, the scores page or a previous-meetings link, but the game page has no clear way to return to the exact place they came from. This interrupts browsing through one team’s season or a chain of historical meetings.
- Desired behavior: Add a compact back control at the upper-left of every game page, above or beside the season/week line. Its label should describe the actual destination when known, such as “Back to Notre Dame,” “Back to scores,” or “Back to Wisconsin vs. Notre Dame.”
- Navigation logic: Prefer the real same-tab browser history entry so filters, scroll position and client-side state can be restored. Internal game links should also record a safe same-origin return path and human-readable label for new-tab navigation or cases where browser history is unavailable. A directly opened or externally linked game page falls back to `/games/` with “Back to scores & schedule.” Never accept an external or unvalidated return URL.
- Source contexts to preserve: Team upcoming-games and results views return to that team; scores and schedule returns to the selected week or recent-results view; previous-meetings links return to the game page that contained the link; other internal game links return to their immediate Saturday Lab source.
- Visual treatment: Use a quiet left-arrow text control rather than another large card or primary button. Keep it visible above the game hero, keyboard accessible and large enough to tap on mobile.
- Routes affected: Every `/games/{season}/{game}/` page plus each internal component that links to a game center.
- Acceptance checks: Same-tab return restores the correct origin; team A and team B links return to their respective team pages; previous-meeting chains return one step at a time; score-page filters survive when possible; direct entry has a useful fallback; repeated forward/back navigation does not loop; open-in-new-tab remains useful; malicious or external return values are rejected.
- Notes and dependencies: During implementation, consider making team report sections and score-page filters URL-backed so the return path can restore “Upcoming games,” “Results,” a selected week or “Latest results” reliably after a reload.

### Completed-game scoring by period

- Status: Published
- Source commit: `53dfd4d`
- Pages artifact: `2dcad875d6bdecd306610c8ca41fd56083961ef0`
- Priority: High
- Area: Games / Data / Mobile
- User problem: A completed game currently jumps from the matchup header to summary facts and aggregate box-score statistics. It does not show how the score developed by quarter.
- Desired behavior: Add an ESPN-style scoring summary near the top of every completed-game page. Show both teams as rows and Q1, Q2, Q3, Q4 and final score as columns. Support overtime periods when the source provides them. Place this above the broader team box score because it is a primary game fact.
- Data needed: Period-by-period scoring is not part of the current normalized `box-YYYY.json` team-stat rows. Investigate the ESPN/SportsDataverse event or summary source, archive the source provenance, normalize regulation and overtime periods, and preserve missing periods as unavailable rather than zero unless the source explicitly reports zero.
- Routes affected: Every completed `/games/{season}/{game}/` page for 2018–2026.
- Acceptance checks: Quarter totals add to the published final score; overtime games label every available overtime period; abandoned, shortened or incomplete records do not fabricate quarters; table remains readable on mobile; non-available period data has a clear fallback.
- Delivery: Published validated period scores for all 7,146 completed archive games from 2018–2026. All period totals match the stored final score; 282 overtime games retain their extra periods. Missing-source fallback remains in the interface even though the current archive has complete coverage.

### Cross-season recent meetings

- Status: Published
- Source commit: `53dfd4d`
- Pages artifact: `2dcad875d6bdecd306610c8ca41fd56083961ef0`
- Priority: Medium
- Area: Games / Navigation / Historical data
- User problem: “Recent meetings in the archive” currently searches only the selected season, when most college teams play each other only once per year. The section is therefore usually empty.
- Desired behavior: Search across the previous three to four seasons and show the latest meetings between the same two programs. Each meeting should include season, date, site, final score and winner. Selecting a meeting opens that historical game’s permanent Saturday Lab game-center URL.
- Data needed: Reuse the existing 2018–2026 game catalog. Match teams by stable ESPN team IDs, not display names, so renamed teams still connect correctly.
- Routes affected: All `/games/{season}/{game}/` pages and their static generation data.
- Acceptance checks: Current game is excluded; meetings are ordered newest first; both home/away orientations match; each listed result links to the correct permanent game route; no same-season-only wording remains; mobile links remain easy to select.
- Delivery: Each game now searches its season plus the previous four, only before the selected game date, matches by stable ESPN team IDs and links the four latest meetings to their permanent game centers.

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

### Reader-first scores and game archive

- Status: Published
- Source commit: `53dfd4d`
- Pages artifact: `2dcad875d6bdecd306610c8ca41fd56083961ef0`
- Added a scores and schedule center, complete period scoring, linked five-season meeting history, a more direct team-report opening, a full navigation footer and clearer game facts.

### Context-aware Matchup Lab defaults

- Status: Published
- Source commit: `3b9f2c3`
- Pages artifact: `01011afbeefcd814270a067057239c8308f64e43`
- Direct visits feature the current top two, team-page links leave the opponent open and completed user selections persist locally.

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
