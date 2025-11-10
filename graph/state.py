from typing import List, TypedDict, Literal
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document  # type: ignore


class GraphState(TypedDict, total=False):
    """
    State carried through the graph (used at runtime by LangGraph).
    Because StateGraph(GraphState) uses this at runtime, this symbol must import cleanly.
    """
    question: str
    generation: str
    documents: List[Document]

    web_search: bool
    used_web_search: bool
    route: Literal["vector", "web", "hybrid"]
