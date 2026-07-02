from abc import abstractmethod
from typing import Set, Tuple, List, Iterator
import heapq

from ..structures.roadmap_entitites import Step
from ..structures.constraints import ConstraintZone, ConstraintEdge, ConstrMap
from ..heuristics.costheuristics import Heuristic, ZeroHeuristic
from ...model.graph.Zone import Zone, StartZone, BlockedZone, RestrictedZone, \
    PriorityZone
from ...model.graph.Connection import Connection
from ...model.graph.Graph import Graph


class PathRules:
    ...
    # def __init__(self, *args, **kargs) -> None:
    #     ...
    # def can_transition(self, *args, **kargs) -> bool:
    #     ...

    # def is_forbidden(self, *args, **kargs) -> bool:
    #     ...

    # def compute_cost(self, *args, **kargs) -> float:
    #     ...

class PathAlgorithm:
    def search(self, *args, **kargs) -> None:
        ...

    def expand(self, *args, **kargs) -> None:
        ...

class DijkstraRules(PathRules):
    def __init__(self) -> None:
        self.constraints: ConstrMap | None = None
        self.visited: Set[Tuple[str, int]] | None = None
        self.unfeasible: Set[Tuple[str, int]] | None = None
        self.best_cost: dict[tuple[str, int], float] | None = None

    def evaluate(self,
                 new_cost: float,
                 state: Tuple[str, int],
                 next_tick: int,
                 agent_id: int,
                 conn: Connection,
                 current: Step) -> bool:
        if self.is_forbidden(next_tick, agent_id, conn):
            self.unfeasible.add(state)
        return new_cost > self.best_cost.get(state, float('inf')) or \
            state in self.unfeasible or \
            not self.can_transition(current, conn) or \
            conn.edge and conn.edge.nodenames in self.visited

    def is_forbiden(self,
                    tick: int,
                    agent_id: int,
                    conn: Connection) -> bool:
        candzone: str = conn.zone.name
        candedge: None | tuple = None
        # print(f"[FORBID CHECK] agent={agent_id} tick={tick} zone={candzone} edge={candedge} constraint_keys={list(constraints.keys())}")
        # does the zone has spare capacity?
        if not self.constraints or tick not in self.constraints:
            return False
        cons_zones: ConstraintZone = self.constraints.get(tick, {}).get("zones", {})
        zone = cons_zones.get(candzone)
        if zone and agent_id in zone["agents"]:
            # print(f"[BLOCK ZONE] agent={agent_id} tick={tick} zone={candzone}")
            return True
        if conn.edge is not None:
            candedge = conn.edge.nodenames
            cons_edges: ConstraintEdge = self.constraints.get(tick, {}).get("edges", {})
            edge = cons_edges.get(frozenset({candedge[0], candedge[1]}))
            if edge and agent_id in edge["agents"]:
                # print(f"[BLOCK EDGE] agent={agent_id} tick={tick} edge={candedge}")
                return True
        return False

    def can_transition(self,
                       current: Step,
                       connection: Connection) -> bool:
        zone = connection.zone
        # cannot re-enter start
        if isinstance(zone, StartZone) and current.g_cost > 0:
            return False
        # waiting rules
        if zone == current.zone:
            if current.wait >= zone.max_wait:
                return False
        # is blocked
        if isinstance(zone, BlockedZone):
            return False
        # allow the first tick in start even if visited
        if isinstance(zone, StartZone) and current.tick == current.parent.tick\
                if current.parent else -1:
            return True
        return True

class DijkstraHeuristic(PathAlgorithm, PathRules):
    def expand(self,
               current: Step,
               graph: Graph,
               agent_id: int,
               constraints: ConstrMap,
               open_set: List[Step],
               visited: Set[Tuple[str, int]],
               unfeasible: Set[Tuple[str, int]],
               counter: Iterator[int],
               best_cost: dict[tuple[str, int], float]) -> None:
        if current is None or current.zone is None:
            return None
        step_options = current.zone.neighbours

        if isinstance(current.zone, RestrictedZone) \
                and current.wait < current.zone.max_wait - 1:
            # Only wait in place; do not consider other neighbors
            connection = next((c for c in step_options
                               if c.zone == current.zone), None)
            if connection is None:
                raise RuntimeError("No self-connection "
                                   f"found for {current.zone.name}")

            next_tick = current.tick + 1
            resstep: Step | None = None
            if graph is not None and graph.goal is not None:
                resstep = self._build_step(graph,
                                           current,
                                           connection,
                                           graph.goal,
                                           counter)
            if resstep is not None:
                heapq.heappush(open_set, resstep)
            else:
                raise Exception("Could not make a restricted waiting step")

            return None  # short-circuit: do not expand any other neighbour
        for connection in step_options:

            next_zone = connection.zone
            next_tick = current.tick + 1
            # print("check tick 1111", agent_id, next_tick)

            state = (next_zone.name, next_tick)
            new_cost = self._compute_f_cost(next_zone, current.f_cost)
            if self.rules.evalute(new_cost, state, next_tick, agent_id, connection, current):
                continue
            # print("selected", agent_id, current, state)
            # print("check tick 2222", agent_id, next_tick, current.zone.name, connection.zone.name)
            step: Step | None = None
            # print("selected candidate", agent_id, next_tick, connection.zone.name)
            if graph is not None and graph.goal is not None:
                step = self._build_step(graph,
                                        current,
                                        connection,
                                        graph.goal,
                                        counter)
            if step is not None:
                if step.f_cost == float("inf"):
                    unfeasible.add(state)
                    continue
            else:
                raise Exception("Could not make a step")
            assert step.f_cost == new_cost
            best_cost[state] = new_cost
            if connection.edge:
                visited.add(connection.edge.nodenames)
            heapq.heappush(open_set, step)

    def compute_f_cost(self,
                       current: Zone,
                       goal: Zone) -> float:
        """
        REMEMBER: Even if using something like Dijkstra-ish algo,
        I dont need to compare 'distances' because the priority
        queue is already doing that work form me. Just almost forgot
        that the Step is a link list and that I will have more than
        one Step instance, only that I will be checking the new tail (?)
        to compare for costs, so it is only about updating the new cost
        for this STEP INSTANCE (again, the prio queue then will put the
        one with the lowest cost first) 
        """
        # Once in the game, cannot return to start zone
        if isinstance(goal, StartZone):
            return 0
        # all other zones are valid
        if not isinstance(goal, BlockedZone) and current.f_cost != None:
            return current.f_cost + (goal.weighted_cost if isinstance(goal, PriorityZone) else 1)
        else:
            return float('inf')

