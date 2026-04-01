import logging
import structlog


def _mask_secrets(_, __, event_dict: dict) -> dict:
    """API 키 등 민감 정보를 로그에서 마스킹"""
    sensitive = ("api_key", "secret", "token", "password", "key")
    for k in list(event_dict.keys()):
        if any(s in k.lower() for s in sensitive):
            event_dict[k] = "***MASKED***"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """structlog JSON 로깅 설정. 애플리케이션 시작 시 1회 호출."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            _mask_secrets,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


def get_logger(name: str):
    return structlog.get_logger(name)
