import streamlit as st
from pipeline import QuranQAPipeline
import io
import sys
from contextlib import contextmanager
import time

# Set page config
st.set_page_config(
    page_title="Quran Chatbot",
    page_icon="📖",
    layout="centered"
)

# Custom CSS
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        direction: rtl;
        text-align: right;
    }
    .stMarkdown {
        direction: rtl;
        text-align: right;
    }
    .status-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("🤖 Quran Chatbot")
st.markdown("""
    مرحباً! أنا مساعد لغوي متخصص في القرآن الكريم. يمكنك طرح أسئلتك باللغة العربية
    وسأحاول مساعدتك في فهم الكلمات والجذور القرآنية.
""")

# Initialize session state for chat history and status
if "messages" not in st.session_state:
    st.session_state.messages = []
if "status" not in st.session_state:
    st.session_state.status = ""
if "processing" not in st.session_state:
    st.session_state.processing = False
if "status_updates" not in st.session_state:
    st.session_state.status_updates = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("اكتب سؤالك هنا...", disabled=st.session_state.processing):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get bot response
    with st.chat_message("assistant"):
        # Create a placeholder for status updates
        status_placeholder = st.empty()
        
        # Set processing state
        st.session_state.processing = True
        st.session_state.status = ""
        st.session_state.status_updates = []
        
        # Function to update status in real-time
        def update_status(msg: str):
            try:
                st.session_state.status_updates.append(msg)
                st.session_state.status = "".join(st.session_state.status_updates)
                status_placeholder.markdown(
                    f'<div class="status-container">{st.session_state.status}</div>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                print(f"Error updating status: {e}", file=sys.stderr)
        
        try:
            # Create a new pipeline instance with the status callback
            pipeline = QuranQAPipeline(verbose=True, status_callback=update_status)
            
            # Get the response
            response = pipeline.answer_question(prompt)
            
            # Final status update
            status_placeholder.markdown(
                f'<div class="status-container">{st.session_state.status}</div>',
                unsafe_allow_html=True
            )
            
            # Display the final response
            st.markdown(response)
            
        except Exception as e:
            error_msg = f"❌ حدث خطأ: {str(e)}"
            st.error(error_msg)
            response = error_msg
        
        finally:
            # Reset processing state
            st.session_state.processing = False
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response}) 