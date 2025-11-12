# pinecone_init.py

import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")  # us-east-1 for you
INDEX_NAME = "research-memory"

pc = None  # global pinecone client


def init_pinecone():
    global pc
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is missing")

    pc = Pinecone(api_key=PINECONE_API_KEY)
    print(" Pinecone client created successfully.")

    return pc


def ensure_index(index_name: str, dimension: int):
    """
    For the new Pinecone Serverless, we must create index manually with:
    - cloud
    - region
    - dimension
    """

    global pc
    if pc is None:
        raise ValueError("Pinecone client not initialized")

    existing = pc.list_indexes().names()

    if index_name in existing:
        print(f"Index '{index_name}' already exists.")
        return

    # Create new index
    print(f"Creating index: {index_name}")

    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENV  # your region = us-east-1
        )
    )

    print(" Index created successfully.")
