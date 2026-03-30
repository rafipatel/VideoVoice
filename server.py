"""
server.py — FastAPI backend for VideoVoice.

Endpoints:
  POST /api/jobs          — Submit a video for translation (file upload or URL)
  GET  /api/jobs/{id}     — SSE stream of pipeline progress
  GET  /api/jobs/{id}/result — Download the translated video
  GET  /api/demo-videos   — List available demo videos (outputs + data)
  GET  /api/demo-videos/{video_id}/stream — Stream demo video by ID
"""
import asyncio
import hashlib
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

load_dotenv()

# ── App ────────────────────────────────────────────────
app = FastAPI(title="VideoVoice API", version="1.0.0")

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory job store ────────────────────────────────
# Structure: { job_id: { status, messages[], result_path, error, created_at } }
jobs: dict = {}

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DEMO_VIDEO_DIRS = {
    "outputs": OUTPUT_DIR,
    "data": Path("data"),
}


# ── Helpers ────────────────────────────────────────────
def _download_url(url: str, dest: str) -> str:
    """Download video from Instagram/YouTube using yt-dlp."""
    import subprocess

    result = subprocess.run(
        [
            "yt-dlp",
            "--no-playlist",
            "--max-filesize", "50M",
            "-f", "mp4/best[ext=mp4]",
            "-o", dest,
            url,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[:300]}")
    return dest


def _demo_video_id(folder: str, filename: str) -> str:
    """Generate a stable opaque ID for a whitelisted demo video."""
    raw = f"{folder}/{filename}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def _collect_demo_videos():
    """Discover demo videos and return (metadata list, id -> path lookup)."""
    videos = []
    video_lookup = {}

    for folder, directory in DEMO_VIDEO_DIRS.items():
        if not directory.exists() or not directory.is_dir():
            continue

        for file_path in directory.iterdir():
            if not file_path.is_file() or file_path.suffix.lower() != ".mp4":
                continue

            stat = file_path.stat()
            video_id = _demo_video_id(folder, file_path.name)
            videos.append(
                {
                    "id": video_id,
                    "name": file_path.name,
                    "url": f"/api/demo-videos/{video_id}/stream",
                    "folder": folder,
                    "size_bytes": stat.st_size,
                    "modified_at": int(stat.st_mtime),
                }
            )
            video_lookup[video_id] = file_path

    videos.sort(
        key=lambda item: (
            item["name"].lower(),
            item["folder"].lower(),
            item["url"].lower(),
        )
    )
    return videos, video_lookup


async def _run_pipeline_async(job_id: str, video_path: str, target_lang: str, source_lang: str):
    """Run the translation pipeline in a background thread, pushing progress to the job store."""
    from pipeline import run_pipeline

    job = jobs[job_id]
    job["status"] = "running"
    start = time.time()

    try:
        output_path = str(OUTPUT_DIR / f"{job_id}.mp4")
        gen = run_pipeline(
            video_path=video_path,
            target_language=target_lang,
            source_language=source_lang,
            output_path=output_path,
        )

        step = 0

        def _run_gen():
            nonlocal step
            messages = []
            output = None
            try:
                while True:
                    msg = next(gen)
                    messages.append(msg)
                    # Detect step number from messages
                    if "Step" in msg and "/6" in msg:
                        try:
                            step = int(msg.split("Step")[1].split("/")[0].strip())
                        except (ValueError, IndexError):
                            pass
                    job["messages"].append({"type": "progress", "message": msg.strip(), "step": step})
            except StopIteration as e:
                output = e.value
            return output

        loop = asyncio.get_event_loop()
        result_path = await loop.run_in_executor(None, _run_gen)

        elapsed = round(time.time() - start)
        job["status"] = "complete"
        job["result_path"] = result_path or output_path
        job["messages"].append({"type": "complete", "elapsed": elapsed})

    except Exception as e:
        job["status"] = "error"
        job["messages"].append({"type": "error", "message": str(e)})


# ── Routes ─────────────────────────────────────────────

@app.get("/api/demo-videos")
async def list_demo_videos():
    """List whitelisted MP4 demo videos from outputs/ and data/."""
    videos, _ = _collect_demo_videos()
    return JSONResponse({"videos": videos})


@app.get("/api/demo-videos/{video_id}/stream")
async def stream_demo_video(video_id: str):
    """Stream a demo video by opaque ID (no client-provided path)."""
    _, video_lookup = _collect_demo_videos()
    video_path = video_lookup.get(video_id)
    if not video_path:
        raise HTTPException(404, "Demo video not found.")

    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename=video_path.name,
    )


@app.post("/api/jobs")
async def create_job(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    target_language: str = Form("Spanish"),
    source_language: str = Form("en"),
):
    """Submit a video for translation."""
    if not file and not url:
        raise HTTPException(400, "Provide either a file upload or a URL.")

    job_id = str(uuid.uuid4())[:12]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    video_path = ""

    if file:
        # Save uploaded file
        ext = Path(file.filename or "video.mp4").suffix or ".mp4"
        video_path = str(job_dir / f"input{ext}")
        with open(video_path, "wb") as f:
            content = await file.read()
            if len(content) > 50 * 1024 * 1024:
                raise HTTPException(400, "File must be under 50MB.")
            f.write(content)
    elif url:
        # Download from URL
        video_path = str(job_dir / "input.mp4")
        try:
            _download_url(url, video_path)
        except Exception as e:
            shutil.rmtree(job_dir, ignore_errors=True)
            raise HTTPException(400, f"Failed to download video: {e}")

    # Initialize job
    jobs[job_id] = {
        "status": "queued",
        "messages": [],
        "result_path": None,
        "error": None,
        "created_at": time.time(),
    }

    # Start pipeline in background
    asyncio.create_task(_run_pipeline_async(job_id, video_path, target_language, source_language))

    return JSONResponse({"job_id": job_id, "status": "queued"})


@app.get("/api/jobs/{job_id}")
async def job_status_sse(job_id: str):
    """SSE endpoint streaming real-time pipeline progress."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found.")

    async def event_generator():
        import json
        sent = 0
        while True:
            job = jobs.get(job_id)
            if not job:
                break

            # Send any new messages
            while sent < len(job["messages"]):
                msg = job["messages"][sent]
                yield {"event": "message", "data": json.dumps(msg)}
                sent += 1

                # If terminal message, stop
                if msg.get("type") in ("complete", "error"):
                    return

            await asyncio.sleep(0.3)

    return EventSourceResponse(event_generator())


@app.get("/api/jobs/{job_id}/result")
async def job_result(job_id: str):
    """Download the translated video."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    if job["status"] != "complete":
        raise HTTPException(400, f"Job is {job['status']}, not complete.")
    if not job["result_path"] or not Path(job["result_path"]).exists():
        raise HTTPException(404, "Result file not found.")

    return FileResponse(
        job["result_path"],
        media_type="video/mp4",
        filename=f"videovoice_{job_id}.mp4",
    )


# ── Serve frontend static files ───────────────────────
frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


# ── Startup ───────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
