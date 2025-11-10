from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from graph.chains.answer_grader import answer_grader
from graph.chains.hallucination_grader import hallucination_grader
from graph.chains.router import question_router, RouteQuery
from graph.node_constants import RETRIEVE, GRADE_DOCUMENTS, GENERATE, WEBSEARCH
from graph.nodes import generate, grade_documents, retrieve, web_search
from graph.state import GraphState
from typing import Dict, Any

load_dotenv()

def decide_to_generate(state: GraphState):
    print("---ASSESS GRADED DOCUMENTS---")
    if state.get("web_search"):
        print("---DECISION: SOME DOCS IRRELEVANT → INCLUDE WEB SEARCH---")
        return WEBSEARCH
    else:
        print("---DECISION: GENERATE---")
        return GENERATE

def grade_generation_grounded_in_documents_and_question(state: GraphState) -> str:
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state.get("documents", [])
    generation = state.get("generation", "")

    score = hallucination_grader.invoke({"documents": documents, "generation": generation})
    if score.binary_score:  # grounded
        print("---DECISION: GENERATION IS GROUNDED---")
        score2 = answer_grader.invoke({"question": question, "generation": generation})
        if score2.binary_score:
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: NOT GROUNDED → RE-TRY---")
        return "not supported"

def route_question(state: GraphState) -> str:
    print("---ROUTE QUESTION---")
    source: RouteQuery = question_router.invoke({"question": state["question"]})
    if source.datasource == WEBSEARCH:
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return WEBSEARCH
    else:
        print("---ROUTE QUESTION TO RAG---")
        return RETRIEVE

# NEW: finalize node to emit clean UI-friendly output
def finalize(state: GraphState) -> Dict[str, Any]:
    docs = state.get("documents", []) or []
    sources = []
    for d in docs:
        try:
            sources.append(getattr(d, "metadata", {}))
        except Exception:
            pass
    return {
        "generation": state.get("generation", ""),
        "doc_count": len(docs),
        "sources": sources,
        "used_web_search": bool(state.get("used_web_search", False)),
        "route": state.get("route", "vector"),
    }

workflow = StateGraph(GraphState)
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node(GENERATE, generate)
workflow.add_node(WEBSEARCH, web_search)
workflow.add_node("finalize", finalize)

workflow.set_conditional_entry_point(
    route_question,
    { WEBSEARCH: WEBSEARCH, RETRIEVE: RETRIEVE },
)

workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    { WEBSEARCH: WEBSEARCH, GENERATE: GENERATE },
)
workflow.add_conditional_edges(
    GENERATE,
    grade_generation_grounded_in_documents_and_question,
    {
        "not supported": GENERATE,  # retry
        "useful": "finalize",
        "not useful": WEBSEARCH,
    },
)
workflow.add_edge(WEBSEARCH, GENERATE)

app = workflow.compile()
