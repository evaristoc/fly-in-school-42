from fastapi import APIRouter, HTTPException
from typing import Optional
from ..config.config import SOLUTIONS_DIR
from ..services.graph_loader import GraphError, load_graph

router = APIRouter(prefix="/api", tags=["graphs"])

# In-memory graph state
_current_graph: Optional[dict] = None


@router.get("/graph")
def get_graph() -> dict:
    """Return current graph state."""
    if _current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded yet")
    return _current_graph


@router.get("/solutions")
def list_graph_files() -> dict:
    """Return available config file names."""
    files = sorted(f.name for f in SOLUTIONS_DIR.glob("*.json"))
    return {"files": files}


@router.get("/solution/{filename}")
def graph_loader(filename: str) -> dict:
    """Return processed graph files."""
    global _current_graph
    try:
        _current_graph = load_graph(SOLUTIONS_DIR / filename)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found."
        )
    except GraphError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    return {
        "status": "ok",
        "graph": _current_graph,
    }