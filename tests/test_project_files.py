import os
import importlib


def test_readme_exists():
    assert os.path.isfile("README.md"), "README.md must exist at project root"


def test_requirements_contains_streamlit():
    assert os.path.isfile("requirements.txt"), "requirements.txt must exist"
    with open("requirements.txt", "r", encoding="utf-8") as f:
        req = f.read().lower()
    assert "streamlit" in req, "requirements.txt should include streamlit"


def test_graph_module_has_expected_functions():
    # Import the compiled graph module and check key functions are present
    mod = importlib.import_module("graph.graph")
    for name in ("route_question", "decide_to_generate", "grade_generation_grounded_in_documents_and_question"):
        assert hasattr(mod, name), f"graph.graph should define {name}"

