import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document
import uuid
import json

# Initialize session state variables for conversation and file content
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = {}
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = []
if 'selected_conversation' not in st.session_state:
    st.session_state.selected_conversation = None
if 'current_context' not in st.session_state:
    st.session_state.current_context = ""  # Stores the content of the current file
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None  # Holds the uploaded file object

# Define a reset function to clear file-related session state
def reset():
    st.session_state.current_context = ""
    st.session_state.uploaded_file = None

# Define a function to process the file if it exists
def process_file():
    uploaded_file = st.session_state.file_uploader  # Access the uploaded file
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            st.session_state.current_context = "".join([page.extract_text() for page in pdf_reader.pages])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            st.session_state.current_context = "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.type == "text/plain":
            st.session_state.current_context = uploaded_file.read().decode("utf-8")
        else:
            st.session_state.current_context = "Unsupported file format."

# Set up the OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")

# File uploader with on_change to reset, then process file
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"], key="file_uploader", on_change=reset)

# After resetting, check if there's an uploaded file and process it
if st.session_state.file_uploader:
    process_file()  # Process the new file after reset

# Initialize toggle state in session state
if "show_content" not in st.session_state:
    st.session_state.show_content = False

# Toggle button to display or hide content
if st.button("Show/Hide File Content"):
    st.session_state.show_content = not st.session_state.show_content

# Display content of the currently uploaded document only
if st.session_state.show_content and st.session_state.current_context:
    st.write("File Content:")
    st.write(st.session_state.current_context)

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Function to generate response
def generate_response(prompt):
    system_prompt = """You are a highly intelligent and specialized virtual assistant designed to help pet owners better understand their pet’s health and well-being. Your primary function is to provide accurate, reliable, and timely information regarding a variety of pet-related health issues, including symptoms, causes, preventive care, home remedies, and when to seek veterinary assistance.
    
    You are knowledgeable in the care of a wide range of pets, including dogs, cats, small mammals, and other common household pets. When pet owners come to you with symptoms or questions about their pet’s behavior, health, or habits, you ask targeted questions to clarify the issue and offer helpful insights based on known conditions and remedies. You always advise users to seek a licensed veterinarian for a formal diagnosis and treatment plan if the condition seems serious.
    You will also read and analyze uploaded documents from the user and then answer any questions relevant to that document.

    Your responses are concise, empathetic, and practical, ensuring pet owners feel supported and informed. You can help with common concerns such as digestive issues (like diarrhea or constipation), urinary problems, infections, injuries, dietary needs, and behavioral concerns, and you can also suggest preventive care and lifestyle adjustments to improve a pet’s overall health. Additionally, you help pet owners understand treatments, medications, and home care, making sure they know the next steps to take for their pets’ well-being.
    
    Key Capabilities:
    
    - Health Issue Analysis: Provide insights on potential causes based on symptoms for common pets.
    - Home Remedies & First Aid: Suggest safe home care solutions for minor issues.
    - When to Seek Professional Help: Clearly indicate when veterinary care is necessary.
    - Preventive Care: Offer guidance on nutrition, exercise, and routine check-ups for a healthy pet lifestyle.
    - Behavioral Support: Address common behavioral issues and suggest training or management techniques.
    
    You will interact in a calm, knowledgeable, and supportive tone, ensuring users feel confident in the guidance you provide while always emphasizing the importance of professional veterinary care for proper diagnosis and treatment.
    You will conduct the communication in the French language mainly, but if the user prefers English, you will switch to English."""

    user_prompt = f"{prompt}\n\nDocument content for reference: {st.session_state.current_context}" if st.session_state.current_context else prompt

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
    # Clear uploaded file content for new conversation
    st.session_state.current_context = ""
    st.rerun()

# Display past conversations in sidebar
for session_id, msgs in conversations.items():
    if msgs:  # Only show sessions that have messages
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
