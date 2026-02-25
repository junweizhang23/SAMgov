"""
Proposal Generator

Auto-generates draft proposal outlines and TODO lists based on opportunity details.
Uses OpenAI-compatible API (gpt-4.1-mini) for intelligent proposal drafting.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.db import OpportunityDB

# OpenAI client setup (API key and base URL pre-configured via env)
try:
    from openai import OpenAI
    client = OpenAI()
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    client = None


OWNER_PROFILE = """
Alfred is the principal of an SDVOSB (Service-Disabled Veteran-Owned Small Business) with:
- PhD in Applied Mathematics with focus on AI/ML
- Extensive experience in software development, data analytics, and cloud computing
- Air Force Reserve officer background
- Enterprise-level product and growth experience
- IEEE reviewer and academic publication experience
- Currently at Meta with deep expertise in AI/ML systems
- Target: building reputation through successful small-to-medium government contract delivery
"""

PROPOSAL_SYSTEM_PROMPT = """You are an expert government contract proposal writer specializing in 
technology and AI/ML contracts for the U.S. Department of Defense. You help a Service-Disabled 
Veteran-Owned Small Business (SDVOSB) principal draft compelling, compliant proposal responses.

Your outputs must be:
1. Professional and compliant with federal acquisition standards
2. Technically detailed but accessible
3. Focused on demonstrating unique value and capability
4. Structured according to standard proposal sections
5. Actionable with clear next steps

Owner profile:
{owner_profile}
""".format(owner_profile=OWNER_PROFILE)


def generate_proposal_draft(
    opp: dict,
    custom_instructions: str = "",
) -> dict:
    """
    Generate a draft proposal outline and TODO list for an opportunity.
    
    Returns:
    {
        "proposal_outline": str (markdown),
        "todo_list": list[dict],
        "executive_summary_draft": str,
        "technical_approach_notes": str,
        "key_personnel_section": str,
        "generated_at": str,
    }
    """
    if not HAS_OPENAI or client is None:
        return _generate_template_proposal(opp)

    # Build the opportunity context
    opp_context = _format_opportunity_context(opp)

    # Generate proposal outline
    proposal_prompt = f"""Based on this government contract opportunity, generate a comprehensive 
proposal outline with draft content for an SDVOSB response.

OPPORTUNITY DETAILS:
{opp_context}

{f"ADDITIONAL INSTRUCTIONS: {custom_instructions}" if custom_instructions else ""}

Please provide:

1. **EXECUTIVE SUMMARY DRAFT** (2-3 paragraphs)
   - Opening hook connecting our capabilities to the requirement
   - Key differentiators (SDVOSB, AI/ML PhD expertise, veteran status)
   - Value proposition

2. **TECHNICAL APPROACH** (structured outline with key points)
   - Understanding of the problem
   - Proposed solution architecture
   - Innovation elements
   - Risk mitigation

3. **MANAGEMENT APPROACH** (brief outline)
   - Team structure
   - Quality assurance
   - Communication plan

4. **PAST PERFORMANCE** (talking points)
   - Relevant experience areas to highlight
   - How to frame Meta/industry experience for government context

5. **TODO LIST** with specific deadlines relative to the response date
   - Each item should have: task, deadline, priority (high/medium/low), notes

Format the entire response in Markdown."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": PROPOSAL_SYSTEM_PROMPT},
                {"role": "user", "content": proposal_prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        proposal_content = response.choices[0].message.content
    except Exception as e:
        print(f"  [WARN] OpenAI API call failed: {e}")
        return _generate_template_proposal(opp)

    # Generate TODO list separately for structured data
    todo_list = _generate_todo_list(opp)

    result = {
        "notice_id": opp.get("notice_id", ""),
        "title": opp.get("title", ""),
        "proposal_draft": proposal_content,
        "todo_list": todo_list,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_used": "gpt-4.1-mini",
    }

    # Save to file
    _save_proposal(result)

    return result


def _format_opportunity_context(opp: dict) -> str:
    """Format opportunity details into a context string for the LLM."""
    parts = [
        f"Notice ID: {opp.get('notice_id', 'N/A')}",
        f"Title: {opp.get('title', 'N/A')}",
        f"Agency: {opp.get('agency', 'N/A')}",
        f"Department: {opp.get('department', 'N/A')}",
        f"Office: {opp.get('office', 'N/A')}",
        f"Notice Type: {opp.get('notice_type', 'N/A')}",
        f"Set-Aside: {opp.get('set_aside', 'N/A')}",
        f"NAICS Code: {opp.get('naics_code', 'N/A')}",
        f"PSC Code: {opp.get('psc_code', 'N/A')}",
        f"Response Date: {opp.get('response_date', 'N/A')}",
        f"Estimated Value: {opp.get('estimated_value', 'N/A')}",
        f"Place of Performance: {opp.get('place_of_performance', 'N/A')}",
        f"SAM.gov URL: {opp.get('sam_url', 'N/A')}",
        f"\nDescription:\n{opp.get('description', 'No description available.')}",
    ]

    contacts = opp.get("contacts", [])
    if contacts:
        parts.append("\nContacts:")
        for c in contacts:
            parts.append(f"  - {c.get('name', '')} ({c.get('email', '')})")

    return "\n".join(parts)


def _generate_todo_list(opp: dict) -> list[dict]:
    """Generate a structured TODO list based on opportunity details."""
    response_date = opp.get("response_date", "")
    now = datetime.now(timezone.utc)

    # Calculate days until deadline
    days_left = 30  # default
    if response_date:
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y"]:
            try:
                deadline = datetime.strptime(response_date[:19], fmt)
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                days_left = max(1, (deadline - now).days)
                break
            except ValueError:
                continue

    notice_type = opp.get("notice_type", "").lower()

    todos = []

    # Common todos for all types
    todos.append({
        "task": "Download and review all attachments from SAM.gov notice",
        "deadline": "Day 1",
        "priority": "high",
        "status": "pending",
        "notes": f"SAM.gov URL: {opp.get('sam_url', '')}",
    })

    todos.append({
        "task": "Review the full solicitation/RFI document for requirements",
        "deadline": "Day 1-2",
        "priority": "high",
        "status": "pending",
        "notes": "Identify all mandatory sections and page limits",
    })

    if "solicitation" in notice_type or "combined" in notice_type:
        todos.extend([
            {
                "task": "Identify all mandatory proposal sections and compliance requirements",
                "deadline": f"Day 2",
                "priority": "high",
                "status": "pending",
                "notes": "Create compliance matrix",
            },
            {
                "task": "Draft Executive Summary",
                "deadline": f"Day {min(5, days_left // 3)}",
                "priority": "high",
                "status": "pending",
                "notes": "Focus on SDVOSB status and AI/ML expertise",
            },
            {
                "task": "Draft Technical Approach section",
                "deadline": f"Day {min(7, days_left // 2)}",
                "priority": "high",
                "status": "pending",
                "notes": "Emphasize innovative AI/ML solutions",
            },
            {
                "task": "Prepare Past Performance references",
                "deadline": f"Day {min(7, days_left // 2)}",
                "priority": "medium",
                "status": "pending",
                "notes": "Frame Meta/industry experience for government context",
            },
            {
                "task": "Draft Management Approach",
                "deadline": f"Day {min(10, days_left * 2 // 3)}",
                "priority": "medium",
                "status": "pending",
                "notes": "Include QA plan and communication approach",
            },
            {
                "task": "Prepare cost/price volume",
                "deadline": f"Day {min(12, days_left * 3 // 4)}",
                "priority": "high",
                "status": "pending",
                "notes": "Competitive pricing for SDVOSB",
            },
            {
                "task": "Internal review and compliance check",
                "deadline": f"Day {min(14, days_left - 3)}",
                "priority": "high",
                "status": "pending",
                "notes": "Verify all sections meet requirements",
            },
            {
                "task": "Submit proposal via SAM.gov",
                "deadline": f"Day {days_left} (DEADLINE)",
                "priority": "critical",
                "status": "pending",
                "notes": f"Response date: {response_date}",
            },
        ])
    elif "sources sought" in notice_type or "rfi" in notice_type:
        todos.extend([
            {
                "task": "Prepare capability statement highlighting AI/ML expertise",
                "deadline": f"Day {min(3, days_left // 2)}",
                "priority": "high",
                "status": "pending",
                "notes": "Include SDVOSB certification, NAICS codes, past projects",
            },
            {
                "task": "Draft response to specific RFI questions",
                "deadline": f"Day {min(5, days_left * 2 // 3)}",
                "priority": "high",
                "status": "pending",
                "notes": "Address each question directly",
            },
            {
                "task": "Submit RFI response",
                "deadline": f"Day {days_left} (DEADLINE)",
                "priority": "critical",
                "status": "pending",
                "notes": f"Response date: {response_date}",
            },
        ])

    # Contact outreach
    contacts = opp.get("contacts", [])
    if contacts:
        email = contacts[0].get("email", "")
        if email:
            todos.append({
                "task": f"Send introduction email to contracting officer ({email})",
                "deadline": "Day 1-2",
                "priority": "medium",
                "status": "pending",
                "notes": "Brief, professional intro highlighting SDVOSB and relevant capabilities",
            })

    return todos


def _generate_template_proposal(opp: dict) -> dict:
    """Fallback template-based proposal when OpenAI is not available."""
    notice_id = opp.get("notice_id", "N/A")
    title = opp.get("title", "N/A")
    agency = opp.get("agency", "N/A")

    template = f"""# Draft Proposal: {title}

## Notice ID: {notice_id}
## Agency: {agency}

---

## 1. Executive Summary

[DRAFT - To be customized]

We are pleased to submit this proposal in response to {notice_id}. As a Service-Disabled 
Veteran-Owned Small Business (SDVOSB) with deep expertise in artificial intelligence, 
machine learning, and software engineering, we are uniquely positioned to deliver 
innovative solutions that meet the requirements outlined in this solicitation.

Our principal investigator holds a PhD in Applied Mathematics with specialization in AI/ML 
and brings extensive experience from both the private sector (Meta) and military service 
(Air Force Reserve). This combination of academic rigor, industry-scale engineering 
experience, and understanding of DoD operations enables us to bridge the gap between 
cutting-edge AI research and practical government applications.

## 2. Technical Approach

[To be developed based on specific requirements]

### 2.1 Understanding of the Problem
### 2.2 Proposed Solution
### 2.3 Innovation Elements
### 2.4 Risk Mitigation

## 3. Management Approach

### 3.1 Team Structure
### 3.2 Quality Assurance
### 3.3 Communication Plan

## 4. Past Performance

### 4.1 Relevant Experience
### 4.2 Key Personnel

## 5. Cost/Price

[To be developed]

---

*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*
"""

    return {
        "notice_id": notice_id,
        "title": title,
        "proposal_draft": template,
        "todo_list": _generate_todo_list(opp),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_used": "template",
    }


def _save_proposal(result: dict):
    """Save proposal draft to file."""
    proposals_dir = PROJECT_ROOT / "data" / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)

    notice_id = result["notice_id"].replace("/", "_").replace("\\", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save full result as JSON
    json_path = proposals_dir / f"{notice_id}_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    # Save proposal draft as markdown
    md_path = proposals_dir / f"{notice_id}_{timestamp}.md"
    with open(md_path, "w") as f:
        f.write(result["proposal_draft"])

    print(f"  Proposal saved: {md_path}")


def generate_for_notice(notice_id: str, custom_instructions: str = "") -> dict:
    """Generate a proposal for a specific notice ID from the database."""
    db = OpportunityDB()
    opp = db.get_opportunity(notice_id)
    if not opp:
        raise ValueError(f"Opportunity not found: {notice_id}")

    result = generate_proposal_draft(opp, custom_instructions)

    # Update proposal status in DB
    db.update_proposal_status(notice_id, "draft_generated")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate proposal for a SAM.gov opportunity")
    parser.add_argument("--notice-id", required=True, help="Notice ID to generate proposal for")
    parser.add_argument("--instructions", default="", help="Custom instructions for the proposal")
    args = parser.parse_args()

    result = generate_for_notice(args.notice_id, args.instructions)
    print(f"\nProposal generated for: {result['title']}")
    print(f"TODO items: {len(result['todo_list'])}")
