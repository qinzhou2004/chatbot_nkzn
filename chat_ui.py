import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration Section ---
def initialize_openai_client():
    """Initialize OpenAI client with secure API key loading"""
    
    # Load from .env first (development)
    load_dotenv()  
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Fallback to Streamlit secrets (production)
    if not api_key and 'OPENAI_API_KEY' in st.secrets:
        api_key = st.secrets['OPENAI_API_KEY']
    
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment variables")
        st.stop()
    
    return OpenAI(api_key=api_key)

# Constants
ASSISTANT_ID = "asst_i2ivyEjwxcYQT2QFwuioPzKh"
client = initialize_openai_client()

# --- UI Configuration ---
st.set_page_config(
    page_title="🧠 ChatGPT Local - Español",
    page_icon="🤖",
    layout="centered"
)
st.title("💬 ChatBot powered by NKZN")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    # Create new conversation thread
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    
    # Initial assistant message
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de IA. ¿En qué puedo ayudarte hoy?"}
    ]

# --- Display Message History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Message Processing ---
if prompt := st.chat_input("Escribe tu mensaje aquí..."):
    # Add user message to UI and state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # Add message to thread
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=prompt
                )
                
                # Create and monitor run
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID
                )
                
                # Poll for completion
                while run.status != "completed":
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
                
                # Retrieve and display response
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                
                assistant_messages = [
                    msg for msg in messages.data if msg.role == "assistant"
                ]
                
                if assistant_messages:
                    reply = assistant_messages[0].content[0].text.value
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    raise Exception("No assistant response received")
                    
            except Exception as e:
                error_msg = "Disculpa, estoy teniendo dificultades. ¿Podrías intentarlo de nuevo?"
                st.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                st.error(f"API Error: {str(e)}")