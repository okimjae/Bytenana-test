import logging
from typing import Any, Dict, Optional
from src.config import settings
from src.observability.logger import logger


def init_sentry():
    """Initializes Sentry SDK if SENTRY_DSN is configured. Falls back gracefully."""
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            logger.info("Sentry APM & Error Tracking initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")
    else:
        logger.info("Sentry DSN not provided. Running in local observability mode (JSON Logs).")


class SentrySpanContext:
    """Context manager wrapping Sentry spans with no-op fallback."""

    def __init__(self, op: str, description: str, tags: Optional[Dict[str, Any]] = None):
        self.op = op
        self.description = description
        self.tags = tags or {}
        self.span = None

    def __enter__(self):
        if settings.SENTRY_DSN:
            try:
                import sentry_sdk

                self.span = sentry_sdk.start_span(op=self.op, description=self.description)
                for k, v in self.tags.items():
                    sentry_sdk.set_tag(k, v)
                self.span.__enter__()
            except Exception:
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            try:
                self.span.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass
