from __future__ import annotations
from contextlib import contextmanager
from typing import Any, Iterable, Optional, Sequence
import psycopg2
from psycopg2.extras import RealDictCursor
from src.core.config import settings
from psycopg2.extras import Json


class DB:
    """
    Núcleo de acesso ao Postgres (Supabase).
    Centraliza conexão, commit/rollback e fechamento de recursos.
    """

    @staticmethod
    def connect():
        return psycopg2.connect(
            user=settings.SUPABASE_DB_USER,
            password=settings.SUPABASE_DB_PASSWORD,
            host=settings.SUPABASE_DB_HOST,
            port=settings.SUPABASE_DB_PORT,
            dbname=settings.SUPABASE_DB_NAME,
            sslmode="require",
        )

    @staticmethod
    @contextmanager
    def cursor(dict_cursor: bool = False):
        conn = DB.connect()
        cur = None
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor) if dict_cursor else conn.cursor()
            yield conn, cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cur is not None:
                cur.close()
            conn.close()

    @staticmethod
    def fetch_one(sql: str, params: Optional[Sequence[Any]] = None) -> Optional[dict]:
        with DB.cursor(dict_cursor=True) as (_, cur):
            cur.execute(sql, params or ())
            return cur.fetchone()

    @staticmethod
    def fetch_all(sql: str, params: Optional[Sequence[Any]] = None) -> list[dict]:
        with DB.cursor(dict_cursor=True) as (_, cur):
            cur.execute(sql, params or ())
            return cur.fetchall()

    @staticmethod
    def execute(sql: str, params: Optional[Sequence[Any]] = None) -> int:
        """
        Executa comando (INSERT/UPDATE/DELETE). Retorna rowcount.
        """
        with DB.cursor(dict_cursor=False) as (_, cur):
            cur.execute(sql, params or ())
            return cur.rowcount
