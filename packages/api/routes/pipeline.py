"""
Full Pipeline endpoints - Topic → Video + Pedagogical Metadata

Provides synchronous and asynchronous endpoints for the complete
Layer 1 → Layer 2 → Layer 3 → Layer 4 pipeline.

Uses Supabase for persistent job storage and video hosting.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from pathlib import Path
from datetime import datetime
import uuid

from orchestrator import (
    FullPipelineOrchestrator,
    FullPipelineRequest,
    FullPipelineResponse,
    PipelineProgress,
    PipelineStage,
)

from supabase_client import JobStore, VideoStore

router = APIRouter()

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
    job_id = str(uuid.uuid4())[:8]

    try:
        # Create job in database
        JobStore.create_job(job_id, request.topic)

        orch = get_orchestrator()

        def progress_callback(progress: PipelineProgress):
            JobStore.update_progress(
                job_id,
                stage=progress.stage.value,
                progress_percent=progress.progress_percent,
                message=progress.message,
                error=progress.error
            )

        # Run pipeline (blocking)
        result = orch.run(
            topic=request.topic,
            domain=request.domain,
            difficulty_level=request.difficulty_level,
            include_generated_code=request.include_generated_code,
            progress_callback=progress_callback,
        )

        # Upload video to Supabase Storage
        video_url = None
        if result.video and result.video.video_path:
            storage_path = VideoStore.upload_video(
                job_id,
                result.video.video_path,
                request.topic
            )
            if storage_path:
                video_url = f"/api/pipeline/video/{job_id}"
                result.video.video_url = video_url

        # Update job_id to match our generated one
        result.job_id = job_id

        # Mark job complete
        JobStore.complete_job(job_id, result.model_dump(), video_url)

        return result

    except Exception as e:
        JobStore.fail_job(job_id, str(e))
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

    # Create job in database
    JobStore.create_job(job_id, request.topic)

    def run_pipeline():
        try:
            orch = get_orchestrator()

            def progress_callback(progress: PipelineProgress):
                JobStore.update_progress(
                    job_id,
                    stage=progress.stage.value,
                    progress_percent=progress.progress_percent,
                    message=progress.message,
                    error=progress.error
                )

            result = orch.run(
                topic=request.topic,
                domain=request.domain,
                difficulty_level=request.difficulty_level,
                include_generated_code=request.include_generated_code,
                progress_callback=progress_callback,
            )

            # Upload video to Supabase Storage
            video_url = None
            if result.video and result.video.video_path:
                storage_path = VideoStore.upload_video(
                    job_id,
                    result.video.video_path,
                    request.topic
                )
                if storage_path:
                    video_url = f"/api/pipeline/video/{job_id}"
                    result.video.video_url = video_url

            # Override result's job_id to match the route's job_id
            result.job_id = job_id

            # Mark job complete in database
            JobStore.complete_job(job_id, result.model_dump(), video_url)

        except Exception as e:
            JobStore.fail_job(job_id, str(e))

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
        - If in progress: { "status": "in_progress", "progress": {...} }
        - If failed: { "status": "failed", "error": "..." }
        - If not found: 404 error
    """
    job = JobStore.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["status"] == "completed":
        return {
            "status": "completed",
            "result": job["result"],
        }

    if job["status"] == "failed":
        return {
            "status": "failed",
            "progress": {
                "job_id": job["job_id"],
                "stage": job["stage"],
                "progress_percent": job["progress_percent"],
                "message": job["message"],
            },
            "error": job["error"],
        }

    # In progress or pending
    return {
        "status": "in_progress",
        "progress": {
            "job_id": job["job_id"],
            "stage": job["stage"],
            "progress_percent": job["progress_percent"],
            "message": job["message"],
            "started_at": job["created_at"],
            "updated_at": job["updated_at"],
        },
    }


@router.get("/video/{job_id}")
async def get_video(job_id: str):
    """
    Get a signed URL for the generated video.

    Redirects to a time-limited signed URL from Supabase Storage.
    """
    job = JobStore.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    # Get video path from result
    result = job.get("result", {})
    video_info = result.get("video", {})

    if not video_info:
        raise HTTPException(status_code=404, detail="No video in job result")

    # Construct storage path
    topic = job.get("topic", "video")
    safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:50]
    storage_path = f"{job_id}/{safe_topic}.mp4"

    # Get signed URL (valid for 1 hour)
    signed_url = VideoStore.get_signed_url(storage_path, expires_in=3600)

    if not signed_url:
        raise HTTPException(status_code=404, detail="Video not found in storage")

    # Redirect to the signed URL
    return RedirectResponse(url=signed_url)


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Clean up a completed or failed job.

    Removes the job from database and deletes the video from storage.
    """
    job = JobStore.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Delete video from storage if exists
    topic = job.get("topic", "video")
    safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:50]
    storage_path = f"{job_id}/{safe_topic}.mp4"
    VideoStore.delete_video(storage_path)

    # Delete from database
    from supabase_client import get_client
    get_client().table("pipeline_jobs").delete().eq("job_id", job_id).execute()

    return {"status": "deleted", "job_id": job_id}


@router.get("/jobs")
async def list_jobs(status: str = None, limit: int = 50):
    """
    List all jobs from database.

    Query params:
        - status: Filter by status (pending, in_progress, completed, failed)
        - limit: Max number of jobs to return (default 50)
    """
    jobs = JobStore.list_jobs(status=status, limit=limit)

    return {
        "jobs": [
            {
                "job_id": j["job_id"],
                "topic": j["topic"],
                "status": j["status"],
                "stage": j["stage"],
                "progress_percent": j["progress_percent"],
                "created_at": j["created_at"],
                "updated_at": j["updated_at"],
            }
            for j in jobs
        ],
        "total": len(jobs),
    }
