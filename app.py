import streamlit as st
from ingestion import process_documents
import os
from PIL import Image

st.set_page_config(page_title="Advanced RAG Dashboard", layout="wide")

# Warn if critical environment variables are missing
OPENAI_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
if not OPENAI_KEY:
    st.sidebar.warning(
        "OPENAI_API_KEY not set. Set it in your environment or in a .env file for the RAG system to work (embeddings & LLM)."
    )

st.title("Advanced RAG System Dashboard")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Query System", "Document Ingestion", "System Info"])

if page == "Query System":
    st.header("Query the RAG System")

    # Input for user query
    user_query = st.text_input("Enter your question:")

    if st.button("Submit Query"):
        if user_query:
            with st.spinner('Processing your query...'):
                try:
                    # Lazy import of the compiled workflow app to avoid heavy startup at import time
                    from main import app
                except Exception as e:
                    st.error("Failed to load the workflow app. See details below.")
                    st.exception(e)
                else:
                    try:
                        response = app.invoke(input={"question": user_query})

                        # Try to convert to JSON-serializable form
                        def normalize(obj):
                            if hasattr(obj, "to_dict"):
                                try:
                                    return obj.to_dict()
                                except Exception:
                                    pass
                            if isinstance(obj, dict):
                                return obj
                            if hasattr(obj, "__dict__"):
                                try:
                                    return {k: normalize(v) for k, v in obj.__dict__.items()}
                                except Exception:
                                    pass
                            if isinstance(obj, (list, tuple)):
                                return [normalize(x) for x in obj]
                            return str(obj)

                        normalized = normalize(response)

                        st.subheader("Raw Response")
                        try:
                            st.json(normalized)
                        except Exception:
                            st.write(normalized)

                        if isinstance(normalized, dict):
                            for key in ("generation", "answer", "output", "value", "result"):
                                if key in normalized:
                                    st.subheader(f"{key.capitalize()}")
                                    st.write(normalized[key])

                    except Exception as e:
                        if "OPENAI_API_KEY" in str(e) or "openai" in str(e).lower():
                            st.error("LLM or embeddings call failed. Check that OPENAI_API_KEY is set and valid.")
                        else:
                            st.error("An error occurred while invoking the workflow. See details below.")
                        st.exception(e)
        else:
            st.warning("Please enter a query first.")

elif page == "Document Ingestion":
    st.header("Document Ingestion")

    # File uploader
    uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True, type=['txt', 'pdf', 'doc', 'docx'])

    if uploaded_files:
        if st.button("Process Documents"):
            with st.spinner('Processing documents...'):
                try:
                    # Save uploaded files temporarily and process them
                    temp_paths = []
                    for file in uploaded_files:
                        temp_path = os.path.join(".", f"temp_{file.name}")
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                            temp_paths.append(temp_path)

                    # Process the documents
                    process_documents(temp_paths)

                    # Clean up temporary files
                    for path in temp_paths:
                        try:
                            os.remove(path)
                        except Exception:
                            pass

                    st.success("Documents processed successfully!")
                except Exception as e:
                    st.error(f"An error occurred during document processing: {str(e)}")

elif page == "System Info":
    st.header("System Information")

    st.subheader("Workflow Diagram")
    if st.button("Render Workflow Diagram"):
        try:
            from main import app
        except Exception as e:
            st.error("Failed to load the workflow app to render the diagram.")
            st.exception(e)
        else:
            try:
                graph = None
                try:
                    graph = app.get_graph()
                except Exception:
                    graph = None

                if graph is not None and hasattr(graph, "draw_mermaid_png"):
                    try:
                        graph.draw_mermaid_png(output_file_path="graph.png")
                        st.success("Rendered graph to graph.png")
                    except Exception as e:
                        st.warning(f"Failed to draw graph image: {e}")
                else:
                    st.info("Graph drawing not available on this app object.")
            except Exception as e:
                st.error("Failed while attempting to render the graph.")
                st.exception(e)

    # Display workflow diagram if available
    try:
        image = Image.open('graph.png')
        st.image(image, caption='RAG System Workflow', use_column_width=True)
    except Exception:
        st.info("Workflow diagram not available. Click 'Render Workflow Diagram' to attempt to generate it.")

    # Display system architecture information
    st.subheader("System Architecture")
    st.write("""
    This Advanced RAG system implements a sophisticated retrieval-augmented generation pipeline with:
    - Multi-step retrieval process
    - Answer generation with fact-checking
    - Multiple grading components for quality control
    - Dynamic routing based on query type
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Advanced RAG System v1.0")
