import gradio as gr
from gradio import ChatMessage
from datatalker import talker
import dspy


if not dspy.settings.get("lm", None):
    lm = dspy.LM(model="ollama_chat/gemma3", api_base="http://localhost:11434", cache=False)
    dspy.configure(lm=lm, caching=False)


def message_handler(message, history = list()):
    gen = talker.handle(message, history)
    response = ChatMessage(
        content="",
        metadata={"title": "_Thinking_ step-by-step", "id": 0, "status": "pending"}
    )
    yield response
    messages = [response]
    while True:
        reply = next(gen, None)
        if reply is None:
            break
        messages.append(reply)
        yield messages
    messages[0].metadata["status"] = "done"
    yield messages
    return messages

demo = gr.ChatInterface(
    fn=message_handler,
    type="messages",
    title="Data📅Talker🗣️",
    description="Conversational AI for Data Portals",
    theme="ocean",
    fill_width=True,
    examples=[
        "What's the trend of fertilizer utilization in Punjab broken down by fertilizer type (N, P, K)?",
        "Find data related to agricultural productivity in Punjab.",
        "What's the average paddy yield in Sangrur district for the last five years?",
    ],
    # save_history=True,
    flagging_mode="manual",
    flagging_options=["Like", "Not good enough"]
    # cache_examples=True,
    # additional_inputs=gr.Radio(["OGD", "IDP"], label="Source", info="Select data portal")
)

if __name__ == "__main__":
    demo.launch()