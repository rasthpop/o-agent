"""Minimalist web interface for o-agent investigations."""

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse

from app.investigation_runner import InvestigationRunner

app = FastAPI(title="o-agent Web Interface")

# Store active investigations
active_investigations: dict[str, InvestigationRunner] = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main interface."""
    html_path = Path(__file__).parent / "static" / "index.html"
    return html_path.read_text()


@app.post("/api/investigate")
async def start_investigation(
    file: UploadFile = File(...), mode: str = Form(default="quick")
) -> dict[str, str]:
    """
    Start a new investigation with an uploaded image.

    Args:
        file: Uploaded image file
        mode: Investigation mode ("quick" or "deep")

    Returns:
        Dict with investigation_id for tracking progress
    """
    # Generate unique investigation ID
    investigation_id = str(uuid.uuid4())

    # Save uploaded file temporarily
    upload_dir = Path("app/images/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{investigation_id}_{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create investigation runner with selected mode
    runner = InvestigationRunner(str(file_path), mode=mode)
    active_investigations[investigation_id] = runner

    return {"investigation_id": investigation_id, "status": "started", "mode": mode}


@app.get("/api/progress/{investigation_id}")
async def stream_progress(investigation_id: str):
    """
    Stream investigation progress via Server-Sent Events (SSE).

    Args:
        investigation_id: Unique investigation identifier

    Returns:
        SSE stream of progress updates
    """
    if investigation_id not in active_investigations:
        return {"error": "Investigation not found"}

    runner = active_investigations[investigation_id]

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events from investigation progress."""
        # Start investigation in background
        asyncio.create_task(runner.run())

        # Stream progress updates
        async for update in runner.progress_stream():
            # Format as SSE
            data = json.dumps(update.model_dump())
            yield f"data: {data}\n\n"

        # Cleanup after completion
        del active_investigations[investigation_id]

    return StreamingResponse(
        event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "active_investigations": len(active_investigations)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
