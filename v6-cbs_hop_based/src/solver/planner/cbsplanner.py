from __future__ import annotations
import heapq
from collections import defaultdict
from typing import List, Optional, Dict
from ..pathfinder.pathfinder import Pathfinder
from ..structures.ConflictNode import CTNode, Tree, Conflict, VertexConflict, EdgeConflict, State
from ..structures.roadmap_entitites import RoadMap
from ...model.agent.Agent import Agent
# from model.graph import Connection

# TODO ignoring ctnodes in conflict detection? Solution (roadmap) should be then correct after including for constraints
# NOTE in correct CBS, all conflicted agents are passed at once for branching; this wont be the case here
# TODO this is CBS : conflict → choose one agent → add constraint → replan only affected agent
# NOTE this is my code: conflict → rebuild full solution for both children


class CBSPlanner:
    def __init__(self, agents: List[Agent], pathfinder: Pathfinder):
        self.agents: List[Agent] = agents
        self.pathfinder = pathfinder
        if len(agents) == 0:
            raise Exception("ERROR at init CBSPlanner: no agents?")
        self.constraints = []
        self.tree: Optional[Tree] = None
        self.bisect: State = 'WAIT'

    def solve(self) -> Dict[RoadMap]:
        return self._best_first()

    def _best_first(self) -> RoadMap:
        # TODO found circular, infinite loops
        # TODO one case was immediately giving an error before even running
        counter = 0
        self._add_ctnode()
        if self.tree:
            root = self.tree
            Q = []
            if root.update_solution(self.pathfinder, self.agents):
                root.calc_sol_cost()
                heapq.heappush(Q, (root.cost, counter, root))
            else:
                raise Exception("Error at Planner: no root solution.")
            while Q:
                _, _, node = heapq.heappop(Q)
                conflict = self.find_conflict(node)
                #print(f"[CBS] node={id(node)} conflict={conflict.zone.name} t={conflict.tick}")
                #print(f"[CBS] Q len {len(Q)}")
                if conflict:
                    left_node = CTNode(self.agents, node)
                    node.left = left_node
                    # print("cbsplanner:", id(node))
                    # print("cbsplanner left:", id(node.left))
                    node.left.add_constraint(conflict)
                    self.pathfinder = Pathfinder(
                        heuristic=None,          # or a specific Heuristic subclass
                        heuristic_weight=1.0,    # lambda factor
                        time_horizon_factor=3    # default time horizon multiplier
                    )
                    if node.left.update_solution(self.pathfinder, self.agents):
                        node.left.calc_sol_cost()
                        counter += 1
                        heapq.heappush(Q, (node.left.cost, counter, node.left))
                    else:
                        raise Exception("Error at Planner: no a left solution.")
                    right_node = CTNode(self.agents, node)
                    node.right = right_node
                    node.right.add_constraint(conflict)
                    self.pathfinder = Pathfinder(
                        heuristic=None,          # or a specific Heuristic subclass
                        heuristic_weight=1.0,    # lambda factor
                        time_horizon_factor=3    # default time horizon multiplier
                    )
                    if node.right.update_solution(self.pathfinder, self.agents):
                        node.right.calc_sol_cost()
                        counter += 1
                        heapq.heappush(Q, (node.right.cost, counter, node.right))
                    else:
                        raise Exception("Error at Planner: no a right solution.")
                else:
                    return node.solution

    # def register_agents(self, agents: List[Agent]) -> None:
    #     self.agents = agents

    def _add_ctnode(self):
        if not self.tree:
            self.tree = CTNode(self.agents)

    def find_conflict(self, node: CTNode) -> Optional[Conflict]:
        if not node or not node.solution:
            raise Exception("ERROR: no solution found")

        max_t = max(
            max(rm.states.keys()) 
            for rm in node.solution.values()
        )

        for t in range(1, max_t + 1):
            occupancy = defaultdict(list)  # zone -> agents
            edge_moves = defaultdict(list)  # (from, to) -> agents

            for agent in self.agents:
                states = node.solution[agent.agent_id].states

                # if agent has no state at this time, assume it stays in place
                if t not in states:
                    if t - 1 in states:
                        _, zone = states[t - 1]
                    else:
                        continue
                else:
                    _, zone = states[t]

                _, prev_zone = states[t - 1] if t - 1 in states else (None, zone)

                occupancy[zone].append(agent.agent_id)

                if prev_zone != zone:
                    edge_moves[(prev_zone, zone)].append(agent.agent_id)

            # --------------------
            # Vertex conflicts only
            # --------------------
            for zone, agents in occupancy.items():
                if len(agents) > 1:
                    return VertexConflict(
                        agent_1=agents[0],
                        agent_2=agents[1],
                        zone=zone,
                        tick=t
                    )

            # --------------------
            # Swap conflicts only
            # --------------------
            for (a, b), agents in edge_moves.items():
                if (b, a) in edge_moves:
                    return EdgeConflict(
                        agent_1=agents[0],
                        agent_2=edge_moves[(b, a)][0],
                        zone_from=a,
                        zone_to=b,
                        tick=t
                    )

        return None