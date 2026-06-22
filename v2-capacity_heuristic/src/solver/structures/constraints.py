from typing import Dict, TypeAlias

# TODO : might it be Connections instead?
# TODO : changing constraint to {tick: {"zones" | "edges": {Zone | Edge: {"capacity": val, "counter": val}}}}
ConstraintValues: TypeAlias = dict[str, int]
# str == name of zone; tuple == name of edge
ConstraintZone: TypeAlias = dict[str, ConstraintValues]
ConstraintEdge: TypeAlias = dict[tuple, ConstraintValues]
# "zones" or "edges"
Constraints: TypeAlias = dict[str, ConstraintZone | ConstraintEdge]
ConstrMap: TypeAlias = Dict[int, Constraints]
