from ...structures.constraints import ConstraintZone, ConstraintEdge
from ....model.graph.Connection import Connection


class ForbiddenPolicy:
    def is_forbidden(self, *args, **kargs):
        ...


class ForbiddenCBS(ForbiddenPolicy):
    def is_forbidden(self,
                     tick: int,
                     agent_id: int,
                     conn: Connection) -> bool:
        candzone: str = conn.zone.name
        candedge: None | tuple = None
        # print(f"[FORBID CHECK] agent={agent_id} tick={tick} zone={candzone} edge={candedge} constraint_keys={list(self.constraints.keys())}")
        # does the zone has spare capacity?
        if not self.constraints or tick not in self.constraints:
            return False
        cons_zones: ConstraintZone = self.constraints.get(tick, {}).get("zones")
        if cons_zones:
            zone = cons_zones.get(candzone)
            if zone and agent_id in zone["agents"]:
                # print(f"[BLOCK ZONE] agent={agent_id} tick={tick} zone={candzone}")
                return True
        if conn.edge is not None:
            candedge = conn.edge.nodenames
            cons_edges: ConstraintEdge = self.constraints.get(tick, {}).get("edges")
            if cons_edges:
                edge = cons_edges.get(frozenset({candedge[0], candedge[1]}))
                if edge and agent_id in edge["agents"]:
                    # print(f"[BLOCK EDGE] agent={agent_id} tick={tick} edge={candedge}")
                    return True
        return False


class ForbiddenPriority(ForbiddenPolicy):
    def is_forbidden(
        self,
        tick: int,
        agent_id: int,
        conn: Connection
    ) -> bool:
        candzone: str = conn.zone.name
        candedge: None | tuple = None
        # does the zone has spare capacity?
        cons_zones: ConstraintZone = self.constraints.get(tick, {}).get("zones", {})
        zone = cons_zones.get(candzone)
        if zone and zone["capacity"] == zone["counter"]:
            print("in pathfinder - candidate zone: ", candzone, zone)
            return True
        #print(zone, zone["capacity"], zone["counter"])
        # zone has spare capacity, and the edge?
        if conn.edge is not None:
            candedge = conn.edge.nodenames
            cons_edges: ConstraintEdge = self.constraints.get(tick, {}).get("edges", {})
            edge = cons_edges.get(candedge)
            if edge and edge["capacity"] == edge["counter"]:
                print("in pathfinder - candidate edge: ", candedge, edge)
                return True
        # both has capacity: is not forbidden
        return False