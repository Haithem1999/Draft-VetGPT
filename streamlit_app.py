import streamlit as st
from openai import OpenAI
import uuid 
import json
from PyPDF2 import PdfReader
import datetime

# Initialize session states if not present
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = {}
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = []
if 'selected_conversation' not in st.session_state:
    st.session_state.selected_conversation = None
if 'documents' not in st.session_state:
    st.session_state.documents = {}
    st.session_state.current_context = ""
    st.session_state.uploaded_file = None
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = str(uuid.uuid4())
if 'show_content' not in st.session_state:
    st.session_state.show_content = False
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Set up the OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")

# File upload with a dynamic key
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"], key=st.session_state.file_uploader_key)

# Process the uploaded file and store its content in session state
if uploaded_file:
    # Clear previous content before processing new file
    st.session_state.current_context = ""
    st.session_state.uploaded_file = uploaded_file
    
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        from docx import Document
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
        st.session_state.current_context = text  # Store parsed text for chatbot use
    else:
        st.session_state.current_context = "Unsupported file format."

# Toggle button to display or hide content
if st.button("Show/Hide File Content"):
    st.session_state.show_content = not st.session_state.show_content

# Display or hide content based on the toggle state and current document content
if st.session_state.show_content and st.session_state.current_context:
    st.write(st.session_state.current_context)

# Function to generate response
def generate_response(prompt):
    # Define the system prompt
    system_prompt = """ You are a highly intelligent and specialized virtual assistant designed to help pet owners better understand their pet’s health and well-being. Your primary function is to provide accurate, reliable, and timely information regarding a variety of pet-related health issues, including symptoms, causes, preventive care, home remedies, and when to seek veterinary assistance.
    
    You are knowledgeable in the care of a wide range of pets, including dogs, cats, small mammals, and other common household pets. When pet owners come to you with symptoms or questions about their pet’s behavior, health, or habits, you ask targeted questions to clarify the issue and offer helpful insights based on known conditions and remedies. You always advise users to seek a licensed veterinarian for a formal diagnosis and treatment plan if the condition seems serious.
    You will also read and analyze uploaded documents from the user and then answer any questions relevant to that document.

    Your responses are concise, empathetic, and practical, ensuring pet owners feel supported and informed. You can help with common concerns such as digestive issues (like diarrhea or constipation), urinary problems, infections, injuries, dietary needs, and behavioral concerns, and you can also suggest preventive care and lifestyle adjustments to improve a pet’s overall health. Additionally, you help pet owners understand treatments, medications, and home care, making sure they know the next steps to take for their pets’ well-being.
    
    Key Capabilities:
    
    Health Issue Analysis: Provide insights on potential causes based on symptoms for common pets.
    Home Remedies & First Aid: Suggest safe home care solutions for minor issues.
    When to Seek Professional Help: Clearly indicate when veterinary care is necessary.
    Preventive Care: Offer guidance on nutrition, exercise, and routine check-ups for a healthy pet lifestyle.
    Behavioral Support: Address common behavioral issues and suggest training or management techniques.
    You will interact in a calm, knowledgeable, and supportive tone, ensuring users feel confident in the guidance you provide while always emphasizing the importance of professional veterinary care for proper diagnosis and treatment.
    You will conduct the communication in the French language mainly but if the user prefers English, you will switch to English.
    """

    user_prompt = f"{prompt}\n\nDocument content for reference: {st.session_state.current_context}" if st.session_state.current_context else prompt

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": user_prompt}],
    )
    return response.choices[0].message.content

# Create a "New Conversation" button
if st.sidebar.button("➕ New Conversation"):
    # Reset session state variables for a new conversation
    st.session_state.messages = []
    st.session_state.current_context = ""  # Clear document content
    st.session_state.uploaded_file = None  # Clear uploaded file
    st.session_state.documents = {}
    
    # Generate a new key for the file uploader to force it to reset
    st.session_state.file_uploader_key = str(uuid.uuid4())
    
    # Reset show/hide toggle
    st.session_state.show_content = False
    
    # Optional: Generate a new session ID if needed
    st.session_state.session_id = str(uuid.uuid4())
    
    # Rerun the app to apply the reset state and new file uploader key
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
    
    # Save the updated conversation if necessary
    # conversations[st.session_state.session_id] = st.session_state.messages
    # save_conversations(conversations)
