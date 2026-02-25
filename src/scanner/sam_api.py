"""
SAM.gov Official Public API Client

Uses the official api.sam.gov endpoints for reliable, rate-limited access.
Docs: https://open.gsa.gov/api/get-opportunities-public-api/

Environment:
    SAM_API_KEY: Your api.sam.gov API key (register at https://sam.gov/content/entity-registration)
"""

import os
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SAM_API_BASE = "https://api.sam.gov/opportunities/v2/search"

# Rate limit: 10 requests per second (official limit)
_RATE_LIMIT_DELAY = 0.15  # 150ms between requests for safety


def _get_api_key() -> Optional[str]:
    """Get SAM.gov API key from environment."""
    return os.environ.get("SAM_API_KEY")


def _get_session() -> requests.Session:
    """Create a session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session = _get_session()
_last_request_time = 0.0


def _rate_limited_get(url: str, params: dict, headers: dict, timeout: int = 30) -> Optional[requests.Response]:
    """Make a rate-limited GET request."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _RATE_LIMIT_DELAY:
        time.sleep(_RATE_LIMIT_DELAY - elapsed)
    _last_request_time = time.time()
    try:
        return _session.get(url, params=params, headers=headers, timeout=timeout)
    except Exception as e:
        print(f"  [ERROR] API request failed: {e}")
        return None


def search_opportunities(
    keyword: str = "",
    naics_codes: list[str] = None,
    psc_codes: list[str] = None,
    set_aside: str = "",
    notice_type: str = "",
    posted_from: str = "",
    posted_to: str = "",
    response_deadline_from: str = "",
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "-modifiedDate",
    active_only: bool = True,
) -> dict:
    """
    Search SAM.gov opportunities using the official API.

    Args:
        keyword: Search keyword(s)
        naics_codes: List of NAICS codes to filter
        psc_codes: List of PSC codes to filter
        set_aside: Set-aside type filter (e.g., "SDVOSB", "SBA")
        notice_type: Notice type filter (e.g., "s" for solicitation, "r" for sources sought)
        posted_from: Start date for posting (MM/dd/yyyy)
        posted_to: End date for posting (MM/dd/yyyy)
        response_deadline_from: Minimum response deadline (MM/dd/yyyy)
        limit: Max results per page (max 1000)
        offset: Pagination offset
        sort_by: Sort field
        active_only: Only return active opportunities

    Returns:
        dict with 'opportunities' list and 'totalRecords' count
    """
    api_key = _get_api_key()
    if not api_key:
        return {"opportunities": [], "totalRecords": 0, "error": "SAM_API_KEY not set"}

    params = {
        "api_key": api_key,
        "limit": str(min(limit, 1000)),
        "offset": str(offset),
    }

    if keyword:
        params["keyword"] = keyword
    if naics_codes:
        params["ncode"] = ",".join(naics_codes)
    if psc_codes:
        params["ptype"] = ",".join(psc_codes)
    if set_aside:
        params["typeOfSetAside"] = set_aside
    if notice_type:
        params["ptype"] = notice_type
    if posted_from:
        params["postedFrom"] = posted_from
    if posted_to:
        params["postedTo"] = posted_to
    if response_deadline_from:
        params["rdlfrom"] = response_deadline_from
    if active_only:
        params["status"] = "active"

    headers = {"Accept": "application/json"}

    resp = _rate_limited_get(SAM_API_BASE, params=params, headers=headers)
    if resp is None:
        return {"opportunities": [], "totalRecords": 0, "error": "Request failed"}

    if resp.status_code == 200:
        data = resp.json()
        return {
            "opportunities": data.get("opportunitiesData", []),
            "totalRecords": data.get("totalRecords", 0),
        }
    elif resp.status_code == 403:
        return {"opportunities": [], "totalRecords": 0, "error": "Invalid API key"}
    elif resp.status_code == 429:
        print("  [WARN] Rate limited. Waiting 60s...")
        time.sleep(60)
        return search_opportunities(
            keyword=keyword, naics_codes=naics_codes, psc_codes=psc_codes,
            set_aside=set_aside, notice_type=notice_type,
            posted_from=posted_from, posted_to=posted_to,
            limit=limit, offset=offset, sort_by=sort_by, active_only=active_only,
        )
    else:
        return {
            "opportunities": [],
            "totalRecords": 0,
            "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
        }


def get_opportunity_by_id(notice_id: str) -> Optional[dict]:
    """Fetch a single opportunity by notice ID."""
    api_key = _get_api_key()
    if not api_key:
        return None

    url = f"https://api.sam.gov/opportunities/v2/search"
    params = {
        "api_key": api_key,
        "noticeid": notice_id,
        "limit": "1",
    }
    headers = {"Accept": "application/json"}

    resp = _rate_limited_get(url, params=params, headers=headers)
    if resp and resp.status_code == 200:
        data = resp.json()
        opps = data.get("opportunitiesData", [])
        return opps[0] if opps else None
    return None


def parse_official_api_result(raw: dict) -> dict:
    """
    Parse an opportunity from the official SAM.gov API into our standardized format.
    The official API has different field names than the internal API.
    """
    now = datetime.now(timezone.utc).isoformat()

    notice_id = raw.get("solicitationNumber", "") or raw.get("noticeId", "")
    title = raw.get("title", "")
    description = raw.get("description", "")

    # Organization hierarchy
    org = raw.get("fullParentPathName", "")
    department = raw.get("departmentName", "") or (org.split(".")[0] if org else "")
    sub_tier = raw.get("subtierName", "") or raw.get("organizationName", "")
    office = raw.get("officeName", "") or raw.get("office", "")

    # Dates
    response_date = raw.get("responseDeadLine", "") or raw.get("archiveDate", "")
    published_date = raw.get("postedDate", "")
    modified_date = raw.get("modifiedDate", "")

    # Classification
    notice_type = raw.get("type", "") or raw.get("noticeType", "")
    set_aside = raw.get("typeOfSetAsideDescription", "") or raw.get("typeOfSetAside", "None")
    naics_code = raw.get("naicsCode", "")
    psc_code = raw.get("classificationCode", "")

    # Contact
    contacts = []
    poc_list = raw.get("pointOfContact", [])
    if isinstance(poc_list, list):
        for c in poc_list:
            contacts.append({
                "name": c.get("fullName", "") or f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
                "email": c.get("email", ""),
                "phone": c.get("phone", ""),
                "type": c.get("type", "primary"),
            })

    # URL
    ui_link = raw.get("uiLink", "")
    sam_url = ui_link if ui_link else f"https://sam.gov/opp/{notice_id}/view"

    # Place of performance
    pop = raw.get("placeOfPerformance", {})
    pop_parts = []
    if isinstance(pop, dict):
        city = pop.get("city", {})
        if isinstance(city, dict):
            pop_parts.append(city.get("name", ""))
        elif isinstance(city, str):
            pop_parts.append(city)
        state = pop.get("state", {})
        if isinstance(state, dict):
            pop_parts.append(state.get("name", ""))
        elif isinstance(state, str):
            pop_parts.append(state)
        country = pop.get("country", {})
        if isinstance(country, dict):
            pop_parts.append(country.get("name", ""))
    place_of_performance = ", ".join(p for p in pop_parts if p)

    # Award info
    award = raw.get("award", {}) or {}
    estimated_value = award.get("amount", "") or raw.get("estimatedValue", "")

    # Attachments / resource links
    attachments = []
    for link in raw.get("resourceLinks", []):
        if isinstance(link, str):
            attachments.append({"name": link.split("/")[-1], "url": link, "type": ""})

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
        "opp_id": notice_id,
        "raw_data": raw,
        "fit_score": 0,
        "fit_rationale": "",
        "recommendation_status": "unscored",
        "recommendation_date": "",
        "proposal_status": "not_started",
    }


def search_sdvosb_ai_opportunities(
    days_back: int = 30,
    limit: int = 100,
) -> list[dict]:
    """
    Convenience function: Search for SDVOSB-eligible AI/ML opportunities
    posted in the last N days.
    """
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y")
    to_date = datetime.now().strftime("%m/%d/%Y")

    all_results = []
    seen_ids = set()

    # Search with key AI/ML keywords
    keywords = [
        "artificial intelligence",
        "machine learning",
        "data science",
        "software development AI",
    ]

    for kw in keywords:
        result = search_opportunities(
            keyword=kw,
            posted_from=from_date,
            posted_to=to_date,
            limit=limit,
            active_only=True,
        )

        if "error" in result and result["error"]:
            print(f"  [WARN] Search error for '{kw}': {result['error']}")
            continue

        for raw in result["opportunities"]:
            parsed = parse_official_api_result(raw)
            nid = parsed["notice_id"]
            if nid and nid not in seen_ids:
                seen_ids.add(nid)
                all_results.append(parsed)

    return all_results


if __name__ == "__main__":
    # Quick test
    api_key = _get_api_key()
    if api_key:
        print("Testing SAM.gov Official API...")
        results = search_sdvosb_ai_opportunities(days_back=7, limit=10)
        print(f"Found {len(results)} opportunities")
        for r in results[:3]:
            print(f"  [{r['notice_type']}] {r['notice_id']}: {r['title'][:80]}")
    else:
        print("SAM_API_KEY not set. Set it to use the official API.")
        print("Register at: https://sam.gov/content/entity-registration")
