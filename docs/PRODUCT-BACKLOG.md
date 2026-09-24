# Saturday Lab product backlog

This document collects requested site changes before the next grouped implementation pass. Adding an item here does not change the production website.

## Workflow

1. Record each idea with its user-facing problem and desired behavior.
2. Keep related ideas together so navigation, data and responsive behavior can be designed as one system.
3. Do not implement or publish backlog items until the user asks to begin the batch.
4. Before implementation, check data availability, affected routes, mobile behavior and interactions with the production v6 model.
5. After implementation, verify locally, run model and build checks, publish, and mark completed items with the release commit.

## Pending requests

No unimplemented requests have been recorded yet.

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
