import streamlit as st
import os
from openai import OpenAI
#from dotenv import load_dotenv
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

# # Create a layout with sidebar for history
# with st.sidebar:
#     st.title("Conversation History")
    
#     # New conversation button at the top
#     if st.button("➕ New Conversation", key="new_chat"):
#         st.session_state.current_conversation = []
#         st.session_state.selected_conversation = None
#         st.rerun()

#     # Display conversations in sidebar
#     for conv_id, conv_data in st.session_state.conversation_history.items():
#         if st.button(f"📝 {conv_data['title']}", key=conv_id):
#             st.session_state.current_conversation = conv_data['messages']
#             st.session_state.selected_conversation = conv_id
#             st.rerun()

#     # Save current conversation
#     if st.session_state.current_conversation and not st.session_state.selected_conversation:
#         title = st.text_input("Conversation title:", 
#                             value=f"Conversation {len(st.session_state.conversation_history) + 1}")
#         if st.button("💾 Save Conversation"):
#             conversation_id = str(uuid.uuid4())
#             st.session_state.conversation_history[conversation_id] = {
#                 'title': title,
#                 'messages': st.session_state.current_conversation,
#                 'timestamp': str(datetime.datetime.now())
#             }
#             st.session_state.selected_conversation = conversation_id
#             st.success("Conversation saved!")
#             st.rerun()

#     # Download conversations as JSON
#     if st.session_state.conversation_history:
#         json_str = json.dumps(st.session_state.conversation_history, indent=2)
#         st.download_button(
#             label="⬇️ Download Conversations",
#             file_name="conversations.json",
#             mime="application/json",
#             data=json_str
#         )

# Set up the OpenAI API key
# OPENAI API KEY

#api_key = os.getenv("OPENAI_API_KEY")
api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key= api_key)



# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")

# st.markdown(
#     """
#     <style>
#     .stApp {
#         background-image: linear-gradient(
#             rgba(255, 255, 255, 0.1),
#             rgba(255, 255, 255, 0.1)
#         ),
#         url("https://img.freepik.com/free-photo/cute-pets-collage_23-2150007429.jpg");
#         background-size: cover;
#         background-attachment: fixed;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )


# -------------------------------------------------------

# Store uploaded documents in session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
    st.session_state.current_context = ""


# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"])

# Display content if toggled on
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        # Update the document context in session state
        st.session_state.current_context = text  # Store the parsed text for chatbot use
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        # Update the document context in session state
        st.session_state.current_context = text  # Store the parsed text for chatbot use
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
        # Update the document context in session state
        st.session_state.current_context = text  # Store the parsed text for chatbot use
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
else:
    pass

# ---------------------------------------------------------




# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

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
    # Clear current context if it exists
    if 'current_context' in st.session_state:
        st.session_state.current_context = None
    st.rerun()

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


# # User input
# user_input = st.text_input("You:", "")

# if user_input:
#     # Generate response from OpenAI
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_input},
#         ],

#     )

#     # Display the response
#     st.write("VetBot:", response.choices[0].message.content)

# End Generation Here
