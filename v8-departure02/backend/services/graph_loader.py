import json
from pathlib import Path


class GraphError(Exception):
    """Raised when a graph configuration is invalid."""
    pass


def load_graph(path: Path) -> dict:
    """Load, validate and prepare a graph."""
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open() as f:
        raw = json.load(f)
    validate_graph(raw)
    raw["schedule"] = build_schedule(raw)
    return raw


def validate_graph(graph: dict) -> None:
    """Validate graph consistency."""
    node_ids = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            raise GraphError(
                f"Edge {edge} references an unknown node."
            )
    for agent in graph["agents"]:
        for step in agent["path"]:
            if step not in node_ids:
                raise GraphError(
                    f"Agent '{agent['name']}' references unknown node '{step}'."
                )


def build_schedule(graph: dict) -> list[dict]:
    """Build animation frames from the agent paths."""
    max_steps = max(len(agent["path"]) for agent in graph["agents"])
    schedule = []
    for step in range(max_steps):
        frame = {}
        for agent in graph["agents"]:
            path = agent["path"]
            frame[str(agent["id"])] = path[min(step, len(path) - 1)]
        schedule.append(frame)
    return schedule