"""Predeclared audit of the v6 venue coefficient.

Run from the repository root:
    python analytics/home_field_audit.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime

import numpy as np
from scipy.optimize import minimize

from pipeline import ROOT, YEARS, load_data, metrics, sigmoid
import cohort_review as cohort
import qb_review as qb
import ranking_review as r
import opponent_stability_review as opp
from stability_review import bootstrap_probability


BLUEPRINT = ROOT / "analytics/HOME-FIELD-AUDIT.md"
RESULTS = ROOT / "analytics/home-field-audit-results.json"
REPORT = ROOT / "analytics/HOME-FIELD-AUDIT-RESULTS.md"
HOME_INDEX = 15
REST_INDEX = 16
RIDGE = 1.0
INDICES = [0, 6, 8, 9, 10, 11, 12, 13, 15, 16]
FIXED = [0.15, 0.20, 0.25, 0.30]
EVALUATION_YEARS = [2023, 2024, 2025, 2026]
BUNDLE_DIAGNOSTICS = {
    "score_only": [0, 15, 16],
    "baseline": [0, 13, 15, 16],
    "stable_pair": [0, 6, 8, 13, 15, 16],
    "broad": INDICES,
}


def number(row, key):
    try:
        value = float(row[key])
        return value if math.isfinite(value) else None
    except (KeyError, TypeError, ValueError):
        return None


def rest(state, date):
    if not state["lastDate"]:
        return 7.0
    days = (
        datetime.fromisoformat(date.replace("Z", "+00:00"))
        - datetime.fromisoformat(state["lastDate"].replace("Z", "+00:00"))
    ).total_seconds() / 86400
    return max(3.0, min(21.0, days))


def build_dataset():
    """Rebuild the exact v6 broad feature matrix from frozen local inputs."""
    cohort.configure()
    r.NAMES = opp.NAMES
    r.UNIT_INDICES = list(range(9))
    teams, seasons, talents, coverage = cohort.read_inputs()

    for year in YEARS:
        rows = list(
            csv.DictReader(
                (r.DIR / f"adv_team_gamelog_{year}.csv").open(encoding="utf-8-sig")
            )
        )
        lookup = {(v["game_id"], v["team_id"]): v for v in rows}
        for game in seasons[year]["games"]:
            for i, team in enumerate([game["home"], game["away"]]):
                row = lookup.get((game["id"], team), {})
                game["units"][i].extend(
                    [
                        number(row, "first_downs_created_rate"),
                        number(row, "EPA_passing_per_play"),
                        number(row, "EPA_rushing_per_play"),
                        number(row, "yards_per_play"),
                        number(row, "EPA_explosive_rate"),
                    ]
                )

    production = json.loads((ROOT / "lib/production-config.json").read_text())
    cfg = production["selected"]["ratingConfig"]
    states = cohort.build(teams, seasons, talents, cfg)
    _, _, boxes, _ = load_data(r.SOURCE_DATA)
    passers, passer_coverage = qb.passer_states(teams, seasons, boxes)
    for key, snapshot in states.items():
        for team, state in snapshot.items():
            state["q"].extend(passers[key][team]["values"])

    games = [
        game
        for year in YEARS
        if year >= 2019
        for game in seasons[year]["games"]
        if game["fbs"]
    ]
    seasons_array = np.array([g["season"] for g in games])
    outcomes = np.array([g["hs"] > g["as"] for g in games], dtype=float)
    matrix = []
    for game in games:
        home = states[f'{game["season"]}:{game["week"]}'][game["home"]]
        away = states[f'{game["season"]}:{game["week"]}'][game["away"]]
        matrix.append(
            [
                *(np.array(home["q"]) - np.array(away["q"])),
                0.0 if game["neutral"] else 1.0,
                rest(home, game["date"]) - rest(away, game["date"]),
            ]
        )
    matrix = np.asarray(matrix)
    assert matrix.shape[1] == len(opp.NAMES)
    return games, seasons_array, outcomes, matrix, coverage, passer_coverage, production


def fit_fixed_home(x, y, indices, penalty, fixed_home):
    """Fit the original objective while holding the raw home coefficient fixed."""
    active = [i for i in indices if i != HOME_INDEX]
    a = x[:, active]
    scale = np.maximum(np.sqrt(np.mean(a * a, axis=0)), 1e-6)
    z = a / scale
    offset = fixed_home * x[:, HOME_INDEX]

    def objective(beta):
        logits = offset + z @ beta
        loss = (
            np.logaddexp(0, logits).sum()
            - y @ logits
            + penalty / 2 * (beta @ beta)
        )
        gradient = z.T @ (sigmoid(logits) - y) + penalty * beta
        return loss, gradient

    bounds = [
        (None, None) if index == REST_INDEX else (0, None) for index in active
    ]
    result = minimize(
        objective,
        np.zeros(len(active)),
        jac=True,
        method="L-BFGS-B",
        bounds=bounds,
        options={"ftol": 1e-12, "gtol": 1e-7, "maxiter": 500},
    )
    if not result.success:
        raise RuntimeError(result.message)
    coefficients = np.zeros(len(opp.NAMES))
    coefficients[active] = result.x / scale
    coefficients[HOME_INDEX] = fixed_home
    return coefficients


def loss_rows(games, outcomes, free_prob, candidate_prob, mask):
    rows = []
    for i in np.where(mask)[0]:
        actual = outcomes[i]
        p0 = np.clip(free_prob[i], 1e-9, 1 - 1e-9)
        p1 = np.clip(candidate_prob[i], 1e-9, 1 - 1e-9)
        rows.append(
            {
                "season": int(games[i]["season"]),
                "week": int(games[i]["week"]),
                "candidateLoss": float(
                    -actual * np.log(p1) - (1 - actual) * np.log(1 - p1)
                ),
                "v5Loss": float(
                    -actual * np.log(p0) - (1 - actual) * np.log(1 - p0)
                ),
            }
        )
    return rows


def slice_report(prob, outcomes, mask):
    base = metrics(prob[mask], outcomes[mask])
    if base["n"]:
        actual = float(np.mean(outcomes[mask]))
        z = 1.959963984540054
        denominator = 1 + z * z / base["n"]
        center = (actual + z * z / (2 * base["n"])) / denominator
        radius = (
            z
            * math.sqrt(
                actual * (1 - actual) / base["n"]
                + z * z / (4 * base["n"] * base["n"])
            )
            / denominator
        )
        base["actualHomeWinRate"] = actual
        base["actualHomeWinRateWilson95"] = [center - radius, center + radius]
        base["predictedHomeWinRate"] = float(np.mean(prob[mask]))
        base["calibrationError"] = float(
            base["predictedHomeWinRate"] - base["actualHomeWinRate"]
        )
    return base


def main():
    games, years, outcomes, x, coverage, passer_coverage, production = build_dataset()
    probabilities = {"free": np.full(len(games), np.nan)}
    coefficients = {"free": {}}
    for value in FIXED:
        key = f"fixed_{value:.2f}"
        probabilities[key] = np.full(len(games), np.nan)
        coefficients[key] = {}

    bundle_coefficients = {}
    for year in EVALUATION_YEARS:
        train = (years >= 2019) & (years < year)
        test = years == year
        free_coef = r.fit(x[train], outcomes[train], INDICES, RIDGE)
        coefficients["free"][str(year)] = free_coef.tolist()
        probabilities["free"][test] = sigmoid(x[test] @ free_coef)
        for value in FIXED:
            key = f"fixed_{value:.2f}"
            coef = fit_fixed_home(x[train], outcomes[train], INDICES, RIDGE, value)
            coefficients[key][str(year)] = coef.tolist()
            probabilities[key][test] = sigmoid(x[test] @ coef)
        bundle_coefficients[str(year)] = {}
        for name, indices in BUNDLE_DIAGNOSTICS.items():
            coef = r.fit(x[train], outcomes[train], indices, RIDGE)
            bundle_coefficients[str(year)][name] = {
                "coefficient": float(coef[HOME_INDEX]),
                "equalTeamHomeWinProbability": float(sigmoid(coef[HOME_INDEX])),
            }

    # The production coefficient is the 2026 free fit. This is the strongest
    # integrity check because production was trained through 2025.
    calculated = np.asarray(coefficients["free"]["2026"])
    published = np.asarray(production["coefficients"])
    max_coefficient_error = float(np.max(np.abs(calculated - published)))
    if max_coefficient_error > 1e-8:
        raise AssertionError(f"v6 reconstruction error: {max_coefficient_error}")

    annual = {}
    close_masks = {}
    for year in EVALUATION_YEARS:
        test = years == year
        free_coef = np.asarray(coefficients["free"][str(year)])
        neutral_logit = x @ free_coef - free_coef[HOME_INDEX] * x[:, HOME_INDEX]
        neutral_probability = sigmoid(neutral_logit)
        close = (
            test
            & (x[:, HOME_INDEX] == 1)
            & (neutral_probability >= 0.40)
            & (neutral_probability <= 0.60)
        )
        close_masks[year] = close
        annual[str(year)] = {
            "freeCoefficient": float(free_coef[HOME_INDEX]),
            "equalTeamHomeWinProbability": float(sigmoid(free_coef[HOME_INDEX])),
            "variants": {},
        }
        for key, prob in probabilities.items():
            annual[str(year)]["variants"][key] = {
                "all": metrics(prob[test], outcomes[test]),
                "nearEven": slice_report(prob, outcomes, close),
            }

    selection = np.isin(years, [2023, 2024])
    fixed_keys = [f"fixed_{value:.2f}" for value in FIXED]
    selected_key = min(
        fixed_keys,
        key=lambda key: metrics(probabilities[key][selection], outcomes[selection])[
            "logLoss"
        ],
    )
    completed = np.isin(years, [2023, 2024, 2025])
    close_completed = np.logical_or.reduce([close_masks[y] for y in [2023, 2024, 2025]])
    free_complete = metrics(probabilities["free"][completed], outcomes[completed])
    candidate_complete = metrics(probabilities[selected_key][completed], outcomes[completed])
    free_close = slice_report(probabilities["free"], outcomes, close_completed)
    candidate_close = slice_report(
        probabilities[selected_key], outcomes, close_completed
    )
    bootstrap = bootstrap_probability(
        loss_rows(
            games,
            outcomes,
            probabilities["free"],
            probabilities[selected_key],
            completed,
        ),
        seed=20260926,
    )
    per_season_regression = {
        str(year): annual[str(year)]["variants"][selected_key]["all"]["logLoss"]
        - annual[str(year)]["variants"]["free"]["all"]["logLoss"]
        for year in [2023, 2024, 2025]
    }
    confirmation_free = annual["2025"]["variants"]["free"]["all"]
    confirmation_candidate = annual["2025"]["variants"][selected_key]["all"]
    gate = {
        "selectedCandidate": selected_key,
        "pooledLogLossImprovement": free_complete["logLoss"]
        - candidate_complete["logLoss"],
        "pooledBrierImprovement": free_complete["brier"]
        - candidate_complete["brier"],
        "maximumSeasonLogLossRegression": max(per_season_regression.values()),
        "bootstrap": bootstrap,
        "nearEvenAbsoluteCalibrationImprovement": abs(free_close["calibrationError"])
        - abs(candidate_close["calibrationError"]),
        "confirmationLogLossImprovement": confirmation_free["logLoss"]
        - confirmation_candidate["logLoss"],
        "confirmationAccuracyDelta": confirmation_candidate["accuracy"]
        - confirmation_free["accuracy"],
    }
    gate["passed"] = (
        gate["pooledLogLossImprovement"] >= 0.0005
        and gate["pooledBrierImprovement"] >= 0
        and gate["maximumSeasonLogLossRegression"] <= 0.001
        and bootstrap["probabilityLowerLogLoss"] >= 0.80
        and gate["nearEvenAbsoluteCalibrationImprovement"] > 0
        and gate["confirmationLogLossImprovement"] > 0
        and gate["confirmationAccuracyDelta"] >= -0.005
    )

    report = {
        "protocol": {
            "version": "6-home-field-audit-1",
            "blueprintSha256": hashlib.sha256(BLUEPRINT.read_bytes()).hexdigest(),
            "features": opp.NAMES,
            "indices": INDICES,
            "ridge": RIDGE,
            "fixedHomeCoefficients": FIXED,
            "selectionYears": [2023, 2024],
            "confirmationYear": 2025,
            "partialDiagnosticYear": 2026,
        },
        "integrity": {
            "publishedCoefficient": float(published[HOME_INDEX]),
            "reconstructedCoefficient": float(calculated[HOME_INDEX]),
            "maximumCoefficientError": max_coefficient_error,
        },
        "annual": annual,
        "bundleCoefficientDiagnostics": bundle_coefficients,
        "selection": {
            key: metrics(probabilities[key][selection], outcomes[selection])
            for key in ["free", *fixed_keys]
        },
        "pooled2023To2025": {
            "free": free_complete,
            "candidate": candidate_complete,
            "freeNearEven": free_close,
            "candidateNearEven": candidate_close,
        },
        "promotionGate": gate,
        "decision": "promote" if gate["passed"] else "retain-v6",
        "coverage": coverage,
        "passerCoverage": passer_coverage,
        "scope": (
            "Retrospective audit of inspected seasons. Every target-season fit "
            "uses only earlier seasons; 2026 is partial."
        ),
    }
    RESULTS.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    write_markdown(report)
    print(
        json.dumps(
            {
                "integrity": report["integrity"],
                "freeHomeByYear": {
                    year: {
                        "coefficient": annual[year]["freeCoefficient"],
                        "equalTeamHomeWinProbability": annual[year][
                            "equalTeamHomeWinProbability"
                        ],
                    }
                    for year in annual
                },
                "selection": report["selection"],
                "pooled": report["pooled2023To2025"],
                "gate": gate,
                "decision": report["decision"],
            },
            indent=2,
        )
    )


def pct(value):
    return f"{100 * value:.1f}%"


def dec(value):
    return f"{value:.6f}"


def write_markdown(report):
    annual = report["annual"]
    gate = report["promotionGate"]
    selected = gate["selectedCandidate"]
    pooled = report["pooled2023To2025"]
    lines = [
        "# Home-field audit results",
        "",
        f"**Decision: `{report['decision']}`.** The predeclared gate "
        + ("passed." if gate["passed"] else "did not pass, so production v6 is unchanged."),
        "",
        "## Free coefficient by target season",
        "",
        "| Target | Coefficient | Equal-team home win probability |",
        "|---:|---:|---:|",
    ]
    for year in annual:
        lines.append(
            f"| {year} | {annual[year]['freeCoefficient']:.4f} | "
            f"{pct(annual[year]['equalTeamHomeWinProbability'])} |"
        )
    lines += [
        "",
        "## Fixed-coefficient selection (2023-2024)",
        "",
        "| Variant | Log loss | Brier | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for key, value in report["selection"].items():
        lines.append(
            f"| {key} | {dec(value['logLoss'])} | {dec(value['brier'])} | "
            f"{pct(value['accuracy'])} |"
        )
    lines += [
        "",
        "## Pooled completed seasons (2023-2025)",
        "",
        "| Model | Log loss | Brier | Accuracy | Near-even predicted | Near-even actual |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, base, close in [
        ("Free v6", pooled["free"], pooled["freeNearEven"]),
        (selected, pooled["candidate"], pooled["candidateNearEven"]),
    ]:
        lines.append(
            f"| {label} | {dec(base['logLoss'])} | {dec(base['brier'])} | "
            f"{pct(base['accuracy'])} | {pct(close['predictedHomeWinRate'])} | "
            f"{pct(close['actualHomeWinRate'])} |"
        )
    interval = pooled["freeNearEven"]["actualHomeWinRateWilson95"]
    lines += [
        "",
        f"The near-even sample's 95% Wilson interval for the actual home win rate is "
        f"{pct(interval[0])}–{pct(interval[1])}.",
        "",
        "## Promotion gate",
        "",
        f"- Selected fixed candidate: `{selected}`.",
        f"- Pooled log-loss improvement: {gate['pooledLogLossImprovement']:+.6f}.",
        f"- Pooled Brier improvement: {gate['pooledBrierImprovement']:+.6f}.",
        f"- Worst single-season log-loss regression: {gate['maximumSeasonLogLossRegression']:+.6f}.",
        f"- Week-block bootstrap probability of lower log loss: {pct(gate['bootstrap']['probabilityLowerLogLoss'])}.",
        f"- Near-even absolute calibration improvement: {gate['nearEvenAbsoluteCalibrationImprovement']:+.6f}.",
        f"- 2025 confirmation log-loss improvement: {gate['confirmationLogLossImprovement']:+.6f}.",
        f"- 2025 confirmation accuracy change: {pct(gate['confirmationAccuracyDelta'])}.",
        "",
        "## Feature-set diagnostic",
        "",
        "| Target | Score only | Baseline + passer | Stable pair | Broad v6 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for year, bundles in report["bundleCoefficientDiagnostics"].items():
        lines.append(
            f"| {year} | {bundles['score_only']['coefficient']:.4f} | "
            f"{bundles['baseline']['coefficient']:.4f} | "
            f"{bundles['stable_pair']['coefficient']:.4f} | "
            f"{bundles['broad']['coefficient']:.4f} |"
        )
    lines += [
        "",
        "The feature-set table is a double-counting diagnostic: a sharp collapse or "
        "jump after adding efficiency inputs would indicate that those inputs are "
        "absorbing venue in an unstable way. It is evidence, not a causal proof.",
        "",
        f"Integrity check: maximum difference between the reconstructed 2026 "
        f"coefficient vector and the published vector was "
        f"{report['integrity']['maximumCoefficientError']:.3g}.",
        "",
        "This is a retrospective audit of seasons already inspected during model "
        "development. The 2026 sample is incomplete and is not used for promotion.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
