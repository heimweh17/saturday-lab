import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FullScoreLayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layer = json.loads((ROOT / "public" / "data" / "score-layer.json").read_text(encoding="utf-8"))
        cls.results = json.loads((ROOT / "analytics" / "full-score-layer-results.json").read_text(encoding="utf-8"))

    def projected(self, probability: float, a_score: float, b_score: float):
        probability = min(.999999, max(.000001, probability))
        margin = self.layer["margin"]["scale"] * math.log(probability / (1 - probability))
        total = max(abs(margin), self.layer["total"]["intercept"] + self.layer["total"]["slope"] * (a_score + b_score))
        return (total + margin) / 2, (total - margin) / 2, margin

    def test_promotion_gate_and_probability_contract(self):
        self.assertEqual(self.layer["decision"], "promote")
        self.assertTrue(self.layer["probabilityUnchanged"])
        self.assertTrue(self.results["promotionGate"]["passed"])
        self.assertFalse(self.results["promotionGate"]["probabilityChanged"])

    def test_score_leader_always_matches_probability(self):
        for probability in (.01, .10, .25, .496, .50, .504, .75, .90, .99):
            a, b, margin = self.projected(probability, 18.6, 19.4)
            self.assertGreaterEqual(a, 0)
            self.assertGreaterEqual(b, 0)
            self.assertEqual(a > b, probability > .5)
            self.assertEqual(a < b, probability < .5)
            self.assertAlmostEqual(a - b, margin)

    def test_untouched_2025_score_metrics_improve(self):
        year = self.layer["validation"]["2025"]
        for metric in ("marginMAE", "totalMAE", "teamScoreMAE"):
            self.assertLess(year["candidate"][metric], year["baseline"][metric])

    def test_close_iowa_michigan_example_is_consistent(self):
        iowa, michigan, _ = self.projected(.504, 18.6, 19.4)
        self.assertGreater(iowa, michigan)
        self.assertEqual((round(iowa, 1), round(michigan, 1)), (22.2, 22.0))


if __name__ == "__main__":
    unittest.main()

