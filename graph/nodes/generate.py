from __future__ import annotations
from typing import Any, Dict, List

from graph.state import GraphState

try:
    from graph.chains.generation import generation_chain
except Exception as e:
    print("[generate] Falling back to local generation chain due to import error:", e)
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        _llm = ChatOpenAI(temperature=0)
        _prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant. Use ONLY the context to answer.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "If the answer is not in the context, say you don't know."
        )
        generation_chain = _prompt | _llm | StrOutputParser()
    except Exception as ee:
        print("[generate] Could not build fallback chain:", ee)
        generation_chain = None

def generate(state: GraphState) -> Dict[str, Any]:
    print("---GENERATE---")
    q = state["question"]
    docs = state.get("documents", []) or []

    context_text = "\n\n".join([getattr(d, "page_content", str(d)) for d in docs])

    if generation_chain is None:
        return {
            "question": q,
            "documents": docs,
            "generation": "Generation chain is not available (import/build error).",
            "web_search": state.get("web_search", False),
            "used_web_search": state.get("used_web_search", False),
            "route": state.get("route", "vector"),
        }

    generation = generation_chain.invoke({"context": context_text, "question": q})

    return {
        "question": q,
        "documents": docs,
        "generation": generation,
        "web_search": state.get("web_search", False),
        "used_web_search": state.get("used_web_search", False),
        "route": state.get("route", "vector"),
    }
