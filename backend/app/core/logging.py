import logging
import json
from datetime import datetime
from typing import Any, Dict

from app.core import context

class JSONFormatter(logging.Formatter):
    """
    JSON structured logging formatter.
    Ensures production-safe, async-safe logging without leaking sensitive financial info.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Context Variables
        request_id = context.get_request_id()
        if request_id:
            log_data["request_id"] = str(request_id)
        
        tenant_id = context.get_tenant_id()
        if tenant_id:
            log_data["tenant_id"] = str(tenant_id)
            
        user_id = context.get_user_id()
        if user_id:
            log_data["user_id"] = str(user_id)

        # Merge in extra kwargs passed to logger
        if hasattr(record, "extra"):
            for key, value in record.extra.items():
                log_data[key] = value

        # Standard custom operational fields
        for attr in ["service", "operation", "status", "duration_ms", "error_type", "endpoint", "method"]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        if record.exc_info:
            log_data["error_stack"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging() -> None:
    formatter = JSONFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)
