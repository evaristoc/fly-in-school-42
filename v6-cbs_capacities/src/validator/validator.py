import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# class ZoneType(str, Enum):
#     NORMAL = "normal"
#     BLOCKED = "blocked"
#     RESTRICTED = "restricted"
#     PRIORITY = "priority"


class ValidZone(BaseModel):
    name: str = Field(...)
    x: int = Field(...)
    y: int = Field(...)

    @field_validator("name")
    @classmethod
    def validate_node_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(
                "node name should be only lowercase "
                "alphanum and or underscore")
        return v


class ValidZoneMetadata(BaseModel):
    zone: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default="white")
    max_drones: Optional[int] = Field(default=1, ge=0)
    weighted_cost: float = Field(default=0)
    max_wait: int = Field(default=99999)

    @field_validator("weighted_cost")
    @classmethod
    def validate_weigcost(cls, v: float) -> float:
        c = v
        if c < 0:
            raise ValueError("values of weighted_cost must be non-negative")
        return v

    @field_validator("max_wait")
    @classmethod
    def validate_maxwait(cls, v: int) -> int:
        c = v
        if c < 0:
            raise ValueError("values of max_wait must be non-negative")
        return v


class ValidEdge(BaseModel):
    node1: str = Field(...)
    node2: str = Field(...)

    @field_validator("node1", "node2")
    @classmethod
    def validate_node_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("edge nodes should be only "
                             "lowercase alphanum and or underscore")
        return v


class ValidEdgeMetadata(BaseModel):
    max_link_capacity: int = Field(default=1, ge=0)
