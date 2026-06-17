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

        open_set: List[Step] = []
        visited: Set[Tuple[str, int]] = set()
        unfeasible: Set[Tuple[str, int]] = set()
        counter = count()

        start = self._init_step(graph, entry_time, counter)
        if not start:
            raise Exception("Could not create first step")
        heapq.heappush(open_set, start)

        max_ticks = len(graph.zones) * self.time_horizon_factor

        while open_set:
            current = heapq.heappop(open_set)

            if current.zone == graph.goal:
                return self._build_roadmap(current, agent_id)

            if current.tick >= max_ticks:
                continue

            self._expand(
                current,
                graph,
                agent_id,
                constraints,
                open_set,
                visited,
                unfeasible,
                counter,
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
            step.f_cost = self._compute_f_cost(graph, step.g_cost,
                                               step.zone, graph.goal)
            return step
        else:
            return None

    def _compute_f_cost(self,
                        graph: Graph,
                        g_cost: float, zone: Zone, goal: Zone) -> float:
        # h = self.heuristic(zone, goal)
        # # once in the game, can not come back
        # if isinstance(zone, StartZone) and g_cost > 0:
        #     return float('inf')
        # return g_cost + self.heuristic_weight * h
        """
        Compute the A*/forward cost using g_cost (actual cost so far)
        plus a timeless hop-based heuristic to the goal.
        """
        # Access hop_map from the graph associated with this pathfinder
        if graph is None or graph.hop_map is None:
            return float('inf')
        hops_to_goal = graph.hop_map.get(zone, float('inf'))

        # prio PrioZones
        if isinstance(zone, PriorityZone):
            hops_to_goal = hops_to_goal - 1 + zone.weighted_cost

        # Once in the game, cannot return to start zone
        if isinstance(zone, StartZone) and g_cost > 0:
            return float('inf')

        # f = g + h, h is just hop count (forward incentive)
        return g_cost + self.heuristic_weight * hops_to_goal

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
    ) -> None:
        if current is None or current.zone is None:
            return None
        step_options = current.zone.neighbours

        # Case: restricted zone and waiting not done
        # should skip any other options if waiting time not over
        # notice that I requires to put them in the heap as they are
        # valid states in the ticking
        if isinstance(current.zone, RestrictedZone) \
                and current.wait < current.zone.max_wait - 1:
            # Only wait in place; do not consider other neighbors
            connection = next((c for c in step_options
                               if c.zone == current.zone), None)
            if connection is None:
                raise RuntimeError("No self-connection "
                                   f"found for {current.zone.name}")

            next_tick = current.tick + 1

            if (connection.zone.name, next_tick) not in visited:
                visited.add((connection.zone.name, next_tick))
                resstep: Step | None = None
                if graph is not None and graph.goal is not None:
                    resstep = self._build_step(graph,
                                               current,
                                               connection, graph.goal, counter)
                if resstep is not None:
                    heapq.heappush(open_set, resstep)
                else:
                    raise Exception("Could not make a restricted waiting step")

            return None  # short-circuit: do not expand any other neighbour
        for connection in step_options:

            next_zone = connection.zone
            next_tick = current.tick + 1
            # print("check tick", agent_id, next_tick)

            state = (next_zone.name, next_tick)

            # unfeasible / forbidden == banned states at time `tick`
            if state in unfeasible:
                continue
            # TODO : for _is_forbidden, better connection than next_zone
            if self._is_forbidden(next_tick, connection, constraints):
                # print(agent_id, state)
                # print("unfeasible", agent_id, unfeasible)
                unfeasible.add(state)
                continue
            # visited == not banned, just redundant
            if state in visited:
                # print("visited", agent_id, visited)
                continue
            # can_transition == temporary or permanent (not) evaluable state
            # include cases to which prioplanner doesn't have access
            if not self._can_transition(current, connection):
                continue
            #print("selected", agent_id, current, state)
            visited.add(state)
            step: Step | None = None
            # print("selected candidate", agent_id, next_tick, connection.zone.name)
            if graph is not None and graph.goal is not None:
                step = self._build_step(graph, current,
                                        connection, graph.goal, counter)
            if step is not None:
                if step.f_cost == float("inf"):
                    unfeasible.add(state)
                    continue
            else:
                raise Exception("Could not make a step")

            heapq.heappush(open_set, step)

    # -------------------------
    # Rules (clean separation)
    # -------------------------

    # def _is_forbidden(
    #     self,
    #     tick: int,
    #     agent_id: int,
    #     zone: Zone,
    #     constraints: Dict[int, Dict[int, Dict[str, List[Zone | Edge]]]],
    # ) -> bool:
    #     return zone in constraints.get(tick, {}) \
    #                               .get(agent_id, {}) \
    #                               .get("zones", list) or \
    #                     zone in constraints.get(tick, {}) \
    #                               .get(agent_id, {}) \
    #                               .get("edges", list)
    
    def _is_forbidden(
        self,
        tick: int,
        conn: Connection,
        constraints: ConstrMap,
    ) -> bool:
        # TODO 
        # is not a set: it is a dict of zones / edges
        # with counted capacity
        # TODO 
        # this should replace is_forbidden
        candzone: str = conn.zone.name
        candedge: None | tuple = None
        # does the zone has spare capacity?
        cons_zones: ConstraintZone = constraints.get(tick, {}).get("zones", {})
        zone = cons_zones.get(candzone)
        if zone and zone["capacity"] == zone["counter"]:
            print(candzone, zone)
            return True
        #print(zone, zone["capacity"], zone["counter"])
        # zone has spare capacity, and the edge?
        if conn.edge is not None:
            candedge = conn.edge.nodenames
            cons_edges: ConstraintEdge = constraints.get(tick, {}).get("edges", {})
            edge = cons_edges.get(candedge)
            if edge and edge["capacity"] == edge["counter"]:
                print(candedge, edge)
                return True
        # both has capacity
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

        g_cost = current.g_cost + zone.weighted_cost

        step = Step(
            zone=zone,
            tick=current.tick + 1,
            g_cost=g_cost,
            parent=current,
            wait=wait,
            counter=next(counter),
            f_cost=0.0,
        )

        step.f_cost = self._compute_f_cost(graph, g_cost, zone, goal)
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
