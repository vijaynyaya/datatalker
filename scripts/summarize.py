from pymongo import MongoClient
import dspy
from tqdm import tqdm
from multiprocessing import Pool
import traceback

client = MongoClient("mongodb://localhost:27017/")

db = client["datatalker"]
rsrcs = db["ogd_resources"]

lm = dspy.LM(model="ollama_chat/gemma3", api_base="http://localhost:11434")
dspy.configure(lm=lm)

RESOURCE_NOTES = """
Your job is to write a professional long descripton of the Resource using the following notes on its schema. Highlight it's content, spatio-temporal span, variables, data collection methodology or body, and potential use cases.

#### Resrouce Schema Notes
##### Schema Note 1: Boolean values respresented as 0 and 1
The following fields represent boolean values using '0' or '1':
- active — whether the resource is currently active.
- visualizable — whether the resource supports visualization (charts, graphs, etc.).
- external_ws — indicates whether the data is fetched from an external web service.

##### Schema Note 2: Link to Catalogs
- catalog_uuid — a reference to the parent catalog this resource belongs to. Use this to group or trace resources back to their catalog definition.

##### Schema Note 3: Metadata for temporal tracking
Several fields provide timestamps and date information:
- created, updated — Unix timestamps indicating creation and last modification time.
- created_date, updated_date — ISO 8601 formatted timestamps for the same.
- timestamp, data_fetch_date — may be used to track dataset ingestion or updates (usage context dependent).

##### Schema Note 4: Schema description of the resource
These fields help describe and identify the resource meaningfully:
- title — title of the resource.
- desc — short description or summary of the resource.
- sector — high-level thematic categories (e.g., "Agriculture").
- source — origin platform or system (e.g., "data.gov.in").

##### Schema Note 5: Organizational context
These fields indicate the governing or contributing organizations:
- org — hierarchical list of government organizations involved in the dataset.
- org_type — identifies if the organization is Central or State.

##### Schema Note 6: Field-level metadata
These fields define the schema of the actual data:
- field — list of fields present in the resource, each with name, id, and type (e.g., keyword, date).
- field_exposed — fields that are exposed via the public API/UI. May include extra metadata such as mandatory, format.
- field_dependent — defines hierarchical relationships (e.g., State → District).
- order — default sort order of fields for displaying or querying data.
- primary_field — may designate the main identifier or dimension (if present).

##### Schema Note 7: Internal indexing and linking
These fields are primarily used for system indexing, Elasticsearch compatibility, or internal routing and should not be part of user-facing content:
- _id, resource_uuid, index_name
- target_bucket — includes host, index, type, and internal field mappings.
- target_type
- query, script, doc, domain, user_id

##### Schema Note 8: Resource access and type
These fields govern how the resource is accessed and its visibility:
- is_public — (if present) whether the resource is public.
- public_type — may indicate category/type of public access.
- status — current state of the resource (e.g., "active", "deprecated").
- external_ws_url — URL of the external web service if external_ws == 1.

#### API Usage Note
Resources can be queried directly using their uuid via internal APIs.
// data = fetch_records("https://api.data.gov.in/resource/{resource_uuid}") 
"""

WriteResourceDescription = dspy.Signature(
    "resource_json -> textual_description: str",
    RESOURCE_NOTES
)
writer = dspy.ChainOfThought(WriteResourceDescription)

def add_summary(resource):
    try:
        ai_writeup = writer(resource_json=resource)
        desc = ai_writeup.textual_description
        _id = resource["_id"]
        rsrcs.update_one(
            {"_id": _id},
            {"$set": {"ai_long_text": desc}}
        )
    except:
        traceback.print_exc()


filters = {
    "source": {"$ne": "visualize.data.gov.in"},
    "ai_long_text": {"$exists": 0}
}
total = rsrcs.count_documents(filters)
gen = rsrcs.find(filters)
for doc in tqdm(gen):
   add_summary(doc)