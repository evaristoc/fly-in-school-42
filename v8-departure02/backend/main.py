from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .config.config import PROJECT_ROOT, FRONTEND_URL
from .routers.graphs import router as graphs_router
# from .routers.editor import router as editor_router
app = FastAPI(title="Graph Scheduler Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(graphs_router)
# app.include_router(editor_router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(request.method, request.url)
    response = await call_next(request)
    print(response.status_code)
    return response
STATIC_DIR = PROJECT_ROOT / "app/static"


# @app.get("/api/map_editor", response_class=FileResponse)
# async def get_editor():
#     """Open editor."""
#     return "./app/map_editor/index.html"

# ── Static files (must be last) ──────────────────────────────────────────────
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="app")