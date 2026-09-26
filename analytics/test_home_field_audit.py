import unittest

import numpy as np

from home_field_audit import HOME_INDEX, fit_fixed_home


class HomeFieldAuditTest(unittest.TestCase):
    def test_fixed_home_is_an_offset_while_other_terms_refit(self):
        rng = np.random.default_rng(17)
        x = np.zeros((800, 17))
        x[:, 0] = rng.normal(size=len(x))
        x[:, HOME_INDEX] = rng.integers(0, 2, size=len(x))
        x[:, 16] = rng.normal(scale=2, size=len(x))
        logits = 0.7 * x[:, 0] + 0.25 * x[:, HOME_INDEX] - 0.04 * x[:, 16]
        outcomes = rng.binomial(1, 1 / (1 + np.exp(-logits))).astype(float)

        coefficient = fit_fixed_home(
            x, outcomes, [0, HOME_INDEX, 16], penalty=1.0, fixed_home=0.25
        )

        self.assertEqual(coefficient[HOME_INDEX], 0.25)
        self.assertGreater(coefficient[0], 0)
        self.assertNotEqual(coefficient[16], 0)
        self.assertTrue(np.all(coefficient[[i for i in range(17) if i not in (0, 15, 16)]] == 0))


if __name__ == "__main__":
    unittest.main()
