from flask import Blueprint, jsonify, request
from psycopg.errors import UniqueViolation

from ..db import connection

bp = Blueprint("records", __name__)


@bp.get("/records")
def list_records():
    # Paginacao defensiva: limit clampado em 1..100 (default 100),
    # offset >= 0. Evita queries sem limite e valores negativos.
    limit = max(1, min(request.args.get("limit", type=int) or 100, 100))
    offset = max(request.args.get("offset", type=int) or 0, 0)
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, email, created_at FROM records "
            "ORDER BY id DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cur.fetchall()
    return jsonify(
        [
            {
                "id": r[0],
                "name": r[1],
                "email": r[2],
                "created_at": r[3].isoformat() if r[3] else None,
            }
            for r in rows
        ]
    )


@bp.post("/records")
def create_record():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    if not name or not email:
        return jsonify(error="name and email are required"), 400
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO records (name, email) VALUES (%s, %s) "
                "RETURNING id, created_at",
                (name, email),
            )
            rid, created_at = cur.fetchone()
    except UniqueViolation:
        return jsonify(error="email already registered"), 409
    return (
        jsonify(
            id=rid,
            name=name,
            email=email,
            created_at=created_at.isoformat() if created_at else None,
        ),
        201,
    )