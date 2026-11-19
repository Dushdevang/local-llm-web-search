import streamlit as st
import ollama
from ddgs import DDGS

st.set_page_config(page_title="My Web Search AI", page_icon="🔎")
st.title("🔎 Local AI with Web Search")

# Sidebar settings
models = [m.model for m in ollama.list().models]
model = st.sidebar.selectbox("Model", models)
use_web = st.sidebar.toggle("Search the web", value=True)
n_results = st.sidebar.slider("Number of results", 1, 8, 5)

if "history" not in st.session_state:
    st.session_state.history = []

# Show past messages
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def web_search(query, n):
    try:
        return DDGS().text(query, max_results=n)
    except Exception as e:
        return []

if question := st.chat_input("Ask anything..."):
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    prompt = question
    sources = []
    if use_web:
        with st.spinner("Searching the web..."):
            sources = web_search(question, n_results)
        if sources:
            context = "\n\n".join(
                f"[{i+1}] {r['title']}\n{r['body']}\n{r['href']}"
                for i, r in enumerate(sources)
            )
            prompt = (
                "Answer the question using the search results below. "
                "Cite sources like [1], [2]. If the results don't help, say so.\n\n"
                f"Search results:\n{context}\n\nQuestion: {question}"
            )

    def stream():
        for chunk in ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        ):
            yield chunk["message"]["content"]

    with st.chat_message("assistant"):
        answer = st.write_stream(stream())
        if sources:
            with st.expander("Sources"):
                for i, r in enumerate(sources):
                    st.markdown(f"[{i+1}] [{r['title']}]({r['href']})")

    st.session_state.history.append({"role": "assistant", "content": answer})
