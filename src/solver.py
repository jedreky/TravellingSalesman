from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Route:
    """Route definition: start, end and locations to visit."""

    start: int
    end: int
    locs_to_visit: tuple


@dataclass(frozen=True)
class Solution:
    """Route solution: optimal path and its length."""

    path: list
    length: float

    def to_json(self):
        return {"path": self.path, "length": self.length}


class TSP:
    def __init__(self, *, coords=None, dist_matrix=None):
        assert (coords is None) ^ (
            dist_matrix is None
        ), "Exactly one input argument should be specified"

        # validate input data
        if coords:
            assert isinstance(coords, list | tuple) and all(
                map(lambda x: isinstance(x, list | tuple), coords)
            ), "When specifying coordinates input must be a list of lists"
            assert (
                len(set(map(len, coords))) == 1
            ), "Every sublist must have the same length"
            self.num_locs = len(coords)
            self.dist_matrix = self._compute_dist_matrix(coords)

        if dist_matrix:
            assert isinstance(
                dist_matrix, np.ndarray
            ), "Distance matrix should be a NumPy array"
            assert (
                dist_matrix.shape[0] == dist_matrix.shape[1]
            ), "Distance matrix should be a square matrix"
            self.num_locs = dist_matrix.shape[0]
            self.dist_matrix = dist_matrix

        assert self.num_locs >= 3, "At least 3 locations must be specified"
        self.solved_routes = {}

    @staticmethod
    def _compute_dist_matrix(coords):
        """Compute distance matrix from coordinates."""
        n = len(coords)
        # initialise an empty matrix
        dist_matrix = np.zeros([n, n])

        # iterate over the entries of the matrix
        for j in range(n):
            for k in range(j + 1, n):
                v = np.array(coords[j]) - np.array(coords[k])
                dist_matrix[j, k] = np.sqrt(np.dot(v, v))

        # fill up the other half of the matrix
        dist_matrix = dist_matrix + np.transpose(dist_matrix)
        return dist_matrix

    def solve(self, route=None):
        # if route is not specified, solve the complete tour
        if route is None:
            route = Route(start=0, end=0, locs_to_visit=tuple(range(1, self.num_locs)))

        if route not in self.solved_routes:
            if len(route.locs_to_visit) == 1:
                loc = route.locs_to_visit[0]
                self.solved_routes[route] = Solution(
                    (route.start, loc, route.end),
                    self.dist_matrix[route.start, loc]
                    + self.dist_matrix[loc, route.end],
                )
            else:
                possible_routes = []

                for x in route.locs_to_visit:
                    subroute = Route(
                        start=route.start,
                        end=x,
                        locs_to_visit=tuple(y for y in route.locs_to_visit if y != x),
                    )
                    solution = self.solve(route=subroute)
                    possible_routes.append(
                        Solution(
                            solution.path + (route.end,),
                            solution.length + self.dist_matrix[x, route.end],
                        )
                    )

                idx = np.argmin([x.length for x in possible_routes])
                self.solved_routes[route] = possible_routes[idx]

        return self.solved_routes[route]
