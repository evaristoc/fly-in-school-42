from abc import ABC, abstractmethod
from math import sqrt
from ...model.graph.Zone import Zone, RestrictedZone
from ...model.graph.Connection import Connection


class GraphHeuristic(ABC):
    @abstractmethod   
    def hub_connections(self):
        ...
    
    @abstractmethod
    def compute_reverse_map(self):
        ...


class GraphBellmanFord(GraphHeuristic):
    def hub_connections(self):
        for z in self.zones:
            for edge in self.edges:
                if z.name in edge.nodenames:
                    for neigh in self.zones:
                        if neigh.name != z.name and \
                                neigh.name in edge.nodenames:
                            conn = Connection(neigh, edge)
                            if conn not in z.neighbours:
                                z.neighbours.append(conn)
            # # the following will solve the "waiting" case later...
            z.neighbours.append(Connection(z))

    def compute_reverse_map(self):
        # return {zone: min_hops_to_goal}
        reversecost_map = {zone: float('inf') for zone in self.zones}
        if self.goal:
            reversecost_map[self.goal] = 0
            queue = [self.goal]
        else:
            queue = []
        while queue:
            current = queue.pop(0)
            if current:
                current_hop = reversecost_map[current]
                for conn in current.neighbours:
                    if conn:
                        neighbor = conn.zone
                        # TODO a pattern start to emerge - there is something about waiting times by zone type that could be better handled
                        # TODO check overall implementation as it appears that some of the cost handling seems to be redundant and hard to track
                        if reversecost_map[neighbor] > current_hop + (1 if not isinstance(current, RestrictedZone) else current.max_wait):
                            reversecost_map[neighbor] = current_hop + (1 if not isinstance(current, RestrictedZone) else current.max_wait)
                            queue.append(neighbor)
        if reversecost_map:
            self.reversecost_map = reversecost_map


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
