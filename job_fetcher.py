import os
import re
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CACHE_FILE = "jobs_cache.json"
BACKUP_FILE = "jobs_backup.json"
CACHE_EXPIRY_SECONDS = 12 * 3600  # 12 hours


def clean_html(raw_html: str) -> str:
    """Strips HTML tags and collapses extra whitespace from job descriptions."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_from_remotive() -> list[dict]:
    """Fetches live tech jobs from Remotive's free, keyless public API."""
    url = "https://remotive.com/api/remote-jobs?category=software-dev"
    resp = requests.get(url, timeout=12)
    resp.raise_for_status()
    data = resp.json().get("jobs", [])

    jobs = []
    for item in data[:25]:
        jobs.append({
            "title": item.get("title", "Software Engineer"),
            "company": item.get("company_name", "Unknown Company"),
            "location": item.get("candidate_required_location", "Remote"),
            "description": clean_html(item.get("description", ""))[:2000],
            "apply_link": item.get("url", ""),
            "source": "Remotive (Live)",
        })
    return jobs


def fetch_from_arbeitnow() -> list[dict]:
    """Fetches live tech jobs from Arbeitnow's free, keyless public API."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    resp = requests.get(url, timeout=12)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    jobs = []
    for item in data[:25]:
        jobs.append({
            "title": item.get("title", "Software Engineer"),
            "company": item.get("company_name", "Unknown Company"),
            "location": item.get("location", "Remote"),
            "description": clean_html(item.get("description", ""))[:2000],
            "apply_link": item.get("url", ""),
            "source": "Arbeitnow (Live)",
        })
    return jobs


def fetch_from_adzuna_india() -> list[dict]:
    """Optional Indian regional feed if ADZUNA_APP_ID and ADZUNA_APP_KEY are set."""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 20,
        "what": "software engineer ai machine learning data python",
        "content-type": "application/json",
    }
    resp = requests.get(url, params=params, timeout=12)
    resp.raise_for_status()
    data = resp.json().get("results", [])

    jobs = []
    for item in data:
        jobs.append({
            "title": item.get("title", "Software Engineer"),
            "company": item.get("company", {}).get("display_name", "Unknown Company"),
            "location": item.get("location", {}).get("display_name", "India"),
            "description": clean_html(item.get("description", ""))[:2000],
            "apply_link": item.get("redirect_url", ""),
            "source": "Adzuna India (Live)",
        })
    return jobs


def save_json(filepath: str, jobs: list[dict]) -> None:
    payload = {"timestamp": time.time(), "jobs": jobs}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_valid_cache(filepath: str, ignore_expiry: bool = False) -> list[dict]:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if ignore_expiry or (time.time() - payload.get("timestamp", 0) < CACHE_EXPIRY_SECONDS):
            return payload.get("jobs", [])
    except Exception:
        return []
    return []


def get_live_jobs(force_refresh: bool = False) -> tuple[list[dict], str]:
    """
    Returns (jobs_list, status_message):
    1. Reads 12-hour local cache unless force_refresh=True.
    2. Combines unlimited keyless APIs (Remotive + Arbeitnow) + optional Adzuna India.
    3. Deduplicates jobs by (title, company) before caching and indexing.
    4. Falls back to offline backup snapshot if network is unavailable.
    """
    if not force_refresh:
        cached_jobs = load_valid_cache(CACHE_FILE, ignore_expiry=False)
        if cached_jobs:
            return cached_jobs, f"Loaded {len(cached_jobs)} unique jobs from local 12-hr cache (0 API credits used)."

    combined_jobs = []
    sources_used = []

    # Layer 1: Unlimited keyless Remotive API
    try:
        remotive_jobs = fetch_from_remotive()
        if remotive_jobs:
            combined_jobs.extend(remotive_jobs)
            sources_used.append(f"Remotive ({len(remotive_jobs)})")
    except Exception:
        pass

    # Layer 2: Unlimited keyless Arbeitnow API
    try:
        arbeitnow_jobs = fetch_from_arbeitnow()
        if arbeitnow_jobs:
            combined_jobs.extend(arbeitnow_jobs)
            sources_used.append(f"Arbeitnow ({len(arbeitnow_jobs)})")
    except Exception:
        pass

    # Layer 3: Optional Adzuna India API (never crashes if quota runs out)
    try:
        adzuna_jobs = fetch_from_adzuna_india()
        if adzuna_jobs:
            combined_jobs.extend(adzuna_jobs)
            sources_used.append(f"Adzuna India ({len(adzuna_jobs)})")
    except Exception:
        pass

    if combined_jobs:
        seen = set()
        unique_jobs = []
        for job in combined_jobs:
            key = (job["title"].strip().lower(), job["company"].strip().lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        save_json(CACHE_FILE, unique_jobs)
        save_json(BACKUP_FILE, unique_jobs)
        msg = f"Fetched {len(unique_jobs)} unique live jobs from {' + '.join(sources_used)}!"
        return unique_jobs, msg

    # Layer 4: Offline backup fallback
    backup_jobs = load_valid_cache(BACKUP_FILE, ignore_expiry=True)
    if backup_jobs:
        return backup_jobs, f"Loaded {len(backup_jobs)} jobs from offline backup snapshot."

    return [], "Failed to fetch live jobs and no local cache/backup was found."


if __name__ == "__main__":
    jobs, status = get_live_jobs(force_refresh=True)
    print(status)
    if jobs:
        print(f"Sample job 1: {jobs[0]['title']} at {jobs[0]['company']} ({jobs[0]['source']})")
        print(f"Sample job last: {jobs[-1]['title']} at {jobs[-1]['company']} ({jobs[-1]['source']})")