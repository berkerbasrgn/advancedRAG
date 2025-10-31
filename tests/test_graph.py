import types
import pytest

from graph import graph as rg
from graph.node_constants import WEBSEARCH, RETRIEVE, GENERATE


def test_route_question_routes_to_websearch(monkeypatch):
    # Patch question_router.invoke to return an object with datasource == WEBSEARCH
    monkeypatch.setattr(rg, "question_router", types.SimpleNamespace(invoke=lambda input: types.SimpleNamespace(datasource=WEBSEARCH)))
    state = {}
    result = rg.route_question(state)
    assert result == WEBSEARCH


def test_route_question_routes_to_retrieve(monkeypatch):
    # Patch question_router.invoke to return an object with datasource == 'vectorstore'
    monkeypatch.setattr(rg, "question_router", types.SimpleNamespace(invoke=lambda input: types.SimpleNamespace(datasource="vectorstore")))
    state = {}
    result = rg.route_question(state)
    assert result == RETRIEVE


def test_decide_to_generate_prefers_websearch_when_flag_set():
    state = {"web_search": True}
    assert rg.decide_to_generate(state) == WEBSEARCH


def test_decide_to_generate_generates_when_no_web_search():
    state = {"web_search": False}
    assert rg.decide_to_generate(state) == GENERATE


def test_grade_generation_hallucination_false(monkeypatch):
    # If hallucination_grader.invoke returns object with binary_score falsy -> 'not supported'
    monkeypatch.setattr(rg, "hallucination_grader", types.SimpleNamespace(invoke=lambda input: types.SimpleNamespace(binary_score=False)))
    state = {"question": "q", "documents": [], "generation": "g"}
    assert rg.grade_generation_grounded_in_documents_and_question(state) == "not supported"


def test_grade_generation_grounded_and_answer_useful(monkeypatch):
    # hallucination true, answer_grader returns binary_score True -> 'useful'
    monkeypatch.setattr(rg, "hallucination_grader", types.SimpleNamespace(invoke=lambda input: types.SimpleNamespace(binary_score=True)))
    monkeypatch.setattr(rg, "answer_grader", types.SimpleNamespace(invoke=lambda input: types.SimpleNamespace(binary_score=True)))
    state = {"question": "q", "documents": ["d"], "generation": "g"}
    assert rg.grade_generation_grounded_in_documents_and_question(state) == "useful"


def test_grade_generation_grounded_but_not_answering(monkeypatch):
    # hallucination true, answer_grader returns binary_score False -> 'not useful'
    monkeypatch.setattr(rg, "hallucination_grader", types.SimpleNamespace(invoke=lambda input: types.SimpleNamespace(binary_score=True)))
    monkeypatch.setattr(rg, "answer_grader", types.SimpleNamespace(invoke=lambda input: types.SimpleNamespace(binary_score=False)))
    state = {"question": "q", "documents": ["d"], "generation": "g"}
    assert rg.grade_generation_grounded_in_documents_and_question(state) == "not useful"

