"""
SAM.gov Opportunity Scanner Engine

Scans SAM.gov for active contract opportunities matching configured search criteria.
Implements deduplication logic to avoid recommending the same opportunity repeatedly.
Stores all results with full detail and timestamps.
"""

import json
import os
import re
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.db import OpportunityDB
from src.scanner.scoring import score_opportunity


# ---------------------------------------------------------------------------
# SAM.gov search URL builder
# ---------------------------------------------------------------------------

SAM_SEARCH_BASE = "https://sam.gov/search/"
SAM_OPP_BASE = "https://sam.gov/opp/"

# SAM.gov public search API (undocumented but functional)
SAM_API_SEARCH = "https://sam.gov/api/prod/sgs/v1/search/"
SAM_API_OPP = "https://sam.gov/api/prod/opps/v1/by-opp-id/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://sam.gov/search/",
}


def load_config() -> dict:
    """Load the search profile configuration."""
    config_path = PROJECT_ROOT / "config" / "profile.json"
    with open(config_path, "r") as f:
        return json.load(f)


def build_search_url(keyword: str, page: int = 1, page_size: int = 25) -> str:
    """Build a SAM.gov search URL for a given keyword."""
    params = {
        "index": "opp",
        "page": str(page),
        "pageSize": str(page_size),
        "sort": "-modifiedDate",
        "sfm[status][is_active]": "true",
        "sfm[simpleSearch][keywordRadio]": "ALL",
        "sfm[simpleSearch][keywordTags][0][key]": keyword,
        "sfm[simpleSearch][keywordTags][0][value]": keyword,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{SAM_SEARCH_BASE}?{query}"


def build_api_search_params(keyword: str, page: int = 0, size: int = 25) -> dict:
    """Build params for the SAM.gov internal search API."""
    return {
        "index": "opp",
        "q": keyword,
        "qMode": "ALL",
        "status": "active",
        "sort": "-modifiedDate",
        "page": str(page),
        "size": str(size),
        "mode": "search",
        "is_active": "true",
    }


def search_sam_api(keyword: str, page: int = 0, size: int = 25) -> list[dict]:
    """
    Search SAM.gov using the internal API endpoint.
    Returns a list of raw opportunity dicts from the API response.
    """
    params = build_api_search_params(keyword, page, size)
    try:
        resp = requests.get(SAM_API_SEARCH, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # The API nests results under _embedded.results or similar
            if isinstance(data, dict):
                results = data.get("_embedded", {}).get("results", [])
                if not results:
                    results = data.get("opportunityList", [])
                if not results:
                    results = data.get("results", [])
                return results
        return []
    except Exception as e:
        print(f"  [WARN] API search failed for '{keyword}': {e}")
        return []


def fetch_opportunity_detail_api(opp_id: str) -> Optional[dict]:
    """Fetch full opportunity details from SAM.gov API."""
    try:
        url = f"{SAM_API_OPP}{opp_id}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"  [WARN] Detail fetch failed for {opp_id}: {e}")
    return None


def parse_search_result(raw: dict) -> dict:
    """
    Parse a raw search result from the SAM.gov API into our standardized format.
    Handles multiple possible API response structures.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Try multiple field name patterns (SAM.gov API is inconsistent)
    notice_id = (
        raw.get("noticeId")
        or raw.get("solicitationNumber")
        or raw.get("_id", "")
    )
    title = raw.get("title") or raw.get("subject") or ""
    description = raw.get("description") or raw.get("descriptionText") or ""

    # Agency info
    department = raw.get("departmentName") or raw.get("department", "")
    sub_tier = raw.get("subtierName") or raw.get("subtier", "")
    office = raw.get("officeName") or raw.get("office", "")

    # Dates
    response_date = raw.get("responseDate") or raw.get("responseDateStr") or ""
    published_date = raw.get("publishDate") or raw.get("postedDate") or ""
    modified_date = raw.get("modifiedDate") or raw.get("lastModifiedDate") or ""

    # Classification
    notice_type = raw.get("type") or raw.get("noticeType") or ""
    set_aside = raw.get("setAside") or raw.get("typeOfSetAside") or "None"
    naics_code = raw.get("naicsCode") or raw.get("naics", "")
    psc_code = raw.get("pscCode") or raw.get("classificationCode", "")

    # Contact
    contacts = []
    poc = raw.get("pointOfContact") or raw.get("poc") or []
    if isinstance(poc, list):
        for c in poc:
            contacts.append({
                "name": c.get("fullName", ""),
                "email": c.get("email", ""),
                "phone": c.get("phone", ""),
                "type": c.get("type", "primary"),
            })
    elif isinstance(poc, dict):
        contacts.append({
            "name": poc.get("fullName", ""),
            "email": poc.get("email", ""),
            "phone": poc.get("phone", ""),
            "type": "primary",
        })

    # URL
    opp_id = raw.get("_id") or raw.get("opportunityId") or ""
    sam_url = f"https://sam.gov/opp/{opp_id}/view" if opp_id else ""

    # Estimated value
    award_info = raw.get("award") or {}
    estimated_value = award_info.get("amount") or raw.get("estimatedValue") or ""

    # Attachments
    attachments = []
    for att in raw.get("attachments", []):
        attachments.append({
            "name": att.get("name", ""),
            "url": att.get("url", ""),
            "type": att.get("mimeType", ""),
        })

    # Place of performance
    pop = raw.get("placeOfPerformance") or {}
    place_of_performance = ""
    if isinstance(pop, dict):
        parts = [pop.get("city", ""), pop.get("state", ""), pop.get("country", "")]
        place_of_performance = ", ".join(p for p in parts if p)

    return {
        "notice_id": notice_id,
        "title": title,
        "description": description,
        "scan_timestamp": now,
        "first_seen": now,
        "last_updated": modified_date or now,
        "status": "active",
        "agency": sub_tier or department,
        "department": department,
        "sub_tier": sub_tier,
        "office": office,
        "notice_type": notice_type,
        "set_aside": set_aside if set_aside else "None",
        "naics_code": str(naics_code),
        "psc_code": str(psc_code),
        "response_date": response_date,
        "published_date": published_date,
        "modified_date": modified_date,
        "place_of_performance": place_of_performance,
        "estimated_value": str(estimated_value) if estimated_value else "",
        "contacts": contacts,
        "attachments": attachments,
        "sam_url": sam_url,
        "opp_id": opp_id,
        "raw_data": raw,
        "fit_score": 0,
        "fit_rationale": "",
        "recommendation_status": "unscored",
        "recommendation_date": "",
        "proposal_status": "not_started",
    }


def run_scan(config: Optional[dict] = None, verbose: bool = True) -> list[dict]:
    """
    Execute a full scan across all configured keywords.
    Returns a list of parsed, scored, and deduplicated opportunities.
    """
    if config is None:
        config = load_config()

    db = OpportunityDB()
    keywords = config["search"]["keywords"]
    all_results = []
    seen_notice_ids = set()

    if verbose:
        print(f"[{datetime.now().isoformat()}] Starting SAM.gov scan...")
        print(f"  Keywords: {keywords}")

    for keyword in keywords:
        if verbose:
            print(f"\n  Scanning keyword: '{keyword}'...")

        # Try API search first
        raw_results = search_sam_api(keyword, page=0, size=100)

        if verbose:
            print(f"    Found {len(raw_results)} results via API")

        for raw in raw_results:
            parsed = parse_search_result(raw)
            nid = parsed["notice_id"]

            # Skip if no notice ID
            if not nid:
                continue

            # Deduplicate within this scan
            if nid in seen_notice_ids:
                continue
            seen_notice_ids.add(nid)

            # Score the opportunity
            parsed["fit_score"], parsed["fit_rationale"] = score_opportunity(
                parsed, config
            )

            all_results.append(parsed)

    if verbose:
        print(f"\n  Total unique opportunities found: {len(all_results)}")

    # Store all results
    new_count, updated_count = db.upsert_opportunities(all_results)

    if verbose:
        print(f"  New opportunities: {new_count}")
        print(f"  Updated opportunities: {updated_count}")

    # Get recommendations (new or updated, above threshold, not recently recommended)
    recommendations = db.get_recommendations(
        min_score=config["scoring"]["thresholds"]["recommend"],
        max_results=config["recommendations"]["max_per_day"],
        cooldown_days=config["recommendations"]["cooldown_days"],
    )

    if verbose:
        print(f"\n  Today's recommendations ({len(recommendations)}):")
        for rec in recommendations:
            print(f"    [{rec['fit_score']}] {rec['notice_id']}: {rec['title'][:80]}")

    return recommendations


def run_scan_and_save(verbose: bool = True) -> dict:
    """
    Run a full scan, save results, and return a summary.
    This is the main entry point for the scheduled daily scan.
    """
    config = load_config()
    recommendations = run_scan(config, verbose)

    # Save today's recommendations
    today = datetime.now().strftime("%Y-%m-%d")
    rec_dir = PROJECT_ROOT / "data" / "recommendations"
    rec_dir.mkdir(parents=True, exist_ok=True)
    rec_file = rec_dir / f"recommendations_{today}.json"

    with open(rec_file, "w") as f:
        # Remove raw_data for the recommendation file (too large)
        clean_recs = []
        for r in recommendations:
            clean = {k: v for k, v in r.items() if k != "raw_data"}
            clean_recs.append(clean)
        json.dump(clean_recs, f, indent=2, default=str)

    summary = {
        "scan_date": today,
        "total_recommendations": len(recommendations),
        "recommendations": [
            {
                "notice_id": r["notice_id"],
                "title": r["title"],
                "agency": r["agency"],
                "fit_score": r["fit_score"],
                "response_date": r["response_date"],
                "sam_url": r["sam_url"],
            }
            for r in recommendations
        ],
    }

    if verbose:
        print(f"\n  Recommendations saved to: {rec_file}")
        print(f"  Scan complete.")

    return summary


if __name__ == "__main__":
    summary = run_scan_and_save(verbose=True)
    print(json.dumps(summary, indent=2, default=str))
