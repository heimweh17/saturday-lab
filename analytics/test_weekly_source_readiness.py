import unittest
from datetime import datetime, timezone

from weekly_source_readiness import weekly_boundary


class WeeklySourceReadinessTests(unittest.TestCase):
    def test_boundary_tracks_eastern_time_across_dst(self):
        summer = weekly_boundary(datetime(2026, 10, 19, 16, 0, tzinfo=timezone.utc))
        winter = weekly_boundary(datetime(2026, 11, 9, 17, 0, tzinfo=timezone.utc))
        self.assertEqual(summer.isoformat(), "2026-10-19T04:00:00-04:00")
        self.assertEqual(winter.isoformat(), "2026-11-09T04:00:00-05:00")

    def test_before_monday_boundary_uses_prior_week(self):
        boundary = weekly_boundary(datetime(2026, 10, 19, 7, 0, tzinfo=timezone.utc))
        self.assertEqual(boundary.isoformat(), "2026-10-12T04:00:00-04:00")


if __name__ == "__main__":
    unittest.main()
