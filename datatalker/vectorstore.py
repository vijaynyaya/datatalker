import dspy
from dspy.retrieve.chromadb_rm import ChromadbRM
from chromadb.utils import embedding_functions
from datatalker.config import CHROMADB_DIR


def get_retriever(
    collection_name = "datasets",
    db_path = CHROMADB_DIR,
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
):
    embedder = dspy.Embedder(embedding_fn)
    retriever = ChromadbRM(
        collection_name,
        db_path,
        embedding_function=embedder,
    )
    return retriever
