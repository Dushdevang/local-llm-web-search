# Local LLM Web Search Assistant

A private, offline-first AI assistant that answers questions using **live web results**, running a small open-source LLM entirely on your own machine. Built to work on a **4 GB VRAM** GPU.

![Demo screenshot](docs/screenshot.png)

## Why this exists

Language models only know their training data, so they cannot answer questions about recent events and may confidently invent answers. This project fixes that with **retrieval-augmented generation (RAG)**: the app searches the web first, gives the results to the model, and the model answers from that evidence with numbered citations you can click and verify.

## How it works

```
Question → Web search (DuckDuckGo) → Build prompt (question + top results + rules)
        → Ollama (local server) → Qwen2.5 3B (quantized) → Streamed answer + sources
```

1. **Retrieve:** the question is sent to a search engine and the top results (title, snippet, URL) are collected.
2. **Augment:** the results are numbered and inserted into a prompt that tells the model to answer only from them, cite as `[1]`, `[2]`, and admit when the results do not contain the answer.
3. **Generate:** Ollama runs the model on the local GPU and streams the answer token by token.
4. **Verify:** the sources are listed under each answer.

## Features

- Streamlit chat interface with streaming responses
- Cited answers with a clickable sources list
- Conversation memory across turns
- Toggle web search on or off, and choose how many results to use
- Switch between any model installed in Ollama
- Graceful handling of search failures and Ollama being offline
- Runs on 4 GB VRAM using a 4-bit quantized 3B model

## Tech stack

| Part | Tool |
|------|------|
| Model runtime | [Ollama](https://ollama.com) |
| Model | Qwen2.5 3B (Q4_K_M quantization) |
| Search | DuckDuckGo via the `ddgs` library |
| UI | Streamlit |
| Language | Python 3.10+ |

## Setup

### 1. Install Ollama and a model

Install Ollama from https://ollama.com, then either pull a ready model:

```bash
ollama pull qwen2.5:3b
```

or import your own GGUF file by placing it next to the `Modelfile` and running:

```bash
ollama create qwen-local -f Modelfile
```

### 2. Install and run the app

```bash
git clone https://github.com/YOUR-USERNAME/local-llm-web-search.git
cd local-llm-web-search
pip install -r requirements.txt
streamlit run app.py
```

Make sure Ollama is running, then pick your model in the sidebar and start asking.

## Design decisions

- **Fixed pipeline instead of model-driven tool calling.** Small models are unreliable at deciding when to call tools, so the app always searches. This is more predictable on limited hardware.
- **Snippets instead of full pages.** Full pages would overflow the model's context window and slow generation on a 4 GB GPU.
- **Quantized model.** Q4_K_M stores weights in about 4 bits, cutting memory use to roughly a quarter of full precision with a small quality loss.
- **Search is one swappable function.** `web_search()` is isolated, so DuckDuckGo can be replaced with SearXNG or a paid API without touching the rest of the code.
- **Manual streaming.** The app streams with a plain placeholder loop instead of `st.write_stream`, which avoids a pandas import that is blocked by some Windows application control policies.

## Limitations

- Answers are only as good as the search snippets, which can be short or incomplete.
- A 3B model can still misread or over-summarize sources, so check the citations.
- The raw question is used as the search query, which is not always optimal.
- `ddgs` scrapes results rather than using an official API, so it can be rate-limited or break.
- Web content is untrusted text placed into the prompt, so prompt injection is possible. The app has no tool access, which limits the impact.

## Roadmap

- [ ] SearXNG as a self-hosted search backend
- [ ] Rewrite the user question into a better search query before searching
- [ ] Fetch and extract full page text (e.g. with `trafilatura`)
- [ ] Model-driven tool calling with a larger model
- [ ] Evaluation set comparing answers with and without search

## Troubleshooting

- **"Cannot reach Ollama":** start the Ollama app and check that `ollama list` works.
- **Slow first answer:** the model is loading into VRAM; later answers are faster.
- **`DLL load failed ... Application Control policy`:** Windows is blocking a compiled library. Use Python 3.12 or 3.13 rather than a pre-release version, or ask your IT team to allow it.

## License

MIT, see [LICENSE](LICENSE).
