from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Literal, cast
from src import ValidZone, ValidZoneMetadata, ValidEdge, ValidEdgeMetadata


@dataclass
class Connection:
    zone: 'Zone'
    edge: Optional['Edge'] = field(default=None)


@dataclass
class GraphData():
    nb_drones: int = field(default=0)
    zones: List[Zone] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def add_edge(self,  mandatory: ValidEdge,
                 meta: Optional[ValidEdgeMetadata] = None) -> None:
        new_edge = Edge(mandatory, meta)
        self.edges.append(new_edge)

    def add_zone(
                    self,
                    mandatory: ValidZone,
                    meta: Optional[ValidZoneMetadata] = None,
                    prefix: Optional[str] = None
                ) -> None:
        new_zone = HubFactory.create(mandatory, meta, prefix)
        self.zones.append(new_zone)


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
        self.neighbours: List['Connection'] = []

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
            max_wait=99999
        )


class EndZone(Zone):
    @classmethod
    def defaults(cls) -> ValidZoneMetadata:
        return ValidZoneMetadata(
            color="yellow",
            max_drones=1,
            weighted_cost=1,
            max_wait=99999
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
            weighted_cost=.8,
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
            weighted_cost=99999,
            max_wait=0
        )


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
        print(prefix)
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
        ZoneType = Literal["restricted", "normal", "priority",
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


class Graph:
    def __init__(self, graphdata: GraphData) -> None:
        self.nb_drones = graphdata.nb_drones
        self.zones = graphdata.zones
        self.edges = graphdata.edges
        if len(self.edges) == 0 or len(self.zones) == 0:
            raise Exception("Graph doesn't have nodes / edges?")
        if int(self.nb_drones) <= 0:
            raise Exception("Incorrect value of drones")
        if not all(self.zones) or not all(self.edges):
            raise Exception("Either None-valued zones or None-valued edges")
        self.hop_map: Optional[Dict[Zone, float]] = None
        self._hub_connections()
        self._compute_hop_map()

    @property
    def startzone(self) -> Optional[Zone]:
        if self.zones:
            for z in self.zones:
                if isinstance(z, StartZone):
                    return z
        return None

    @property
    def goal(self) -> Optional[Zone]:
        if self.zones:
            for z in self.zones:
                if isinstance(z, EndZone):
                    return z
        return None

    def register_zone(self, zone: Zone) -> None:
        self.zones.append(zone)

    def register_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def _hub_connections(self) -> None:
        for z in self.zones:
            for edge in self.edges:
                if z.name in edge.nodenames:
                    for neigh in self.zones:
                        if neigh.name != z.name and \
                                neigh.name in edge.nodenames:
                            conn = Connection(neigh, edge)
                            if conn not in z.neighbours:
                                z.neighbours.append(conn)
            # # the following will solve the "waiting" case later...
            z.neighbours.append(Connection(z))

    def _compute_hop_map(self) -> None:
        # return {zone: min_hops_to_goal}
        hop_map = {zone: float('inf') for zone in self.zones}
        if self.goal:
            hop_map[self.goal] = 0
            queue = [self.goal]
        else:
            queue = []
        while queue:
            current = queue.pop(0)
            if current:
                current_hop = hop_map[current]
                for conn in current.neighbours:
                    if conn:
                        neighbor = conn.zone
                        if hop_map[neighbor] > current_hop + 1:
                            hop_map[neighbor] = current_hop + 1
                            queue.append(neighbor)
        if hop_map:
            self.hop_map = hop_map
