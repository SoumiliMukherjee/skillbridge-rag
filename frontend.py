import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="SkillBridge RAG", page_icon="💼")
st.title("💼 SkillBridge RAG")
st.write("Enter your skills to find matching live tech jobs with direct apply links.")

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
            try:
                res = requests.post(
                    f"{API_URL}/match",
                    json={"skills": skills.strip(), "top_k": 4},
                    timeout=60,
                )
                res.raise_for_status()
                data = res.json()

                st.caption(f"Searched {data['jobs_searched']} live jobs • {data['source_message']}")
                st.markdown(data["recommendations"])
            except Exception as e:
                st.error(f"Could not connect to backend: {e}")

st.divider()

with st.expander("📋 Browse All Indexed Live Jobs"):
    try:
        jobs_res = requests.get(f"{API_URL}/jobs", timeout=10)
        jobs_res.raise_for_status()
        all_jobs = jobs_res.json().get("jobs", [])

        st.caption(f"Showing all {len(all_jobs)} indexed jobs:")
        for i, job in enumerate(all_jobs, 1):
            st.markdown(
                f"**{i}. {job['title']}** — {job['company']} ({job['location']}) • [Apply Here]({job['apply_link']})"
            )
    except Exception as e:
        st.error(f"Could not load job list: {e}")