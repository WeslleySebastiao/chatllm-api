# telemetry_runs.py
import time, uuid, hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.data.supaBase.supaBase_log_db import SupaBaseRunsDB  # <- novo repo (psycopg2)

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def ms_since(start_perf: float) -> int:
    return int((time.perf_counter() - start_perf) * 1000)

def hash_error(msg: str) -> str:
    return hashlib.sha256(msg.encode("utf-8")).hexdigest()[:16]

def start_run(*, agent_id: str, user_id: Optional[str], session_id: Optional[str],
            agent_version: Optional[str] = None, model: Optional[str] = None,
            provider: str = "openai", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    start_perf = time.perf_counter()

    SupaBaseRunsDB.insert_run({
        "id": run_id,
        "created_at": now_utc(),
        "status": "running",
        "agent_id": agent_id,
        "agent_version": agent_version,
        "user_id": user_id,
        "session_id": session_id,
        "provider": provider,
        "model": model,
        "metadata": metadata or {},
    })

    return {"run_id": run_id, "start_perf": start_perf}

def finish_run_success(*, run_id: str, start_perf: float, session_id: Optional[str],
                    model: Optional[str], prompt_tokens: Optional[int],
                    completion_tokens: Optional[int], total_tokens: Optional[int],
                    cost_usd: Optional[float], prompt_tokens_cached: Optional[int] = None,
                    reasoning_tokens: Optional[int] = None, metadata_patch: Optional[Dict[str, Any]] = None) -> None:

    patch = {
        "status": "success",
        "finished_at": now_utc(),
        "duration_ms": ms_since(start_perf),
        "session_id": session_id,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
        "prompt_tokens_cached": prompt_tokens_cached,
        "reasoning_tokens": reasoning_tokens,
    }

    if metadata_patch:
        patch["metadata"] = {"telemetry": metadata_patch}

    SupaBaseRunsDB.update_run(run_id, patch)

def finish_run_error(*, run_id: str, start_perf: float, error_type: str, error_message: str,
                    session_id: Optional[str] = None, model: Optional[str] = None,
                    metadata_patch: Optional[Dict[str, Any]] = None) -> None:

    patch = {
        "status": "error",
        "finished_at": now_utc(),
        "duration_ms": ms_since(start_perf),
        "session_id": session_id,
        "model": model,
        "error_type": error_type,
        "error_message": (error_message or "")[:800],
        "error_hash": hash_error(f"{error_type}:{error_message}"),
    }

    if metadata_patch:
        patch["metadata"] = {"telemetry": metadata_patch}

    SupaBaseRunsDB.update_run(run_id, patch)
