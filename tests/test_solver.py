import numpy as np
import pytest

from numpy.testing import assert_almost_equal

from src.solver import TSP


@pytest.mark.parametrize(
    "coords, expected_length",
    [
        ([(1, 0), (0, -1), (0, 1)], 2 * (1 + np.sqrt(2))),
        ([(1, 0), (0, 1), (0, -1), (-1, 0)], 4 * np.sqrt(2)),
        ([(1, 0), (0, 1), (0, -1), (-1, 0), (0, 0)], 2 + 3 * np.sqrt(2)),
        ([(2, 0), (0, 1), (-1, 1), (0, 0)], 3 + np.sqrt(2) + np.sqrt(5)),
        (
            [(-1, 0), (-1, 1), (0, 1), (2, 0), (-2, -1)],
            2 + np.sqrt(2) + np.sqrt(5) + np.sqrt(17),
        ),
    ],
)
def test_TSP_solver_from_coords(coords, expected_length):
    problem = TSP(coords=coords)
    solution = problem.solve()
    assert_almost_equal(solution.length, expected_length)
