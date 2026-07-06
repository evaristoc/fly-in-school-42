from dataclasses import dataclass, field
from types import MethodType
from typing import List, Optional, Dict
from src import ValidZone, ValidZoneMetadata, ValidEdge, ValidEdgeMetadata
from ...solver.heuristics.graphmethods import GraphHeuristic

from .Zone import Zone, StartZone, EndZone, HubFactory
from .Edge import Edge
from .Connection import Connection

@dataclass
class GraphData():
    nb_drones: int = field(default=0)
    zones: List["Zone"] = field(default_factory=list)
    edges: List["Edge"] = field(default_factory=list)

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
        self.hub_connections()
        self.reversecost_map: Optional[Dict[Zone, float]] = None
        self.exec_methods = methods
        #self.compute_reverse_map = MethodType(self.exec_methods().compute_reverse_map, self)
        self.exec_methods().compute_reverse_map(self)


    @property
    def startzone(self) -> Optional["Zone"]:
        if self.zones:
            for z in self.zones:
                if isinstance(z, StartZone):
                    return z
        return None

    @property
    def goal(self) -> Optional["Zone"]:
        if self.zones:
            for z in self.zones:
                if isinstance(z, EndZone):
                    return z
        return None

    def register_zone(self, zone: "Zone") -> None:
        self.zones.append(zone)

    def register_edge(self, edge: "Edge") -> None:
        self.edges.append(edge)

    def hub_connections(self):
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

    # def exec_methods(self, graph: "Graph") -> None:
    #     self.methods.compute_reverse_map(graph)
    #     print("methods", self.methods.compute_reverse_map.__dict__)

    # def _hub_connections(self) -> None:
    #     ...

    # def _compute_reverse_map(self) -> None:
    #     ...

