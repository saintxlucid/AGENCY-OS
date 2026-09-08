"""
ASTRA OS — Worker settings (ARQ + fallback stub).

Canonical entrypoint referenced by docker-compose.yml:
  command: arq aurora.workers.settings.WorkerSettings

If `arq` is not installed, the API still boots — workers are optional.
"""
from __future__ import annotations

import os
from typing import Any


async def health_task(ctx: dict[str, Any]) -> str:
    """Minimal liveness task for queue smoke tests."""
    return "ok"


async def interpret_task(ctx: dict[str, Any], media_path: str) -> dict[str, Any]:
    """Deferred media interpretation (lazy import to avoid heavy deps at boot)."""
    from aurora.core import AuroraCore

    aurora = AuroraCore()
    await aurora.initialize()
    try:
        result = await aurora.interpret(media_path)
        return {"media_id": result.media_id, "summary": result.summary}
    finally:
        await aurora.shutdown()


class WorkerSettings:
    """ARQ worker configuration. Import-safe without arq installed."""

    functions = [health_task, interpret_task]
    redis_settings_kwargs = {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
    }
    max_jobs = 10
    job_timeout = 300
