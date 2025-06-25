# Quran Chatbot 📖🤖

An Arabic Question-Answering assistant specialised in *Qur'anic linguistics*.  
Ask in Arabic about meanings, frequencies, roots, semantic differences, and the bot will answer with concise, well-sourced information.

## Key Features

- **Arabic in / Arabic out** – full right-to-left (RTL) support.
- **5-stage QA pipeline** (classification → entity extraction → context retrieval → prompt building → LLM answer).
- **Word / root frequency** and **ayah extraction** with zero-hallucination guarantees.
- **Lightweight** – no database; all resources are local JSONL files (< 200 KB total).
- **Dual UI** – command-line interface **and** Streamlit web app with real-time status trace.
- **Auto-generated technical report** (`generate_tech_report.py`) for reproducible documentation.

---

## Prerequisites

1. **Python 3.9+** (3.11 recommended).
2. An **OpenAI API key** (`OPENAI_API_KEY`).
3. (Optional) [Graphviz](https://graphviz.org/) in your `PATH` – enables pipeline diagrams in the tech report.

---

## Quick Start

```bash
# 1 — Clone
$ git clone https://github.com/YOUR_USERNAME/quran_chatbot.git
$ cd quran_chatbot

# 2 — Create & activate a virtual env (recommended)
$ python -m venv .venv
$ source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3 — Install deps
$ pip install -r requirements.txt

# 4 — Configure secrets (.env)
$ echo "OPENAI_API_KEY=sk-…"  > .env
# (Optional overrides)
$ echo "QURAN_LLM_MODEL=gpt-4o-mini-2024-07-18" >> .env
$ echo "QURAN_LLM_TIMEOUT=30"                   >> .env
```

### Run from CLI

```bash
# Example: How many times does the triliteral root سجد occur?
$ python main.py "كم مرة ورد جذر سجد في القرآن؟"
```

### Run the Web App

```bash
$ streamlit run app.py
```
Then open http://localhost:8501 and chat in Arabic.  
The sidebar shows a live, coloured log of the five pipeline stages.

---

## Generating the Technical Report

The repository can produce a 15-page DOCX report (with architecture diagrams):

```bash
$ python generate_tech_report.py 
# Output → reports/Quran_Chatbot_Technical_Report.docx (and /images/*.png)
```

If Graphviz is unavailable the script still works – diagrams are just skipped.

---

## Repository Layout

```
quran_chatbot/
├── main.py               # Thin CLI wrapper
├── app.py                # Streamlit UI (real-time status)
├── pipeline/             # 5-stage orchestration
│   ├── __init__.py       # QuranQAPipeline class
│   ├── classifier.py     # Stage 1
│   ├── extractor.py      # Stage 2
│   ├── retrieval_*.py    # Stage 3 helpers
│   └── prompt_builder.py # Stage 4
├── services/             # Out-of-pipeline helpers
│   ├── llm.py            # OpenAI wrapper
│   └── extractors/…      # Regex + LLM entity extractors
├── utils/                # Arabic normalisation, etc.
├── data/                 # Small JSONL corpora
└── generate_tech_report.py
```

---

## Configuration Reference

| Env var | Default | Purpose |
|---------|---------|---------|
| `OPENAI_API_KEY` | – | Access token for ChatCompletion. |
| `QURAN_LLM_MODEL` | `gpt-4o-mini-2024-07-18` | Override model name. |
| `QURAN_LLM_TIMEOUT` | `30` | Per-request timeout (seconds). |

These can be set in your shell or a `.env` file (auto-loaded).

---

## Contributing

Pull Requests are welcome — especially for:

* Expanding the regex extractor for more Arabic patterns.
* Adding new retrievers or local LLM back-ends.
* Translating the README to Arabic.

Please open an issue first to discuss significant changes.

---

## License

[MIT](LICENSE) © 2024 Your Name 