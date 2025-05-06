from agents import (
    Agent,
    function_tool,
    RunContextWrapper,
    trace,
    Runner,
    RawResponsesStreamEvent,
    TResponseInputItem,
    RunConfig
)
from openai.types.responses import ResponseContentPartDoneEvent, ResponseTextDeltaEvent
from typing import Literal
from pydantic import BaseModel
from dataclasses import dataclass
import asyncio
import uuid
from datatalker.config import MODEL
from datatalker.resources import get_relevant_resources
from datatalker.ogdp import OGDProxy

@function_tool
def get_datasets(query: str) -> list[dict]:
    """
    Gets a list of datasets relevant to the provided query.
    This function uses the query to search and retrieve relevant datasets/resources 
    that match the search criteria.
    Args:
        query (str): The search query string to find relevant datasets
    Returns:
        list[dict]: A list of dictionaries containing metadata about relevant datasets
    """

    return list(get_relevant_resources(query))

retriever = Agent(
    name="Dataset Retriever",
    instructions=(
        "Find relevant datasets."
        "Useful for locating dataset to support data analysis"
        "or answering user queries"
    ),
    tools=[get_datasets],
    model=MODEL,
    
)

@function_tool
def build_visualization(dataframe, instruction: str):
    raise NotImplementedError()

dataviz = Agent(
    name="Data Visualzation Expert",
    instructions=(
        "Build data visualations such as plots, charts, graphs, and tables"
        "to assist in exploring patterns, communicating insights, and "
        "support decision-making with clear visual evidence"
    ),
    tools=[build_visualization],
    model=MODEL
)


@dataclass
class ConversationContext:
    resources: list[dict]
    dataframes: list # pd.DataFrame (maybe)


ResourceType = Literal["ogd:resource", "ogd:catalog"]
class SelectedDataset(BaseModel):
    dataset_id: str
    dataset_interface: ResourceType


dataset_selector = Agent[ConversationContext](
    name="Dataset Selector",
    instructions="Select a resource for data fetching or data analysis.",
    model=MODEL
)


ogd = OGDProxy(api_key="579b464db66ec23bdd000001edd87d62b40343d54d7f4653d5d391a7")
# @function_tool
def fetch_data(uuid: str, interface: ResourceType, filter_params: dict[str, str]):
    """Fetches records from a dataset based on specified filters.
    This function retrieves data from the underlying dataset using provided filters
    and exclusion criteria.
    Args:
        uuid (str): Unique identifier for the dataset.
        interface (ResourceType): Type of resource/interface to fetch data from.
        filter_params (dict[str, str]): Dictionary containing filter parameters where:
            - Keys can be in format "filters[field_name]" for inclusion filters
            - Keys can be in format "notfilters[field_name]" for exclusion filters
            - Values are the corresponding filter criteria as strings
    Returns:
        The filtered dataset records (format depends on implementation)
    """
    return ogd.catalog(uuid, limit=100, params=filter_params).json()


data_fetcher = Agent(
    name="Data Analyst",
    instructions=(
        "Fetches the underlying dataset for a specific resource"
    ),
    model=MODEL,
    # tools=[fetch_data],
)


def analyse_dataset( 
    context: RunContextWrapper[ConversationContext], agent: Agent[ConversationContext]
):
    return f"Analyse {context.context.active_resource}. Help the user with their questions."

data_scientist = Agent[ConversationContext](
    name="Senior Data Scientist",
    instructions=analyse_dataset,
    model=MODEL
)


# observe the agent lifecycle using AgentHooks



chatbot = Agent(
    name="Virtual Assistant",
    instructions="Mediates interactions between the system and the user.",
    model=MODEL,
    handoffs=[retriever]
)


async def main():
    # We'll create an ID for this conversation, so we can link each trace
    msg = input("Hi! We speak Hindi, English, and Punjabi. How can I help? ")
    agent = chatbot
    inputs: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

    while True:
        # Each conversation turn is a single trace. Normally, each input from the user would be an
        # API request to your app, and you can wrap the request in a trace()
        result = Runner.run_streamed(
            agent,
            input=inputs,
            run_config=RunConfig(model=MODEL)
        )
        async for event in result.stream_events():
            if not isinstance(event, RawResponsesStreamEvent):
                continue
            data = event.data
            if isinstance(data, ResponseTextDeltaEvent):
                print(data.delta, end="", flush=True)
            elif isinstance(data, ResponseContentPartDoneEvent):
                print("\n")

        inputs = result.to_input_list()
        print("\n")

        user_msg = input("Enter a message: ")
        inputs.append({"content": user_msg, "role": "user"})
        agent = result.current_agent


if __name__ == "__main__":
    asyncio.run(main())