import logging
import os
import json
import warnings


def _level(name: str, default: str) -> int:
    value = os.getenv(name, default).strip().upper()
    return getattr(logging, value, logging.INFO)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except Exception:
        return default


TRACE_ENABLED = _env_bool("APP_TRACE_ENABLED", True)
TRACE_MAX_CHARS = _env_int("APP_TRACE_MAX_CHARS", 1200)
TRACE_VERBOSE = _env_bool("APP_TRACE_VERBOSE", False)
TRACE_MINIMAL_EVENTS = {
    item.strip()
    for item in os.getenv(
        "APP_TRACE_MINIMAL_EVENTS",
        "http.ask.in,http.ask.out,http.ask.error",
    ).split(",")
    if item.strip()
}


def _preview(value, max_chars: int = TRACE_MAX_CHARS):
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, str):
        if len(value) <= max_chars:
            return value
        return value[:max_chars] + "...[truncated]"
    if isinstance(value, list):
        return [_preview(v, max_chars=max_chars) for v in value]
    if isinstance(value, dict):
        return {str(k): _preview(v, max_chars=max_chars) for k, v in value.items()}
    return _preview(str(value), max_chars=max_chars)


def trace_event(event: str, **fields) -> None:
    if not TRACE_ENABLED:
        return
    if not TRACE_VERBOSE and event not in TRACE_MINIMAL_EVENTS:
        return
    payload = {"event": event, **{k: _preview(v) for k, v in fields.items()}}
    logging.getLogger("app.trace").info(
        json.dumps(payload, ensure_ascii=False, default=str)
    )


def configure_logging() -> None:
    root_level = _level("LOG_LEVEL", "INFO")
    sql_level = _level("SQLALCHEMY_LOG_LEVEL", "WARNING")
    access_level = _level("UVICORN_ACCESS_LOG_LEVEL", "WARNING")
    httpx_level = _level("HTTPX_LOG_LEVEL", "WARNING")
    hf_level = _level("HUGGINGFACE_LOG_LEVEL", "ERROR")
    st_level = _level("SENTENCE_TRANSFORMERS_LOG_LEVEL", "WARNING")
    google_api_level = _level("GOOGLE_API_LOG_LEVEL", "ERROR")

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=root_level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    else:
        root_logger.setLevel(root_level)

    logging.getLogger("sqlalchemy.engine").setLevel(sql_level)
    logging.getLogger("sqlalchemy.pool").setLevel(sql_level)
    logging.getLogger("sqlalchemy.dialects").setLevel(sql_level)
    logging.getLogger("uvicorn.access").setLevel(access_level)
    logging.getLogger("httpx").setLevel(httpx_level)
    logging.getLogger("huggingface_hub").setLevel(hf_level)
    logging.getLogger("sentence_transformers").setLevel(st_level)
    logging.getLogger("transformers").setLevel(st_level)
    logging.getLogger("urllib3").setLevel(httpx_level)
    logging.getLogger("googleapiclient").setLevel(google_api_level)
    logging.getLogger("googleapiclient.discovery_cache").setLevel(google_api_level)

    logging.getLogger("app.trace").setLevel(_level("APP_TRACE_LOG_LEVEL", "INFO"))

    warnings.filterwarnings(
        "ignore",
        message=r".*unauthenticated requests to the HF Hub.*",
    )
