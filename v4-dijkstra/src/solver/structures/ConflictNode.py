from __future__ import annotations
import headq
from copy import deepcopy
from typing import List, Optional
from enum import auto, StrEnum
from roadmap_entitites import Step, RoadMap
from constraints import ConstrMap
from ...model.agent.Agent import Agent
from ...model.graph.Graph import Connection


class Constraint:
    pass


class CTNode:
    def __init__(self, parent: Optional[CTNode] = None, new_conflict):
        self.roadmaps: RoadMap | None = None
        self.parent = parent
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

    def add_constraints(self, c: Constraint) -> None:
        self.constraints.append(c)

    def update_solutions(self, a: Agent) -> None:
        pass

    def calc_sol_cost(self, ) -> float:
        pass



class Tree:
    root: CTNode


class State(StrEnum):
    WAIT = auto()
    MOVE = auto()