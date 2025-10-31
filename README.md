# Advanced RAG — Dashboard and Workflow

A local Retrieval-Augmented Generation (RAG) pipeline with a Streamlit dashboard for interacting with the compiled graph workflow, ingesting documents, and visualizing the workflow graph.

This repository contains a LangGraph-based workflow that performs retrieval, grading, generation and optional web search, plus a lightweight web UI for exploring and interacting with the system.

## Features

- Compiled graph workflow (graph/graph.py) implementing routing, retrieval, grading and generation.
- Streamlit dashboard (`app.py`) with:
  - Query System: submit questions to the compiled workflow
  - Document Ingestion: upload local files (txt / pdf / docx) and index them into Chroma
  - System Info: render and view the workflow diagram (graph.png)
- Ingestion helper (`ingestion.py`) that:
  - Seeds a Chroma collection from a set of web articles
  - Provides `process_documents(file_paths: list[str])` to index local files

## Requirements

- Python 3.10+ (this project used Python 3.12)
- A Python virtual environment is recommended
- System dependency for Graphviz if you wish to render PNGs from the workflow graph (e.g. `brew install graphviz` on macOS)

## Python dependencies

All Python dependencies are listed in `requirements.txt`. Install with:

```bash
pip install -r requirements.txt
```

(If you add or update dependencies, re-run the above command in your virtualenv.)

## Configuration

The RAG system requires API credentials for the LLM and embeddings provider. By default it expects an OpenAI API key in the environment.

- Set the environment variable `OPENAI_API_KEY` (or `OPENAI_KEY`) before running the app, or place it in a `.env` file at the project root.

Example (macOS / Linux):

```bash
export OPENAI_API_KEY="sk-..."
```

## Running the dashboard

1. Activate your virtualenv where `requirements.txt` has been installed.
2. Start the Streamlit dashboard:

   ```bash
   streamlit run app.py
   ```

3. Open the URL Streamlit prints (usually http://localhost:8501).

Dashboard pages:
- Query System — type a question and click Submit. The dashboard will lazy-import the compiled `app` from `main.py` and call `app.invoke(input={"question": ...})`.
- Document Ingestion — upload txt, pdf, doc, docx files and click `Process Documents` to index them into the Chroma collection used by the workflow.
- System Info — click `Render Workflow Diagram` to try to create `graph.png` from the compiled graph, then view it in the page.

## Ingestion notes

- The repository seeds the Chroma collection from a small set of web pages defined in `ingestion.py`.
- The `process_documents` helper (in `ingestion.py`) supports local `txt`, `pdf`, and `docx` files and will split and add chunks to the Chroma collection.
- PDF extraction uses `pypdf`. DOCX extraction uses `python-docx`.
- The Chroma collection persists to `./.chroma`.

## Workflow graph

- The graph is defined and compiled inside `graph/graph.py` as a `StateGraph`. The compiled object is exposed as `app`.
- Graph rendering is optional and may require system Graphviz binaries. If `graph.draw_mermaid_png` is available it will be used to write `graph.png`.

## Troubleshooting

- Missing OpenAI key: the Streamlit UI will warn if `OPENAI_API_KEY` is not found. LLM/embeddings calls will fail without a valid key.
- Graph rendering fails: install Graphviz system package (not just the Python binding) and retry (macOS: `brew install graphviz`).
- PDF/DOCX parsing issues: ensure `pypdf` and `python-docx` are installed (they are listed in `requirements.txt`). Some PDFs may not produce perfect text extraction.
- If ingestion does not appear to update the retriever results, confirm that the Chroma collection was persisted to `./.chroma` and the app is using the same persist directory.

## Project layout (high level)

- app.py — Streamlit dashboard and UI
- ingestion.py — seeding and `process_documents` helper for indexing local files
- main.py — small entrypoint that loads the compiled graph (`app`) from `graph/graph.py`
- graph/ — LangGraph workflow and node/chain implementations
  - graph/graph.py — builds and compiles the workflow
  - graph/nodes/ — node implementations (retrieve, generate, grade...)
  - graph/chains/ — chain implementations used by nodes
- graph.png — optional workflow image

## Development notes

- The Streamlit UI lazy-imports the compiled `app` to avoid heavy startup at import time. When developing the graph you can run `python -m graph.graph` or open `main.py` to exercise the workflow programmatically.
- When changing dependencies, update `requirements.txt` and reinstall.

## Next steps / improvements

- Show retrieved documents and source metadata alongside the generated answer in the dashboard.
- Add a query history panel and per-step state visualization while the workflow runs.
- Add authentication and remote deployment support (FastAPI + React or Streamlit Cloud).

## License & Contributing

Feel free to open issues or submit PRs. No license file included — add one if you plan to open-source this project publicly.

---

If you want, I can also:
- Add a richer response view in the dashboard (show retrieved chunks + sources).
- Add a query history and export tool.

Tell me which enhancement to implement next.

**.env Contents**

OPENAI_API_KEY=

LANGCHAIN_API_KEY=

LANGCHAIN_TRACING_V2=

LANGCHAIN_PROJECT=

TAVILY_API_KEY=

PYTHONPATH=
