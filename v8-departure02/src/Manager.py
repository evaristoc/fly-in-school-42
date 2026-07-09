import os
# https://stackoverflow.com/questions/4627033/how-to-print-a-string-with-a-little-delay-between-the-chars
import sys
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
import time
import inspect
import json
from collections import defaultdict
from typing import Optional, Dict, Union, Any
from src.model.graph.Graph import GraphData, Graph
from .config_parser import Parser
from src.model.agent.Agent import Agent
from src.solver.pathfinder.pathfinder import PathfinderData
from src.solver.strategies.graphmethods.graphmethods import GraphHeuristic
from src.solver.strategies.graphmethods.concreteclasses.BellmanFord_Cap import GraphBellmanFordWait
from src.solver.strategies.pathmethods.concreteclasses.dijkstra import DijkstraAlgo, DijkstraCostFunc, DijkstraRules, PriorityDijkstraRules, CBSDijkstraRules
from src.solver.pathfinder.dijkstrapathfinder import DijkstraPathfinder
from src.solver.planner.priorityplanner import PriorityPlanner
from src.solver.planner.cbsplanner import CBSPlanner


class Manager:
    def __init__(self) -> None:
        self.filepath: Path
        self.graphdata: Optional[GraphData] = None
        self.graph: Optional[Graph] = None

    def _list_files(self, startpath: str) -> None:
        # for root, dirs, files in os.walk(startpath):
        for root, _, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print('{}{}/'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print('{}{}'.format(subindent, f))

    def get_args(self) -> None:
        print('\n============ WELCOME TO Fly In =============\n\n')
        print("\nType 'q' or 'exit' if you dont want any analysis.")
        self._list_files(os.curdir + '/maps')
        while True:
            choice = input("Input the path of the file you want "
                           "to be analyzed (easy|medium|hard/<file name>):")
            if not choice:
                print("selection failed, please try again.")
                continue
            if choice in ['q', 'quit', 'exit']:
                print("Ok... we understand... no analysis then... :(\n\n")
                print("Before you go... close the server terminal "
                      "and the browser window please? Thanks!\n")
                exit(0)
            self.filepath = Path(os.curdir, 'maps', choice)
            break

    def parsing(self) -> None:
        print('\nParsing...\n\n')
        parser = Parser()
        self.graphdata = parser.etl_config(self.filepath)
        if not self.graphdata:
            print("Data Collection Error: No data was found (see main)")
            exit(1)
        print("\nFile successfully parsed.\n")
        print("\n="*20)
        print("=== Check Graph ===")
        print("="*20)
        try:
            graphmethods: GraphHeuristic = GraphBellmanFordWait
            self.graph = Graph(self.graphdata, graphmethods)
            # print("graph in manager: self.graph.reversecost_map", self.graph.reversecost_map)
            members = inspect.getmembers(self.graph,
                                        lambda a: not (inspect.isroutine(a)))
            print("inspect", members)
        except Exception as e:
            print("Error during graph creation. Exiting. ", e)
            exit(1)
        print("\n="*20)
        print("=== Check Agents ===")
        print("="*20)
        agents = [Agent(self.graph, agent_id=id)
                  for id in range(self.graph.nb_drones)]
        if len(agents) == 0:
            print("No agents. Exiting")
            exit(1)
        members = inspect.getmembers(agents[0],
                                     lambda a: not (inspect.isroutine(a)))
        print("inspect", members)
        print("\n="*20)
        print("=== Model ===\n")
        print("="*20)

    def run(self) -> None:
        # print("\033c")
        print("="*20)
        print("=== Run Planner ===")
        time.sleep(2)
        print("="*20)
        print()
        agents = []
        if self.graph:
            for id in range(self.graph.nb_drones):
                agent = Agent(
                    agent_id=id,
                    entry_time=0,  # default start tick
                    graph=self.graph  # assign the pathfinder
                )
                agents.append(agent)
        # NOTE : I had to pass this pathfinder as a declaration, not as an instance...
        # NOTE : so I am passing DATA instead of instances
        dijkstradata = PathfinderData(
                                    algo=DijkstraAlgo,
                                    pathrules=DijkstraRules,
                                    costfunc=DijkstraCostFunc,
                                    heuristic=None,
                                    heuristic_weight=0.0,
                                    time_horizon_factor=3)
        # NOTE: notice that I am not instantiating the pathfinder immediately; it will happen when running for agents
        # cbsplanner = CBSPlanner(agents,
        #                         DijkstraPathfinder,
        #                         dijkstradata)
        # # Solve the MAPF problem using cbs
        # self.roadmaps = cbsplanner.solve()
        """
        The approach is sounding as long as pathfinderdata is non-mutable.
        If I later introduce:
            parallel planners
            caching of dijkstradata
            reuse of pathfinder instances
            incremental replanning

            Then that single mutable field becomes the first place bugs appear.
        """
        planner = PriorityPlanner(agents,
                                  DijkstraPathfinder,
                                  dijkstradata)
        if isinstance(planner, CBSPlanner):
            dijkstradata.pathrules = CBSDijkstraRules
        elif isinstance(planner, PriorityPlanner):
            dijkstradata.pathrules = PriorityDijkstraRules
        else:
            raise TypeError(f"Unsupported planner: {type(planner).__name__}")
        print(dir(dijkstradata.pathrules))
        self.roadmaps = planner.solve()
        if self.roadmaps is None:
            print("No feasible solution found!")
            sys.exit(1)
        else:
            # Pretty-print the results
            print("We got a solution. Printing on terminal...\n\n")
            time.sleep(1)
            logger: Dict[int, str] = defaultdict(str)
            if self.graph:
                for agent_id, roadmap in self.roadmaps.items():
                    if roadmap.states is None:
                        raise Exception("roadmap's states show as None")
                    for tick, (_, current_zone) in roadmap.states.items():
                        if current_zone is None:
                            raise Exception("Either current_zone or "
                                            "graph.startzone is None")
                        if self.graph.startzone\
                            is not None and current_zone.name\
                                != self.graph.startzone.name:
                            logger[tick] += f'D{agent_id}-{current_zone.name} '
            for state in logger.values():
                state = state.strip()
                state += '\n'
                if len(state) < 20:
                    for ch in state:
                        sys.stdout.write(ch)
                        sys.stdout.flush()
                        time.sleep(0.1)
                elif len(state) >= 20 and len(state) < 40:
                    words = state.split(" ")
                    for w in words:
                        sys.stdout.write(w + ' ')
                        sys.stdout.flush()
                        time.sleep(0.1)
                else:
                    print("in the manager - state: ", state)

            print("\nDone with mandatory part. Rendering...\n")

    def create_json(self) -> None:
        print()
        print("="*20)
        print("=== Making json file ===")
        print("="*20)
        print()
        jsondata: Dict[str, Union[Any]] = {}
        filestem = Path(self.filepath).stem
        jsondata["name"] = filestem
        jsondata["nodes"] = []
        maxy = 0
        miny = float('inf')
        maxx = 0
        if self.graph:
            for i, z in enumerate(self.graph.zones):
                n: Dict[str, Any] = {}
                n["id"] = i
                n["x"] = z.x
                maxx = max(n["x"], maxx)
                n["y"] = z.y
                maxy = max(n["y"], maxy)
                miny = min(miny, maxy)
                n["label"] = z.name
                n["color"] = z.color
                jsondata["nodes"].append(n)
            for n in jsondata["nodes"]:
                n["x"] /= maxx / 1.2
                if maxy:
                    n["y"] = (maxy - n["y"]) / maxy / 2
                else:
                    n["y"] = (maxy - n["y"]) / 2 + 0.5
            jsondata["edges"] = []
            for c in self.graph.edges:
                n1 = next((n["id"] for n in jsondata["nodes"]
                           if n["label"] == c.nodenames[0]))
                n2 = next((n["id"] for n in jsondata["nodes"]
                           if n["label"] == c.nodenames[1]))
                e = {}
                e["from"] = n1
                e["to"] = n2
                jsondata["edges"].append(e)
                jsondata["agents"] = []
                minlen = 0
                for agent_id, roadmap in self.roadmaps.items():
                    a: Dict[str, Any] = {}
                    a["id"] = agent_id
                    a["name"] = f"agent {agent_id}"
                    a["color"] = "#00e5ff"
                    a["path"] = []
                    if roadmap.states is not None:
                        minlen = min(minlen, len(roadmap.states))
                        for _, (_, current_zone) in roadmap.states.items():
                            if current_zone is not None:
                                j = jsondata["nodes"]
                                nam = current_zone.name
                                a["path"].append(next((n["id"] for n in j
                                                       if n["label"] == nam)))
                    # TODO this "correction" is now adding too many steps when all agents finish simultaneously
                    # if len(a["path"]) < minlen + self.graph.nb_drones:
                    #     rest = minlen + self.graph.nb_drones - len(a["path"])
                    #     a["path"] = a["path"] + [a["path"][-1]] * rest
                    jsondata["agents"].append(a)
        print("in the manager - jsondata: ", jsondata)

        with open(Path(os.curdir, 'maps', filestem + ".json"), 'w') as file:
            json.dump(jsondata, file)
