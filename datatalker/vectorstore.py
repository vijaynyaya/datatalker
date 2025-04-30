import dspy
from dspy.retrieve.chromadb_rm import ChromadbRM
from chromadb.utils import embedding_functions
from pathlib import Path
import os

CHROMADB_DIR = os.environ["CHROMADB_DIR"]

def get_retriever(
    collection_name = "idp_datasets",
    db_path = CHROMADB_DIR,
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
):
    embedder = dspy.Embedder(embedding_fn)
    retriever = ChromadbRM(
        collection_name,
        CHROMADB_DIR,
        embedding_function=embedder,
    )
    return retriever
