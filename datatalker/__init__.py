import dspy
import inspect
from typing import Callable
from datatalker.resources import get_relevant_resources


# chat handler
POLICY = [
    "Your role is to assist the user in discovering datasets"
    ", fetch datapoints or subsets of datasets to answer user queries"
    ", and to aid in data analysis and visualization.",
    "The conversation should always stay centered around your role as data assistant."
    "You can ask follow up questions from the user to clarify ambiquity.",
    "Your responses must be short, concise and to the point.",
    # "It's okay to be sharp, harsh, and biased as long as you are self aware"
    # ", and can handle it with grace and virtue.",
    "Provide the right amount of information, neither too much nor too little.",
    # "Be clear, brief, and orderly in your communication.",
    "Strive to be truthful. Avoid making statements of fact that can't be "
    "grounded in conversation history.",
]

def chat(message: str, history: list[dict], hint: str = "", log=print) -> str:
    """
    Handles general purpose interactions in the natural language.
    Useful for answering questions or providing explanations based on the
    context set by the ongoing conversation.
    Ideal for confirming intent, clarifying ambiguous queries,
    and providing help in plain language.
    """
    Chat = dspy.Signature(
        "history: list[dict], message: str -> response: str",
        " ".join(POLICY)
    )
    chatter = dspy.ChainOfThoughtWithHint(Chat)
    prediction = chatter(message=message, history=history, hint=hint)
    print("chat.reply.reasoning:", prediction.reasoning)
    return prediction.response    


# resource handler
def retrieve(message: str, history: list[dict], log=print):
    """
    Find relevant datasets based on a user query. Useful for locating
    data sources to support a user's question or analysis task.
    """
    
    if len(history) == 0:
        resources = get_relevant_resources(message, log=log)
    else:    
        # craft a refined search query
        FormulateQuery = dspy.Signature(
            "message: str, history: list[dict] -> search_query: str",
            "The search query will be used for retrieving relevant resources."
        )
        query_generator = dspy.ChainOfThought(FormulateQuery)
        prediction = query_generator(message=message, history=history)
        print("retrieve.generate_query.reasoning:", prediction.reasoning)
        resources = get_relevant_resources(prediction.search_query, log=log)

    
    doc = next(resources, None)
    if doc is None:
        print("retriever: No relevant resources found.")
        return NO_DATASETS_FOUND_MSG, None

    while doc is not None:
        markdown = md_renderer(json=doc)
        yield markdown, doc
        doc = next(resources, None)

# data query handler
class ChooseDataset(dspy.Signature):
    datasets = dspy.InputField(desc="list of datasets to choose from")
    user_message = dspy.InputField(desc="user message")
    conversation_history = dspy.InputField()
    id_of_selected_dataset: str = dspy.OutputField(desc="Id of the selected dataset")

def fetch_data(message: str, history: list[dict], resources: dict = None):
    """
    Downloads or pulls data associated for datasets. Use this
    to actually fetch the underlying data for analysis or processing. It
    supports workflows where raw data access is required following dataset
    discovery. Ideal when the user requests records or a datum.
    """
    dataset_selector = dspy.ChainOfThought(ChooseDataset.with_instructions("Select a dataset."))
    prediction = dataset_selector(
        datasets=list(resources.values()),
        user_message=message,
        conversation_history=history,
    )
    print("fetch_data.dataset_selector.reasoning", prediction.reasoning)
    rsrc = resources[prediction.id_of_selected_dataset]
    msg = next(chat(message=message, history=[], hint=f"inform the user that the system has selected {rsrc}."))
    yield msg

# visualization handler
def visualize(message: str, history: list[dict], data = None):
    """
    Generates visual representations of data (e.g., charts, graphs, tables)
    Use this tool to create plots or diagrams from structured data. It's helpful
    in exploring patterns, communicating insights, or support decision-making with
    clear visual evidence.
    """
    return "You've reached the cutting edge! This portion is still under construction 😅."


# handle handlers
class ChooseHandler(dspy.Signature):    
    list_of_handlers: list = dspy.InputField(desc="list of available hanlders")
    user_message = dspy.InputField(desc="a message from the user")
    conversation_history = dspy.InputField()
    selected_handler_name: str = dspy.OutputField(desc="returns a single tool based on the message")


class DataTalker:
    """
    DataTalker provides a natural language interface to data.

    Envisioned Capabilites:
    - Chat: General conversation and assistance
    - Retrieval: Finding and loading datasets
    - Data Analysis: Analyzing and visualizing data
    - Reasoning: Explaining insights and patterns
    - Tools: Excuting specific functions such as data transformation
    """

    def __init__(self):
        self.HANDLERS = dict()
        self.handler_docs: list[dict] = list()
        self.resources = dict()
        self.dataframes: list = list()

    def add_handler(self, name: str, func: Callable):
        self.HANDLERS[name] = func
        self.handler_docs.append(dict(
            name=name,
            usage=inspect.getdoc(func)
        ))

    def choose_handler(self, message: str, history: list) -> str:
        classifier = dspy.ChainOfThought(ChooseHandler \
            .with_instructions("The selected handler must be from the provided list of handlers.")
        )
        prediction = classifier(
            list_of_handlers = self.handler_docs,
            user_message = message,
            conversation_history = history
        )
        print("datatalker.choose_handler.reasoning", prediction.reasoning)
        return prediction.selected_handler_name

    def handle_retrieval(self, generator):
        texts = list()
        while True:
            chunk = next(generator, None)
            if chunk is None:
                break
            text, doc = chunk
            # TODO: Multi-Hop Search
            self.resources[doc['id']] = doc
            texts.append(text)
            yield text
        yield chat(messge="", history=texts, hint="The system fetched datasets for the user query. Write a short follow up message.")
    
    def handle(self, message: str, history: list[dict]):
        handler_name = self.choose_handler(message, history)
        handler = self.HANDLERS[handler_name]
        if handler_name == "retrieve_datasets":
            # tried_again = False
            response = handler(message, history)
            return self.handle_retrieval(response)
        elif handler_name == "fetch_data":
            response = handler(message, history, self.resources)
            yield response
        else:
            yield "You seemed to have reached the cutting edge! I tripped over."

def build_datatalker():
    talker = DataTalker()
    talker.add_handler("chat", chat)
    talker.add_handler("retrieve_datasets", retrieve)
    talker.add_handler("fetch_data", fetch_data)
    talker.add_handler("visualize_data", visualize)

talker = build_datatalker()
