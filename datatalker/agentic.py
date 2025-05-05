from agents import Agent, function_tool, RunContextWrapper, ModelSettings
from typing import Literal
from pydantic import BaseModel
from dataclasses import dataclass
from .config import MODEL

@function_tool
def get_datasets(query: str) -> list[dict]:
    raise NotImplementedError()

retriever = Agent(
    name="Dataset Retriever",
    instructions=(
        "Find relevant datasets."
        "Useful for locating dataset to support data analysis"
        "or answering user queries"
    ),
    tools=[get_datasets]
    
)

@function_tool
def build_visualization(dataframe, instruction: str):
    raise NotImplementedError()

dataviz = Agent(
    name="Data Visualzation Expert",
    instruction=(
        "Build data visualations such as plots, charts, graphs, and tables"
        "to assist in exploring patterns, communicating insights, and "
        "support decision-making with clear visual evidence"
    ),
    tools=[build_visualization]
)


@dataclass
class ConversationContext:
    resources: list[dict]
    active_resource: str
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


@function_tool
def fetch_data(uuid: str, interface: ResourceType):
    raise NotImplementedError()


data_fetcher = Agent(
    name="Data Analyst",
    instructions=(
        "Fetches the underlying dataset for a specific resource"
    ),
    tools=[fetch_data],
)


def analyse_dataset( 
    context: RunContextWrapper[ConversationContext], agent: Agent[ConversationContext]
):
    return f"Analyse {context.context.active_resource}. Help the user with their questions."

data_scientist = Agent[ConversationContext](
    name="Senior Data Scientist",
    instructions=analyse_dataset,
)


# observe the agent lifecycle using AgentHooks



chatbot = Agent(
    name="Virtual Assistant",
    instructions="Mediates dialogue between the system and the user.",
    model=MODEL,
    handoffs=[retriever, dataviz, data_fetcher]
)

