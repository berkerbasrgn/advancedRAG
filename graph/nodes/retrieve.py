from __future__ import annotations
from typing import Any, Dict
from graph.state import GraphState
from ingestion import get_retriever

def retrieve(state: GraphState) -> Dict[str, Any]:
    print("---RETRIEVE---")
    q = state["question"]
    retriever = get_retriever()
    documents = retriever.invoke(q)
    return {
        "question": q,
        "documents": documents,
        "web_search": state.get("web_search", False),
        "used_web_search": state.get("used_web_search", False),
        "route": "vector",
    }
