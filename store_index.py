from src.helper import load_and_split_able_documents, download_hugging_face_embeddings
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
text_chunks = load_and_split_able_documents(
    json_path="Data/able_data.json",
    chunk_size=300,
    chunk_overlap=100
)

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
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings,
)
