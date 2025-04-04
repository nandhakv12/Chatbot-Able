
from src.helper import pipeline, download_hugging_face_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set Pinecone API key
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Load and split Able.co content from JSON
data_folder = "Data"  # Folder where your PDFs and JSON files are located.
chunked_documents = pipeline(data_folder, max_tokens=40)

# Load HuggingFace embeddings
embeddings = download_hugging_face_embeddings()

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Define Pinecone index name
index_name = "ablechatbot"

# Create index if it doesn't already exist
if index_name not in [index_info.name for index_info in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=768,  # Based on all-MiniLM-L6-v2 or similar
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Embed and upsert documents into Pinecone index
docsearch = PineconeVectorStore.from_documents(
    documents=chunked_documents,
    index_name=index_name,
    embedding=embeddings,
)
