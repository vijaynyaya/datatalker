import streamlit as st
from datatalker.routes import router
from datatalker import DataTalker
import dspy


st.title("DataTalker")
app = DataTalker(router)
if not dspy.settings.get("lm"):
    lm = dspy.LM(model="ollama_chat/gemma3:1b", api_base="http://localhost:11434")
    dspy.configure(lm=lm)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = app.respond(prompt)
        if isinstance(response, str):
            st.write(response)
        else:
            chunk = next(response,)
            chunks = []
            while chunk:
                chunks.append(chunk)
                st.markdown(chunk, unsafe_allow_html=True)
                chunk = next(response, None)
            response = "\n".join(chunks)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})