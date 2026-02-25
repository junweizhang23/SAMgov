"""
Opportunity Scoring Engine

Scores each opportunity based on configurable criteria:
- Technical fit (keyword matching in title/description)
- Agency preference
- Set-aside match (SDVOSB, small business)
- Contract size fit
- Deadline feasibility
- Notice type preference
- NAICS code match
"""

import re
from datetime import datetime, timezone
import time
from typing import Tuple


def score_opportunity(opp: dict, config: dict) -> Tuple[int, str]:
    """
    Score an opportunity on a 0-100 scale based on the configured profile.
    Returns (score, rationale_string).
    """
    weights = config["scoring"]["weights"]
    owner = config["owner"]
    search = config["search"]
    rationale_parts = []

    # -----------------------------------------------------------------------
    # 1. Technical Fit (0-100, weighted)
    # -----------------------------------------------------------------------
    tech_score = _score_technical_fit(opp, search["keywords"], search["exclude_keywords"])
    rationale_parts.append(f"Technical fit: {tech_score}/100")

    # -----------------------------------------------------------------------
    # 2. Agency Preference (0-100, weighted)
    # -----------------------------------------------------------------------
    agency_score = _score_agency(opp, search["preferred_agencies"])
    rationale_parts.append(f"Agency: {agency_score}/100")

    # -----------------------------------------------------------------------
    # 3. Set-Aside Match (0-100, weighted)
    # -----------------------------------------------------------------------
    setaside_score = _score_set_aside(opp, search["preferred_set_asides"])
    rationale_parts.append(f"Set-aside: {setaside_score}/100")

    # -----------------------------------------------------------------------
    # 4. Contract Size Fit (0-100, weighted)
    # -----------------------------------------------------------------------
    size_score = _score_contract_size(opp, owner)
    rationale_parts.append(f"Size fit: {size_score}/100")

    # -----------------------------------------------------------------------
    # 5. Deadline Feasibility (0-100, weighted)
    # -----------------------------------------------------------------------
    deadline_score = _score_deadline(opp)
    rationale_parts.append(f"Deadline: {deadline_score}/100")

    # -----------------------------------------------------------------------
    # 6. Notice Type Preference (0-100, weighted)
    # -----------------------------------------------------------------------
    type_score = _score_notice_type(opp, search["notice_types"])
    rationale_parts.append(f"Notice type: {type_score}/100")

    # -----------------------------------------------------------------------
    # 7. NAICS Match (0-100, weighted)
    # -----------------------------------------------------------------------
    naics_score = _score_naics(opp, search["naics_codes"])
    rationale_parts.append(f"NAICS: {naics_score}/100")

    # -----------------------------------------------------------------------
    # Weighted total
    # -----------------------------------------------------------------------
    total = (
        tech_score * weights["technical_fit"]
        + agency_score * weights["agency_preference"]
        + setaside_score * weights["set_aside_match"]
        + size_score * weights["contract_size_fit"]
        + deadline_score * weights["deadline_feasibility"]
        + type_score * weights["notice_type_preference"]
        + naics_score * weights["naics_match"]
    )

    final_score = min(100, max(0, round(total)))
    rationale = f"Score {final_score}/100 — " + "; ".join(rationale_parts)

    return final_score, rationale


def _score_technical_fit(opp: dict, keywords: list, exclude_kw: list) -> int:
    """Score based on keyword presence in title and description."""
    text = (opp.get("title", "") + " " + opp.get("description", "")).lower()

    # Check for exclusion keywords first
    for ex in exclude_kw:
        if ex.lower() in text:
            return 10  # Heavily penalize excluded topics

    # Count keyword matches
    matches = 0
    for kw in keywords:
        if kw.lower() in text:
            matches += 1

    if matches == 0:
        return 20  # Some base score since it appeared in search
    elif matches == 1:
        return 50
    elif matches == 2:
        return 70
    elif matches >= 3:
        return 90
    return 20


def _score_agency(opp: dict, preferred: list) -> int:
    """Score based on agency preference."""
    agency_text = (
        opp.get("department", "") + " " +
        opp.get("sub_tier", "") + " " +
        opp.get("office", "")
    ).upper()

    for pref in preferred:
        if pref.upper() in agency_text:
            return 100

    # DoD in general gets a decent score
    if "DEFENSE" in agency_text or "DOD" in agency_text:
        return 70

    # Other federal agencies
    return 40


def _score_set_aside(opp: dict, preferred: list) -> int:
    """Score based on set-aside status."""
    sa = opp.get("set_aside", "").upper()

    if not sa or sa == "NONE" or sa == "(BLANK)":
        return 50  # Open competition — neutral

    for pref in preferred:
        if pref.upper() in sa:
            return 100  # Direct match

    # Some set-aside but not ours
    return 30


def _score_contract_size(opp: dict, owner: dict) -> int:
    """Score based on estimated contract value."""
    value_str = opp.get("estimated_value", "")
    if not value_str:
        return 60  # Unknown — neutral-positive

    # Extract numeric value
    try:
        cleaned = re.sub(r"[^\d.]", "", str(value_str))
        if not cleaned:
            return 60
        value = float(cleaned)
    except (ValueError, TypeError):
        return 60

    min_val = owner.get("target_contract_size_min", 100000)
    max_val = owner.get("target_contract_size_max", 5000000)

    if min_val <= value <= max_val:
        return 100  # Perfect fit
    elif value < min_val:
        return 40  # Too small
    elif value <= max_val * 2:
        return 60  # Slightly large but manageable
    else:
        return 20  # Way too large for solo/small team


def _score_deadline(opp: dict) -> int:
    """Score based on how much time remains before the deadline."""
    response_date = opp.get("response_date", "")
    if not response_date:
        return 70  # No deadline — probably open/BAA

    try:
        # Try multiple date formats
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%b %d, %Y",
            "%B %d, %Y",
        ]:
            try:
                deadline = datetime.strptime(response_date[:19], fmt)
                break
            except ValueError:
                continue
        else:
            return 60  # Can't parse — neutral

        now = datetime.now(timezone.utc)
        # Make deadline timezone-aware if it isn't
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        days_left = (deadline - now).days

        if days_left < 0:
            return 0  # Expired
        elif days_left < 3:
            return 20  # Very tight
        elif days_left < 7:
            return 40  # Tight
        elif days_left < 14:
            return 60  # Manageable
        elif days_left < 30:
            return 80  # Comfortable
        elif days_left < 90:
            return 100  # Plenty of time
        else:
            return 90  # Very far out
    except Exception:
        return 60


def _score_notice_type(opp: dict, preferred_types: list) -> int:
    """Score based on notice type."""
    nt = opp.get("notice_type", "").lower()

    type_scores = {
        "solicitation": 100,
        "combined synopsis/solicitation": 95,
        "presolicitation": 80,
        "sources sought": 70,
        "special notice": 60,
        "award notice": 20,
        "intent to bundle": 30,
    }

    for key, score in type_scores.items():
        if key in nt:
            return score

    return 50  # Unknown type


def _score_naics(opp: dict, preferred_naics: list) -> int:
    """Score based on NAICS code match."""
    naics = str(opp.get("naics_code", "")).strip()

    if not naics or naics == "(blank)":
        return 50  # Unknown — neutral

    # Exact match
    if naics in preferred_naics:
        return 100

    # Prefix match (same industry group)
    for pref in preferred_naics:
        if naics[:4] == pref[:4]:
            return 80
        if naics[:3] == pref[:3]:
            return 60

    return 30  # No match
