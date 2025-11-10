# graph/state.py
from typing import List, TypedDict, Literal
try:
    # LangChain v0.2+
    from langchain_core.documents import Document
except ImportError:
    # Older LangChain fallback
    from langchain.schema import Document  # type: ignore


class GraphState(TypedDict, total=False):
    """
    State carried through the graph (used at runtime by LangGraph).
    Because StateGraph(GraphState) uses this at runtime, this symbol must import cleanly.
    """
    question: str                 # user question
    generation: str               # model answer
    documents: List[Document]     # retrieved + web docs (LangChain Document objects)

    # Routing + telemetry flags
    web_search: bool              # router trigger: should we perform web search next?
    used_web_search: bool         # telemetry: did we actually perform web search?
    route: Literal["vector", "web", "hybrid"]
