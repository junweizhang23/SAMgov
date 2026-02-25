"""
SAMgov — Proposal Templates Library

Pre-built proposal templates for common government contract types.
Each template includes:
- Standard sections required by FAR (Federal Acquisition Regulation)
- SDVOSB-specific compliance language
- Alfred's capability matrix auto-populated
- Past performance narrative structure
- Cost/price volume framework

Templates are designed for:
1. SBIR/STTR (Small Business Innovation Research)
2. 8(a) Set-Aside contracts
3. SDVOSB sole-source (under $5M threshold)
4. Professional services (IT, AI/ML, data analytics)
5. Research & development contracts
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "templates"


# ---------------------------------------------------------------------------
# Alfred's Capability Matrix (auto-populated in all proposals)
# ---------------------------------------------------------------------------
CAPABILITY_MATRIX = {
    "company": {
        "name": "BUILD&LINK LLC",
        "cage_code": "TBD",
        "uei": "TBD",
        "naics_codes": [
            "541511",  # Custom Computer Programming Services
            "541512",  # Computer Systems Design Services
            "541519",  # Other Computer Related Services
            "541715",  # Research and Development in the Physical, Engineering, and Life Sciences
            "518210",  # Data Processing, Hosting, and Related Services
            "611430",  # Professional and Management Development Training
        ],
        "certifications": [
            "SDVOSB (Service-Disabled Veteran-Owned Small Business)",
            "Small Business (SBA)",
        ],
        "socioeconomic_status": "SDVOSB",
    },
    "key_personnel": {
        "principal": {
            "name": "Alfred Zhang",
            "title": "Principal / Chief Technology Officer",
            "clearance": "Eligible (Air Force Reserve Officer)",
            "education": "PhD, Applied Mathematics (AI/ML focus)",
            "experience_years": 10,
            "expertise": [
                "Artificial Intelligence / Machine Learning",
                "Large Language Models (LLM) and NLP",
                "Cloud Architecture (AWS, GCP, Azure)",
                "Full-Stack Software Development",
                "Data Analytics and Visualization",
                "Computer Vision and Signal Processing",
                "Cybersecurity and Information Assurance",
            ],
            "notable_experience": [
                "Meta Platforms — Senior AI/ML Engineer",
                "Air Force Reserve — Officer",
                "IEEE Reviewer — Peer-reviewed publications",
                "Real estate portfolio management ($4.5M assets)",
            ],
        }
    },
    "past_performance": [
        {
            "project": "AI-Powered Content Moderation System",
            "client": "Meta Platforms (commercial)",
            "value": "Internal project (enterprise scale)",
            "period": "2023-present",
            "relevance": "ML model development, large-scale data processing, production deployment",
        },
        {
            "project": "Military Career Advisory System (ASVAB Prep)",
            "client": "Internal / Military community",
            "value": "Open-source contribution",
            "period": "2024-present",
            "relevance": "Adaptive learning, military domain expertise, full-stack development",
        },
    ],
}


# ---------------------------------------------------------------------------
# Template: SBIR/STTR Phase I
# ---------------------------------------------------------------------------
def sbir_phase1_template(opportunity: dict) -> dict:
    """Generate SBIR/STTR Phase I proposal template."""
    title = opportunity.get("title", "Untitled Opportunity")
    solicitation = opportunity.get("solicitationNumber", opportunity.get("noticeId", "N/A"))
    agency = opportunity.get("department", opportunity.get("fullParentPathName", "N/A"))
    deadline = opportunity.get("responseDeadLine", "TBD")

    return {
        "template_type": "SBIR/STTR Phase I",
        "opportunity_title": title,
        "solicitation_number": solicitation,
        "agency": agency,
        "deadline": deadline,
        "sections": {
            "cover_page": {
                "title": title,
                "company": CAPABILITY_MATRIX["company"]["name"],
                "principal_investigator": CAPABILITY_MATRIX["key_personnel"]["principal"]["name"],
                "cage_code": CAPABILITY_MATRIX["company"]["cage_code"],
                "uei": CAPABILITY_MATRIX["company"]["uei"],
                "topic_number": solicitation,
                "proposal_title": f"[Your Technical Title for {title}]",
            },
            "technical_volume": {
                "1_identification_and_significance": (
                    "## 1. Identification and Significance of the Problem\n\n"
                    f"[Describe the specific problem addressed by {solicitation}]\n\n"
                    "### 1.1 Problem Statement\n"
                    "[Clearly state the technical problem and its significance to the agency]\n\n"
                    "### 1.2 Current State of the Art\n"
                    "[Review existing approaches and their limitations]\n\n"
                    "### 1.3 Innovation Gap\n"
                    "[Identify the gap your solution fills]"
                ),
                "2_technical_objectives": (
                    "## 2. Phase I Technical Objectives\n\n"
                    "### Objective 1: [Primary Technical Goal]\n"
                    "- Approach: [Methodology]\n"
                    "- Success Criteria: [Measurable outcomes]\n\n"
                    "### Objective 2: [Secondary Technical Goal]\n"
                    "- Approach: [Methodology]\n"
                    "- Success Criteria: [Measurable outcomes]"
                ),
                "3_work_plan": (
                    "## 3. Phase I Work Plan\n\n"
                    "### Task 1: Requirements Analysis & Design (Month 1)\n"
                    "- Subtask 1.1: [Detail]\n"
                    "- Subtask 1.2: [Detail]\n"
                    "- Deliverable: Technical Design Document\n\n"
                    "### Task 2: Prototype Development (Months 2-4)\n"
                    "- Subtask 2.1: [Detail]\n"
                    "- Subtask 2.2: [Detail]\n"
                    "- Deliverable: Working Prototype\n\n"
                    "### Task 3: Testing & Evaluation (Months 5-6)\n"
                    "- Subtask 3.1: [Detail]\n"
                    "- Deliverable: Test Report & Phase II Proposal Draft"
                ),
                "4_related_work": (
                    "## 4. Related Work\n\n"
                    "[Describe relevant prior work by the PI and the company]\n\n"
                    f"Dr. {CAPABILITY_MATRIX['key_personnel']['principal']['name']} brings "
                    f"{CAPABILITY_MATRIX['key_personnel']['principal']['experience_years']}+ years "
                    "of experience in:\n"
                    + "\n".join(f"- {e}" for e in CAPABILITY_MATRIX["key_personnel"]["principal"]["expertise"][:5])
                ),
                "5_key_personnel": _format_key_personnel(),
                "6_facilities_equipment": (
                    "## 6. Facilities and Equipment\n\n"
                    "BUILD&LINK LLC maintains:\n"
                    "- Cloud computing infrastructure (AWS/GCP) for scalable development\n"
                    "- Secure development environment meeting NIST 800-171 guidelines\n"
                    "- High-performance computing resources for AI/ML model training\n"
                    "- Collaboration tools for distributed team coordination"
                ),
            },
            "cost_volume": {
                "direct_labor": "[PI hours x rate + support staff]",
                "materials": "[Cloud computing, software licenses]",
                "travel": "[If applicable]",
                "indirect_costs": "[Overhead rate]",
                "total_cost": "[Phase I typically $50K-$250K depending on agency]",
                "note": "SBIR Phase I awards are typically 6-12 months, $50K-$250K",
            },
            "commercialization_plan": (
                "## Commercialization Plan\n\n"
                "### Phase II Path\n"
                "[Describe how Phase I results lead to Phase II development]\n\n"
                "### Market Analysis\n"
                "[Government and commercial market size for the solution]\n\n"
                "### Revenue Model\n"
                "[SaaS, licensing, integration services, etc.]"
            ),
        },
        "compliance_checklist": [
            "Page limit compliance (typically 20-25 pages for technical volume)",
            "Font size and margin requirements met",
            "All required forms included (SF 424, budget justification)",
            "SDVOSB certification documentation attached",
            "PI commitment letter included",
            "Subcontracting plan (if applicable)",
            "Data rights assertions included",
        ],
    }


# ---------------------------------------------------------------------------
# Template: Professional Services (IT/AI/ML)
# ---------------------------------------------------------------------------
def professional_services_template(opportunity: dict) -> dict:
    """Generate professional services proposal template for IT/AI/ML contracts."""
    title = opportunity.get("title", "Untitled Opportunity")
    solicitation = opportunity.get("solicitationNumber", opportunity.get("noticeId", "N/A"))
    agency = opportunity.get("department", opportunity.get("fullParentPathName", "N/A"))
    deadline = opportunity.get("responseDeadLine", "TBD")

    return {
        "template_type": "Professional Services (IT/AI/ML)",
        "opportunity_title": title,
        "solicitation_number": solicitation,
        "agency": agency,
        "deadline": deadline,
        "sections": {
            "executive_summary": (
                "## Executive Summary\n\n"
                f"BUILD&LINK LLC, a certified Service-Disabled Veteran-Owned Small Business (SDVOSB), "
                f"is pleased to submit this proposal in response to {solicitation} — {title}.\n\n"
                "Our team brings deep expertise in artificial intelligence, machine learning, "
                "and enterprise software development, combined with military domain knowledge "
                "and a commitment to delivering mission-critical solutions.\n\n"
                "### Key Differentiators\n"
                "1. **SDVOSB with Active Military Connection** — Principal is an Air Force Reserve Officer\n"
                "2. **PhD-Level AI/ML Expertise** — Applied Mathematics with production ML experience at Meta\n"
                "3. **Agile Delivery** — Small team, fast iteration, direct access to decision-makers\n"
                "4. **Cost-Effective** — Low overhead, competitive rates, high-value delivery"
            ),
            "technical_approach": (
                "## Technical Approach\n\n"
                "### Understanding of Requirements\n"
                "[Demonstrate thorough understanding of the SOW/PWS]\n\n"
                "### Proposed Solution\n"
                "[Detail the technical approach, architecture, and methodology]\n\n"
                "### Technology Stack\n"
                "- **AI/ML**: PyTorch, TensorFlow, Hugging Face, OpenAI API\n"
                "- **Cloud**: AWS (GovCloud), Azure Government, GCP\n"
                "- **Backend**: Python, FastAPI, Node.js\n"
                "- **Frontend**: React, TypeScript, TailwindCSS\n"
                "- **Data**: PostgreSQL, Redis, Elasticsearch\n"
                "- **DevOps**: Docker, Kubernetes, GitHub Actions CI/CD\n\n"
                "### Quality Assurance\n"
                "- Automated testing (unit, integration, E2E)\n"
                "- Code review and static analysis\n"
                "- Security scanning (SAST/DAST)\n"
                "- Performance benchmarking"
            ),
            "management_approach": (
                "## Management Approach\n\n"
                "### Project Management Methodology\n"
                "Agile/Scrum with 2-week sprints, adapted for government reporting requirements.\n\n"
                "### Communication Plan\n"
                "- Weekly status reports\n"
                "- Bi-weekly sprint demos\n"
                "- Monthly progress reviews\n"
                "- Ad-hoc technical discussions as needed\n\n"
                "### Risk Management\n"
                "| Risk | Probability | Impact | Mitigation |\n"
                "|------|------------|--------|------------|\n"
                "| [Risk 1] | [H/M/L] | [H/M/L] | [Strategy] |\n"
                "| [Risk 2] | [H/M/L] | [H/M/L] | [Strategy] |"
            ),
            "past_performance": _format_past_performance(),
            "key_personnel": _format_key_personnel(),
            "sdvosb_compliance": (
                "## SDVOSB Compliance\n\n"
                "BUILD&LINK LLC is a certified Service-Disabled Veteran-Owned Small Business.\n\n"
                "- **Veteran Status**: Principal is a Service-Disabled Veteran (Air Force Reserve Officer)\n"
                "- **Ownership**: 100% veteran-owned\n"
                "- **Control**: Day-to-day management and strategic decisions made by veteran owner\n"
                "- **Performance**: At least 50% of contract performance by SDVOSB employees\n"
                "- **Certification**: [VetBiz / SBA certification number]"
            ),
        },
        "cost_volume_framework": {
            "labor_categories": [
                {"category": "Principal Investigator / Project Lead", "rate_range": "$150-200/hr"},
                {"category": "Senior AI/ML Engineer", "rate_range": "$120-160/hr"},
                {"category": "Full-Stack Developer", "rate_range": "$100-140/hr"},
                {"category": "Data Analyst", "rate_range": "$80-110/hr"},
                {"category": "Project Manager", "rate_range": "$90-120/hr"},
            ],
            "other_direct_costs": [
                "Cloud computing (AWS GovCloud / Azure Government)",
                "Software licenses (development tools, AI APIs)",
                "Travel (if required by SOW)",
            ],
            "indirect_rates": {
                "overhead": "[Your overhead rate]%",
                "g_and_a": "[Your G&A rate]%",
                "profit": "Typically 8-12% for professional services",
            },
        },
        "compliance_checklist": [
            "SAM.gov registration current and active",
            "SDVOSB certification valid",
            "UEI number included",
            "CAGE code included",
            "All NAICS codes listed",
            "SF 330 (if A&E services) or SF 1449 included",
            "Representations and certifications current",
            "Insurance requirements met",
            "Section 508 compliance addressed (if IT)",
            "NIST 800-171 compliance addressed (if CUI)",
        ],
    }


# ---------------------------------------------------------------------------
# Template: SDVOSB Sole-Source
# ---------------------------------------------------------------------------
def sdvosb_sole_source_template(opportunity: dict) -> dict:
    """Generate SDVOSB sole-source proposal template (under $5M threshold)."""
    title = opportunity.get("title", "Untitled Opportunity")
    solicitation = opportunity.get("solicitationNumber", opportunity.get("noticeId", "N/A"))

    return {
        "template_type": "SDVOSB Sole-Source (FAR 19.1405)",
        "opportunity_title": title,
        "solicitation_number": solicitation,
        "note": (
            "Under FAR 19.1405, contracting officers may award sole-source contracts "
            "to SDVOSBs up to $5M (manufacturing) or $5M (services) without competition. "
            "This template is designed for direct outreach to contracting officers."
        ),
        "sections": {
            "capability_statement": (
                "## Capability Statement — BUILD&LINK LLC\n\n"
                "### Company Overview\n"
                "BUILD&LINK LLC is a certified SDVOSB specializing in AI/ML solutions, "
                "software development, and data analytics for federal agencies.\n\n"
                "### Core Competencies\n"
                + "\n".join(f"- {e}" for e in CAPABILITY_MATRIX["key_personnel"]["principal"]["expertise"])
                + "\n\n"
                "### Differentiators\n"
                "- **Veteran-Led**: Air Force Reserve Officer with active security clearance eligibility\n"
                "- **PhD-Level Technical Depth**: Applied Mathematics with AI/ML specialization\n"
                "- **Enterprise Experience**: Production systems at Meta scale\n"
                "- **Agile & Cost-Effective**: Small team, low overhead, high delivery velocity\n\n"
                "### NAICS Codes\n"
                + "\n".join(f"- {code}" for code in CAPABILITY_MATRIX["company"]["naics_codes"])
            ),
            "sole_source_justification": (
                "## Sole-Source Justification Support\n\n"
                "BUILD&LINK LLC is uniquely qualified for this requirement because:\n\n"
                "1. **Unique Technical Expertise**: [Specific capability that only your firm provides]\n"
                "2. **SDVOSB Status**: Certified SDVOSB meeting FAR 19.1405 requirements\n"
                "3. **Past Performance**: [Relevant past performance demonstrating capability]\n"
                "4. **Cost Efficiency**: Direct engagement eliminates competition overhead\n"
                "5. **Schedule Advantage**: Ready to start within [X] days of award"
            ),
            "price_proposal": (
                "## Price Proposal\n\n"
                "### Firm-Fixed-Price Option\n"
                "| Deliverable | Price |\n"
                "|------------|-------|\n"
                "| [Deliverable 1] | $[Amount] |\n"
                "| [Deliverable 2] | $[Amount] |\n"
                "| **Total** | **$[Total]** |\n\n"
                "### Time-and-Materials Option\n"
                "| Labor Category | Rate | Est. Hours |\n"
                "|---------------|------|------------|\n"
                "| Principal / PI | $[Rate]/hr | [Hours] |\n"
                "| Sr. Engineer | $[Rate]/hr | [Hours] |"
            ),
        },
    }


# ---------------------------------------------------------------------------
# Helper formatters
# ---------------------------------------------------------------------------
def _format_key_personnel() -> str:
    """Format key personnel section."""
    p = CAPABILITY_MATRIX["key_personnel"]["principal"]
    return (
        "## Key Personnel\n\n"
        f"### {p['name']} — {p['title']}\n"
        f"- **Education**: {p['education']}\n"
        f"- **Clearance**: {p['clearance']}\n"
        f"- **Experience**: {p['experience_years']}+ years\n"
        f"- **Expertise**:\n"
        + "\n".join(f"  - {e}" for e in p["expertise"])
        + "\n\n"
        "**Notable Experience**:\n"
        + "\n".join(f"  - {e}" for e in p["notable_experience"])
    )


def _format_past_performance() -> str:
    """Format past performance section."""
    lines = ["## Past Performance\n"]
    for pp in CAPABILITY_MATRIX["past_performance"]:
        lines.append(f"### {pp['project']}")
        lines.append(f"- **Client**: {pp['client']}")
        lines.append(f"- **Value**: {pp['value']}")
        lines.append(f"- **Period**: {pp['period']}")
        lines.append(f"- **Relevance**: {pp['relevance']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Template selector
# ---------------------------------------------------------------------------
def select_template(opportunity: dict) -> dict:
    """
    Auto-select the best proposal template based on opportunity characteristics.
    """
    title = (opportunity.get("title", "") + " " + opportunity.get("description", "")).lower()
    opp_type = opportunity.get("type", "").lower()
    set_aside = opportunity.get("typeOfSetAside", "").lower()

    # SBIR/STTR detection
    if "sbir" in title or "sttr" in title or "sbir" in opp_type:
        return sbir_phase1_template(opportunity)

    # SDVOSB sole-source detection
    if "sdvosb" in set_aside or "sole source" in title or "sole-source" in title:
        return sdvosb_sole_source_template(opportunity)

    # Default: professional services
    return professional_services_template(opportunity)


def save_template(template: dict, output_dir: Optional[Path] = None) -> Path:
    """Save a generated template to disk."""
    if output_dir is None:
        output_dir = TEMPLATES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"template_{template['template_type'].replace(' ', '_').replace('/', '_')}_{ts}.json"
    path = output_dir / filename

    with open(path, "w") as f:
        json.dump(template, f, indent=2)

    return path


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test with a mock opportunity
    mock_opp = {
        "title": "AI/ML Support Services for DoD Research Lab",
        "solicitationNumber": "W911NF-26-R-0042",
        "department": "Department of the Army",
        "responseDeadLine": "2026-04-15",
        "typeOfSetAside": "SDVOSB",
    }

    template = select_template(mock_opp)
    print(f"Selected template: {template['template_type']}")
    print(f"Sections: {list(template['sections'].keys())}")

    path = save_template(template)
    print(f"Saved to: {path}")

    # Clean up
    import shutil
    if TEMPLATES_DIR.exists():
        shutil.rmtree(TEMPLATES_DIR)
