from __future__ import annotations  # optional, but helps
from langchain.schema import Document
from langchain_community.tools.tavily_search import TavilySearchResults
from graph.state import GraphState
from typing import Any, Dict, List

web_search_tool = TavilySearchResults(k=3)

def web_search(state: GraphState) -> Dict[str, Any]:
    print("---WEB SEARCH---")
    question = state["question"]
    documents: List[Document] = state.get("documents", []) or []

    results = web_search_tool.invoke({"query": question})  # list[dict]
    web_docs = [
        Document(
            page_content=r.get("content", ""),
            metadata={**{k: v for k, v in r.items() if k != "content"}, "source": "tavily"},
        )
        for r in results if r.get("content")
    ]
    documents.extend(web_docs)

    return {
        "question": question,
        "documents": documents,
        "web_search": False,
        "used_web_search": True,
        "route": "web" if not state.get("route") else state["route"],
    }
