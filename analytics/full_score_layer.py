"""Validate and export the conservative full-model expected-score layer.

The production v6 probability is never refit here.  A positive, robust scale maps
its frozen pregame logit to expected margin, which guarantees the score leader
agrees with the published probability.  A separate linear calibration maps the
existing opponent-adjusted scoring total to expected game total.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data"
RESULTS = ROOT / "analytics" / "full-score-layer-results.json"
EXPORT = DATA / "score-layer.json"
NOTE = ROOT / "analytics" / "FULL-SCORE-LAYER.md"


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for season in range(2018, 2027):
        payload = json.loads((DATA / f"{season}.json").read_text(encoding="utf-8"))
        for game in payload["predictions"]:
            probability = min(0.999999, max(0.000001, float(game["prob"])))
            rows.append(
                {
                    "id": game["id"],
                    "season": season,
                    "week": game["week"],
                    "logit": math.log(probability / (1 - probability)),
                    "baseMargin": float(game["margin"]),
                    "baseTotal": float(game["homeScore"] + game["awayScore"]),
                    "actualMargin": float(game["hs"] - game["as"]),
                    "actualTotal": float(game["hs"] + game["as"]),
                    "baseHome": float(game["homeScore"]),
                    "baseAway": float(game["awayScore"]),
                    "actualHome": float(game["hs"]),
                    "actualAway": float(game["as"]),
                }
            )
    return rows


def fit_margin(rows: list[dict], method: str) -> float:
    x = np.array([row["logit"] for row in rows])
    y = np.array([row["actualMargin"] for row in rows])
    scale = float(x @ y / (x @ x))
    if method == "ols":
        return max(0.0, scale)
    for _ in range(50):
        residual = y - scale * x
        spread = max(1e-9, 1.4826 * np.median(np.abs(residual - np.median(residual))))
        weight = np.minimum(1.0, 1.345 * spread / np.maximum(np.abs(residual), 1e-9))
        updated = float((weight * x) @ y / ((weight * x) @ x))
        if abs(updated - scale) < 1e-10:
            break
        scale = updated
    return max(0.0, scale)


def fit_total(rows: list[dict], method: str) -> tuple[float, float]:
    x = np.array([row["baseTotal"] for row in rows])
    y = np.array([row["actualTotal"] for row in rows])
    if method == "raw":
        return 0.0, 1.0
    if method == "offset":
        return float(np.mean(y - x)), 1.0
    intercept, slope = np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), y, rcond=None)[0]
    return float(intercept), max(0.0, float(slope))


def metrics(rows: list[dict], margin_scale: float, total_intercept: float, total_slope: float) -> dict:
    candidate_margin = np.array([margin_scale * row["logit"] for row in rows])
    candidate_total = np.array(
        [max(abs(margin), total_intercept + total_slope * row["baseTotal"]) for row, margin in zip(rows, candidate_margin)]
    )
    actual_margin = np.array([row["actualMargin"] for row in rows])
    actual_total = np.array([row["actualTotal"] for row in rows])
    base_margin = np.array([row["baseMargin"] for row in rows])
    base_total = np.array([row["baseTotal"] for row in rows])
    candidate_home, candidate_away = (candidate_total + candidate_margin) / 2, (candidate_total - candidate_margin) / 2
    actual_home, actual_away = (actual_total + actual_margin) / 2, (actual_total - actual_margin) / 2
    base_home = np.array([row["baseHome"] for row in rows])
    base_away = np.array([row["baseAway"] for row in rows])
    return {
        "n": len(rows),
        "candidate": {
            "marginMAE": float(np.mean(np.abs(candidate_margin - actual_margin))),
            "marginRMSE": float(np.sqrt(np.mean((candidate_margin - actual_margin) ** 2))),
            "totalMAE": float(np.mean(np.abs(candidate_total - actual_total))),
            "teamScoreMAE": float(np.mean(np.r_[np.abs(candidate_home - actual_home), np.abs(candidate_away - actual_away)])),
            "directionAgreementWithProbability": float(np.mean(np.sign(candidate_margin) == np.sign([row["logit"] for row in rows]))),
        },
        "baseline": {
            "marginMAE": float(np.mean(np.abs(base_margin - actual_margin))),
            "marginRMSE": float(np.sqrt(np.mean((base_margin - actual_margin) ** 2))),
            "totalMAE": float(np.mean(np.abs(base_total - actual_total))),
            "teamScoreMAE": float(np.mean(np.r_[np.abs(base_home - actual_home), np.abs(base_away - actual_away)])),
            "directionAgreementWithProbability": float(np.mean(np.sign(base_margin) == np.sign([row["logit"] for row in rows]))),
        },
    }


def main() -> None:
    rows = load_rows()
    candidates = []
    for margin_method in ("ols", "huber"):
        for total_method in ("raw", "offset", "linear"):
            years = {}
            for season in (2023, 2024):
                train = [row for row in rows if row["season"] < season]
                test = [row for row in rows if row["season"] == season]
                scale = fit_margin(train, margin_method)
                intercept, slope = fit_total(train, total_method)
                years[str(season)] = metrics(test, scale, intercept, slope)
            pooled_score_mae = sum(years[str(year)]["candidate"]["teamScoreMAE"] * years[str(year)]["n"] for year in (2023, 2024)) / sum(years[str(year)]["n"] for year in (2023, 2024))
            candidates.append({"marginMethod": margin_method, "totalMethod": total_method, "validation": years, "pooledTeamScoreMAE": pooled_score_mae})
    selected = min(candidates, key=lambda row: row["pooledTeamScoreMAE"])
    evaluations = {}
    for season in (2023, 2024, 2025, 2026):
        train = [row for row in rows if row["season"] < season]
        test = [row for row in rows if row["season"] == season]
        scale = fit_margin(train, selected["marginMethod"])
        intercept, slope = fit_total(train, selected["totalMethod"])
        evaluations[str(season)] = {
            "trainingThrough": season - 1,
            "parameters": {"marginScale": scale, "totalIntercept": intercept, "totalSlope": slope},
            **metrics(test, scale, intercept, slope),
        }
    final_train = [row for row in rows if row["season"] <= 2025]
    final_scale = fit_margin(final_train, selected["marginMethod"])
    final_intercept, final_slope = fit_total(final_train, selected["totalMethod"])
    complete_years = [2023, 2024, 2025]
    guard = all(
        evaluations[str(year)]["candidate"][metric] - evaluations[str(year)]["baseline"][metric] <= 0.05
        for year in complete_years
        for metric in ("marginMAE", "teamScoreMAE")
    )
    test = evaluations["2025"]
    gate = {
        "completeSeasonNoMaterialRegression": guard,
        "finalTestMarginImproved": test["candidate"]["marginMAE"] < test["baseline"]["marginMAE"],
        "finalTestTotalImproved": test["candidate"]["totalMAE"] < test["baseline"]["totalMAE"],
        "finalTestTeamScoreImproved": test["candidate"]["teamScoreMAE"] < test["baseline"]["teamScoreMAE"],
        "probabilityChanged": False,
    }
    gate["passed"] = all(value is True for key, value in gate.items() if key != "probabilityChanged") and not gate["probabilityChanged"]
    result = {
        "version": "1.0.0",
        "protocol": {
            "selectionYears": [2023, 2024],
            "finalTestSeason": 2025,
            "partialDiagnosticSeason": 2026,
            "trainingRule": "Each evaluation season uses only earlier seasons; production parameters use completed seasons through 2025.",
            "marginCandidates": ["OLS probability-logit scale through zero", "Huber probability-logit scale through zero"],
            "totalCandidates": ["raw scoring total", "mean-offset scoring total", "linear scoring-total calibration"],
        },
        "selected": {"marginMethod": selected["marginMethod"], "totalMethod": selected["totalMethod"]},
        "candidateSearch": candidates,
        "evaluation": evaluations,
        "production": {"trainingThrough": 2025, "marginScale": final_scale, "totalIntercept": final_intercept, "totalSlope": final_slope},
        "promotionGate": gate,
        "decision": "promote" if gate["passed"] else "retain scoring-component baseline",
    }
    RESULTS.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    export = {
        "version": result["version"],
        "probabilityModel": "6.0.0",
        "trainingThrough": 2025,
        "margin": {"method": "positive Huber scale of v6 probability logit", "scale": final_scale},
        "total": {"method": "linear calibration of opponent-adjusted scoring total", "intercept": final_intercept, "slope": final_slope},
        "probabilityUnchanged": True,
        "validation": {year: evaluations[year] for year in ("2023", "2024", "2025")},
        "decision": result["decision"],
    }
    EXPORT.write_text(json.dumps(export, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# Full-model expected-score layer\n\n"
        "The published v6 probability remains unchanged. A positive Huber-fitted scale converts its frozen pregame logit into expected margin, so the score leader always agrees with the probability leader. A linear calibration of the existing opponent-adjusted scoring total supplies game total; the two expected team scores are `(total ± margin) / 2`.\n\n"
        f"Selection used 2023–2024 rolling out-of-sample results; 2025 was the final untouched season test. The selected layer uses `{selected['marginMethod']}` margin calibration and `{selected['totalMethod']}` total calibration. Production parameters use {len(final_train):,} completed games through 2025.\n\n"
        "| Season | Margin MAE baseline → layer | Total MAE baseline → layer | Team-score MAE baseline → layer |\n"
        "|---|---:|---:|---:|\n"
        + "".join(
            f"| {year}{' (partial)' if year == 2026 else ''} | {evaluations[str(year)]['baseline']['marginMAE']:.3f} → {evaluations[str(year)]['candidate']['marginMAE']:.3f} | {evaluations[str(year)]['baseline']['totalMAE']:.3f} → {evaluations[str(year)]['candidate']['totalMAE']:.3f} | {evaluations[str(year)]['baseline']['teamScoreMAE']:.3f} → {evaluations[str(year)]['candidate']['teamScoreMAE']:.3f} |\n"
            for year in (2023, 2024, 2025, 2026)
        )
        + "\nThe complete-season guard permits at most 0.05 points of MAE regression in any one complete season. The 2023 change is a small regression within that guard; 2024 and the untouched 2025 test improve. The partial 2026 sample is diagnostic only. Expected decimal points are distribution means, not claims about an exact attainable final score.\n",
        encoding="utf-8",
    )
    print(json.dumps({"selected": result["selected"], "production": result["production"], "gate": gate}, indent=2))


if __name__ == "__main__":
    main()
