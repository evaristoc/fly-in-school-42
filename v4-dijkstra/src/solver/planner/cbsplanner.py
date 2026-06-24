from __future__ import annotations
import headq
from typing import List, Optional
from model.agent.Agent import Agent
from model.graph.Graph import Edge
from structures.ConflictNode import CTNode, Tree, VertexConflict, EdgeConflict, State
from structures.constraints import ConstrMap
from structures.roadmap_entitites import RoadMap
# from model.graph import Connection


class Planner:
    def __init__(self):
        self.agents: List[Agent] = []
        self.constraints = []
        self.tree: Optional[Tree] = None
        self.bisect: State = 'WAIT'

    def _best_first(self) -> RoadMap:
        counter = 0
        if self.tree:
            node = self.tree.root
            Q = []
            entry = (node.cost, counter, node)
            headq.heappush(Q, entry)
            while Q:
                _, _, node = Q.heappop()
                # if self.is_conflict(node):
                conflict = \
                    self.find_conflict(node)
                if conflict:
                    agent1: Agent = conflict.agent1
                    agent2: Agent = conflict.agent2
                    # TODO create a clearer class for the list of agents
                    # NOTE: agent on left is WAIT, agent on right is MOVE
                    left_node = CTNode(node, [agent1, agent2])
                    node.left = left_node
                    left_node.update_constraints(conflict)
                    left_node.update_solution()
                    left_node.calc_sol_cost()
                    counter += 1
                    headq.heappush(Q, (left_node.cost, counter, left_node))
                    right_node = CTNode(node, [agent2, agent1])
                    node.right = right_node
                    right_node.update_constraints(conflict)
                    right_node.update_solution()
                    right_node.calc_sol_cost()
                    counter += 1
                    headq.heappush(Q, (right_node.cost, counter, right_node))
                else:
                    return node.roadmaps

    def register_agents(self, agent: Agent) -> None:
        self.agents.append(agent)

    def _add_ctnode(self):
        if not self.tree:
            self.tree = CTNode()

    def find_conflict(self, node: CTNode) -> Optional[Conflict] | None:
        # Determine the time horizon (longest path)
        if not node or not node.agents or not node.roadmaps:
            raise Exception('Error when finding conflict - no agents or roadmaps found')
        # for agent find the max tick and then the max of all (in this case, the last arrival time)
        parentconstraints: ConstrMap = node.constraints
        max_t = max(max(rm.states.keys()) for rm in node.roadmaps)
        # Iterate through time (Start at 1 to skip T=0 shared start)
        for t in range(1, max_t + 1):
            occupancy = {}  # {zone_id: agent_id}
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

                # TODO Evaluate for capacity; while still enough capacity, there is no conflict
                # Check Vertex Conflict
                zname: str = curr_zone.name
                """
                The following reads:
                if zone in list of constraints and
                there is still a spot in the real situation
                but that spot is disputed between me and previous one
                """
                if zname in parentconstraints["zones"] and \
                        len(parentconstraints["zones"][zname]["agents"]) == \
                        parentconstraints["zones"][zname]["capacity"] - 1 and \
                        curr_zone in occupancy and \
                        len(occupancy.get(curr_zone, {})) == parentconstraints["zones"][zname]["capacity"] + 1:
                    # there could be several agents...
                    # we evaluate the agent
                    return VertexConflict(
                        agent_1=agent.agent_id,
                        agent_2=parentconstraints["zones"][zname]["agents"]
                        .difference(occupancy.get(curr_zone, {})),
                        zone=curr_zone,
                        tick=t
                    )
                
                # it was empty, agent can take it
                occupancy[curr_zone].add(agent.agent_id)
                if  len(parentconstraints["zones"][zname]["agents"]) < \
                        parentconstraints["zones"][zname]["capacity"] - 1:
                    parentconstraints["zones"][zname]["agents"].add(agent)

                # Check Edge Swap Conflict
                # We compare this agent against every other agent at the same tick
                for other in self.agents:
                    if other.agent_id == agent.agent_id:
                        continue
                    other_states = other.roadmap.states
                    if t in other_states:
                        o_prev, o_curr = other_states[t]
                        edge: Edge | None = None
                        for n in prev_zone.neighbours:
                            if curr_zone.name in n.edge.nodenames:
                                edge = n.edge
                        if edge.nodenames in parentconstraints["edges"] and \
                                len(parentconstraints["edges"][edge.nodenames]["agents"]) == \
                                parentconstraints["edges"][edge.nodenames]["capacity"]:
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
                            # Traffic: both A and B want to use same connection
                            if curr_zone == o_curr and prev_zone == o_prev:
                                if curr_zone != prev_zone:
                                    return EdgeConflict(
                                        agent_1=agent.agent_id,
                                        agent_2=other.agent_id,
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