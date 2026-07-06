from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Type
from ..structures.roadmap_entitites import Step, RoadMap
from ..strategies.costheuristics.costheuristics import Heuristic, ZeroHeuristic
from ..strategies.pathmethods.pathmethods import PathAlgorithm, PathRules, CostFunction
from ...model.graph.Zone import Zone

@dataclass
class PathfinderData:
    algo: Type[PathAlgorithm]
    pathrules: Type[PathRules]
    costfunc: Type[CostFunction]
    heuristic: Optional[Heuristic]
    heuristic_weight: float
    time_horizon_factor: int


class Pathfinder:
    def __init__(self, pfdata: PathfinderData) -> None:
        self.heuristic = pfdata.heuristic or ZeroHeuristic()
        self.heuristic_weight = pfdata.heuristic_weight if pfdata.heuristic_weight is not None else 0.0
        self.time_horizon_factor = pfdata.time_horizon_factor if pfdata.time_horizon_factor is not None else 3
        self.algo = pfdata.algo(pfdata.pathrules(), pfdata.costfunc())
        self.algo.mastersolver = self

    def solve(self, *args, **kargs):
        """return Optional[RoadMap]"""
        ...

    def _init_step(self, *args, **kargs):
        """return Optional[Step]"""
        ...

    def _build_step(self, *args, **kargs):
        """return Step"""
        ...

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
