import dspy
from dspy.retrieve.chromadb_rm import ChromadbRM
# from chromadb.utils import embedding_functions
from datatalker.config import CHROMADB_DIR
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction
)


ollama_ef = OllamaEmbeddingFunction(
    url="http://localhost:11434",
    model_name="bge-m3"
)


def get_retriever(
    collection_name = "datasets_bge-m3",
    db_path = CHROMADB_DIR,
    embedding_fn = ollama_ef
):
    embedder = dspy.Embedder(embedding_fn)
    retriever = ChromadbRM(
        collection_name,
        db_path,
        embedding_function=embedder,
    )
    return retriever
