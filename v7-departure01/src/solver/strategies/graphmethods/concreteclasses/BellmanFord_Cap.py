from ...graphmethods.graphmethods import GraphHeuristic
from .....model.graph.Zone import RestrictedZone


class GraphBellmanFordWait(GraphHeuristic):
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
