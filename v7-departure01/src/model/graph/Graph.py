from dataclasses import dataclass, field
from typing import List, Optional, Dict
from src import ValidZone, ValidZoneMetadata, ValidEdge, ValidEdgeMetadata
from .Zone import Zone, StartZone, EndZone, HubFactory
from .Edge import Edge
from ...solver.heuristics.heuristics import GraphHeuristic


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


class Graph:
    def __init__(self, graphdata: GraphData, methods: GraphHeuristic) -> None:
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
        self.exec_methods = methods
        self.exec_methods()

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

    def exec_methods(self) -> None:
        self.methods.hub_connections(self)
        self.methods.compute_reverse_map(self)

    # def _hub_connections(self) -> None:
    #     ...

    # def _compute_reverse_map(self) -> None:
    #     ...

