from datatalker.vectorstore import get_retriever
from dspy.retrieve.chromadb_rm import ChromadbRM
from datatalker.types import (
    Message,
    Thought,
    MessageRole,
    ResponseType,
    Resource,
    SystemLog
)
from datatalker.renderer import ResourceRenderer
from datatalker.context import get_context
import dspy


TOPK_DOCS_TO_RETRIEVE = 7
RETRIEVER = get_retriever(collection_name="datasets_bge-m3")


class JudgeDatasetRelevance(dspy.Signature):
    """Assess whether the provided dataset is relevant to the user query"""

    dataset_description: str = dspy.InputField(
        desc="textual description of the resource"
    )
    query: str = dspy.InputField(desc="search query")
    is_relevant: bool = dspy.OutputField(desc="Whether the dataset is relevant?")
    how: str = dspy.OutputField(desc="How the dataset is relevant?")


class RelevanceJudge(dspy.Module):
    def __init__(self):
        self.judge = dspy.ChainOfThought(JudgeDatasetRelevance)

    def forward(self, document: str, query: str) -> bool:
        return self.judge(dataset_description=document, query=query)


class ResourceRetriever(dspy.Module):
    def __init__(self, retriever: ChromadbRM):
        self.retriever = retriever
        self.judge_relevance = RelevanceJudge()

    def forward(self, query: str, k: int = TOPK_DOCS_TO_RETRIEVE):
        docs = self.retriever(query, k=k)

        yield Thought(f"Found {len(docs)} similar documents for query '{query}'")

        for doc in docs:
            grade = self.judge_relevance(document=doc.long_text, query=query)
            yield Thought(
                f"Judged resource '{doc['metadatas']['title']}' as '{'relevant' if grade.is_relevant else 'irrelevant'}'"
            )
            if grade.is_relevant:
                doc["relevance_rationale"] = grade.how
                yield Message(
                    role=MessageRole.SYSTEM, type=ResponseType.OBJECT, content=doc
                )


class ContextualSearchQuery(dspy.Signature):
    """Construct a query to search a vector database for retrieving relevant resources"""

    history: list[str] = dspy.InputField(desc="ordered list of messages from the user")
    user_message: str = dspy.InputField(desc="current message from the user")
    search_query: str = dspy.OutputField(desc="query to search the vectorstore")


def get_relevant_resources(
    query: str, k: int = TOPK_DOCS_TO_RETRIEVE, retriever=RETRIEVER
):
    res_retriever = ResourceRetriever(retriever)
    docs = res_retriever(query, k=k)
    return docs


def adapt_ogdp_catalog_doc(catalog_doc) -> Resource:
    return {
        "interface": "ogd:catalog",
        "webpage": catalog_doc["metadatas"]["website"],
        "title": catalog_doc["metadatas"]["title"],
        "long_text": catalog_doc["long_text"],
        "id": catalog_doc["metadatas"]["uuid"],
        "relevance_rationale": catalog_doc["relevance_rationale"],
    }

def resource_handler():
    ctx = get_context()
    usr_msg_history = [
        msg.content
        for msg in ctx.history
        if msg.role == MessageRole.USER
    ]
    msg = ctx.user_message.content

    query_formulator = dspy.ChainOfThought(ContextualSearchQuery)
    prediction = query_formulator(history=usr_msg_history, user_message=msg)
    yield Thought(prediction.reasoning)
    search_query = prediction.search_query
    
    rsrcs = get_relevant_resources(search_query)

    doc = next(rsrcs, None)
    if doc is None:
        yield SystemLog(f"No relevant resources found for query '{search_query}'")
        yield Message(MessageRole.ASSISTANT, "Couldn't find any datasets relevant to your query.")
    
    while doc is not None:
        ctx.resources[doc["id"]] = doc
        prediction = ResourceRenderer(doc)
        yield Message(MessageRole.ASSISTANT, prediction.markdown)

