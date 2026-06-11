import numpy as np

from satlight.services.sun import is_sunlit, sun_unit_vector_eci


def test_sun_unit_vector_is_normalized():
    v = sun_unit_vector_eci(2460000.0, 0.25)
    assert abs(np.linalg.norm(v) - 1.0) < 1e-9


def test_shadow_geometry():
    sun = np.array([1.0, 0.0, 0.0])
    positions = np.array(
        [
            [7000.0, 0.0, 0.0],  # toward sun -> lit
            [-7000.0, 0.0, 0.0],  # directly behind earth -> shadow
            [-7000.0, 8000.0, 0.0],  # behind but off-axis -> lit
        ]
    )
    lit = is_sunlit(positions, sun)
    assert lit.tolist() == [True, False, True]
