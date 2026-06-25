from dataclasses import dataclass
from typing import Dict, Set, Optional
from ..graph.Graph import Graph
from ...solver.structures.roadmap_entitites import RoadMap
from ...solver.pathfinder.pathfinder import Pathfinder
from ...solver.structures.constraints import ConstrMap


@dataclass
class Agent:
    graph: Graph
    agent_id: int
    entry_time: int = 0

    def plan(self,
             pathfinder: Pathfinder,
             constraints: ConstrMap)\
            -> Optional[RoadMap]:
        """
        Delegates pathfinding to a pathfinder.
        Keeps Agent free from algorithmic complexity.
        """
        return pathfinder.solve(
            graph=self.graph,
            agent_id=self.agent_id,
            entry_time=self.entry_time,
            constraints=constraints,
        )
