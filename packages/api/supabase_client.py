"""
Supabase client for job storage and video uploads.
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from supabase import create_client, Client
from dotenv import load_dotenv

# Load env from pedagogy-engine (where credentials are stored)
_env_path = Path(__file__).parent.parent / "pedagogy-engine" / ".env"
load_dotenv(_env_path)


def get_supabase_client() -> Client:
    """Get initialized Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set")

    return create_client(url, key)


# Singleton client instance
_client: Optional[Client] = None


def get_client() -> Client:
    """Get or create singleton Supabase client."""
    global _client
    if _client is None:
        _client = get_supabase_client()
    return _client


class JobStore:
    """Supabase-backed job storage."""

    TABLE = "pipeline_jobs"

    @staticmethod
    def create_job(job_id: str, topic: str) -> dict:
        """Create a new job record."""
        client = get_client()
        data = {
            "job_id": job_id,
            "status": "pending",
            "stage": "pending",
            "progress_percent": 0,
            "message": "Job queued",
            "topic": topic,
        }
        result = client.table(JobStore.TABLE).insert(data).execute()
        return result.data[0] if result.data else data

    @staticmethod
    def update_progress(
        job_id: str,
        stage: str,
        progress_percent: int,
        message: str,
        error: Optional[str] = None
    ) -> dict:
        """Update job progress."""
        client = get_client()
        data = {
            "stage": stage,
            "progress_percent": progress_percent,
            "message": message,
            "status": "failed" if error else "in_progress",
        }
        if error:
            data["error"] = error

        result = client.table(JobStore.TABLE).update(data).eq("job_id", job_id).execute()
        return result.data[0] if result.data else {}

    @staticmethod
    def complete_job(job_id: str, result: dict, video_url: Optional[str] = None) -> dict:
        """Mark job as completed with result."""
        client = get_client()
        data = {
            "status": "completed",
            "stage": "completed",
            "progress_percent": 100,
            "message": "Pipeline completed",
            "result": result,
        }
        if video_url:
            data["video_url"] = video_url

        db_result = client.table(JobStore.TABLE).update(data).eq("job_id", job_id).execute()
        return db_result.data[0] if db_result.data else {}

    @staticmethod
    def fail_job(job_id: str, error: str, stage: str = "failed") -> dict:
        """Mark job as failed."""
        client = get_client()
        data = {
            "status": "failed",
            "stage": stage,
            "error": error,
            "message": f"Pipeline failed: {error}",
        }
        result = client.table(JobStore.TABLE).update(data).eq("job_id", job_id).execute()
        return result.data[0] if result.data else {}

    @staticmethod
    def get_job(job_id: str) -> Optional[dict]:
        """Get job by ID."""
        client = get_client()
        result = client.table(JobStore.TABLE).select("*").eq("job_id", job_id).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def list_jobs(status: Optional[str] = None, limit: int = 50) -> list:
        """List jobs, optionally filtered by status."""
        client = get_client()
        query = client.table(JobStore.TABLE).select("*").order("created_at", desc=True).limit(limit)
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return result.data or []


class VideoStore:
    """Supabase Storage for videos."""

    BUCKET = "pipeline-videos"

    @staticmethod
    def upload_video(job_id: str, video_path: str, topic: str) -> Optional[str]:
        """
        Upload video to Supabase Storage.

        Returns the storage path (not a URL).
        """
        client = get_client()
        path = Path(video_path)

        if not path.exists():
            return None

        # Create a clean filename
        safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:50]
        storage_path = f"{job_id}/{safe_topic}.mp4"

        with open(path, "rb") as f:
            video_bytes = f.read()

        # Upload to storage
        client.storage.from_(VideoStore.BUCKET).upload(
            storage_path,
            video_bytes,
            file_options={"content-type": "video/mp4"}
        )

        return storage_path

    @staticmethod
    def get_signed_url(storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get a signed URL for a video.

        Args:
            storage_path: Path in storage (e.g., "job_id/topic.mp4")
            expires_in: URL expiry in seconds (default 1 hour)

        Returns:
            Signed URL or None if not found
        """
        client = get_client()
        try:
            result = client.storage.from_(VideoStore.BUCKET).create_signed_url(
                storage_path,
                expires_in
            )
            return result.get("signedURL")
        except Exception:
            return None

    @staticmethod
    def delete_video(storage_path: str) -> bool:
        """Delete a video from storage."""
        client = get_client()
        try:
            client.storage.from_(VideoStore.BUCKET).remove([storage_path])
            return True
        except Exception:
            return False
