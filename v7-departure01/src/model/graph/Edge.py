from dataclasses import dataclass, field
from typing import Optional, Tuple
from src import ValidEdge, ValidEdgeMetadata
from .Zone import Zone


@dataclass
class Connection:
    zone: 'Zone'
    edge: Optional['Edge'] = field(default=None)


class Edge():
    def __init__(
                    self,
                    mandatory: ValidEdge,
                    meta: Optional[ValidEdgeMetadata] = None
                ):
        self.nodenames: Tuple[str, str] = (mandatory.node1, mandatory.node2)
        self.max_link_capacity: int = 1
        if meta:
            self.max_link_capacity = meta.max_link_capacity
