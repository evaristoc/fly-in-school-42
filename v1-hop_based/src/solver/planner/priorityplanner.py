from collections import defaultdict
import random
from typing import List, Dict, Set
from ..pathfinder.pathfinder import Pathfinder
from ..structures.roadmap_entitites import RoadMap
from ...model.agent.Agent import Agent
from ...model.graph.Graph import Zone, Edge, StartZone


class PriorityPlanner:
    """
    Implements a prioritized planning MAPF solver.

    Each agent is planned sequentially based on a priority order.
    Higher-priority agents constrain lower-priority agents via
    zone and edge reservations.
    """
    def __init__(self, agents: List[Agent]) -> None:
        self.agents = agents
        # Master Schedule: { tick: { agent_id:
        # { "zones": {Zone}, "edges": {Zone} } } }
        CONSTR_T = Dict[int, Dict[int, Dict[str, Set[Zone | Edge]]]]
        self.master_constraints: CONSTR_T = defaultdict(
            lambda: defaultdict(lambda: {"zones": set(), "edges": set()})
        )

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
                    print(agent.agent_id, None, {})
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
            # CAPACITY FIX: If the drone is still in the StartZone,
            # don't block it for others. This allows the 'queue' to form.
            if isinstance(current_z, StartZone):
                continue
            for other_agent in self.agents:
                if other_agent.agent_id == agent_id:
                    continue
                # Block the position
                constraints: Dict[str, Set[Zone | Edge]] =\
                    self.master_constraints[tick][other_agent.agent_id]
                constraints["zones"].add(current_z)  # was current
                # Block the swap (Edge constraint)
                if parent_z != current_z:  # was just parent_z, no comparison
                    constraints["edges"].add(current_z)  # was parent
