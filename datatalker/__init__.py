import dspy
import inspect
from typing import Callable
from datatalker.resources import get_relevant_resources


# chat handler
POLICY = [
    "Your role is to assist the user in discovering datasets"
    ", fetch datapoints or subsets of datasets to answer user queries"
    ", and to aid in data analysis and visualization.",
    "You must never let the conversation stray away from your role."
    "Your responses must be short, consice and to the point.",
    "You can ask follow up questions from the user to clarify ambiquity.",
    "It's okay to be sharp, harsh, and biased as long as you are self aware"
    ", and can handle it with grace and virtue.",
    "Provide the right amount of information, neither too much nor too little.",
    "Be clear, brief, and orderly in your communication.",
    "Strive to be truthful. Avoid making statements of fact that can't be "
    "grounded in conversation history.",
]

def chat(message: str, history: list[dict], hint: str = "") -> str:
    """
    Handles short, focused conversations. Useful for answering questions,
    providing explanations, or interacting naturally. Ideal for confirming
    intent, clarifying ambiguous queries, and providing help in plain language.
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
def retrieve(message: str, history: list[dict]) -> str:
    """
    Find relevant datasets based on a user query. Useful for locating
    data sources to support a user's question or analysis task.
    """

    if len(history) == 0:
        resources = get_relevant_resources(message)
        return resources
    
    # craft a refined search query
    FormulateQuery = dspy.Signature(
        "message: str, history: list[dict] -> search_query: str",
        "The search query will be used for retrieving relevant resources."
    )
    query_generator = dspy.ChainOfThought(FormulateQuery)
    prediction = query_generator(message=message, history=history)
    print("retrieve.generate_query.reasoning:", prediction.reasoning)
    resources = get_relevant_resources(prediction)
    return resources
    
# data query handler
def fetch_data(message: str, history: list[dict], resource: dict = None):
    """
    Downloads or pulls data associated with a specified resource. Use this
    after identifying a relevant dataset to actually fetch the underlying data
    for analysis or processing. It supports workflows where raw data access
    is required following resource discovery.
    """
    return "You've reached the cutting edge! This portion is still under construction 😅."

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
    def __init__(self):
        self.HANDLERS = dict()
        self.handler_docs: list[dict] = list()
        self.notes: list[str] = list()
        self.resources: list[dict] = list()
        self.dataframes: list = list()

    def add_handler(self, name: str, func: Callable):
        self.HANDLERS[name] = func
        self.handler_docs.append(dict(
            name=name,
            usage=inspect.getdoc(func)
        ))

    def choose_handler(self, message: str, history: list) -> str:
        classifier = dspy.ChainOfThought(ChooseHandler)
        prediction = classifier(
            list_of_handlers = self.handler_docs,
            user_message = message,
            conversation_history = history
        )
        print("datatalker.choose_handler.reasoning", prediction.reasoning)
        return prediction.selected_handler_name
    
    def handle(self, message: str, history: list[dict]):
        hanlder_name = self.choose_handler(message, history)
        handler = self.HANDLERS[hanlder_name]
        return handler(message, history)


talker = DataTalker()
talker.add_handler("chat", chat)
talker.add_handler("retrieve_datasets", retrieve)
talker.add_handler("fetch_data", fetch_data)
talker.add_handler("visualize_data", visualize)
