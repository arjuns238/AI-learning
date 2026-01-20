"""
Full Pipeline endpoints - Topic → Video + Pedagogical Metadata

Provides synchronous and asynchronous endpoints for the complete
Layer 1 → Layer 2 → Layer 3 → Layer 4 pipeline.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict
from pathlib import Path
import asyncio
from datetime import datetime
import uuid

from orchestrator import (
    FullPipelineOrchestrator,
    FullPipelineRequest,
    FullPipelineResponse,
    PipelineProgress,
    PipelineStage,
)

router = APIRouter()

# In-memory job storage (for async jobs)
# In production, use Redis or a database
active_jobs: Dict[str, PipelineProgress] = {}
completed_jobs: Dict[str, FullPipelineResponse] = {}
video_paths: Dict[str, str] = {}  # job_id -> video_path

# Orchestrator instance (lazy init)
_orchestrator = None


def get_orchestrator() -> FullPipelineOrchestrator:
    """Lazy initialization of orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FullPipelineOrchestrator(
            video_resolution="480p15",  # Fast for development
            output_dir="output/pipeline",
        )
    return _orchestrator


@router.post("/generate", response_model=FullPipelineResponse)
async def generate_full_pipeline(request: FullPipelineRequest):
    """
    Generate complete educational content from a topic (synchronous).

    This endpoint blocks until the entire pipeline completes.
    For long-running operations, use /generate/async instead.

    Returns:
        FullPipelineResponse with video URL + all pedagogical metadata
    """
    try:
        orch = get_orchestrator()

        # Run pipeline (blocking)
        result = orch.run(
            topic=request.topic,
            domain=request.domain,
            difficulty_level=request.difficulty_level,
            include_generated_code=request.include_generated_code,
        )

        # Store video path for serving
        if result.video and result.video.video_path:
            video_paths[result.job_id] = result.video.video_path

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/async")
async def start_async_pipeline(
    request: FullPipelineRequest,
    background_tasks: BackgroundTasks
):
    """
    Start an asynchronous pipeline job.

    Returns immediately with job_id for polling progress.

    Example response:
        {
            "job_id": "abc123",
            "status": "started",
            "poll_url": "/api/pipeline/status/abc123"
        }
    """
    job_id = str(uuid.uuid4())[:8]

    # Initialize progress
    active_jobs[job_id] = PipelineProgress(
        job_id=job_id,
        stage=PipelineStage.PENDING,
        progress_percent=0,
        message="Job queued",
        started_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    def progress_callback(progress: PipelineProgress):
        active_jobs[job_id] = progress

    def run_pipeline():
        try:
            orch = get_orchestrator()
            result = orch.run(
                topic=request.topic,
                domain=request.domain,
                difficulty_level=request.difficulty_level,
                include_generated_code=request.include_generated_code,
                progress_callback=progress_callback,
            )

            # Store video path for serving (use route's job_id, not orchestrator's)
            if result.video and result.video.video_path:
                video_paths[job_id] = result.video.video_path

            # Override result's job_id to match the route's job_id
            result.job_id = job_id
            completed_jobs[job_id] = result

        except Exception as e:
            # Mark as failed
            active_jobs[job_id] = PipelineProgress(
                job_id=job_id,
                stage=PipelineStage.FAILED,
                progress_percent=0,
                message=f"Pipeline failed: {str(e)}",
                started_at=active_jobs[job_id].started_at,
                updated_at=datetime.now().isoformat(),
                error=str(e),
            )
        finally:
            # Clean up active job (keep for a bit for final status check)
            pass

    background_tasks.add_task(run_pipeline)

    return {
        "job_id": job_id,
        "status": "started",
        "poll_url": f"/api/pipeline/status/{job_id}",
    }


@router.get("/status/{job_id}")
async def get_pipeline_status(job_id: str):
    """
    Get status of an async pipeline job.

    Returns:
        - If completed: { "status": "completed", "result": FullPipelineResponse }
        - If in progress: { "status": "in_progress", "progress": PipelineProgress }
        - If not found: 404 error
    """
    # Check if completed
    if job_id in completed_jobs:
        result = completed_jobs[job_id]
        return {
            "status": "completed",
            "result": result.model_dump(),
        }

    # Check if in progress
    if job_id in active_jobs:
        progress = active_jobs[job_id]

        # Check if failed
        if progress.stage == PipelineStage.FAILED:
            return {
                "status": "failed",
                "progress": progress.model_dump(),
                "error": progress.error,
            }

        return {
            "status": "in_progress",
            "progress": progress.model_dump(),
        }

    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.get("/video/{job_id}")
async def get_video(job_id: str):
    """
    Serve the generated video file.

    Returns the video as a downloadable MP4 file.
    """
    # Check completed jobs first
    if job_id in completed_jobs:
        result = completed_jobs[job_id]
        if result.video and result.video.video_path:
            video_path = Path(result.video.video_path)
            if video_path.exists():
                return FileResponse(
                    video_path,
                    media_type="video/mp4",
                    filename=f"{result.topic.replace(' ', '_')}.mp4",
                )

    # Check video_paths cache
    if job_id in video_paths:
        video_path = Path(video_paths[job_id])
        if video_path.exists():
            return FileResponse(
                video_path,
                media_type="video/mp4",
                filename=f"video_{job_id}.mp4",
            )

    raise HTTPException(status_code=404, detail="Video not found")


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Clean up a completed or failed job.

    Removes the job from memory and optionally deletes the video file.
    """
    deleted = False

    if job_id in completed_jobs:
        del completed_jobs[job_id]
        deleted = True

    if job_id in active_jobs:
        del active_jobs[job_id]
        deleted = True

    if job_id in video_paths:
        del video_paths[job_id]
        deleted = True

    if deleted:
        return {"status": "deleted", "job_id": job_id}

    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.get("/jobs")
async def list_jobs():
    """
    List all active and completed jobs.

    Useful for debugging and monitoring.
    """
    return {
        "active_jobs": list(active_jobs.keys()),
        "completed_jobs": list(completed_jobs.keys()),
        "total_active": len(active_jobs),
        "total_completed": len(completed_jobs),
    }
