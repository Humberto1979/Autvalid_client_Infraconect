# F9 Disposability: Gunicorn como PID 1, graceful-timeout trata SIGTERM.
# F11 Logs: accesslog/errorlog em "-" (stdout/stderr).
import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('APP_PORT', '5000')}"
workers = int(
    os.environ.get(
        "GUNICORN_WORKERS",
        str(min(multiprocessing.cpu_count() * 2 + 1, 4)),
    )
)
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "20"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
preload_app = True