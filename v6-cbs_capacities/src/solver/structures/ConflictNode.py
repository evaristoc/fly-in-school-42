from __future__ import annotations
import sys
from copy import deepcopy
from typing import List, Optional, Dict
from enum import auto, StrEnum
from dataclasses import dataclass
from .roadmap_entitites import RoadMap
from .constraints import ConstrMap, ConstraintZone, ConstraintEdge
from ..pathfinder.pathfinder import Pathfinder
from ...model.agent.Agent import Agent
from ...model.graph.Graph import Zone, Edge


class Conflict:
    pass


def print_solution(solution: dict):
    print("\n=== CBS SOLUTION (readable) ===")

    agents = list(solution.keys())

    # collect all ticks
    max_t = max(
        max(rm.states.keys()) for rm in solution.values()
    )

    # build time table
    for t in range(max_t + 1):
        line = f"t={t}: "
        for aid in agents:
            rm = solution[aid]

            if t in rm.states:
                _, zone = rm.states[t]
            else:
                _, zone = rm.states[max(rm.states.keys())]

            line += f"A{aid}={zone.name}\t"
        print(line)

    print("\n=== END ===\n")

@dataclass
class VertexConflict(Conflict):
    agent_1: Agent
    agent_2: Agent
    zone: Zone
    tick: int


@dataclass
class EdgeConflict(Conflict):
    agent_1: Agent
    agent_2: Agent
    zone_from: Zone
    zone_to: Zone
    tick: int


class CTNode:
    def __init__(self, allagents: List[Agent], parent: Optional[CTNode] = None):
        self.solution: Dict[RoadMap] = {}
        self.parent = parent
        self.agent_id: int = -1
        self.allagents: List[Agent] = allagents
        self.cost: float = float('inf')
        self._left: Optional[CTNode] = None
        self._right: Optional[CTNode] = None
        self.constraints: ConstrMap = {}
        if self.parent:
            self.constraints = deepcopy(self.parent.constraints)
            self.solution = deepcopy(self.parent.solution)

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

    def add_constraint(self, conflict: Conflict) -> None:
        if not conflict:
            return
        if not self.parent:
            return None
        if self.parent.left and self.parent.left is self:
            print("ctnode check:", conflict.agent_1)
            self.agent_id = conflict.agent_1
        if self.parent.right and self.parent.right is self:
            self.agent_id = conflict.agent_2
        # print("ctnode self:", id(self))
        # print("ctnode parent:", id(self.parent))
        # # print("ctnode same?", self.parent.left is self)
        # # print("in ct node class - printing parent:", self.parent.left)
        # print("in ct node class - printing conflict:", conflict)
        # print("in ct node class - printing conflict agent:", conflict.agent_1)
        # print("in ct node class - printing self agent:", self.agent_id)
        # sys.exit(1) 
        # if self.agent_id == -1:
        #     raise Exception("ERROR at Conflict Node: No agent was created. Stopping.")
        if conflict.tick not in self.constraints:
            self.constraints[conflict.tick] = {"zones": {}, "edges": {}}
        if isinstance(conflict, VertexConflict):
            zconstrs: ConstraintZone = self.constraints[conflict.tick]["zones"]
            zname: str = conflict.zone.name
            if zname not in zconstrs:
                zconstrs[zname] = {"capacity": conflict.zone.max_drones, 
                                   "agents": set()}
            zconstrs[zname]["agents"].add(self.agent_id)
        if isinstance(conflict, EdgeConflict):
            edge: Edge | None = None
            for n in conflict.zone_from.neighbours:
                if n.zone.name == conflict.zone_to.name:
                    edge = n.edge
            econstrs: ConstraintEdge = self.constraints[conflict.tick]["edges"]
            # ename: tuple = edge.nodenames
            ename: set | None = frozenset({conflict.zone_from.name, conflict.zone_to.name})
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", ename, edge)
            if ename and ename not in econstrs:
                econstrs[ename] = {
                                "capacity": edge.max_link_capacity,
                                "agents": set()}
            econstrs[ename]["agents"].add(self.agent_id)
        print("in conflict node instance: ", conflict.tick, self.constraints[conflict.tick])

    def update_solution(self, pathfinder: Pathfinder, agents: List[Agent] = []) -> bool:
        if self.agent_id != -1:
            agents = [agents[self.agent_id]]
        if len(agents) == 0:
            return False
        for agent in agents:
            roadmap: RoadMap = agent.plan(pathfinder, self.constraints)
            if roadmap is None:
                return False
            # print("in ct node, update sol - agents: ", agent.agent_id)
            # print("in ct node, update sol - constraints: ", self.constraints)
            # print("in ct node, update sol - states: ", roadmap.states)
            print(f"[CTNode {id(self)}] constraints keys:", self.constraints)
            self.solution[agent.agent_id] = roadmap
        print(f"[CTNode {id(self)}]: finished solution")
        print_solution(self.solution)
        return True

    def calc_sol_cost(self) -> float:
        for roadmap in self.solution.values():
            self.cost += roadmap.cost


class Tree:
    root: CTNode


class State(StrEnum):
    WAIT = auto()
    MOVE = auto()