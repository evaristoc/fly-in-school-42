from abc import ABC, abstractmethod
from math import sqrt
from ...model.graph.Graph import Zone


class Heuristic(ABC):
    @abstractmethod
    def __call__(self, current: Zone, goal: Zone) -> float:
        pass


class ZeroHeuristic(Heuristic):
    def __call__(self, current: Zone, goal: Zone) -> float:
        return 0.0


class EuclideanHeuristic(Heuristic):
    def __call__(self, current: Zone, goal: Zone) -> float:
        return sqrt((goal.x - current.x) ** 2 + (goal.y - current.y) ** 2)


class ManhattanHeuristic(Heuristic):
    def __call__(self, current: Zone, goal: Zone) -> float:
        return abs(goal.x - current.x) + abs(goal.y - current.y)


class ChebyshevHeuristic(Heuristic):
    def __call__(self, current: Zone, goal: Zone) -> float:
        dx = abs(current.x - goal.x)
        dy = abs(current.y - goal.y)
        return float(max(dx, dy))
