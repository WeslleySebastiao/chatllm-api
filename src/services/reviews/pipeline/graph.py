from langgraph.graph import StateGraph, END

from src.services.reviews.pipeline.state import ReviewState
from src.services.reviews.pipeline.nodes.ingest_pr import ingest_pr
from src.services.reviews.pipeline.nodes.run_specialists import run_specialists
from src.services.reviews.pipeline.nodes.aggregate import aggregate


def build_review_graph():
    g = StateGraph(ReviewState)

    g.add_node("ingest_pr", ingest_pr)
    g.add_node("run_specialists", run_specialists)
    g.add_node("aggregate", aggregate)

    g.set_entry_point("ingest_pr")
    g.add_edge("ingest_pr", "run_specialists")
    g.add_edge("run_specialists", "aggregate")
    g.add_edge("aggregate", END)

    return g.compile()
