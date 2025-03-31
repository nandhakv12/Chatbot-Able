# helper.py
import os
import json
import re
import spacy
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader

# Load spaCy language model once
nlp = spacy.load("en_core_web_sm")

def extract_all_strings(data, path=""):
    """
    Recursively extracts all string values from nested dictionaries/lists in the JSON structure.
    Returns a list of tuples (path, string_value).
    """
    results = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            results.extend(extract_all_strings(value, new_path))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            new_path = f"{path}[{idx}]"
            results.extend(extract_all_strings(item, new_path))
    elif isinstance(data, str):
        results.append((path, data))
    elif isinstance(data, (int, float, bool)):
        results.append((path, str(data)))
    else:
        try:
            string_value = str(data).strip()
            if string_value and "object at 0x" not in string_value:
                results.append((path, string_value))
        except Exception:
            pass
    return results

def clean_text(text):
    """
    Basic cleaning: stripping, collapsing whitespace, and removing URLs, hashtags, mentions,
    and unwanted characters.
    """
    text = text.strip()
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[^A-Za-z0-9\s.,?!\'\"():;%&\-]', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text

boilerplate_phrases = [
    "Let’s build together.",
    "Join our newsletter",
    "Follow us on LinkedIn"
]

def remove_boilerplate(text):
    """Remove known repeated boilerplate phrases."""
    for phrase in boilerplate_phrases:
        text = text.replace(phrase, "")
    return text

def filter_useful_sentences(text, min_words=4):
    """
    Uses spaCy to split the text into sentences and returns those with at least min_words.
    """
    doc = nlp(text)
    useful = [sent.text.strip() for sent in doc.sents if len(sent.text.split()) >= min_words]
    return ' '.join(useful)

def preprocess_scraped_text(raw_text):
    """
    Final text preprocessor pipeline that cleans text, removes boilerplate, and filters sentences.
    """
    cleaned = clean_text(raw_text)
    cleaned = remove_boilerplate(cleaned)
    return filter_useful_sentences(cleaned)

def load_documents_from_directory(data_dir: str) -> list[Document]:
    """
    Loads and preprocesses documents from PDF and JSON files located in `data_dir`.
    For PDFs, it uses the DirectoryLoader from LangChain. For JSONs, it recursively extracts text.
    """
    documents = []
    # Load PDFs
    pdf_loader = DirectoryLoader(data_dir, glob="*.pdf", loader_cls=PyPDFLoader)
    for doc in pdf_loader.load():
        clean_content = preprocess_scraped_text(doc.page_content)
        documents.append(Document(page_content=clean_content, metadata=doc.metadata))
    
    # Load JSON files
    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            json_path = os.path.join(data_dir, filename)
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            extracted = extract_all_strings(json_data)
            for i, (key_path, value) in enumerate(extracted):
                clean_content = preprocess_scraped_text(value)
                documents.append(
                    Document(
                        page_content=clean_content,
                        metadata={"source": filename, "field": key_path}
                    )
                )
    return documents

def spacy_split_documents(documents, max_tokens=300):
    """
    Splits each document into chunks based on sentence boundaries using spaCy,
    ensuring that each chunk has at most `max_tokens` (approximate word count).
    """
    split_docs = []
    for doc in documents:
        cleaned_text = clean_text(doc.page_content)
        cleaned_text = remove_boilerplate(cleaned_text)
        spacy_doc = nlp(cleaned_text)
        current_chunk = ""
        current_tokens = 0
        for sent in spacy_doc.sents:
            sent_text = sent.text.strip()
            sent_tokens = len(sent_text.split())
            if current_tokens + sent_tokens > max_tokens:
                if current_chunk:
                    split_docs.append(Document(page_content=current_chunk.strip(), metadata=doc.metadata))
                current_chunk = sent_text
                current_tokens = sent_tokens
            else:
                current_chunk += " " + sent_text
                current_tokens += sent_tokens
        if current_chunk:
            split_docs.append(Document(page_content=current_chunk.strip(), metadata=doc.metadata))
    return split_docs

def chunk_sentences(sentences, max_tokens=400):
    """
    Chunks a list of sentences into groups where each group has at most `max_tokens` words.
    """
    chunks = []
    current_chunk = ""
    current_length = 0
    for sent in sentences:
        sent_length = len(sent.split())
        if current_length + sent_length <= max_tokens:
            current_chunk += " " + sent
            current_length += sent_length
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent
            current_length = sent_length
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def chunk_documents_using_chunk_sentences(documents, max_tokens=40):
    """
    Processes each document by extracting sentences using spaCy, then chunks the list of sentences
    using the chunk_sentences function. Returns a list of Document objects with chunked text.
    """
    chunked_docs = []
    for doc in documents:
        # Use the already loaded spaCy model to split into sentences
        sentences = [sent.text.strip() for sent in nlp(doc.page_content).sents]
        # Use the chunk_sentences function to further group sentences into chunks
        chunks = chunk_sentences(sentences, max_tokens)
        for chunk in chunks:
            chunked_docs.append(Document(page_content=chunk, metadata=doc.metadata))
    return chunked_docs

def pipeline(data_dir: str, max_tokens: int = 40) -> list[Document]:
    """
    Full pipeline that:
      1. Loads and preprocesses documents (PDFs and JSON files) from the specified data folder.
      2. Splits the loaded documents into chunks using sentence-based chunking.
    
    Args:
        data_dir: Path to the folder containing your data files.
        max_tokens: Maximum number of words per chunk for the chunking process.
    
    Returns:
        A list of Document objects, where each Document represents a text chunk.
    """
    # Load and preprocess documents from the data directory.
    docs = load_documents_from_directory(data_dir)
    # Further split the documents into smaller chunks.
    chunked_docs = chunk_documents_using_chunk_sentences(docs, max_tokens=max_tokens)
    return chunked_docs

from langchain.embeddings import HuggingFaceEmbeddings
#Download the Embeddings from Hugging Face
def download_hugging_face_embeddings():
    embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')
    return embeddings
