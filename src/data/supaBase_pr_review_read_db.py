from __future__ import annotations
from typing import Optional
from src.data.supaBase_db import DB


class SupaBasePRReviewReadDB:
    @staticmethod
    def get_latest_job(repo_full_name: str, pr_number: int) -> Optional[dict]:
        sql = """
        select *
        from public.pr_review_jobs
        where repo_full_name = %s and pr_number = %s
        order by created_at desc
        limit 1
        """
        return DB.fetch_one(sql, (repo_full_name, pr_number))

    @staticmethod
    def get_job(job_id: str) -> Optional[dict]:
        sql = "select * from public.pr_review_jobs where id = %s"
        return DB.fetch_one(sql, (job_id,))

    @staticmethod
    def get_report_by_job(job_id: str) -> Optional[dict]:
        sql = "select * from public.pr_review_reports where job_id = %s"
        return DB.fetch_one(sql, (job_id,))

    @staticmethod
    def get_findings(report_id: str) -> list[dict]:
        sql = """
        select *
        from public.pr_review_findings
        where report_id = %s
        order by
          case severity
            when 'BLOCKER' then 1
            when 'MAJOR' then 2
            when 'MINOR' then 3
            when 'NIT' then 4
            else 5
          end,
          created_at asc
        """
        return DB.fetch_all(sql, (report_id,))

    @staticmethod
    def get_test_suggestions(report_id: str) -> list[dict]:
        sql = """
        select *
        from public.pr_review_test_suggestions
        where report_id = %s
        order by created_at asc
        """
        return DB.fetch_all(sql, (report_id,))

    @staticmethod
    def get_counts_by_severity(report_id: str) -> dict:
        sql = """
        select severity, count(*)::int as count
        from public.pr_review_findings
        where report_id = %s
        group by severity
        """
        rows = DB.fetch_all(sql, (report_id,))
        counts = {"BLOCKER": 0, "MAJOR": 0, "MINOR": 0, "NIT": 0}
        for r in rows:
            counts[r["severity"]] = r["count"]
        return counts

    @staticmethod
    def list_jobs(repo_full_name: str, pr_number: int, limit: int = 20, offset: int = 0) -> list[dict]:
        sql = """
        select *
        from public.pr_review_jobs
        where repo_full_name = %s and pr_number = %s
        order by created_at desc
        limit %s offset %s
        """
        return DB.fetch_all(sql, (repo_full_name, pr_number, limit, offset))


    @staticmethod
    def list_reviewed_repos(limit: int = 50, offset: int = 0) -> list[dict]:
        sql = """
        with last_job as (
        select distinct on (repo_full_name)
            repo_full_name,
            created_at as last_review_at,
            status as last_status
        from public.pr_review_jobs
        order by repo_full_name, created_at desc
        ),
        counts as (
        select
            repo_full_name,
            count(*)::int as jobs_total,
            count(distinct pr_number)::int as prs_reviewed
        from public.pr_review_jobs
        group by repo_full_name
        )
        select
        c.repo_full_name,
        l.last_review_at,
        l.last_status,
        c.prs_reviewed,
        c.jobs_total
        from counts c
        join last_job l using (repo_full_name)
        order by l.last_review_at desc
        limit %s offset %s;
        """
        return DB.fetch_all(sql, (limit, offset))


    @staticmethod
    def list_reviewed_prs_by_repo(repo_full_name: str, limit: int = 50, offset: int = 0) -> list[dict]:
        sql = """
        with last_job as (
        select distinct on (repo_full_name, pr_number)
            repo_full_name,
            pr_number,
            id as last_job_id,
            head_sha as last_head_sha,
            status as last_status,
            created_at as last_review_at
        from public.pr_review_jobs
        where repo_full_name = %s
        order by repo_full_name, pr_number, created_at desc
        ),
        counts as (
        select
            repo_full_name,
            pr_number,
            count(*)::int as jobs_total
        from public.pr_review_jobs
        where repo_full_name = %s
        group by repo_full_name, pr_number
        )
        select
        l.repo_full_name,
        l.pr_number,
        l.last_job_id,
        l.last_head_sha,
        l.last_status,
        l.last_review_at,
        c.jobs_total
        from last_job l
        join counts c
        on c.repo_full_name = l.repo_full_name and c.pr_number = l.pr_number
        order by l.last_review_at desc
        limit %s offset %s;
        """
        return DB.fetch_all(sql, (repo_full_name, repo_full_name, limit, offset))
