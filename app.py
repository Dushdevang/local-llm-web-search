"""Local LLM web search assistant.

Pipeline: question -> web search -> build prompt with results -> local LLM (Ollama) -> cited answer.
"""
import ollama
import streamlit as st
from ddgs import DDGS

st.set_page_config(page_title="Local AI Web Search", page_icon="🔎")
st.title("🔎 Local AI with Web Search")
st.caption("Runs on your own machine with Ollama. Answers are grounded in live web results.")

# ---------- Sidebar ----------
try:
    models = [m.model for m in ollama.list().models]
except Exception:
    models = []
    st.sidebar.error("Cannot reach Ollama. Make sure it is running.")

model = st.sidebar.selectbox("Model", models) if models else None
use_web = st.sidebar.toggle("Search the web", value=True)
n_results = st.sidebar.slider("Number of results", 1, 8, 5)
if st.sidebar.button("Clear chat"):
    st.session_state.history = []
    st.rerun()

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def web_search(query: str, n: int) -> list[dict]:
    """Return up to n results as dicts with title, body, href. Empty list on failure."""
    try:
        return DDGS().text(query, max_results=n)
    except Exception:
        return []


def build_prompt(question: str, sources: list[dict]) -> str:
    """Put the search results and rules around the user's question."""
    context = "\n\n".join(
        f"[{i + 1}] {r['title']}\n{r['body']}\n{r['href']}"
        for i, r in enumerate(sources)
    )
    return (
        "Answer the question using the search results below. "
        "Cite sources like [1], [2]. If the results don't contain the answer, say so "
        "instead of guessing.\n\n"
        f"Search results:\n{context}\n\nQuestion: {question}"
    )


if question := st.chat_input("Ask anything...") if model else None:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    prompt, sources = question, []
    if use_web:
        with st.spinner("Searching the web..."):
            sources = web_search(question, n_results)
        if sources:
            prompt = build_prompt(question, sources)
        else:
            st.warning("No web results found. Answering from the model's own knowledge.")

    # Earlier turns give the model conversation memory; the last turn uses the search-augmented prompt.
    messages = st.session_state.history[:-1] + [{"role": "user", "content": prompt}]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        answer = ""
        try:
            for chunk in ollama.chat(model=model, messages=messages, stream=True):
                answer += chunk["message"]["content"]
                placeholder.markdown(answer + "▌")
        except Exception as e:
            answer = f"Model error: {e}"
        placeholder.markdown(answer)

        if sources:
            with st.expander("Sources"):
                for i, r in enumerate(sources):
                    st.markdown(f"[{i + 1}] [{r['title']}]({r['href']})")

    st.session_state.history.append({"role": "assistant", "content": answer})
