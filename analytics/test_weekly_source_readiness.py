import unittest
from datetime import datetime, timezone

from weekly_source_readiness import sunday_boundary


class WeeklySourceReadinessTests(unittest.TestCase):
    def test_boundary_tracks_eastern_time_across_dst(self):
        summer = sunday_boundary(datetime(2026, 10, 18, 16, 0, tzinfo=timezone.utc))
        winter = sunday_boundary(datetime(2026, 11, 8, 17, 0, tzinfo=timezone.utc))
        self.assertEqual(summer.isoformat(), "2026-10-18T04:00:00-04:00")
        self.assertEqual(winter.isoformat(), "2026-11-08T04:00:00-05:00")

    def test_before_sunday_boundary_uses_prior_week(self):
        boundary = sunday_boundary(datetime(2026, 10, 18, 7, 0, tzinfo=timezone.utc))
        self.assertEqual(boundary.isoformat(), "2026-10-11T04:00:00-04:00")


if __name__ == "__main__":
    unittest.main()
