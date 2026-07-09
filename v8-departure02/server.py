import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

app = FastAPI(title="Graph Scheduler Demo")

GRAPHS_DIR = Path(__file__).parent / "maps"
STATIC_DIR = Path(__file__).parent / "app/static"

# In-memory graph state
_current_graph: Optional[dict] = None


# ── Routes ──────────────────────────────────────────────────────────────────

# app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="app")

templates = Jinja2Templates(directory="app/templates")

@app.get("/map_editor", response_class=HTMLResponse)
async def get_templateeditor(request: Request):
    return templates.TemplateResponse(request=request, name="map_editor.html")

# @app.get("/api/map_editor", response_class=HTMLResponse)
# async def get_editor():
#     """Open editor."""
#     return "<h1>Items</h1><p>This is a list of items.</p>"

@app.get("/api/map_editor", response_class=FileResponse)
async def get_editor():
    """Open editor."""
    return "./app/map_editor/index.html"

@app.get("/api/files")
def list_graph_files() -> dict:
    """Return available config file names."""
    files = sorted(f.name for f in GRAPHS_DIR.glob("*.json"))
    return {"files": files}


@app.post("/api/load/{filename}")
def load_graph(filename: str) -> dict:
    """Parse a config file and store the processed graph in memory."""
    global _current_graph
    path = GRAPHS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not"
                            "found")

    with open(path) as f:
        raw = json.load(f)

    # Validate: all edge endpoints must exist
    node_ids = {n["id"] for n in raw["nodes"]}
    for edge in raw["edges"]:
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Edge {edge} references unknown node"
            )

    # Validate: all agent paths reference valid nodes
    for agent in raw["agents"]:
        for step in agent["path"]:
            if step not in node_ids:
                raise HTTPException(
                    status_code=422,
                    detail=f"Agent {agent['name']} path references "
                    f"unknown node {step}"
                )

    # Build schedule: list of frames, each frame = agent positions
    # (node indices)
    max_steps = max(len(a["path"]) for a in raw["agents"])
    schedule = []
    for step in range(max_steps):
        frame = {}
        for agent in raw["agents"]:
            path = agent["path"]
            pos = path[min(step, len(path) - 1)]
            frame[str(agent["id"])] = pos
        schedule.append(frame)

    _current_graph = {
        "name": raw["name"],
        "nodes": raw["nodes"],
        "edges": raw["edges"],
        "agents": raw["agents"],
        "schedule": schedule,
    }
    return {"status": "ok", "graph": _current_graph}


@app.get("/api/graph")
def get_graph() -> dict:
    """Return current graph state."""
    if _current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded yet")
    return _current_graph



# ── Static files (must be last) ──────────────────────────────────────────────
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="app")

# templates = Jinja2Templates(directory="app/templates")

# @app.get("/map_editor", response_class=HTMLResponse)
# async def get_templateeditor(request: Request):
#     return templates.TemplateResponse(request=request, name="map_editor.html")

