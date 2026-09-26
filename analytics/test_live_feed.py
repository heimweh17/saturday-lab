import unittest

import live_feed


class LiveFeedTest(unittest.TestCase):
    def test_box_rates_preserve_missing_denominators(self):
        box = live_feed.normalized_box([
            {"name": "completionAttempts", "displayValue": "18/30"},
            {"name": "rushingAttempts", "displayValue": "35"},
            {"name": "totalYards", "displayValue": "390"},
            {"name": "thirdDownEff", "displayValue": "0-0"},
            {"name": "possessionTime", "displayValue": "31:30"},
        ])
        self.assertEqual(box["plays"], 65)
        self.assertEqual(box["yardsPerPlay"], 6)
        self.assertIsNone(box["thirdRate"])
        self.assertEqual(box["possessionMinutes"], 31.5)

    def test_canonical_ignores_only_refresh_time(self):
        first = {"updatedAt": "one", "games": [{"id": "1", "hs": 7}]}
        second = {"updatedAt": "two", "games": [{"id": "1", "hs": 7}]}
        changed = {"updatedAt": "two", "games": [{"id": "1", "hs": 10}]}
        self.assertEqual(live_feed.canonical(first), live_feed.canonical(second))
        self.assertNotEqual(live_feed.canonical(first), live_feed.canonical(changed))

    def test_pregame_probability_is_complementary_when_teams_swap(self):
        def team(team_id, strength):
            return {"id": team_id, "modelState": {"q": [strength], "lastDate": None}}
        season = {
            "snapshots": {"99": {"through": "2026-09-20T00:00Z", "teams": [team("a", 1), team("b", 0)]}},
            "model": {"version": "test", "coefficients": [1, 0, 0]},
        }
        base = {"date": "2026-10-01T00:00Z", "neutral": True}
        ab = live_feed.pregame_prediction({**base, "home": "a", "away": "b"}, season)
        ba = live_feed.pregame_prediction({**base, "home": "b", "away": "a"}, season)
        self.assertAlmostEqual(ab["homeWinProbability"] + ba["homeWinProbability"], 1)
        self.assertEqual(ab["snapshotThrough"], "2026-09-20T00:00Z")

    def test_pregame_probability_cannot_use_a_post_kickoff_snapshot(self):
        season = {
            "snapshots": {"99": {"through": "2026-10-02T00:00Z", "teams": []}},
            "model": {"version": "test", "coefficients": []},
        }
        game = {"date": "2026-10-01T00:00Z", "home": "a", "away": "b", "neutral": True}
        self.assertIsNone(live_feed.pregame_prediction(game, season))


if __name__ == "__main__":
    unittest.main()
