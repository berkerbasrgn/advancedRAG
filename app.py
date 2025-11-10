"""
Advanced Streamlit interface for Corrective RAG.
Improved version with proper environment variable loading.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from {env_path.absolute()}")
else:
    parent_env = Path('..') / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)
        print(f"✓ Loaded .env from {parent_env.absolute()}")
    else:
        print("⚠ No .env file found")
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

os.environ.setdefault("USER_AGENT", "corrective-rag/1.0")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import streamlit as st
from PIL import Image


st.set_page_config(
    page_title="Advanced RAG Dashboard",
    page_icon="🔄",
    layout="wide",
)

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")


if not OPENAI_KEY:
    st.sidebar.error("⚠️ OPENAI_API_KEY not found. Add it to your .env.")
    st.error("Cannot proceed without OPENAI_API_KEY. Please add it to your .env file.")
    st.stop()
else:
    st.sidebar.success("✅ OpenAI API key loaded")

if TAVILY_KEY:
    st.sidebar.success("✅ Tavily web search enabled")
else:
    st.sidebar.info("ℹ️ Tavily not configured — web search disabled")

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "vectorstore_loaded" not in st.session_state:
        st.session_state.vectorstore_loaded = False


def load_vectorstore():
    """Load or create the vectorstore."""
    if not st.session_state.vectorstore_loaded:
        try:
            from ingestion import get_or_create_vectorstore
            with st.spinner("Loading vectorstore..."):
                get_or_create_vectorstore()
                st.session_state.vectorstore_loaded = True
                st.sidebar.success("✅ Vectorstore loaded")
        except Exception as e:
            st.error(f"❌ Failed to load vectorstore: {e}")
            st.exception(e)


def query_page():
    """Query system page."""
    st.markdown('<div class="main-header">🔍 Query System</div>', unsafe_allow_html=True)

    load_vectorstore()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if question := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    from graph.graph import app

                    response = app.invoke({"question": question})

                    answer = ""
                    used_web = False
                    doc_count = 0
                    sources = []

                    if isinstance(response, dict):
                        answer = response.get("generation") or ""
                        used_web = bool(response.get("used_web_search", False))
                        docs = response.get("documents", [])
                        doc_count = len(docs)
                        try:
                            sources = [getattr(d, "metadata", {}) for d in docs]
                        except Exception:
                            sources = []
                    else:
                        answer = str(response)

                    st.markdown(answer or "_No answer generated._")

                    with st.expander("📊 View Details"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Documents Used", doc_count)
                        with col2:
                            st.metric("Web Search", "Yes" if used_web else "No")

                    tab1, tab2 = st.tabs(["Raw Response", "Sources"])
                    with tab1:
                        try:
                            st.json(response if isinstance(response, dict) else {"raw": str(response)})
                        except Exception:
                            st.write(response)
                    with tab2:
                        if sources:
                            st.json(sources)
                        else:
                            st.write("No source metadata available.")


                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)

                    if "OPENAI_API_KEY" in str(e) or "api_key" in str(e).lower():
                        st.info("💡 API key issue. Check your .env file has OPENAI_API_KEY set correctly.")

                    with st.expander("🔍 Full Error Details"):
                        st.exception(e)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


def ingestion_page():
    """Document ingestion page."""
    st.markdown('<div class="main-header">📚 Document Ingestion</div>', unsafe_allow_html=True)

    st.info("""
    Upload documents to add them to the vectorstore. Supported formats:
    - Text files (.txt)
    - PDF files (.pdf)
    - Word documents (.doc, .docx)
    """)

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        type=['txt', 'pdf', 'doc', 'docx']
    )

    if uploaded_files:
        st.write(f"📁 Selected {len(uploaded_files)} file(s):")
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.size / 1024:.1f} KB)")

        if st.button("🚀 Process Documents", type="primary"):
            with st.spinner('Processing documents...'):
                try:
                    temp_dir = Path("temp_uploads")
                    temp_dir.mkdir(exist_ok=True)

                    temp_paths = []
                    for file in uploaded_files:
                        temp_path = temp_dir / file.name
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                        temp_paths.append(str(temp_path))

                    from ingestion import process_documents
                    process_documents(temp_paths)

                    for path in temp_paths:
                        try:
                            Path(path).unlink()
                        except Exception:
                            pass
                    try:
                        temp_dir.rmdir()
                    except:
                        pass

                    st.success("✅ Documents processed successfully!")
                    st.balloons()

                    st.session_state.vectorstore_loaded = False

                except Exception as e:
                    st.error(f"❌ Error processing documents: {str(e)}")
                    with st.expander("🔍 Full Error Details"):
                        st.exception(e)


def system_info_page():
    """System information page."""
    st.markdown('<div class="main-header">ℹ️ System Information</div>', unsafe_allow_html=True)

    st.subheader("🏗️ System Architecture")
    st.write("""
    This Corrective RAG system implements a sophisticated pipeline with:
    
    - **🎯 Smart Query Routing**: Automatically routes queries to vectorstore or web search
    - **📄 Document Grading**: Filters relevant documents before generation
    - **✅ Hallucination Detection**: Validates that answers are grounded in facts
    - **🔍 Answer Validation**: Ensures answers actually address the question
    - **🔄 Self-Correction**: Automatically retries or searches web if quality is insufficient
    """)

    st.subheader("📊 Workflow Diagram")

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("🎨 Generate Diagram", type="primary"):
            with st.spinner("Rendering workflow diagram..."):
                try:
                    from graph.graph import app

                    graph = app.get_graph()
                    graph.draw_mermaid_png(output_file_path="graph.png")

                    st.success("✅ Diagram generated!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Failed to generate diagram: {str(e)}")
                    with st.expander("🔍 Full Error"):
                        st.exception(e)

    with col2:
        if Path("graph.png").exists():
            try:
                try:
                    st.image("graph.png", caption="RAG System Workflow", use_container_width=True)
                except TypeError:
                    st.image("graph.png", caption="RAG System Workflow", use_column_width=True)
            except Exception as e:
                st.error(f"Failed to load diagram: {e}")
        else:
            st.info("💡 Click 'Generate Diagram' to visualize the workflow")

    st.subheader("⚙️ Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**API Keys Status**")
        st.write(f"OpenAI: {'✅' if OPENAI_KEY else '❌'}")
        st.write(f"Tavily: {'✅' if TAVILY_KEY else '❌'}")


    with col2:
        st.write("**System Status**")
        st.write(f"Vectorstore: {'✅ Loaded' if st.session_state.vectorstore_loaded else '⏳ Not loaded'}")
        st.write(f"Messages: {len(st.session_state.messages)}")
        st.write(f"Python: {sys.version.split()[0]}")

    with st.expander("🔍 Environment Variables"):
        env_vars = {
            "OPENAI_API_KEY": "✅ Set" if OPENAI_KEY else "❌ Missing",
            "TAVILY_API_KEY": "✅ Set" if TAVILY_KEY else "❌ Missing",
            "USER_AGENT": os.getenv("USER_AGENT", "Not set"),
            "Working Directory": os.getcwd(),
        }
        for key, value in env_vars.items():
            st.write(f"**{key}**: {value}")


def main():
    """Main application."""
    initialize_session_state()

    with st.sidebar:
        st.title("🔄 Corrective RAG")
        st.markdown("---")

        page = st.radio(
            "Navigate to:",
            ["🔍 Query System", "📚 Document Ingestion", "ℹ️ System Info"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        st.subheader("Actions")

        if st.button("🔄 Reload Vectorstore", use_container_width=True):
            with st.spinner("Reloading..."):
                try:
                    from ingestion import get_or_create_vectorstore
                    get_or_create_vectorstore(force_reload=True)
                    st.session_state.vectorstore_loaded = True
                    st.success("✅ Reloaded!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")

        with st.expander("ℹ️ About"):
            st.markdown("""
            **Corrective RAG v1.0**
            
            A self-correcting Retrieval Augmented Generation system
            with built-in validation and quality control.
            
            - Smart routing
            - Hallucination detection
            - Answer validation
            - Auto-correction
            """)

        st.caption("v1.0.0 | Made with ❤️")

    if page == "🔍 Query System":
        query_page()
    elif page == "📚 Document Ingestion":
        ingestion_page()
    elif page == "ℹ️ System Info":
        system_info_page()


if __name__ == "__main__":
    main()