"""Audit correlated strength features, extreme confidence and nonlinear rest."""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np
from scipy.optimize import minimize

from pipeline import ROOT, metrics, sigmoid
import ranking_review as ranking
from home_field_audit import build_dataset, loss_rows
from stability_review import bootstrap_probability


BLUEPRINT = ROOT / "analytics/FEATURE-OVERLAP-AUDIT.md"
RESULTS = ROOT / "analytics/feature-overlap-audit-results.json"
MARKDOWN = ROOT / "analytics/FEATURE-OVERLAP-AUDIT-RESULTS.md"
YEARS = [2023, 2024, 2025, 2026]
HOME = 15
REST = 16
BROAD = [0, 6, 8, 9, 10, 11, 12, 13, 15, 16]
COMPACT = [0, 8, 13, 15, 16]
STABLE = [0, 6, 8, 13, 15, 16]
FEATURES = ["Scoring strength", "First-down rate", "Rush EPA", "Yards per play"]
FEATURE_COLUMNS = [0, 8, 10, 11]
BANDS = [(0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 0.85), (0.85, 0.90), (0.90, 0.95), (0.95, 1.01)]


def nonlinear_matrix(x):
    """Replace continuous rest with three antisymmetric rest-gap buckets."""
    gap = x[:, REST]
    absolute = np.abs(gap)
    sign = np.sign(gap)
    buckets = np.column_stack(
        [
            sign * ((absolute >= 1) & (absolute < 3)),
            sign * ((absolute >= 3) & (absolute < 10)),
            sign * (absolute >= 10),
        ]
    )
    return np.column_stack([x[:, :REST], buckets])


def constrained_fit(x, y, indices, penalty, signed):
    a = x[:, indices]
    scale = np.maximum(np.sqrt(np.mean(a * a, axis=0)), 1e-6)
    z = a / scale

    def objective(beta):
        logits = z @ beta
        return (
            np.logaddexp(0, logits).sum() - y @ logits + penalty / 2 * (beta @ beta),
            z.T @ (sigmoid(logits) - y) + penalty * beta,
        )

    result = minimize(
        objective,
        np.zeros(len(indices)),
        jac=True,
        method="L-BFGS-B",
        bounds=[(None, None) if index in signed else (0, None) for index in indices],
        options={"ftol": 1e-12, "gtol": 1e-7, "maxiter": 600},
    )
    if not result.success:
        raise RuntimeError(result.message)
    coefficient = np.zeros(x.shape[1])
    coefficient[indices] = result.x / scale
    return coefficient


def favorite_calibration(probability, outcome, mask):
    p = probability[mask]
    y = outcome[mask]
    favorite_probability = np.maximum(p, 1 - p)
    favorite_won = np.where(p >= 0.5, y, 1 - y)
    rows = []
    for low, high in BANDS:
        selected = (favorite_probability >= low) & (favorite_probability < high)
        n = int(selected.sum())
        rows.append(
            {
                "band": f"{int(low * 100)}-{100 if high > 1 else int(high * 100)}",
                "n": n,
                "share": float(n / len(p)) if len(p) else 0,
                "predictedFavoriteWinRate": float(np.mean(favorite_probability[selected])) if n else None,
                "actualFavoriteWinRate": float(np.mean(favorite_won[selected])) if n else None,
                "upsetRate": float(1 - np.mean(favorite_won[selected])) if n else None,
            }
        )
    return rows


def extreme_error(rows):
    chosen = [row for row in rows if row["band"] in ("90-95", "95-100") and row["n"]]
    total = sum(row["n"] for row in chosen)
    if not total:
        return None
    return float(
        sum(
            row["n"]
            * abs(row["predictedFavoriteWinRate"] - row["actualFavoriteWinRate"])
            for row in chosen
        )
        / total
    )


def main():
    games, seasons, outcome, x, coverage, passer_coverage, production = build_dataset()
    xn = nonlinear_matrix(x)
    variants = {
        "broad_ridge_1": {"kind": "fit", "matrix": x, "indices": BROAD, "ridge": 1.0, "signed": {REST}},
        "compact_ridge_1": {"kind": "fit", "matrix": x, "indices": COMPACT, "ridge": 1.0, "signed": {REST}},
        "compact_ridge_10": {"kind": "fit", "matrix": x, "indices": COMPACT, "ridge": 10.0, "signed": {REST}},
        "stable_pair_ridge_1": {"kind": "fit", "matrix": x, "indices": STABLE, "ridge": 1.0, "signed": {REST}},
        "stable_pair_ridge_10": {"kind": "fit", "matrix": x, "indices": STABLE, "ridge": 10.0, "signed": {REST}},
        "broad_ridge_10": {"kind": "fit", "matrix": x, "indices": BROAD, "ridge": 10.0, "signed": {REST}},
        "broad_ridge_50": {"kind": "fit", "matrix": x, "indices": BROAD, "ridge": 50.0, "signed": {REST}},
        "compact_nonlinear_rest": {"kind": "fit", "matrix": xn, "indices": [0, 8, 13, 15, 16, 17, 18], "ridge": 1.0, "signed": {16, 17, 18}},
        "broad_nonlinear_rest": {"kind": "fit", "matrix": xn, "indices": [0, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18], "ridge": 1.0, "signed": {16, 17, 18}},
        "temperature_0.85": {"kind": "temperature", "value": 0.85},
        "temperature_0.90": {"kind": "temperature", "value": 0.90},
        "temperature_0.95": {"kind": "temperature", "value": 0.95},
    }
    probability = {name: np.full(len(games), np.nan) for name in variants}
    coefficients = {name: {} for name, variant in variants.items() if variant["kind"] == "fit"}
    neutral_logits = {name: np.full(len(games), np.nan) for name in variants}

    for year in YEARS:
        train = (seasons >= 2019) & (seasons < year)
        test = seasons == year
        for name, variant in variants.items():
            if variant["kind"] != "fit":
                continue
            matrix = variant["matrix"]
            coefficient = constrained_fit(
                matrix[train], outcome[train], variant["indices"], variant["ridge"], variant["signed"]
            )
            coefficients[name][str(year)] = coefficient.tolist()
            logits = matrix[test] @ coefficient
            probability[name][test] = sigmoid(logits)
            venue_rest = coefficient[HOME] * matrix[test, HOME]
            if matrix.shape[1] == 17:
                venue_rest += coefficient[REST] * matrix[test, REST]
            else:
                venue_rest += matrix[test, 16:19] @ coefficient[16:19]
            neutral_logits[name][test] = logits - venue_rest

        baseline_logit = np.log(
            np.clip(probability["broad_ridge_1"][test], 1e-9, 1 - 1e-9)
            / np.clip(1 - probability["broad_ridge_1"][test], 1e-9, 1 - 1e-9)
        )
        baseline_neutral = neutral_logits["broad_ridge_1"][test]
        for value in (0.85, 0.90, 0.95):
            name = f"temperature_{value:.2f}"
            probability[name][test] = sigmoid(value * baseline_logit)
            neutral_logits[name][test] = value * baseline_neutral

    published = np.asarray(production["coefficients"])
    reconstructed = np.asarray(coefficients["broad_ridge_1"]["2026"])
    integrity = float(np.max(np.abs(published - reconstructed)))
    if integrity > 1e-8:
        raise AssertionError(f"production reconstruction error {integrity}")

    selection_mask = np.isin(seasons, [2023, 2024])
    completed_mask = np.isin(seasons, [2023, 2024, 2025])
    candidate_names = [name for name in variants if name != "broad_ridge_1"]
    selection = {
        name: metrics(probability[name][selection_mask], outcome[selection_mask])
        for name in variants
    }
    selected = min(candidate_names, key=lambda name: selection[name]["logLoss"])

    annual = {}
    for year in YEARS:
        mask = seasons == year
        annual[str(year)] = {
            name: metrics(probability[name][mask], outcome[mask]) for name in variants
        }
    pooled = {
        name: metrics(probability[name][completed_mask], outcome[completed_mask])
        for name in variants
    }
    calibration = {
        name: favorite_calibration(probability[name], outcome, completed_mask)
        for name in ("broad_ridge_1", selected)
    }
    baseline_extreme = extreme_error(calibration["broad_ridge_1"])
    candidate_extreme = extreme_error(calibration[selected])
    bootstrap = bootstrap_probability(
        loss_rows(
            games,
            outcome,
            probability["broad_ridge_1"],
            probability[selected],
            completed_mask,
        ),
        seed=20260926,
    )
    regressions = {
        str(year): annual[str(year)][selected]["logLoss"]
        - annual[str(year)]["broad_ridge_1"]["logLoss"]
        for year in [2023, 2024, 2025]
    }
    gate = {
        "selectedCandidate": selected,
        "pooledLogLossImprovement": pooled["broad_ridge_1"]["logLoss"] - pooled[selected]["logLoss"],
        "pooledBrierImprovement": pooled["broad_ridge_1"]["brier"] - pooled[selected]["brier"],
        "confirmationLogLossImprovement": annual["2025"]["broad_ridge_1"]["logLoss"] - annual["2025"][selected]["logLoss"],
        "confirmationAccuracyDelta": annual["2025"][selected]["accuracy"] - annual["2025"]["broad_ridge_1"]["accuracy"],
        "maximumSeasonLogLossRegression": max(regressions.values()),
        "bootstrap": bootstrap,
        "baselineExtremeCalibrationError": baseline_extreme,
        "candidateExtremeCalibrationError": candidate_extreme,
    }
    gate["passed"] = (
        gate["pooledLogLossImprovement"] >= 0.001
        and gate["pooledBrierImprovement"] >= 0
        and gate["confirmationLogLossImprovement"] >= 0.0005
        and gate["confirmationAccuracyDelta"] >= -0.005
        and gate["maximumSeasonLogLossRegression"] <= 0.0015
        and bootstrap["probabilityLowerLogLoss"] >= 0.85
        and candidate_extreme is not None
        and baseline_extreme is not None
        and candidate_extreme <= baseline_extreme
    )

    correlation_mask = (seasons >= 2019) & (seasons <= 2025)
    correlation = np.corrcoef(x[correlation_mask][:, FEATURE_COLUMNS], rowvar=False)
    gap_distribution = {}
    for name in ("broad_ridge_1", selected):
        gaps = np.abs(neutral_logits[name][completed_mask])
        favorites = np.maximum(probability[name][completed_mask], 1 - probability[name][completed_mask])
        gap_distribution[name] = {
            "neutralAbsoluteLogitQuantiles": {
                str(q): float(np.quantile(gaps, q)) for q in (0.5, 0.75, 0.9, 0.95, 0.99)
            },
            "shareAtLeast90Percent": float(np.mean(favorites >= 0.90)),
            "shareAtLeast95Percent": float(np.mean(favorites >= 0.95)),
        }

    report = {
        "protocol": {
            "version": "6-feature-overlap-audit-1",
            "blueprintSha256": hashlib.sha256(BLUEPRINT.read_bytes()).hexdigest(),
            "selectionYears": [2023, 2024],
            "confirmationYear": 2025,
            "partialDiagnosticYear": 2026,
            "variants": {
                name: {
                    k: sorted(v) if isinstance(v, set) else v
                    for k, v in variant.items()
                    if k != "matrix"
                }
                for name, variant in variants.items()
            },
        },
        "integrity": {"maximumProductionCoefficientError": integrity},
        "featureCorrelation": {
            "names": FEATURES,
            "matrix": correlation.tolist(),
        },
        "selection": selection,
        "annual": annual,
        "pooled2023To2025": pooled,
        "favoriteCalibration": calibration,
        "gapDistribution": gap_distribution,
        "promotionGate": gate,
        "decision": "promote" if gate["passed"] else "retain-v6",
        "coverage": coverage,
        "passerCoverage": passer_coverage,
        "scope": "Retrospective week-forward audit; 2026 is partial and excluded from promotion.",
    }
    RESULTS.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    write_markdown(report)
    print(json.dumps({"selection": selection, "selected": selected, "pooled": {"baseline": pooled["broad_ridge_1"], "candidate": pooled[selected]}, "calibration": calibration, "gate": gate, "decision": report["decision"]}, indent=2))


def fmt(value):
    return f"{value:.6f}"


def pct(value):
    return f"{100 * value:.1f}%"


def write_markdown(report):
    selected = report["promotionGate"]["selectedCandidate"]
    gate = report["promotionGate"]
    lines = [
        "# Feature overlap, confidence and rest audit results",
        "",
        f"**Decision: `{report['decision']}`.** " + ("The frozen gate passed." if gate["passed"] else "The frozen gate failed, so production v6 is unchanged."),
        "",
        "## Earlier-season selection (2023-2024)",
        "",
        "| Variant | Log loss | Brier | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for name, value in sorted(report["selection"].items(), key=lambda item: item[1]["logLoss"]):
        lines.append(f"| {name} | {fmt(value['logLoss'])} | {fmt(value['brier'])} | {pct(value['accuracy'])} |")
    lines += [
        "",
        "## Completed-season comparison (2023-2025)",
        "",
        "| Model | Log loss | Brier | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for name in ("broad_ridge_1", selected):
        value = report["pooled2023To2025"][name]
        lines.append(f"| {name} | {fmt(value['logLoss'])} | {fmt(value['brier'])} | {pct(value['accuracy'])} |")
    lines += ["", "## Favorite calibration", ""]
    for name in ("broad_ridge_1", selected):
        lines += [f"### {name}", "", "| Favorite band | Games | Mean prediction | Actual wins | Upsets |", "|---|---:|---:|---:|---:|"]
        for row in report["favoriteCalibration"][name]:
            pred = "—" if row["predictedFavoriteWinRate"] is None else pct(row["predictedFavoriteWinRate"])
            actual = "—" if row["actualFavoriteWinRate"] is None else pct(row["actualFavoriteWinRate"])
            upset = "—" if row["upsetRate"] is None else pct(row["upsetRate"])
            lines.append(f"| {row['band']}% | {row['n']} | {pred} | {actual} | {upset} |")
        lines.append("")
    lines += [
        "## Promotion gate",
        "",
        f"- Selected candidate: `{selected}`.",
        f"- Pooled log-loss improvement: {gate['pooledLogLossImprovement']:+.6f}.",
        f"- Pooled Brier improvement: {gate['pooledBrierImprovement']:+.6f}.",
        f"- 2025 log-loss improvement: {gate['confirmationLogLossImprovement']:+.6f}.",
        f"- 2025 accuracy change: {pct(gate['confirmationAccuracyDelta'])}.",
        f"- Worst completed-season log-loss regression: {gate['maximumSeasonLogLossRegression']:+.6f}.",
        f"- Bootstrap probability of lower log loss: {pct(gate['bootstrap']['probabilityLowerLogLoss'])}.",
        f"- Baseline/candidate extreme-band calibration error: {gate['baselineExtremeCalibrationError']:.4f} / {gate['candidateExtremeCalibrationError']:.4f}.",
        "",
        "The coefficient reconstruction matched the released production vector exactly. This is retrospective evidence, and partial 2026 results did not participate in promotion.",
    ]
    MARKDOWN.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
