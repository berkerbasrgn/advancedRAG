"""
Document ingestion and vectorstore setup.

This module handles loading documents, creating embeddings,
and setting up the vectorstore for retrieval.
"""

from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

# Default URLs to load (customize for your use case)
DEFAULT_URLS = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]


def load_and_split_documents(
    urls: Optional[List[str]] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Document]:
    """
    Load documents from URLs and split them into chunks.

    Args:
        urls: List of URLs to load documents from
        chunk_size: Size of each text chunk
        chunk_overlap: Overlap between chunks

    Returns:
        List of split document chunks
    """
    if urls is None:
        urls = DEFAULT_URLS

    print(f"Loading documents from {len(urls)} URLs...")

    # Load documents
    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    doc_splits = text_splitter.split_documents(docs_list)

    print(f"Split into {len(doc_splits)} chunks")
    return doc_splits


def create_vectorstore(
    documents: List[Document],
    collection_name: str = "rag-chroma",
    persist_directory: Optional[str] = "./chroma_db",
) -> Chroma:
    """
    Create a vectorstore from documents.

    Args:
        documents: List of documents to add to vectorstore
        collection_name: Name of the collection
        persist_directory: Directory to persist the vectorstore

    Returns:
        Chroma vectorstore instance
    """
    print("Creating vectorstore...")

    # Create embeddings
    embeddings = OpenAIEmbeddings()

    # Create vectorstore
    vectorstore = Chroma.from_documents(
        documents=documents,
        collection_name=collection_name,
        embedding=embeddings,
        persist_directory=persist_directory,
    )

    print(f"Vectorstore created with {len(documents)} documents")
    return vectorstore


def get_or_create_vectorstore(
    force_reload: bool = False,
    urls: Optional[List[str]] = None,
) -> Chroma:
    """
    Get existing vectorstore or create a new one.

    Args:
        force_reload: Force reload documents even if vectorstore exists
        urls: URLs to load documents from if creating new vectorstore

    Returns:
        Chroma vectorstore instance
    """
    persist_directory = "./chroma_db"

    if not force_reload:
        try:
            # Try to load existing vectorstore
            print("Attempting to load existing vectorstore...")
            vectorstore = Chroma(
                collection_name="rag-chroma",
                embedding_function=OpenAIEmbeddings(),
                persist_directory=persist_directory,
            )
            print("Loaded existing vectorstore")
            return vectorstore
        except Exception as e:
            print(f"Could not load existing vectorstore: {e}")

    # Create new vectorstore
    print("Creating new vectorstore...")
    documents = load_and_split_documents(urls)
    vectorstore = create_vectorstore(documents)
    return vectorstore


def process_documents(file_paths: List[str]) -> None:
    """
    Process uploaded documents and add them to vectorstore.

    Args:
        file_paths: List of file paths to process
    """
    from langchain_community.document_loaders import (
        TextLoader,
        PyPDFLoader,
        Docx2txtLoader,
    )

    print(f"Processing {len(file_paths)} documents...")

    all_docs = []
    for file_path in file_paths:
        try:
            # Determine loader based on file extension
            if file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            elif file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(('.doc', '.docx')):
                loader = Docx2txtLoader(file_path)
            else:
                print(f"Skipping unsupported file: {file_path}")
                continue

            # Load documents
            docs = loader.load()
            all_docs.extend(docs)
            print(f"Loaded {len(docs)} documents from {file_path}")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    if not all_docs:
        print("No documents were loaded")
        return

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(all_docs)

    print(f"Split into {len(doc_splits)} chunks")

    # Add to existing vectorstore
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        collection_name="rag-chroma",
        embedding_function=embeddings,
        persist_directory="./chroma_db",
    )

    # Add documents
    vectorstore.add_documents(doc_splits)
    print(f"Added {len(doc_splits)} chunks to vectorstore")


import os
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "false")  # silence Chroma telemetry

from typing import Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# --- lazy singletons ---
_vectorstore: Optional[Chroma] = None
_retriever = None

def _healthcheck(vs: Chroma) -> None:
    """Touch the index to ensure it's usable; don’t crash the app if not."""
    try:
        _ = vs.similarity_search("healthcheck", k=1)
    except Exception as e:
        print(f"[ingestion] Vectorstore healthcheck failed: {e}")

def get_vectorstore(force_reload: bool = False, urls: Optional[list[str]] = None) -> Chroma:
    global _vectorstore
    persist_directory = "./chroma_db"

    if _vectorstore is not None and not force_reload:
        return _vectorstore

    if not force_reload:
        try:
            print("Attempting to load existing vectorstore...")
            _vectorstore = Chroma(
                collection_name="rag-chroma",
                embedding_function=OpenAIEmbeddings(),
                persist_directory=persist_directory,
            )
            _healthcheck(_vectorstore)
            print("Loaded existing vectorstore")
            return _vectorstore
        except Exception as e:
            print(f"Could not load existing vectorstore: {e}")

    print("Creating new vectorstore...")
    documents = load_and_split_documents(urls)
    _vectorstore = create_vectorstore(
        documents,
        collection_name="rag-chroma",
        persist_directory=persist_directory,
    )
    _healthcheck(_vectorstore)
    return _vectorstore

def get_retriever():
    """Lazily create and cache the retriever."""
    global _retriever
    if _retriever is None:
        vs = get_vectorstore()
        _retriever = vs.as_retriever(search_kwargs={"k": 4})
    return _retriever
