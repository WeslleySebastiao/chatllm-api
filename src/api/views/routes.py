from fastapi import APIRouter, Query
from typing import Optional

from src.data.supaBase_db import DB  # seu core DB

router_view = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router_view.get("/overview")
def dashboard_overview(agent_id: Optional[str] = Query(default=None)):
    """
    Visão geral (totais all-time), opcionalmente filtrado por agent_id.
    Retorna JSON direto do Postgres via fn_dashboard_overview_total.
    """
    row = DB.fetch_one(
        "select public.fn_dashboard_overview_total(%s::text) as data;",
        (agent_id,),
    )
    return row["data"] if row else {}


@router_view.get("/totals-by-agent")
def dashboard_totals_by_agent():
    """
    Totais por agente (all-time).
    """
    rows = DB.fetch_all(
        """
        select *
        from public.vw_runs_totals_by_agent
        order by cost_usd_total desc nulls last;
        """
    )
    return {"items": rows}


@router_view.get("/last-runs")
def dashboard_last_runs(
    limit: int = Query(default=50, ge=1, le=200),
    agent_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    """
    Lista as últimas execuções.
    Dá pra filtrar por agent_id e status.
    """
    sql = """
    select
    id, created_at, finished_at,
    agent_id, user_id, session_id,
    status, duration_ms,
    model, total_tokens, cost_usd,
    error_type, error_message
    from public.runs
    where 1=1
    """
    params = []

    if agent_id:
        sql += " and agent_id = %s"
        params.append(agent_id)

    if status:
        sql += " and status = %s"
        params.append(status)

    sql += " order by created_at desc limit %s"
    params.append(limit)

    rows = DB.fetch_all(sql, tuple(params))
    return {"items": rows}
