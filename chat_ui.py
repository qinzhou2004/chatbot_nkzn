import streamlit as st
import os
import time
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

# --- Custom CSS ---
st.markdown("""
    <style>
        /* Main header styling */
        .header {
            background-color: #0056b3;
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        /* Chat container styling */
        .chat-container {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            min-height: 60vh;
            max-height: 60vh;
            overflow-y: auto;
        }
        
        /* User message styling */
        .user-message {
            background-color: #e3f2fd;
            border-radius: 1rem 1rem 0 1rem;
            padding: 0.75rem;
            margin: 0.5rem 0;
            max-width: 80%;
            margin-left: auto;
        }
        
        /* Assistant message styling */
        .assistant-message {
            background-color: white;
            border-radius: 1rem 1rem 1rem 0;
            padding: 0.75rem;
            margin: 0.5rem 0;
            max-width: 80%;
            margin-right: auto;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        /* Loading animation */
        .typing-indicator {
            display: flex;
            padding: 0.5rem;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            margin: 0 2px;
            background-color: #666;
            border-radius: 50%;
            opacity: 0;
            animation: typingAnimation 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typingAnimation {
            0% { opacity: 0.3; transform: translateY(0); }
            50% { opacity: 1; transform: translateY(-5px); }
            100% { opacity: 0.3; transform: translateY(0); }
        }
        
        /* Hide default Streamlit elements */
        .stChatMessage {
            padding: 0;
        }
        
        .stChatMessage .stMarkdown {
            padding: 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- UI Configuration ---
st.set_page_config(
    page_title="Soporte NKZN",
    page_icon="🤖",
    layout="centered"
)

# Show loading animation initially
with st.spinner(""):
    time.sleep(1)  # Simulate loading time

# Custom header with logo and title
st.markdown("""
    <div class="header">
        <h1 style="margin:0;">Soporte NKZN</h1>
        <p style="margin:0; font-size:1.2rem;">Expertos en tecnología!</p>
    </div>
""", unsafe_allow_html=True)

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
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar="🧑"):
            st.markdown(msg["content"])

st.markdown('</div>', unsafe_allow_html=True)

# --- Message Processing ---
if prompt := st.chat_input("Escribe tu mensaje aquí..."):
    # Add user message to UI and state
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
    
    # Generate assistant response
    with st.chat_message("assistant", avatar="🧑"):
        # Show typing indicator
        typing_indicator = st.markdown("""
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        """, unsafe_allow_html=True)
        
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
                typing_indicator.empty()
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                raise Exception("No assistant response received")
                
        except Exception as e:
            typing_indicator.empty()
            error_msg = "Disculpa, estoy teniendo dificultades. ¿Podrías intentarlo de nuevo?"
            st.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.error(f"API Error: {str(e)}")