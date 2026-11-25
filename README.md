# 💼 SkillBridge RAG — Live Tech Job Matcher & Skill-Gap Analyzer

A full-stack Retrieval-Augmented Generation (RAG) application that semantically matches a candidate's technical skills against live software and AI job openings, generating ranked recommendations, skill-gap analyses, and verified direct apply links.
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://skillbridge-rag-udt7nvjdydwjgvtrfvqzlg.streamlit.app/)

**Live Demo:** [https://skillbridge-rag-udt7nvjdydwjgvtrfvqzlg.streamlit.app/](https://skillbridge-rag-udt7nvjdydwjgvtrfvqzlg.streamlit.app/)

## 🏗️ Architecture & Tech Stack

* **Backend API (`app.py`):** FastAPI server with async `@asynccontextmanager` lifespan pre-loading, Pydantic request validation, and REST endpoints (`/health`, `/match`, `/refresh`, `/jobs`).
* **Frontend UI (`frontend.py`):** Clean, minimal Streamlit interface connected to the FastAPI backend with an expandable full-feed job browser.
* **RAG Engine (`rag_engine.py`):** LangChain Expression Language (`LCEL`) pipeline backed by an in-memory **FAISS** vector store, local HuggingFace embeddings (`sentence-transformers/all-MiniLM-L6-v2`), and **Groq** LLM inference with automatic active model discovery and caching.
* **Resilient Multi-Source Ingestion (`job_fetcher.py`):**
  * **Unlimited Keyless Live Feeds:** Aggregates and deduplicates live tech openings from **Remotive** and **Arbeitnow** APIs, with optional **Adzuna India** regional support.
  * **12-Hour Local JSON Cache (`jobs_cache.json`):** Serves repeated startups and refreshes instantaneously with zero redundant API calls.
  * **Offline Fallback (`jobs_backup.json`):** Guarantees uninterrupted operation even without internet access.

## 📂 Project Structure

```text
skillbridge-rag/
├── job_fetcher.py      # Multi-source live job aggregator, deduplicator, & 12-hr cache
├── rag_engine.py       # HuggingFace embeddings, FAISS indexing, & LangChain LCEL chain
├── app.py              # FastAPI backend server
├── frontend.py         # Streamlit frontend interface
├── jobs_backup.json    # Offline fallback job snapshot
├── requirements.txt    # Python dependencies
├── .gitignore          # Excludes .env, venv/, __pycache__/, and runtime cache
└── README.md           # Project documentation
