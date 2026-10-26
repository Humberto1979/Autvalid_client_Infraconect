# F4 Backing services: conexao com Postgres sempre por host/porta via env.
import atexit
import threading
from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool

from .config import settings


def get_conn():
    """Conexao avulsa — processos admin (migrate) e checks pontuais."""
    return psycopg.connect(settings.database_url, connect_timeout=5)


_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def _get_pool() -> ConnectionPool:
    """Singleton preguicoso de conexoes.

    Criado na primeira requisicao de cada worker: com `preload_app=True`
    (gunicorn_conf.py), um pool criado no master do Gunicorn seria herdado
    por fork, e conexoes compartilhadas pelo fork sao um anti-padrao.
    """
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = ConnectionPool(
                settings.database_url,
                min_size=settings.pool_min,
                max_size=settings.pool_max,
                timeout=5,
                open=True,
                name="api-pool",
            )
    return _pool


@contextmanager
def connection():
    """Conexao do pool: commit em sucesso, rollback em falha."""
    with _get_pool().connection() as conn:
        yield conn


def _shutdown_pool() -> None:
    """Fecha o pool no shutdown do worker (SIGTERM do Gunicorn).

    Sem isso, as threads de background do psycopg_pool nao terminam a
    tempo e o interpreter emite `couldn't stop thread ... near exit`.
    No master (preload), `_pool` e None -> no-op.
    """
    if _pool is not None:
        try:
            _pool.close(timeout=5)
        except Exception:
            pass


atexit.register(_shutdown_pool)
