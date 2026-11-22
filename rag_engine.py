import os
import requests
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq

load_dotenv()

embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")

def build_vector_stores(jobs:list[dict]) -> FAISS:
    documents = []
    for job in jobs:
        content = (
            f"Job Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Description: {job['description']}"
        )
        metadata = {
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "apply_link": job["apply_link"],
        }
        documents.append(Document(page_content=content , metadata = metadata))
    vector_store =  FAISS.from_documents(documents , embeddings)
    return vector_store

def format_retrieved_jobs(docs:list[Document])->str:
    formatted = []
    for i , doc in enumerate(docs , 1):
        meta = doc.metadata
        formatted.append(
            f"--- JOB {i} ---\n"
            f"Title: {meta['title']}\n"
            f"Company: {meta['company']}\n"
            f"Location: {meta['location']}\n"
            f"Apply Link: {meta['apply_link']}\n"
            f"Details: {doc.page_content}\n"
        )
    return "\n".join(formatted)
_cached_model = None


def get_active_groq_model() -> str:
    """Finds the first chat model on your Groq API key that actually works, then caches it."""
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    candidates = [
        "openai/gpt-oss-120b",
        "qwen/qwen3-32b",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-20b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    ]
    for model_id in candidates:
        try:
            test_llm = ChatGroq(model=model_id, max_tokens=5, temperature=0)
            test_llm.invoke("hi")
            print(f"Using active Groq model: {model_id}")
            _cached_model = model_id
            return model_id
        except Exception:
            continue
    raise RuntimeError("None of the candidate Groq models worked. Check GROQ_API_KEY and model permissions in console.groq.com.")
def recommend_jobs(user_skills: str, vector_store: FAISS, top_k: int = 4) -> str:
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    retrieved_docs = retriever.invoke(user_skills)
    context = format_retrieved_jobs(retrieved_docs)

    prompt = ChatPromptTemplate.from_template(
        """You are a helpful career assistant. Based ONLY on the retrieved jobs below, evaluate and rank ALL retrieved jobs for the candidate's skills.

Candidate Skills:
{skills}

Retrieved Live Jobs:
{context}

Instructions:
- Evaluate and include ALL {count} distinct retrieved jobs in your response—do NOT skip or omit any job, even if it is only a partial match.
- Rank them from strongest match to weakest match.
- First, create a Markdown summary table with columns: #, Title, Company, Location, Match Level (Strong / Partial), and Apply Link.
- Then, for each job, list which of the candidate's skills match and which missing skills they should learn.
- Copy the exact Apply Link provided in the context. Never invent or modify URLs.
"""
    )
    model_name = get_active_groq_model()
    llm = ChatGroq(model=model_name, temperature=0.2)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "skills": user_skills,
        "context": context,
        "count": len(retrieved_docs),
    })
if __name__ == "__main__":
    from job_fetcher import get_live_jobs

    jobs, msg = get_live_jobs()
    print(msg)
    vs = build_vector_stores(jobs)
    print("FAISS index built! Matching skills...\n")
    output = recommend_jobs("Python, Data Engineering, Machine Learning, SQL", vs, top_k=3)
    print(output)
