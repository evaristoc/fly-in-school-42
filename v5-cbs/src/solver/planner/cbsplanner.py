from __future__ import annotations
import headq
import copy
from typing import List, Optional
from model.agent.Agent import Agent
from model.conflict.ConflictNode import CTNode, Tree
# from model.graph import Connection

class Planner:
    def __init__(self):
        self.agents: List[Agent] = []
        self.constraints = []
        self.tree: Optional[Tree] = None
        self.bisect: State = 'WAIT'

    def _bfs(self) -> CTNode:
        if self.tree:
            node = self.tree.root
            Q = []
            entry = (node.calc_sol_cost(), node)
            headq.headpush(Q, entry)
            while Q:
                _, node = Q.heappop()
                if self.is_conflict(node):
                    (agent1, zone, tick), (agent2, zone, tick) = \
                        self.find_conflict(node)
                    right_node = copy.deepcopy(node)
                    node.right = right_node
                    right_node.update_constraints((agent1, zone, tick))
                    right_node.update_solution(agent1)
                    right_cost = right_node.calc_sol_cost()
                    headq.heappush(Q, (right_cost, right_node))
                    left_node = copy.deepcopy(node)
                    node.left = left_node
                    left_node.update_constraints((agent2, zone, tick))
                    left_node.update_solution(agent2)
                    left_cost = left_node.calc_sol_cost()
                    headq.heappush(Q, (left_cost, left_node))
                else:
                    return node.solution

    def register_agents(self, agent: Agent) -> None:
        self.agents.append(agent)

    def _add_ctnode(self):
        if not self.tree:
            self.tree = CTNode()

    def find_conflict(self, agents: List[Agent]) -> Optional[Conflict]:
        # 1. Determine the time horizon (longest path)
        if not agents:
            return None
            
        max_t = max(max(a.roadmap.states.keys()) for a in agents)

        # 2. Iterate through time (Start at 1 to skip T=0 shared start)
        for t in range(1, max_t + 1):
            occupancy = {}  # {zone_id: agent_id}
            
            for agent in agents:
                # Get current state or stay at goal if tick exceeds roadmap
                curr_states = agent.roadmap.states
                if t in curr_states:
                    prev_zone, curr_zone = curr_states[t]
                else:
                    # Agent is finished; it stays in its last known zone
                    last_tick = max(curr_states.keys())
                    _, curr_zone = curr_states[last_tick]
                    prev_zone = curr_zone 

                # --- Check Vertex Conflict ---
                if curr_zone in occupancy:
                    other_agent_id = occupancy[curr_zone]
                    return VertexConflict(
                        agent_1=other_agent_id,
                        agent_2=agent.agent_id,
                        zone=curr_zone,
                        tick=t
                    )
                occupancy[curr_zone] = agent.agent_id

                # --- Check Edge Swap Conflict ---
                # We compare this agent against every other agent at the same tick
                for other in agents:
                    if other.agent_id == agent.agent_id:
                        continue
                    
                    other_states = other.roadmap.states
                    if t in other_states:
                        o_prev, o_curr = other_states[t]
                        
                        # Swap Logic: A moves U->V while B moves V->U
                        if curr_zone == o_prev and prev_zone == o_curr:
                            # Ensure we don't trigger on 'Wait' vs 'Wait' 
                            # (which is a Vertex conflict handled above)
                            if curr_zone != prev_zone:
                                return EdgeConflict(
                                    agent_1=agent.agent_id,
                                    agent_2=other.agent_id,
                                    zone_from=prev_zone,
                                    zone_to=curr_zone,
                                    tick=t
                                )

        return None

    def add_constraint(self):
        pass

    def bisect_CT(self):
        if self.bisect == 'WAIT':
            self.tree.right = CTNode()
        elif self.bisect == 'MOVE':
            self.tree.left = CTNode()

    def agent_violates_constraints(self, agent_id: int,
                                   step: Connection, thetick: int) -> bool:
        pass