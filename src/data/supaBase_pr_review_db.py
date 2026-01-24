from __future__ import annotations
from typing import Any, Optional
from psycopg2.extras import Json
from src.data.supaBase_db import DB


class SupaBasePRReviewDB:
    @staticmethod
    def upsert_job(
        repo_full_name: str,
        pr_number: int,
        head_sha: str,
        base_sha: Optional[str],
        status: str,
        trigger: str = "github_action",
        error: Optional[str] = None,
    ) -> dict:
        """
        Cria ou atualiza job (idempotente por repo+pr+head_sha).
        Retorna a row (inclui id).
        """
        sql = """
        insert into public.pr_review_jobs
        (repo_full_name, pr_number, head_sha, base_sha, status, trigger, error, started_at, finished_at)
        values
        (%s, %s, %s, %s, %s, %s, %s,
        case when %s = 'running' then now() else null end,
        case when %s in ('completed','failed') then now() else null end)
        on conflict (repo_full_name, pr_number, head_sha)
        do update set
        base_sha = excluded.base_sha,
        status = excluded.status,
        trigger = excluded.trigger,
        error = excluded.error,
        started_at = coalesce(pr_review_jobs.started_at, excluded.started_at),
        finished_at = excluded.finished_at
        returning *;
        """
        return DB.fetch_one(
            sql,
            (
                repo_full_name,
                pr_number,
                head_sha,
                base_sha,
                status,
                trigger,
                error,
                status,
                status,
            ),
        )

    @staticmethod
    def upsert_report(
        job_id: str,
        summary_md: Optional[str],
        result_json: dict,
        agents_executed: Optional[list[str]] = None,
        duration_ms: Optional[int] = None,
    ) -> dict:
        """
        Garante 1 report por job (unique job_id).
        """
        sql = """
        insert into public.pr_review_reports
        (job_id, summary_md, result_json, agents_executed, duration_ms)
        values
        (%s, %s, %s, %s, %s)
        on conflict (job_id)
        do update set
        summary_md = excluded.summary_md,
        result_json = excluded.result_json,
        agents_executed = excluded.agents_executed,
        duration_ms = excluded.duration_ms,
        created_at = now()
        returning *;
        """
        return DB.fetch_one(
            sql,
            (
                job_id,
                summary_md,
                Json(result_json),
                Json(agents_executed) if agents_executed is not None else None,
                duration_ms,
            ),
        )

    @staticmethod
    def replace_findings(report_id: str, findings: list[dict]) -> None:
        """
        Remove findings antigos e insere os novos.
        """
        DB.execute("delete from public.pr_review_findings where report_id = %s", (report_id,))

        if not findings:
            return

        sql = """
        insert into public.pr_review_findings
        (report_id, severity, title, file, line_range, evidence, recommendation, confidence, source_agent)
        values
        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with DB.cursor(dict_cursor=False) as (_, cur):
            for f in findings:
                cur.execute(
                    sql,
                    (
                        report_id,
                        f.get("severity"),
                        f.get("title"),
                        f.get("file"),
                        f.get("line_range"),
                        f.get("evidence"),
                        f.get("recommendation"),
                        f.get("confidence"),
                        f.get("source_agent"),
                    ),
                )

    @staticmethod
    def replace_test_suggestions(report_id: str, tests: list[str]) -> None:
        DB.execute("delete from public.pr_review_test_suggestions where report_id = %s", (report_id,))

        if not tests:
            return

        sql = """
        insert into public.pr_review_test_suggestions (report_id, suggestion)
        values (%s, %s)
        """
        with DB.cursor(dict_cursor=False) as (_, cur):
            for t in tests:
                cur.execute(sql, (report_id, t))
