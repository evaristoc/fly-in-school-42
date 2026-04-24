# models.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple
from ...model.graph.Graph import Zone


@dataclass(order=True)
class Step:
    f_cost: float
    counter: int
    g_cost: float = field(compare=False)
    tick: int = field(compare=False)
    zone: Optional[Zone] = field(compare=False)
    parent: Optional["Step"] = field(compare=False, default=None)
    wait: int = field(compare=False, default=0)


@dataclass
class RoadMap:
    agent_id: int
    cost: float
    states: Optional[Dict[int, Tuple[Zone, Zone]]] = None
