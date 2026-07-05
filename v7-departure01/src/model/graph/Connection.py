from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .Zone import Zone
    from .Edge import Edge


@dataclass
class Connection:
    zone: "Zone"
    edge: Optional["Edge"] = field(default=None)
