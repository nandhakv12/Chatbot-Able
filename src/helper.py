from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
import json
from langchain.schema import Document

def load_and_split_able_documents(
    json_path: str = "Data/able_data.json",
    chunk_size: int = 200,
    chunk_overlap: int = 100
):
    """
    Loads Able.co JSON data, converts to LangChain Documents, and splits into chunks.
    
    Args:
        json_path (str): Path to the JSON file.
        chunk_size (int): Size of each text chunk (in characters).
        chunk_overlap (int): Number of overlapping characters between chunks.

    Returns:
        list: List of LangChain Document chunks.
    """
    # Load the JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert to LangChain Document format
    documents = [
        Document(page_content=entry["text"], metadata={"source": entry["url"]})
        for entry in data
        if "text" in entry and "url" in entry
    ]

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # Split into chunks
    chunks = text_splitter.split_documents(documents)

    print(f"✅ Loaded {len(documents)} documents")
    print(f"✅ Split into {len(chunks)} chunks")
    print("🔹 Preview first chunk:\n", chunks[0])

    return chunks


def download_hugging_face_embeddings():
    embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')
    return embeddings
