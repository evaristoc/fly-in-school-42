from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Type, Literal, cast
from src import ValidZone, ValidZoneMetadata, ValidEdge, ValidEdgeMetadata
from .Edge import Edge
from .Connection import Connection


class Zone(ABC):
    def __init__(
                    self,
                    mandatory: ValidZone,
                    meta: ValidZoneMetadata
                ) -> None:
        self.x = mandatory.x
        self.y = mandatory.y
        self.name = mandatory.name
        self.z: int = 0
        self.zone = meta.zone
        self.max_drones = meta.max_drones
        self.color = meta.color
        self.weighted_cost = meta.weighted_cost
        self.max_wait = meta.max_wait
        self.neighbours: List[Connection] = []

    @classmethod
    @abstractmethod
    def defaults(cls) -> ValidZoneMetadata:
        ...


# TODO why do I have to set max drones for start and end?
class StartZone(Zone):
    @classmethod
    def defaults(cls) -> ValidZoneMetadata:
        return ValidZoneMetadata(
            color="green",
            max_drones=1,
            weighted_cost=0,
            max_wait=99999999999
        )


class EndZone(Zone):
    @classmethod
    def defaults(cls) -> ValidZoneMetadata:
        return ValidZoneMetadata(
            color="yellow",
            max_drones=99999999999,
            weighted_cost=1,
            max_wait=99999999999
        )


class NormalZone(Zone):
    @classmethod
    def defaults(cls) -> ValidZoneMetadata:
        return ValidZoneMetadata(
            zone="normal",
            color="white",
            max_drones=1,
            weighted_cost=1,
            max_wait=20
        )


class PriorityZone(Zone):
    @classmethod
    def defaults(cls) -> ValidZoneMetadata:
        return ValidZoneMetadata(
            zone="priority",
            color="blue",
            max_drones=1,
            weighted_cost=.3,
            max_wait=20
        )


class RestrictedZone(Zone):
    @classmethod
    def defaults(cls) -> ValidZoneMetadata:
        return ValidZoneMetadata(
            zone="restricted",
            color="red",
            max_drones=1,
            weighted_cost=1,
            max_wait=2
        )


class BlockedZone(Zone):
    @classmethod
    def defaults(cls) -> ValidZoneMetadata:
        return ValidZoneMetadata(
            zone="blocked",
            color="red",
            max_drones=0,
            weighted_cost=9999999999,
            max_wait=0
        )


class HubFactory:
    """
    >>> defaultnormalnode = HubBuilder(validnodeinstance)
    >>> definedzonenode = HubBuilder(validnodeinstance, validmetadata)
    >>> startnode =
        HubBuilder(validnodeinstance, meta=validmetadata?, prefix="start_hub:")
    """

    # allowed_fields = {"zone", "color", "max_drones", "waiting_range"}
    # this is required - means: all classes of type Zone... man...
    ZoneClass = type[Zone]
    # need to set type of mapping, otherwise point also to Unknown
    mapping: dict[str, ZoneClass] = {
        "restricted": RestrictedZone,
        "normal": NormalZone,
        "priority": PriorityZone,
        "blocked": BlockedZone,
        "source": StartZone,
        "sink": EndZone
    }

    @classmethod
    def create(
                    cls,
                    mandatory: ValidZone,
                    meta: Optional[ValidZoneMetadata] = None,
                    prefix: Optional[str] = None
                ) -> Zone:
        default_config: ValidZoneMetadata
        print("in graph class instance - prefix:", prefix)
        if prefix == "start_hub:":
            zone_subcls = cls.mapping["source"]
            default_config = zone_subcls.defaults()
            # update the values of that Pydantic instance with
            # the new values if any
            if meta:
                merged_config = default_config.model_copy(
                    update=meta.model_dump(exclude_unset=True))
                # return the correct concrete instance
                return zone_subcls(mandatory, merged_config)
            else:
                return zone_subcls(mandatory, default_config)
        if prefix == "end_hub:":
            zone_subcls = cls.mapping["sink"]
            default_config = zone_subcls.defaults()
            # update the values of that Pydantic instance with
            # the new values if any
            if meta:
                merged_config = default_config.model_copy(
                    update=meta.model_dump(exclude_unset=True))
                # return the correct concrete instance
                return zone_subcls(mandatory, merged_config)
            else:
                return zone_subcls(mandatory, default_config)
        ZoneType: Type = Literal["restricted", "normal", "priority",
                                 "blocked", "source", "sink"]
        # check zone or set to normal zone
        zone = cast(ZoneType, (meta.zone if meta else None) or "normal")
        # get the concrete class to be instantiated based on zone
        # see that if no zone provided, then use the normal subclass as default
        if zone:
            # zone now always get a value
            zone_subcls = cls.mapping[zone]
            # get the default Pydantic instance of selected concrete node
            default_config = zone_subcls.defaults()
            # update the values of that Pydantic instance with
            # the new values if any
            if meta:
                merged_config = default_config.model_copy(
                    update=meta.model_dump(exclude_unset=True))
                # return the correct concrete instance
                return zone_subcls(mandatory, merged_config)
            else:
                return zone_subcls(mandatory, default_config)
        raise Exception("Zone cant be created by the factory")
