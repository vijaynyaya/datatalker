from datatalker.vectorstore import get_retriever
from dspy.retrieve.chromadb_rm import ChromadbRM
import dspy

TOPK_DOCS_TO_RETRIEVE = 20
RETRIEVER = get_retriever()

class DatasetGrader(dspy.Module):
    def __init__(self):
        signature = dspy.Signature(
            "dataset_description: str, query: str -> is_relevant: bool, how: str",
            "Assess whether the dataset is relevant to the query, and covers the intended geography and time period",
        )       
        self.grader = dspy.ChainOfThought(signature)
    
    def forward(self, doc: str, query: str) -> bool:
        return self.grader(dataset_description=doc, query=query)

class ResourceRetriever(dspy.Module):
    def __init__(self, retriever: ChromadbRM):
        self.retriever = retriever
        self.grader = DatasetGrader()

    def forward(self, query: str, k: int = TOPK_DOCS_TO_RETRIEVE):
        docs = self.retriever(query, k=k)
        print(f"Found {len(docs)} similar documents in the vectorstore")
        for doc in docs:
            with dspy.context(lm=dspy.LM("ollama_chat/llama3.2", api_base="http://localhost:11434")):
                grade = self.grader(doc.long_text, query)
                print(f"IsRelevant({grade.is_relevant}) {doc['metadatas']['title']}")
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


def rework_idp_resource_doc(doc):
    meta = doc["metadatas"]
    resource_page = (
        "https://dev.indiadataportal.com"
        f"/p/{meta['package_title']}"
        f"/r/{meta['sku']}"
    )
    # TODO: add datastore info such as record count
    return {
        "id": meta["id"],
        # "resource_sku": meta["sku"],
        "title": meta["name"],
        "long_text": doc["long_text"],
        "relevance_rationale": doc["relevance_rationale"],
        "webpage": resource_page, 
        # "download_url": meta["url"],
    }

def adapt_ogdp_catalog_doc(catalog_doc):
    return {
        "interface": "ogd:catalog",
        "webpage": catalog_doc["metadatas"]["website"],
        "title": catalog_doc["metadatas"]["title"],
        "long_text": catalog_doc["long_text"],
        "id": catalog_doc["metadatas"]["uuid"],
        "relevance_rationale": catalog_doc["relevance_rationale"] 
    }


def resource_view(resource_doc):
    r = resource_doc
    return f"""##### [{r['title']}]({r['webpage']})
{r['relevance_rationale']}
"""