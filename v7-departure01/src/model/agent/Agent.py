from dataclasses import dataclass
from typing import Optional
from ..graph.Graph import Graph
from ...solver.structures.roadmap_entitites import RoadMap
from ...solver.pathfinder.pathfinder import Pathfinder, PathfinderData
from ...solver.structures.constraints import ConstrMap


@dataclass
class Agent:
    graph: Graph
    agent_id: int
    entry_time: int = 0
    pathfinder: Pathfinder
    
    def plan(self,
             pathfinderDecl: Pathfinder,
             pathfinderdata: PathfinderData,
             constraints: ConstrMap)\
            -> Optional[RoadMap]:
        """
        Delegates pathfinding to a pathfinder.
        Instantiate a pathfinder passed from very top of the chain (manager). 
        Keeps Agent free from algorithmic complexity.
        """
        pathfinder = pathfinderDecl(pathfinderdata)
        return pathfinder.solve(
            graph=self.graph,
            agent_id=self.agent_id,
            entry_time=self.entry_time,
            constraints=constraints,
        )
