from dataclasses import dataclass, field
from typing import Optional
from .Zone import Zone
from .Edge import Edge


@dataclass
class Connection:
    zone: Zone
    edge: Optional[Edge] = field(default=None)
