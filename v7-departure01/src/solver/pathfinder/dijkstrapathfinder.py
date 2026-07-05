from typing import Dict, Tuple, Optional, Iterator
from .pathfinder import Pathfinder
from ..structures.roadmap_entitites import Step, RoadMap
from ..structures.constraints import ConstrMap
from ...model.graph.Zone import Zone
from ...model.graph.Connection import Connection
from ...model.graph.Graph import Graph


class DijkstraPathfinder(Pathfinder):
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
        self.algo.mastersolver = self
        return self.algo.search(graph, agent_id, entry_time, constraints)

    # TODO make the step construction a factory adaptable to ANY algo
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
            f_cost=self.algo.costfunc.compute_f_cost(current, zone)
        )
        return step

