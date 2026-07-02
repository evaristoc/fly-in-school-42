import heapq
from collections import defaultdict
from typing import List, Optional, Dict
from ..pathfinder.pathfinder import Pathfinder
from ..structures.ConflictNode import CTNode, Tree, Conflict, VertexConflict, \
    EdgeConflict, State
from ..structures.roadmap_entitites import RoadMap
from ...model.agent.Agent import Agent
from ...model.graph.Zone import StartZone, EndZone

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
                        # TODO this is a patch to keep working later on this
                        # NOTE: using only cost to reduce redundant branches is NOT correct
                        #       but it works for this project for now
                        if node.right.cost <  node.left.cost:
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
            raise Exception("ERROR when finding conflict - no agents or roadmaps found")

        # Longest roadmap
        max_t = max(max(rm.states.keys()) for rm in node.solution.values())

        for t in range(1, max_t + 1):

            # (from_name, to_name) -> [agent_ids]
            eoccupancy = defaultdict(list)

            # zone_name -> [agent_ids]
            zoccupancy = defaultdict(list)

            # zone_name -> canonical Zone instance
            zone_lookup = {}

            # -----------------------------
            # Build occupancy tables
            # -----------------------------
            for agent in self.agents:

                states = node.solution[agent.agent_id].states

                if t not in states:
                    continue

                _, curr_zone = states[t]

                if (t - 1) in states:
                    prev_zone = states[t - 1][1]
                else:
                    prev_zone = curr_zone

                # Always remember canonical references
                zone_lookup[prev_zone.name] = prev_zone
                zone_lookup[curr_zone.name] = curr_zone

                # Edge occupancy (includes start->X and X->goal)
                if prev_zone.name != curr_zone.name:
                    eoccupancy[(prev_zone.name, curr_zone.name)].append(agent.agent_id)

                # Vertex occupancy (ignore start/goal)
                if not (isinstance(curr_zone, StartZone) or isinstance(curr_zone, EndZone)):
                    zoccupancy[curr_zone.name].append(agent.agent_id)

            # -----------------------------
            # EDGE CONFLICTS (checked first)
            # -----------------------------
            for (from_name, to_name), agents in eoccupancy.items():

                from_zone = zone_lookup[from_name]
                to_zone = zone_lookup[to_name]

                edge = next(
                    (
                        n.edge
                        for n in to_zone.neighbours
                        if set(n.edge.nodenames) == {from_name, to_name}
                    ),
                    None,
                )

                if edge is None:
                    raise Exception(
                        f"Cannot find edge between {from_name} and {to_name}"
                    )

                if len(agents) > edge.max_link_capacity:
                    return EdgeConflict(
                        agent_1=agents[0],
                        agent_2=agents[1],
                        zone_from=from_zone,
                        zone_to=to_zone,
                        tick=t,
                    )

            # -----------------------------
            # VERTEX CONFLICTS
            # -----------------------------
            for zone_name, agents in zoccupancy.items():

                zone = zone_lookup[zone_name]

                if len(agents) > zone.max_drones:
                    return VertexConflict(
                        agent_1=agents[0],
                        agent_2=agents[1],
                        zone=zone,
                        tick=t,
                    )

        return None