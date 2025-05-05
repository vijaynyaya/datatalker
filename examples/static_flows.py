from gradio import ChatMessage
import time


def suggest_datasets(message, history):
    response = ChatMessage(
        content="",
        metadata={"title": "_Thinking_ step-by-step", "id": 0, "status": "pending"}
    )
    yield response
    thoughts = [
        "First, I need to understand the core aspects of the query...",
        "Now, considering the broader context and implications...",
        "Analyzing potential approaches to formulate a comprehensive answer...",
        "Finally, structuring the response for clarity and completeness..."
    ]

    accumulated_thoughts = ""
    for thought in thoughts:
        time.sleep(0.5)
        accumulated_thoughts += f"- {thought}\n\n"
        response.content = accumulated_thoughts.strip()
        yield response
    
    response.metadata["status"] = "done"
    yield response

    intro_msg = "Okay, I found a few datasets related to agriculture in Punjab on the India Data Portal"
    d1 = "Punjab Agricultural Census Data (2015-16): Contains data on land holdings, crops, and irrigation."
    d2 = "Fertilizer Consumption in Punjab (2010-2020): Tracks NPK fertilizer usage by district."
    d3 = "Punjab Crop Production Statistics (Annual): Data on yield for major crops like wheat and rice."
    followup_msg = "Choose a dataset for detailed analysis, including querying specific data and visualization."
    response = [
        response,
        ChatMessage(
            content=(
                intro_msg + ". " + followup_msg
            ),
            options=[
                {"value": "1", "label": d1},
                {"value": "2", "label": d2},
                {"value": "3", "label": d3}
            ]
        ),
        # ChatMessage(content=followup_msg)
    ]
    yield response
