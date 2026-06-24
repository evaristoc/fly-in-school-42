from typing import Dict, Set, TypeAlias
from ...model.agent.Agent import Agent

# TODO : changing constraint to {tick: {"zones" | "edges": {Zone | Edge: {"capacity": val, "agents": {Agents}}}}}
ConstraintValues: TypeAlias = dict[str, int | Set[int]]
# str == name of zone; tuple == name of edge
ConstraintZone: TypeAlias = dict[str, ConstraintValues]
ConstraintEdge: TypeAlias = dict[tuple, ConstraintValues]
# "zones" or "edges"
Constraints: TypeAlias = dict[str, ConstraintZone | ConstraintEdge]
ConstrMap: TypeAlias = Dict[int, Constraints]
