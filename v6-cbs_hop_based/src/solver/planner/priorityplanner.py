import random
from typing import List, Dict
from ..pathfinder.pathfinder import Pathfinder
from ..structures.roadmap_entitites import RoadMap
from ..structures.constraints import Constraints, ConstraintZone, ConstraintEdge, ConstrMap
from ...model.agent.Agent import Agent
from ...model.graph.Graph import StartZone, EndZone


class PriorityPlanner:
    """
    Implements a prioritized planning MAPF solver.

    Each agent is planned sequentially based on a priority order.
    Higher-priority agents constrain lower-priority agents via
    zone and edge reservations.
    """
    def __init__(self, agents: List[Agent]) -> None:
        self.agents = agents
        self.master_constraints: ConstrMap = {}

    def solve(self,
              pathfinder: Pathfinder,
              iterations: int = 10) -> Dict[int, RoadMap]:
        """
        Attempt to solve MAPF using prioritized planning with optional
        random agent order.

        Returns:
            Dict[agent_id, RoadMap] on success, or {} if all retries fail.
        """
        for attempt in range(iterations):
            self.master_constraints.clear()
            final_roadmaps = {}
            success = True

            # Shuffle agents to try different priority orders if one fails
            current_order = list(self.agents)
            if attempt > 0:
                random.shuffle(current_order)

            for agent in current_order:
                # The agent plans a path around all higher-priority paths
                roadmap = agent.plan(pathfinder, self.master_constraints)
                if roadmap is None:
                    success = False
                    # retry with different priority order
                    break
                final_roadmaps[agent.agent_id] = roadmap
                self._reserve_path(agent.agent_id, roadmap)

            if success:
                return final_roadmaps

        # Failure after all retries
        return {}

    def _reserve_path(self, agent_id: int, roadmap: RoadMap) -> None:
        """
        Reserve zones and edges along the roadmap for all other agents.

        StartZones are exempt to allow queuing.
        """
        if not isinstance(agent_id, int):
            raise Exception("Error in Planner _reserve_path: agent_id "
                            "is not found or had wrong value")
        if roadmap is None:
            raise Exception("Error in Planner _reserve_path: no roadmap")
        if roadmap.states is None:
            raise Exception("roadmap states are None")
        if len(roadmap.states) == 0:
            raise Exception("roadmap states are empty")
        for tick, (parent_z, current_z) in roadmap.states.items():
            """
            # TODO : see below
            # CAPACITY FIX: If the drone is still in the StartZone,
            # don't block it for others. This allows the 'queue' to form.
            # NONE RESTRICTION AT SINK: I am assuming no restriction to get to
            # the end, but could be some, and then the sim should stop...
            """
            if isinstance(current_z, StartZone) or isinstance(current_z, EndZone):
                continue
            # constraints: Constraints =\
            #     self.master_constraints.get(tick, {})
            if tick not in self.master_constraints:
                self.master_constraints[tick] = {"zones": {}, "edges": {}}
            constraintszones: ConstraintZone = self.master_constraints[tick].get("zones")
            if current_z not in constraintszones:  # was current
                constraintszones[current_z.name] = {
                    "capacity": current_z.max_drones,
                    "counter": 0}
            if constraintszones[current_z.name]["counter"] < constraintszones[current_z.name]["capacity"]:
                constraintszones[current_z.name]["counter"] += 1
            # Block the swap or the simulatenous use (Edge constraint)
            if parent_z != current_z:  # was just parent_z, no comparison
                constraintsedges: ConstraintEdge = self.master_constraints[tick].get("edges")
                for c in current_z.neighbours:
                    if c.edge is None:
                        continue
                    if parent_z.name in c.edge.nodenames:
                        if c.edge.nodenames not in constraintsedges:
                            constraintsedges[c.edge.nodenames] = {
                                "capacity": c.edge.max_link_capacity,
                                "counter": 0}
                        if constraintsedges[c.edge.nodenames]["counter"] < constraintsedges[c.edge.nodenames]["capacity"]:
                            constraintsedges[c.edge.nodenames]["counter"] += 1  # was parent
        # print(self.master_constraints)