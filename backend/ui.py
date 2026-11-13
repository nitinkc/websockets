"""Where the frontend lives.

All pages are plain HTML+JS in the top-level `ui/` directory — the app
keeps its Python in `backend/` and its markup out here, so the two sides
stay separable. `page()` is the one door every route uses.
"""

from pathlib import Path

from fastapi.responses import FileResponse

UI_DIR = Path(__file__).parent.parent / "ui"


def page(name: str) -> FileResponse:
    return FileResponse(UI_DIR / name)
