from __future__ import annotations
from typing import Dict, Set, Tuple, List, Optional, Iterator
import heapq
from itertools import count

from ...model.graph.Graph import Graph, Zone, Connection, StartZone, \
    BlockedZone, RestrictedZone, PriorityZone
from ..structures.roadmap_entitites import Step, RoadMap
from ..structures.constraints import ConstraintZone, ConstraintEdge, ConstrMap
from .heuristics import Heuristic, ZeroHeuristic


class Pathfinder:
    def __init__(
        self,
        heuristic: Optional[Heuristic] = None,
        heuristic_weight: float = 0.0,
        time_horizon_factor: int = 3,
    ):
        self.heuristic = heuristic or ZeroHeuristic()
        self.heuristic_weight = heuristic_weight
        self.time_horizon_factor = time_horizon_factor

    # -------------------------
    # Public API
    # -------------------------
    def solve(
        self,
        # this keep the solver stateless as it doesn't relies on any specific
        # graph
        graph: Graph,
        agent_id: int,
        entry_time: int,
        constraints: ConstrMap,
    ) -> Optional[RoadMap]:
        
        # NOTE: This an IMPORTANT one:
        """
        This part of the project has been modified to resemble a Dijkstra
        """

        open_set: List[Step] = []
        visited: Set[Tuple[str, int]] = set()
        unfeasible: Set[Tuple[str, int]] = set()
        counter = count()
        best_cost: dict[tuple[str, int], float] = {}

        start = self._init_step(graph, entry_time, counter)
        if not start:
            raise Exception("Could not create first step")
        heapq.heappush(open_set, start)
        best_cost[(start.zone.name, start.tick)] = start.f_cost
        max_ticks = len(graph.zones) * self.time_horizon_factor

        while open_set:
            current = heapq.heappop(open_set)
            if current.zone == graph.goal:
                return self._build_roadmap(current, agent_id)

            if current.tick >= max_ticks:
                continue
            state = (current.zone.name, current.tick)
            # visited keeps track of states we've already fully processed in the search.
            # It stays Dijsktra as long as costs stay non-negative and additive
            # The first time we pop a state from the priority queue,
            # we’ve already found the cheapest way to reach that node, so we can ignore all the
            # other options that have been pushed for that (node, tick) tuple into the priority queue.
            # That reduces the number of re-processing the same time-expanded states coming from
            # different paths and improves performance substantially.
            if state in visited:
                continue
            visited.add(state)
            self._expand(
                current,
                graph,
                agent_id,
                constraints,
                open_set,
                visited,
                unfeasible,
                counter,
                best_cost
            )

        return None

    # -------------------------
    # Core helpers
    # -------------------------

    def _init_step(self, graph: Graph, entry_time: int,
                   counter: Iterator[int]) -> Optional[Step]:
        if graph and isinstance(graph.startzone, Zone):
            step = Step(
                zone=graph.startzone,
                tick=entry_time,
                g_cost=graph.startzone.weighted_cost,
                counter=next(counter),
                f_cost=0.0,
            )
        if isinstance(step.zone, Zone) and isinstance(graph.goal, Zone):
            return step
        else:
            return None

    def _compute_f_cost(self,
                        zone: Zone,
                        old_f_cost: float) -> float:
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
        if isinstance(zone, StartZone):
            return 0
        # all other zones are valid
        if not isinstance(zone, BlockedZone):
            return old_f_cost + (zone.weighted_cost if isinstance(zone, PriorityZone) else 1)
        else:
            return float('inf')

    def _expand(
        self,
        current: Step,
        graph: Graph,
        agent_id: int,
        constraints: ConstrMap,
        open_set: List[Step],
        visited: Set[Tuple[str, int]],
        unfeasible: Set[Tuple[str, int]],
        counter: Iterator[int],
        best_cost: dict[tuple[str, int], float]
    ) -> None:
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
            if new_cost > best_cost.get(state, float('inf')):
                continue
            # unfeasible / forbidden == banned states at time `tick`
            if state in unfeasible:
                continue
            if self._is_forbidden(next_tick, agent_id, connection, constraints):
                # print("in the pathfinder aid, state: ", agent_id, state)
                # print("in the pathfinder: unfeasibles (comes before checking forbid) :", agent_id, unfeasible)
                unfeasible.add(state)
                # print("in the pathfinder: unfeasibles after update (comes before checking forbid) :", agent_id, unfeasible)
                continue
            # can_transition == temporary or permanent (not) evaluable state
            # include cases to which prioplanner doesn't have access
            if not self._can_transition(current, connection):
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
            heapq.heappush(open_set, step)

    # -------------------------
    # Rules (clean separation)
    # -------------------------
  
    def _is_forbidden(
        self,
        tick: int,
        agent_id: int,
        conn: Connection,
        constraints: ConstrMap,
    ) -> bool:
        candzone: str = conn.zone.name
        candedge: None | tuple = None
        # print(f"[FORBID CHECK] agent={agent_id} tick={tick} zone={candzone} edge={candedge} constraint_keys={list(constraints.keys())}")
        # does the zone has spare capacity?
        if not constraints or tick not in constraints:
            return False
        cons_zones: ConstraintZone = constraints.get(tick, {}).get("zones", {})
        zone = cons_zones.get(candzone)
        if zone and agent_id in zone["agents"]:
            # print(f"[BLOCK ZONE] agent={agent_id} tick={tick} zone={candzone}")
            return True
        if conn.edge is not None:
            candedge = conn.edge.nodenames
            cons_edges: ConstraintEdge = constraints.get(tick, {}).get("edges", {})
            edge = cons_edges.get(frozenset({candedge[0], candedge[1]}))
            if edge and agent_id in edge["agents"]:
                # print(f"[BLOCK EDGE] agent={agent_id} tick={tick} edge={candedge}")
                return True
        return False

    def _can_transition(self, current: Step, connection: Connection) -> bool:
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

    # -------------------------
    # Step construction
    # -------------------------

    def _build_step(
        self,
        graph: Graph,
        current: Step,
        connection: Connection,
        goal: Zone,
        counter: Iterator[int],
    ) -> Step:

        zone = connection.zone

        wait = current.wait + 1 if zone == current.zone else 0
        step = Step(
            zone=zone,
            tick=current.tick + 1,
            g_cost=0,
            parent=current,
            wait=wait,
            counter=next(counter),
            f_cost=self._compute_f_cost(zone, current.f_cost),
        )
        return step

    # -------------------------
    # Output
    # -------------------------

    def _build_roadmap(self, step: Step, agent_id: int) -> RoadMap:
        roadmap = RoadMap(agent_id=agent_id, cost=step.f_cost)
        states: Dict[int, Tuple[Zone, Zone]] = {}
        while step:
            prev = step.parent.zone if step.parent else step.zone
            assert prev is not None and step.zone is not None
            states[step.tick] = (prev, step.zone)
            if step.parent is None:
                break
            step = step.parent

        roadmap.states = dict(sorted(states.items()))
        return roadmap
