from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..pathfinder.pathfinder import Pathfinder


class PathRules:
    def can_transition(self, *args, **kargs) -> bool:
        ...

    def is_forbidden(self, *args, **kargs) -> bool:
        ...


class CostFunction:
    @staticmethod
    def compute_f_cost(*args, **kargs) -> float:
        ...


class PathAlgorithm:
    def __init__(self, policyinst: PathRules, costfuncinst: CostFunction) -> None:
        """
        get instances of constfunct and policy
        accepts different kind of costfuncs and policies (as long as 
        consistent with the search / expand implementation as well as
        mastersolver implementation)
        """
        self.costfunc = costfuncinst
        self.policy = policyinst
        self.mastersolver: Optional["Pathfinder"] = None

    def search(self, *args, **kargs) -> None:
        ...

    def expand(self, *args, **kargs) -> None:
        ...
