import json
import logging
import time
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import psutil
except ImportError:
    psutil = None


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "structured_data"):
            log_obj.update(record.structured_data)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def get_logger(name: str = "spatial_pipeline") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger()


class PipelineStageTimer:
    """Context manager for structured execution timing and resource monitoring."""

    def __init__(self, stage_name: str, extra_meta: Optional[Dict[str, Any]] = None):
        self.stage_name = stage_name
        self.extra_meta = extra_meta or {}
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.info(
            f"Starting stage: {self.stage_name}",
            extra={"structured_data": {"stage": self.stage_name, "status": "STARTED", **self.extra_meta}},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        mem_mb = 0.0
        if psutil is not None:
            try:
                mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            except Exception:
                mem_mb = 0.0

        if exc_type is not None:
            logger.error(
                f"Stage {self.stage_name} failed: {exc_val}",
                extra={
                    "structured_data": {
                        "stage": self.stage_name,
                        "status": "FAILED",
                        "duration_ms": round(duration_ms, 2),
                        "memory_mb": round(mem_mb, 2),
                        **self.extra_meta,
                    }
                },
                exc_info=(exc_type, exc_val, exc_tb),
            )
        else:
            logger.info(
                f"Stage {self.stage_name} completed in {duration_ms:.2f}ms",
                extra={
                    "structured_data": {
                        "stage": self.stage_name,
                        "status": "COMPLETED",
                        "duration_ms": round(duration_ms, 2),
                        "memory_mb": round(mem_mb, 2),
                        **self.extra_meta,
                    }
                },
            )
