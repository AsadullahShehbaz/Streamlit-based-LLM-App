import streamlit as st
import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import PyPDF2
import docx
import base64
from transformers import pipeline
from pathlib import Path

# =====================
# 🔐 Load Gemini API Key
# =====================
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    api_key=GOOGLE_API_KEY
)

# =====================
# 🧭 Sidebar Navigation
# =====================
st.sidebar.title("💬 AI Chat Assistant – Powered by LLMs")
page = st.sidebar.radio("Navigate", ["🤖 Chatbot", "📄 Document Reader", "🎥Watch Youtube"])

# =====================
# 🤖 Chatbot Page
# =====================
if page == "🤖 Chatbot":
    st.title("🤖 Smart Chat – Ask Anything, Anytime")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)

    user_input = st.chat_input("Type your message...")

    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        response = llm.invoke(user_input)
        reply = response.content
        st.session_state.chat_history.append(("assistant", reply))
        st.rerun()

# =====================
# 📄 Document Reader Page
# =====================
elif page == "📄 Document Reader":
    st.title("🧾 Summarize, search, and quiz any document")

    uploaded_file = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])

    def extract_text(file):
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            return [page.extract_text() or "" for page in reader.pages]
        elif file.name.endswith('.docx'):
            doc = docx.Document(file)
            return ["\n".join(para.text for para in doc.paragraphs)]
        elif file.name.endswith('.txt'):
            return [file.read().decode("utf-8")]
        else:
            return ["Unsupported file type."]

    if uploaded_file:
        doc_pages = extract_text(uploaded_file)
        total_pages = len(doc_pages)
        page_num = st.number_input("Go to page", 1, total_pages, 1)

        st.subheader(f"📖 Page {page_num} Text")
        st.text_area("Text", doc_pages[page_num - 1][:3000], height=300)

        tab1, tab2 = st.tabs(["🧠 Full Summary", "💬 Ask Gemini"])

        with tab1:
            st.subheader("🧠 Gemini Summary")
            if st.button("Generate Summary"):
                with st.spinner("Thinking..."):
                    full_text = "\n".join(doc_pages)
                    response = llm.invoke(f"Summarize this document:\n{full_text}")
                    summary = response.content
                    st.success("✅ Summary created!")
                    st.markdown(summary)

                    b64 = base64.b64encode(summary.encode()).decode()
                    href = f'<a href="data:text/plain;base64,{b64}" download="summary.txt">📥 Download Summary</a>'
                    st.markdown(href, unsafe_allow_html=True)

        with tab2:
            st.subheader("💬 Ask a Question About the Document")
            question = st.text_input("Your question:")
            if question:
                full_text = "\n".join(doc_pages)
                prompt = f"Context:\n{full_text}\n\nQuestion: {question}"
                response = llm.invoke(prompt)
                st.markdown("### 💡 Gemini Answer")
                st.write(response.content)

# =====================
# 🎥 Study Tube Page (YouTube)
# =====================
elif page == "🎥Watch Youtube":
    st.set_page_config(page_title="Study Tube", layout="wide")
    st.title("🧠 Study Tube - Learn Better without Distractions")

    st.subheader("🔗 YouTube Link")
    youtube_url = st.text_input("Paste YouTube video URL")

    st.markdown("---")
    st.header("🎬 Lecture Video")

    @st.cache_data
    def get_video_id(url):
        regex = r"(?:youtube\.com/(?:.*v=|v/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})"
        match = re.search(regex, url)
        return match.group(1) if match else None

    @st.cache_resource
    def load_summarizer():
        return pipeline("summarization")

    video_id = get_video_id(youtube_url)
    notes_key = f"notes_{video_id}" if video_id else "notes_default"

    if youtube_url:
        if video_id:
            embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0"

            st.markdown(
                f"""
                <div style='position:relative;padding-bottom:56.25%;height:0;overflow:hidden;'>
                    <iframe src="{embed_url}" 
                            style='position:absolute;top:0;left:0;width:100%;height:100%;' 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                    </iframe>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.error("❌ Invalid YouTube URL format. Please check the link.")

    st.markdown("---")    



