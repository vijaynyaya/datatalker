from datatalker.vectorstore import get_retriever
from dspy.retrieve.chromadb_rm import ChromadbRM
import dspy
import streamlit as st

TOPK_DOCS_TO_RETRIEVE = 7
RETRIEVER = get_retriever()

class DatasetGrader(dspy.Module):
    def __init__(self):
        signature = dspy.Signature(
            "dataset_description: str, query: str -> is_relevant: bool, how: str",
            "Assess whether the dataset is relevant to the query",
        )       
        self.grader = dspy.ChainOfThought(signature)
    
    def forward(self, doc: str, query: str) -> bool:
        return self.grader(dataset_description=doc, query=query)

class ResourceRetriever(dspy.Module):
    def __init__(self, retriever: ChromadbRM):
        self.retriever = retriever
        self.grader = DatasetGrader()

    def forward(self, query: str, k: int = TOPK_DOCS_TO_RETRIEVE):
        docs = self.retriever(query, k=k, where={"source_type": {"$eq": "resource"}})
        print(f"Found {len(docs)} similar documents in the vectorstore")
        for doc in docs:
            grade = self.grader(doc.long_text, query)
            print(f"IsRelevant({grade.is_relevant}) {doc['metadatas']['name']}")
            if grade.is_relevant:
                doc["relevance_rationale"] = grade.how
                yield doc

def get_relevant_resources(query: str, k: int = TOPK_DOCS_TO_RETRIEVE):
    """
    Retrieve relevant resources based on the query.
    
    Args:
        query: The search query string
        k: Number of top documents to retrieve
    
    Returns:
        List of relevant resources
    """
    res_retriever = ResourceRetriever(RETRIEVER)
    docs = res_retriever(query, k=k)
    return docs


def rework_resource_doc(doc):
    meta = doc["metadatas"]
    resource_page = (
        "https://dev.indiadataportal.com"
        f"/p/{meta['package_title']}"
        f"/r/{meta['sku']}"
    )
    # TODO: add datastore info such as record count
    return {
        "resource_id": meta["id"],
        "resource_sku": meta["sku"],
        "resource_name": meta["name"],
        "resource_description": doc["long_text"],
        "relevance_rationale": doc["relevance_rationale"],
        "resource_page": resource_page, 
        "download_url": meta["url"],
    }

def resource_view(resource_doc):
    r = resource_doc
    title = f"<a href='{r['resource_page']}'>{r['resource_name']}</a>"
    return f"""##### {title}
{r['relevance_rationale']}
"""