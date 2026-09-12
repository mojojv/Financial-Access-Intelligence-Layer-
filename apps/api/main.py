"""FastAPI Application Main Entrypoint with Static Web UI Mount."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from apps.api.routes import router

app = FastAPI(
    title="Financial Access Intelligence Layer API",
    description="Open-source platform for Financial Access Index scoring and Open Payments intervention execution.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_dashboard() -> FileResponse:
    """Serves the live interactive dashboard UI."""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
