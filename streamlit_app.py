import streamlit as st
import os
from openai import OpenAI
import uuid 
import json
from PyPDF2 import PdfReader
import datetime

# Initialize conversation history in session state if not present
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = {}
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = []
if 'selected_conversation' not in st.session_state:
    st.session_state.selected_conversation = None

# Set up the OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")

# Store uploaded documents in session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
    st.session_state.current_context = ""  # Initialize as empty string
    st.session_state.uploaded_file = None  # Initialize uploaded file as None

# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"], key="file_uploader")

# If a file is uploaded, process it and store its content
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file  # Store uploaded file in session state
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
        st.session_state.current_context = text  # Store parsed text for chatbot use
    else:
        text = "Unsupported file format."

# Initialize toggle state in session state
if "show_content" not in st.session_state:
    st.session_state.show_content = False

# Toggle button to display or hide content
if st.button("Show/Hide File Content"):
    st.session_state.show_content = not st.session_state.show_content

# Display or hide content based on the toggle state
if uploaded_file and st.session_state.show_content:
    st.write(text)

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Function to generate response
def generate_response(prompt):
    # Define the system prompt
    system_prompt = """ You are a highly intelligent and specialized virtual assistant designed to help pet owners better understand their pet’s health and well-being..."""

    if st.session_state.current_context:
        user_prompt = f"{prompt}\n\nDocument content for reference: {st.session_state.current_context}"
    else:
        user_prompt = prompt

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": user_prompt}],
    )
    return response.choices[0].message.content

# Load previous conversations from a file
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save conversations to a file
def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)

# Load previous conversations
conversations = load_conversations()

# Create a unique session ID for the current user
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Load previous messages for this session, if any
if st.session_state.session_id in conversations:
    st.session_state.messages = conversations[st.session_state.session_id]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialize sidebar for conversation history
st.sidebar.title("Conversation History")

# Create a "New Conversation" button
if st.sidebar.button("➕ New Conversation"):
    # Clear the current conversation
    st.session_state.messages = []
    # Generate new session ID
    st.session_state.session_id = str(uuid.uuid4())
    # Clear current context and uploaded file when starting a new conversation
    st.session_state.current_context = ""  # Clear document content
    st.session_state.uploaded_file = None  # Clear uploaded file
    st.experimental_rerun()  # Rerun to refresh the file uploader and reset the app

# Display past conversations in sidebar
for session_id, msgs in conversations.items():
    if msgs:  # Only show sessions that have messages
        # Get first user message as title, or use session ID if no messages
        title = next((msg["content"][:30] + "..." for msg in msgs if msg["role"] == "user"), f"Conversation {session_id[:8]}")
        if st.sidebar.button(title, key=session_id):
            st.session_state.session_id = session_id
            st.session_state.messages = msgs
            st.rerun()

# Chat input
if prompt := st.chat_input("You:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = generate_response(prompt)
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Save the updated conversation
    conversations[st.session_state.session_id] = st.session_state.messages
    save_conversations(conversations)
