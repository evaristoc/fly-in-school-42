from __future__ import annotations
import headq
from collections import defaultdict
from typing import List, Optional
from model.agent.Agent import Agent
from ..pathfinder.pathfinder import Pathfinder
from structures.ConflictNode import CTNode, Tree, Conflict, VertexConflict, EdgeConflict, State
from structures.roadmap_entitites import RoadMap
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

    def solve(self):
        self._best_first()

    def _best_first(self) -> RoadMap:
        counter = 0
        self._add_ctnode()
        if self.tree:
            root = self.tree.root
            Q = []
            if root.update_solution(self.pathfinder, self.agents):
                root.calc_sol_cost()
                headq.heappush(Q, (root.cost, counter, node))
            else:
                raise Exception("Error at Planner: no root solution.")
            while Q:
                _, _, node = Q.heappop()
                conflict = self.find_conflict(node)
                if conflict:
                    # NOTE: agent on left is WAIT, agent on right is MOVE
                    left_node = CTNode(self.agents, node)
                    node.left = left_node
                    left_node.update_constraints(conflict)
                    if left_node.update_solution(self.pathfinder):
                        left_node.calc_sol_cost()
                        counter += 1
                        headq.heappush(Q, (left_node.cost, counter, left_node))
                    else:
                        raise Exception("Error at Planner: no a left solution.")
                    right_node = CTNode(self.agents, node)
                    node.right = right_node
                    right_node.update_constraints(conflict)
                    if right_node.update_solution(self.pathfinder):
                        right_node.calc_sol_cost()
                        counter += 1
                        headq.heappush(Q, (right_node.cost, counter, right_node))
                    else:
                        raise Exception("Error at Planner: no a right solution.")
                else:
                    return node.roadmaps

    # def register_agents(self, agents: List[Agent]) -> None:
    #     self.agents = agents

    def _add_ctnode(self):
        if not self.tree:
            self.tree = CTNode(self.agents)

    def find_conflict(self, node: CTNode) -> Optional[Conflict] | None:
        # Determine the time horizon (longest path)
        if not node or not node.agents or not node.roadmaps:
            raise Exception('ERROR when finding conflict - no agents or roadmaps found')
        # for agent find the max tick and then the max of all (in this case, the last arrival time)
        max_t = max(max(rm.states.keys()) for rm in node.roadmaps)
        # Iterate through time (Start at 1 to skip T=0 shared start)
        for t in range(1, max_t + 1):
            zoccupancy = defaultdict(list)  # {zone_id: [agent]}
            eoccupancy = defaultdict(list)  # now {edge_id: [agent]}
            for agent in self.agents:
                # Get current state or stay at goal if tick exceeds roadmap
                curr_states = node.roadmaps[agent.agent_id].states
                if t in curr_states:
                    prev_zone, curr_zone = curr_states[t]
                else:
                    # Agent is finished; it stays in its last known zone
                    # find agent's last move tick (when reached goal)
                    # for now, prev_zone is then the same as GOAL
                    last_tick = max(curr_states.keys())
                    _, curr_zone = curr_states[last_tick]
                    prev_zone = curr_zone
                # it was empty, agent can take it
                zoccupancy[curr_zone].append(agent.agent_id)
                if prev_zone != curr_zone:
                    eoccupancy[(prev_zone, curr_zone)].append(agent.agent_id)
            for curr_zone, agents in zoccupancy.items():
                if len(agents) > 1 and len(agents) > curr_zone.max_drones:
                    return VertexConflict(
                        agent_1=agents[0],
                        agent_2=agents[1],
                        zone=curr_zone,
                        tick=t
                    )
            # Check Edge Conflicts
            # Swap Conflict is not required for the Fly-In School 42 project,
            # but it is common in CBS.
            # it was empty, agent can take it
            # first capacity:
            for (prev_zone, curr_zone), agents in eoccupancy.items():
                actual_edge = next((n.edge for n in curr_zone.neighbours if prev_zone.name in n.edge.nodenames), None)
                if len(agents) > 1 and len(agents) > actual_edge.max_link_capacity:
                    return EdgeConflict(
                        agent_1=agents[0],
                        agent_2=agents[1],
                        zone_from=prev_zone,
                        zone_to=curr_zone,
                        tick=t
                    )
            # now swaping:
                reverse = (curr_zone, prev_zone)
                if reverse in eoccupancy:
                    other_agents = eoccupancy[reverse]
                    return EdgeConflict(
                        agent_1=agents[0],
                        agent_2=other_agents[0],
                        zone_from=prev_zone,
                        zone_to=curr_zone,
                        tick=t
                    )
        return None

    # def add_constraint(self):
    #     pass

    # def bisect_CT(self):
    #     if self.bisect == 'WAIT':
    #         self.tree.right = CTNode()
    #     elif self.bisect == 'MOVE':
    #         self.tree.left = CTNode()

    # def agent_violates_constraints(self, agent_id: int,
    #                                step: Connection, thetick: int) -> bool:
    #     pass