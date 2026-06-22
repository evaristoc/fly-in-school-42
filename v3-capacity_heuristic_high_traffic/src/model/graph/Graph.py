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
        self.reversecost_map: Optional[Dict[Zone, float]] = None
        self._hub_connections()
        self._compute_reverse_map()

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

    # def _compute_hop_map(self) -> None:
    #     # return {zone: min_hops_to_goal}
    #     hop_map = {zone: float('inf') for zone in self.zones}
    #     if self.goal:
    #         hop_map[self.goal] = 0
    #         queue = [self.goal]
    #     else:
    #         queue = []
    #     while queue:
    #         current = queue.pop(0)
    #         if current:
    #             current_hop = hop_map[current]
    #             c = 0
    #             for conn in current.neighbours:
    #                 if conn and conn.edge:
    #                     c += conn.edge.max_link_capacity
    #             c = c - min(current.max_drones, c) + 1
    #             for conn in current.neighbours:
    #                 if conn:
    #                     neighbor = conn.zone
    #                     # OJO: it was 1 before being neighbor.max_drones/(1 + [n.edge.max_link_capacity for n in neighbor.neighbours if current.name in n.edge.nodenames][0])!
    #                     cost = 0
    #                     if conn.edge is not None:
    #                         cost = conn.zone.max_drones - 1 + conn.edge.max_link_capacity / c
    #                     else:
    #                         cost = conn.zone.max_drones
    #                     if hop_map[neighbor] > current_hop + cost:
    #                         hop_map[neighbor] = current_hop + cost
    #                         queue.append(neighbor)
    #     if hop_map:
    #         self.hop_map = hop_map
    def _compute_reverse_map(self) -> None:
        """
        This func computes the remaining cost of the shortest path between
        any node and the sink. It is calculated reverserly from the sink
        to any node, and it implements a Bellman-Ford-ish algo.
        This is in fact the heuristic for the A* used to calculate drone best
        path. Based on the constraints and characteristics of the exercise,
        I found that the best candidate for cost calculation was the capacities.
        As this project is mostly for education purposes, I added detailed
        explanations of the reasoning of how it works further in the script 
        of this function.
        """
        # return {zone: min_hops_to_goal}
        reversecost_map = {zone: float('inf') for zone in self.zones}
        if self.goal:
            reversecost_map[self.goal] = 0
            queue = [self.goal]
        else:
            queue = []
        while queue:
            current = queue.pop(0)
            if current:
                current_hop = reversecost_map[current]
                """
                NOTE: (1)
                """
                overflow = 0
                for conn in current.neighbours:
                    if conn and conn.edge:
                        overflow += conn.edge.max_link_capacity
                """
                NOTE: (2)
                """
                overflow = overflow - min(current.max_drones, overflow) + 1
                # print("overflow", overflow, current.max_drones)
                for conn in current.neighbours:
                    if conn:
                        neighbor = conn.zone
                        # OJO: it was 1 before being neighbor.max_drones/(1 + [n.edge.max_link_capacity for n in neighbor.neighbours if current.name in n.edge.nodenames][0])!
                        overflowcost = 0
                        if conn.edge is not None:
                            """
                            NOTE: (3)
                            """
                            # overflowcost = conn.zone.max_drones - 1 + conn.edge.max_link_capacity / overflow
                            overflowcost = (conn.edge.max_link_capacity / overflow / conn.zone.max_drones) if conn.zone.max_drones > 0 else float('inf')
                        else:
                            """
                            NOTE: (4)
                            """
                            # overflowcost = current.max_drones
                            overflowcost = 1
                        if reversecost_map[neighbor] > current_hop + overflowcost:
                            reversecost_map[neighbor] = current_hop + overflowcost
                            queue.append(neighbor)
        if reversecost_map:
            self.reversecost_map = reversecost_map

"""
NOTE (1) === `  overflow = 0
                for conn in current.neighbours:
                    if conn and conn.edge:
                        overflow += conn.edge.max_link_capacity`
        ===
    We want to calculate a heuristic that internalizes
    the relationship between node capacity and edge traffic.
    The intution for that calculation is inspired on the
    rationale of the min cost max flow algo, but trying to
    evaluate it LOCALLY by node and how its effectiveness
    to solve the usual test examples.
    The result of that inspiration resulted in the notion
    of "overflow".
    We start by calculating the potential for overflow by
    estimating the max number of agents that can cross
    through all the nodes.

NOTE (2) === `overflow = overflow - min(current.max_drones, overflow) + 1` ===
    Then we correct the capacity of the edge to be overflowed given the capacity
    of the current node.
    This is an important aspect: the idea is to evaluate how the current node
    is able to overflow the channels, given it is filled to full its capacity.
    If the current node can contain more than what the connections
    can handle, then the MAX FLOW is what all those connections can support minus
    what the current flow can actually direct through.
    If the current node cannot overflow the channels, than the overflow is low.

NOTE (3) === `overflowcost = (conn.edge.max_link_capacity / overflow / conn.zone.max_drones) if conn.zone.max_drones > 0 else float('inf')` ===
    The value of the cost difference is calculated now as the proportion of
    agents that can cross through the edge against the capacity of the candidate zone.
    If the target node doesnt have capacity, the overflowcost is infinite.
    The expected result of the heuristic is that destinations with higher capacity
    can affort most traffic, so they have less cost. This is probably a more direct, immediate interpretation
    of what someone might expect from the heuristic cost and it might feel like a better analogy to
    what it could be expected from a flow-based interpretation: the most the capacity of the target
    zone, the most it can receive, and therefore lower its cost. In this case, the overflowcost is directly
    proportional to how much can cross through the edges and inversely proportional to how much
    the target zone can hold.
    This heuristic favours routes with high capacity.

NOTE (4) === `overflowcost = 1` ===
    If the incumbent node is "myself", the overflowcost is 
    just the unit.
"""
