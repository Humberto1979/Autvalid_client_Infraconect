from flask import Blueprint, jsonify

from ..db import connection

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def healthz():
    # Liveness: integridade basica do processo.
    return jsonify(status="ok"), 200


@bp.get("/readyz")
def readyz():
    # Readiness: conectividade real com o Postgres (via pool).
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception as exc:
        return jsonify(status="not_ready", error=str(exc)), 503
    return jsonify(status="ready"), 200