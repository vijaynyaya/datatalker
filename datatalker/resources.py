from datatalker.vectorstore import get_retriever
from dspy.retrieve.chromadb_rm import ChromadbRM
import dspy


TOPK_DOCS_TO_RETRIEVE = 7
RETRIEVER = get_retriever(collection_name="datasets_bge-m3")


class RelevanceJudge(dspy.Module):
    def __init__(self):
        signature = dspy.Signature(
            "dataset_description: str, query: str -> is_relevant: bool, how: str",
            "Assess whether the dataset is relevant to the query.",
        )       
        self.judge = dspy.ChainOfThought(signature)
    
    def forward(self, document: str, query: str) -> bool:
        return self.judge(dataset_description=document, query=query)

class ResourceRetriever(dspy.Module):
    def __init__(self, retriever: ChromadbRM, log=print):
        
        self.retriever = retriever
        self.judge_relevance = RelevanceJudge()
        self.log = log

    def forward(self, query: str, k: int = TOPK_DOCS_TO_RETRIEVE):
        docs = self.retriever(query, k=k)
        self.log(f"Found {len(docs)} similar documents for query '{query}'")
        for doc in docs:
            grade = self.judge_relevance(document=doc.long_text, query=query)
            self.log(f"Judged resource '{doc['metadatas']['title']}' as '{'relevant' if grade.is_relevant else 'irrelevant'}'")
            if grade.is_relevant:
                doc["relevance_rationale"] = grade.how
                yield doc


def get_relevant_resources(query: str, k: int = TOPK_DOCS_TO_RETRIEVE, retriever = RETRIEVER, log=print):
    res_retriever = ResourceRetriever(retriever, log=log)
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