from typing import TypedDict, Union, Literal

class ResourceMetadata(TypedDict):
    source_type: Literal["resource"]
    id: str
    name: str
    package_name: str
    package_title: str
    sku: str
    url: str

class DatastoreMetadata(TypedDict):
    source_type: Literal["datastore"]
    id: str
    record_count: int

class PackageMetadata(TypedDict):
    source_type: Literal["package"]
    id: str
    name: str
    title: str

DocumentMetadata = Union[ResourceMetadata, DatastoreMetadata, PackageMetadata]

class RetrievedDocument(TypedDict):
    id: str
    long_text: str
    metadatas: DocumentMetadata
    score: float 
    relevance_rationale: str