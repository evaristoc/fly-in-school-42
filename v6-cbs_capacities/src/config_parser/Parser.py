from __future__ import annotations
import re
from pathlib import Path
from collections import defaultdict
from functools import reduce
from typing import Dict, Any, Optional, Set, List
from pydantic import ValidationError
from ..error_handlers import ConfigError, DuplicatesError, InvalidEntryError
from ..validator import ValidZone, ValidZoneMetadata, ValidEdge, \
    ValidEdgeMetadata
from ..model.graph.Graph import GraphData

named_nodes: List[str] = []
coordinates: Dict[int, List[int]] = defaultdict(list)
edge_sets: List[Set[str]] = []


class Parser:
    def __init__(self) -> None:
        self._graphdata = GraphData()

    def _read_lines(self, path: Path) -> List[str]:
        try:
            with open(path, "r") as f:
                lines = f.readlines()
                return lines
        except Exception as e:
            raise RuntimeError("Failed to read config:"
                               f" {path}") from e

    def _skip(self, line: str) -> bool:
        line = line.strip()
        return not line or line.startswith("#")

    def _parse_num_drones(self, line: str, lineno: int) -> None:
        try:
            nb_drones = int(line.split(' ')[1])
        except Exception:
            raise Exception()
        if nb_drones < 0:
            raise Exception()
        self._graphdata.nb_drones = nb_drones

    def _parse_node_line(self, line: str, lineno: int) -> Dict[str, Any]:
        # this should prevent to split if space is in the metadata section!
        linepattern = r'\s+(?=(?:[^\[]*\[[^\]]*\])*[^\]]*$)'
        node_data = re.split(linepattern, line)
        metapattern = r'\[[^\[\]]+\]$'
        meta_dict: Dict[str, Any] = {}
        if len(node_data) not in [4, 5]:
            raise InvalidEntryError("invalid number of arguments at line "
                                    f"{lineno}")
        if len(node_data) == 5:
            meta_raw = node_data[4]
            if not re.match(metapattern, meta_raw):
                raise InvalidEntryError(f"invalid node metadata at line "
                                        f"{lineno}")
            try:
                meta_items = meta_raw.strip("[]").split()
                meta_dict = {k: v for k, v in (item.split("=", 1)
                                               for item in meta_items)}
            except ValueError:
                raise InvalidEntryError("malformed node metadata at line "
                                        f"{lineno}")
        mandatory_dict = {"name": node_data[1], "x": node_data[2],
                          "y": node_data[3]}
        return {"type": "node", "prefix": node_data[0],
                "mandatory": mandatory_dict, "meta": meta_dict or None}

    def _parse_edge_line(self, line: str, lineno: int) -> Dict[str, Any]:
        edge_data = line.split()
        metapattern = r'\[[^\[\]]+\]$'
        meta_dict: Dict[str, Any] = {}
        if len(edge_data) not in [2, 3]:
            raise InvalidEntryError("invalid number of arguments at line "
                                    f"{lineno}")
        if len(edge_data) == 3:
            meta_raw = edge_data[2]
            if not re.match(metapattern, meta_raw):
                raise InvalidEntryError("invalid edge metadata at line "
                                        f"{lineno}")
            try:
                meta_items = meta_raw.strip("[]").split()
                meta_dict = {k: v for k, v in (item.split("=", 1)
                                               for item in meta_items)}
            except ValueError:
                raise InvalidEntryError("malformed metadata at line "
                                        f"{lineno}")
        nodes = edge_data[1].split("-")
        if len(nodes) != 2:
            raise InvalidEntryError("incorrect number of conn nodes at line "
                                    f"{lineno}")
        node1 = nodes[0]
        node2 = nodes[1]
        if node1 == node2:
            raise DuplicatesError("conn nodes should be different at at line "
                                  f"{lineno}")
        mandatory_dict = {"node1": node1, "node2": node2}
        return {"type": "edge", "mandatory": mandatory_dict,
                "meta": meta_dict or None}

    def _load_validnode(self, node_data: Dict[str, Any], lineno: int) -> None:
        validnodeinst: ValidZone = ValidZone(**node_data["mandatory"])
        validmetainst: Optional[ValidZoneMetadata] = ValidZoneMetadata(
            **node_data["meta"]) if node_data["meta"] else None
        if validnodeinst.name in named_nodes:
            raise DuplicatesError("duplicate hub name at line "
                                  f"{lineno}")
        else:
            named_nodes.append(validnodeinst.name)
        if validnodeinst.x in coordinates and validnodeinst.y in coordinates[
                validnodeinst.x]:
            raise DuplicatesError("duplicate coordinates for a hub at line "
                                  f"{lineno}")
        else:
            coordinates[validnodeinst.x].append(validnodeinst.y)
        self._graphdata.add_zone(validnodeinst, validmetainst,
                                 node_data["prefix"])

    def _load_validedge(self, edge_data: Dict[str, Any], lineno: int) -> None:
        validedgeinst: ValidEdge = ValidEdge(**edge_data["mandatory"])
        if set([validedgeinst.node1, validedgeinst.node2]) in edge_sets:
            raise DuplicatesError("hub connection at line "
                                  f"{lineno} has been already set")
        else:
            edge_sets.append(set([validedgeinst.node1, validedgeinst.node2]))
        validmetainst: Optional[ValidEdgeMetadata] = ValidEdgeMetadata(
            **edge_data["meta"]) if edge_data["meta"] else None
        self._graphdata.add_edge(validedgeinst, validmetainst)

    def _parse_line(self, line: str, lineno: int) -> Optional[Dict[str, Any]]:
        line = line.strip()
        hubpattern = r'^\s*(start_|end_)?hub:.*'
        connpattern = r'^\s*connection:.*'
        dronespattern = r'^nb_drones:'
        if re.match(dronespattern, line):
            # the drone parsing doesnt return a dict, it is directly
            # appended to graphdata
            try:
                self._parse_num_drones(line, lineno)
            except RuntimeError as e:
                print(e)
                exit(1)
            except Exception:
                raise Exception("an error ocurred when parsing nb_drones, "
                                "please verify is integer larger than 0, "
                                f"at line {lineno}")
        if re.match(hubpattern, line):
            return self._parse_node_line(line, lineno)
        if re.match(connpattern, line):
            return self._parse_edge_line(line, lineno)
        return None

    def _check_nodes_and_edges(self) -> None:
        edge_set = reduce(lambda x, y: x.union(y), edge_sets)
        if len(edge_set ^ set(named_nodes)) > 0:
            raise InvalidEntryError("there are either unconnected or not "
                                    "declared hubs: "
                                    f"{edge_set ^ set(named_nodes)}")

    def etl_config(self, path: Path) -> Optional[GraphData]:
        try:
            lines = self._read_lines(path)
        except RuntimeError as e:
            print(f"File Opening Error: {e}")
            exit(1)

        for lineno, line in enumerate(lines):
            if self._skip(line):
                continue
            try:
                parsed = self._parse_line(line, lineno)
                if not parsed:
                    continue
            except ConfigError as e:
                print(f"Config Error: {e}")
                exit(1)
            except Exception as e:
                print(f"Parsing Error: {e}")
                exit(1)
            try:
                if parsed["type"] == "node":
                    print(parsed)
                    self._load_validnode(parsed, lineno)
                elif parsed["type"] == "edge":
                    print(parsed)
                    self._load_validedge(parsed, lineno)
            except ConfigError as e:
                print(f"Config Error: {e}")
                exit(1)
            except ValidationError as errs:
                for ee in errs.errors():
                    print(f"Validation Error: {ee}")
                exit(1)
            except Exception as e:
                raise Exception("Unexpected Error at line "
                                f"{lineno}: {e}") from e
        try:
            self._check_nodes_and_edges()
        except ConfigError as e:
            print(f"Config Error: {e}")
            exit(1)
        except Exception as e:
            print(f"Unexpected Error during node / egde eval: {e}")
            exit(1)
        if self._graphdata:
            return self._graphdata
        else:
            return None
