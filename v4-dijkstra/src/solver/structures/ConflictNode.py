from __future__ import annotations
import headq
from copy import deepcopy
from typing import List, Optional
from enum import auto, StrEnum
from roadmap_entitites import Step, RoadMap
from constraints import ConstrMap, ConstraintZone, ConstraintEdge
from ..pathfinder.pathfinder import Pathfinder
from ...model.agent.Agent import Agent
from ...model.graph.Graph import Zone, Edge

class Conflict:
    pass

class VertexConflict(Conflict):
    agent: Agent
    zone: Zone
    tick: int


class EdgeConflict(Conflict):
    agent: Agent
    zone_from: Zone
    zone_to: Zone
    tick: int

class CTNode:
    def __init__(self, allagents: List[Agent], parent: Optional[CTNode] = None):
        self.roadmaps: RoadMap | None = None
        self.parent = parent
        self.agent: Agent | None = None
        self.allagents: List[Agent] = allagents
        self.cost: float = float('inf')
        self.left: Optional[CTNode] = None
        self.right: Optional[CTNode] = None
        self.constraints: ConstrMap | None = None
        if self.parent:
            self.constraints = deepcopy(self.parent.constraints)

    @property
    def parent(self) -> CTNode:
        return self._parent

    @property
    def left(self) -> CTNode:
        return self._left

    @left.setter
    def left(self, v: CTNode) -> None:
        self._left = v

    @property
    def right(self) -> CTNode:
        return self._right

    @right.setter
    def right(self, v: CTNode) -> None:
        self._right = v

    def register_solutions(self) -> None:
        pass

    def add_constraints(self, conflict: Conflict) -> None:
        if not conflict:
            return
        if not self.parent:
            return None
        if self.parent.left is self:
            self.agent = conflict.agent_1
        else:
            self.agent = conflict.agent_2
        if not self.agent:
            raise Exception("ERROR at Conflict Node: No agent was created. Stopping.")
        if conflict.tick not in self.constraints:
            self.constraints[conflict.tick] = {"zones": {}, "edges": {}}
        if isinstance(conflict, VertexConflict):
            zconstrs: ConstraintZone = self.constraints[conflict.tick]["zones"]
            zname: str = conflict.zone.name
            if zname not in zconstrs:
                zconstrs[zname] = {"capacity": conflict.zone.max_drones, 
                                   "agents": set()}
            zconstrs[zname]["agents"].add(self.agent.agent_id)
        if isinstance(conflict, EdgeConflict):
            edge: Edge | None = None
            for n in conflict.zone_from.neighbours:
                if n.zone == conflict.zone_to:
                    edge = n.edge
            econstrs: ConstraintEdge = self.constraints[conflict.tick]["edges"]
            ename: tuple = edge.nodenames
            if ename not in econstrs:
                econstrs[ename] = {
                                "capacity": edge.max_link_capacity,
                                "agents": set()}
            econstrs[ename]["agents"].add(self.agent.agent_id)

    def update_solutions(self, pathfinder: Pathfinder, agents: List[Agent] | None = None) -> bool:
        if not agents:
            return False
        if agents is None:
            agents = [self.agent]
        for agent in agents:
            roadmap = agent.plan(pathfinder, self.constraints)
            if roadmap is None:
                return False
            else:
                self.roadmaps[agent.agent_id] = roadmap
                return True
        return False

    def calc_sol_cost(self) -> float:
        for roadmap in self.roadmaps.values():
            self.cost += roadmap.cost

class Tree:
    root: CTNode

class State(StrEnum):
    WAIT = auto()
    MOVE = auto()