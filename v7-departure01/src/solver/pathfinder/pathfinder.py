from typing import Dict, Set, Tuple, List, Optional, Iterator
import heapq
from itertools import count

from ..structures.roadmap_entitites import Step, RoadMap
from ..structures.constraints import ConstrMap
from ..heuristics.costheuristics import Heuristic, ZeroHeuristic
from ..heuristics.pathmethods import PathHeuristics
from ...model.graph.Zone import Zone, StartZone, BlockedZone
from ...model.graph.Connection import Connection
from ...model.graph.Graph import Graph
    

class Pathfinder:
    def __init__(
        self,
        policy: PathHeuristics,
        heuristic: Optional[Heuristic] = None,
        heuristic_weight: float = 0.0,
        time_horizon_factor: int = 3,
    ):
        self.heuristic = heuristic or ZeroHeuristic()
        self.heuristic_weight = heuristic_weight
        self.time_horizon_factor = time_horizon_factor
        self.policy = policy

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
        visited: Set[Tuple[str, str]] = set()
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
            self.policy.expand(
                self,
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

    # -------------------------
    # Step construction
    # -------------------------

    def _build_step(
        self,
        current: Step,
        connection: Connection,
        counter: Iterator[int],
    ) -> Step:

        zone = connection.zone

        wait = current.wait + 1 if zone == current.zone else 0
        step = Step(
            zone=zone,
            tick=current.tick + 1,
            g_cost=0.0,
            parent=current,
            wait=wait,
            counter=next(counter),
            f_cost=self.methods.compute_f_cost(self, current, zone)
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
