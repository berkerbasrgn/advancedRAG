from __future__ import annotations  # optional, but helps
from graph.chains.retrieval_grader import retrieval_grader
from graph.state import GraphState
from typing import Any, Dict, List

def grade_documents(state: GraphState) -> Dict[str, Any]:
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state.get("documents", []) or []

    filtered_docs = []
    trigger_web = False
    for d in documents:
        score = retrieval_grader.invoke({"question": question, "document": d.page_content})
        if str(score.binary_score).lower() == "yes":
            filtered_docs.append(d)
        else:
            trigger_web = True

    return {
        "question": question,
        "documents": filtered_docs,
        "web_search": trigger_web,                              # router trigger
        "used_web_search": state.get("used_web_search", False), # keep telemetry
        "route": "hybrid" if trigger_web else "vector",
    }
