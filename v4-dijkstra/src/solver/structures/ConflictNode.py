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
    def __init__(self, parent: Optional[CTNode] = None, conflict: Conflict | None = None):
        self.roadmaps: RoadMap | None = None
        self.parent = parent
        self.conflict: Conflict | None = conflict
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
        if conflict.tick not in self.constraints:
            self.constraints[conflict.tick] = {"zones": {}, "edges": {}}
        if isinstance(conflict, VertexConflict):
            zconstrs: ConstraintZone = self.constraints[conflict.tick]["zones"]
            zname: str = conflict.zone.name
            if zname not in zconstrs:
                zconstrs[zname] = {"capacity": conflict.zone.max_drones, 
                                   "agents": {}}
            if len(zconstrs[zname]["agents"]) < zconstrs[zname]["capacity"]:
                zconstrs[zname]["agents"].add(self.agent1)
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
                                "agents": {}}
            if len(econstrs[ename]["agents"]) < econstrs[ename]["capacity"]:
                econstrs[ename]["agents"].add(self.agent1)

    def update_solutions(self) -> None:
        for agent in self.agents:
            # The agent plans a path around all higher-priority paths
            roadmap = agent.plan(agent.pathfinder, self.constraints)
            if roadmap is None:
                success = False
                break
            self.roadmap[agent.agent_id] = roadmap
        if success:
            return
        else:
            raise Exception("failed to create roadmap")

    def calc_sol_cost(self) -> float:
        for roadmap in self.roadmaps.values():
            self.cost += roadmap.cost

class Tree:
    root: CTNode

class State(StrEnum):
    WAIT = auto()
    MOVE = auto()