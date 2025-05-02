# %%
from datatalker.router import Router
from datatalker.resources import get_relevant_resources, adapt_ogdp_catalog_doc, resource_view

# %%
router = Router(confidence_threshold=0.6)

@router.route("dataset_discovery")
def handle_dataset_discovery(message, *args, **kwargs):
    logger = kwargs.get("logger")
    context = kwargs.get("context")
    logger("Fetching datasets")
    docs = get_relevant_resources(message)

    doc = next(docs, None)
    if doc is None:
        return "No relevant resources were found"

    resources = context.get("resources")
    while doc is not None:
        # update context
        resource = adapt_ogdp_catalog_doc(doc)
        resources.append(resource)
        # 
        response = resource_view(resource)
        yield response
        doc = next(docs, None)


@router.route("fetch_data")
def handle_query_data(message, *args, **kwargs):
    return f"Querying data for: {message}"


@router.route("visualize_data")
def handle_visualization(message, *args, **kwargs):
    return f"Visualizing data for: {message}"