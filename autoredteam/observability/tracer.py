"""Laminar observability wrapper.

If `LMNR_PROJECT_API_KEY` is set, Laminar is initialized at import time and
every `@observe`-decorated function emits a span. If not, `observe` is a
no-op decorator and `set_span_attributes` / `set_trace_metadata` /
`get_trace_id` become safe no-ops. This keeps the pipeline runnable for
users who haven't signed up for Laminar.
"""

from __future__ import annotations

import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable

try:
    from dotenv import load_dotenv

    _env_file = Path(__file__).resolve().parents[2] / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

LMNR_PROJECT_API_KEY = os.environ.get("LMNR_PROJECT_API_KEY", "").strip()
ENABLED: bool = False

_lmnr_observe: Callable | None = None
_Laminar = None

if LMNR_PROJECT_API_KEY:
    try:
        from lmnr import Laminar as _Laminar  # type: ignore
        from lmnr import observe as _lmnr_observe  # type: ignore

        _Laminar.initialize(project_api_key=LMNR_PROJECT_API_KEY)
        ENABLED = True
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[tracer] Laminar init failed ({exc!r}); tracing disabled.")
        ENABLED = False


def observe(name: str | None = None) -> Callable:
    """Decorator that becomes a no-op when Laminar isn't initialized."""

    if ENABLED and _lmnr_observe is not None:
        return _lmnr_observe(name=name)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def set_span_attributes(attrs: dict[str, Any]) -> None:
    if ENABLED and _Laminar is not None:
        try:
            _Laminar.set_span_attributes(attrs)
        except Exception:
            pass


def set_trace_metadata(meta: dict[str, Any]) -> None:
    if ENABLED and _Laminar is not None:
        try:
            _Laminar.set_trace_metadata(meta)
        except Exception:
            pass


def get_trace_id() -> str | None:
    if ENABLED and _Laminar is not None:
        try:
            tid = _Laminar.get_trace_id()
            return str(tid) if tid else None
        except Exception:
            return None
    return None
