# F12 Admin processes: migracoes como processo efemero (Job/InitContainer/
# `docker compose run migrate`) com a mesma imagem e env da app.
from pathlib import Path

from .db import get_conn

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _ensure_registry(conn) -> set:
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "  name TEXT PRIMARY KEY,"
            "  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()"
            ")"
        )
        cur.execute("SELECT name FROM schema_migrations")
        applied = {r[0] for r in cur.fetchall()}
    conn.commit()
    return applied


def main() -> int:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    conn = get_conn()
    try:
        applied = _ensure_registry(conn)
        if not files:
            print("no migrations to apply")
            return 0
        for f in files:
            if f.name in applied:
                print(f"skip  {f.name} (already applied)")
                continue
            print(f"apply {f.name}")
            # Cada arquivo e uma transacao atomica (DDL e transacional em
            # Postgres): aplica o SQL e grava o registro junto, ou nada.
            with conn.cursor() as cur:
                cur.execute(f.read_text(encoding="utf-8"))
                cur.execute(
                    "INSERT INTO schema_migrations (name) VALUES (%s)", (f.name,)
                )
            conn.commit()
        print("migrations done")
    except Exception:
        # Falha -> rollback da transacao em curso e erro para o supervisor
        # (Compose/K8s Job nao inicia a app com schema parcial).
        conn.rollback()
        raise
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())