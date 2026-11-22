import os
import streamlit as st
from job_fetcher import get_live_jobs
from rag_engine import build_vector_store, recommend_jobs

# Load Streamlit Cloud Secrets if deployed
for key in ("GROQ_API_KEY", "ADZUNA_APP_ID", "ADZUNA_APP_KEY"):
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

st.set_page_config(page_title="SkillBridge RAG", page_icon="💼")
st.title("💼 SkillBridge RAG")
st.write("Enter your skills to find matching live tech jobs with direct apply links.")


@st.cache_resource(show_spinner="Indexing live tech jobs...")
def load_rag():
    jobs, status = get_live_jobs()
    return jobs, build_vector_store(jobs), status


jobs, vector_store, source_msg = load_rag()

skills = st.text_input(
    "Your Skills",
    value="Python, Machine Learning, LangChain, FastAPI, SQL",
    placeholder="e.g., Python, PyTorch, SQL, React",
)

if st.button("Find Matching Jobs", type="primary"):
    if not skills.strip():
        st.warning("Please enter at least one skill.")
    else:
        with st.spinner("Finding best job matches..."):
            st.caption(f"Searched {len(jobs)} live jobs • {source_msg}")
            st.markdown(recommend_jobs(skills.strip(), vector_store, top_k=4))

with st.expander("📋 Browse All Indexed Live Jobs"):
    for i, job in enumerate(jobs, 1):
        st.markdown(f"**{i}. {job['title']}** — {job['company']} ({job['location']}) • [Apply Here]({job['apply_link']})")