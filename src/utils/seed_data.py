"""
Seed Data Migration

Migrates the manually collected opportunity data from the initial scan
(Feb 22, 2026) into the structured database. This serves as the first
historical data point for the analytics framework.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.db import OpportunityDB


SEED_OPPORTUNITIES = [
    {
        "notice_id": "DARPA-PA-25-07-02",
        "title": "Compositional Learning-And-Reasoning for AI Complex Systems Engineering (CLARA)",
        "description": "DARPA DSO Disruption Opportunity for high-assurance AI systems. CLARA is an exploratory fundamental research program that aims to create high-assurance, broadly applicable AI systems of systems by tightly integrating Automated Reasoning (AR) and Machine Learning (ML) components. The total award value for the combined Phase 1 base (Feasibility Study) and Phase 2 option (Proof of Concept) is limited to $2,000,000.",
        "status": "active",
        "agency": "DEFENSE ADVANCED RESEARCH PROJECTS AGENCY (DARPA)",
        "department": "DEPT OF DEFENSE",
        "sub_tier": "DEFENSE ADVANCED RESEARCH PROJECTS AGENCY",
        "office": "DEF ADVANCED RESEARCH PROJECTS AGCY",
        "notice_type": "Solicitation",
        "set_aside": "None",
        "naics_code": "",
        "psc_code": "AC11",
        "response_date": "2026-04-10T16:00:00Z",
        "published_date": "2026-02-10",
        "modified_date": "2026-02-10",
        "place_of_performance": "",
        "estimated_value": "$2,000,000",
        "contacts": [
            {"name": "", "email": "clara@darpa.mil", "phone": "", "type": "primary"}
        ],
        "attachments": [],
        "sam_url": "https://sam.gov/opp/3530b2c0a68d4de786079e7305d4f625/view",
        "opp_id": "3530b2c0a68d4de786079e7305d4f625",
    },
    {
        "notice_id": "CDAO_26-01",
        "title": "Call for Solution - AI-Enabled Software Development Coding Capabilities",
        "description": "The Chief Digital and Artificial Intelligence Office (CDAO) is seeking innovative solutions for AI-Enabled Software Development Coding Capabilities under the Army Open Solicitation (AOS) framework. This Call for Solution seeks to leverage AI to enhance and accelerate the software development lifecycle within the Department of Defense.",
        "status": "active",
        "agency": "CHIEF DIGITAL AND ARTIFICIAL INTELLIGENCE OFFICE",
        "department": "DEPT OF DEFENSE",
        "sub_tier": "DEPT OF THE ARMY",
        "office": "W6QK ACC-APG CONT CT SW SECTOR",
        "notice_type": "Solicitation",
        "set_aside": "",
        "naics_code": "",
        "psc_code": "",
        "response_date": "2026-03-06",
        "published_date": "2026-02-06",
        "modified_date": "2026-02-20",
        "place_of_performance": "",
        "estimated_value": "",
        "contacts": [
            {"name": "", "email": "thomas.j.lueddeke.civ@army.mil", "phone": "", "type": "primary"},
            {"name": "", "email": "kristen.l.weiman.civ@army.mil", "phone": "", "type": "alternative"}
        ],
        "attachments": [
            {"name": "Call_for_Solutions_AI_Coding_Capabilities.pdf", "url": "", "type": "application/pdf"}
        ],
        "sam_url": "https://sam.gov/opp/a13c653b5a1440fca2fb4457c192b5fb/view",
        "opp_id": "a13c653b5a1440fca2fb4457c192b5fb",
    },
    {
        "notice_id": "FA8730-FALCONER-NG",
        "title": "Kessel Run - Next-Generation Air Operations Center (AOC) Weapon System (FALCONER-NG)",
        "description": "Program Announcement: Kessel Run Seeking Innovative Solutions for the Next-Generation Air Operations Center (AOC) Weapon System. The Air Force Life Cycle Management Center (AFLCMC) is seeking innovative solutions to modernize the AOC weapon system through agile software development and DevSecOps practices.",
        "status": "active",
        "agency": "DEPT OF THE AIR FORCE",
        "department": "DEPT OF DEFENSE",
        "sub_tier": "DEPT OF THE AIR FORCE",
        "office": "FA8730 AFLCMC HBKI",
        "notice_type": "Special Notice",
        "set_aside": "None",
        "naics_code": "541512",
        "psc_code": "D302",
        "response_date": "",
        "published_date": "2026-02-14",
        "modified_date": "2026-02-14",
        "place_of_performance": "Hanscom AFB, MA",
        "estimated_value": "",
        "contacts": [],
        "attachments": [],
        "sam_url": "https://sam.gov/opp/a2be5bc280d948b886cd4ad8998ef552/view",
        "opp_id": "a2be5bc280d948b886cd4ad8998ef552",
    },
    {
        "notice_id": "FA8688-RFI-26-0001",
        "title": "Current and Emerging Artificial Intelligence (AI) Tools to Accelerate Air Force Mobility Aircraft Acquisition Activities",
        "description": "The Air Force is seeking information on current and emerging AI tools that can accelerate mobility aircraft acquisition activities. This RFI is for market research purposes to identify potential solutions for AI-assisted acquisition processes.",
        "status": "active",
        "agency": "DEPT OF THE AIR FORCE",
        "department": "DEPT OF DEFENSE",
        "sub_tier": "DEPT OF THE AIR FORCE",
        "office": "FA8688 AFLCMC WL",
        "notice_type": "Sources Sought",
        "set_aside": "None",
        "naics_code": "541715",
        "psc_code": "R425",
        "response_date": "2026-03-14",
        "published_date": "2026-02-14",
        "modified_date": "2026-02-14",
        "place_of_performance": "",
        "estimated_value": "",
        "contacts": [],
        "attachments": [],
        "sam_url": "https://sam.gov/opp/f294572b9b8a4bb5a1c24c67fd77dd09/view",
        "opp_id": "f294572b9b8a4bb5a1c24c67fd77dd09",
    },
    {
        "notice_id": "FA875024S7002",
        "title": "NETWORKING THE FIGHT - AFRL Rome BAA",
        "description": "Air Force Research Laboratory (AFRL) Information Directorate, Rome, NY, Broad Agency Announcement for Networking the Fight. Seeks innovative research in information systems, cyber, and networking technologies for the Air Force.",
        "status": "active",
        "agency": "DEPT OF THE AIR FORCE",
        "department": "DEPT OF DEFENSE",
        "sub_tier": "DEPT OF THE AIR FORCE",
        "office": "FA8750 AFRL RIK",
        "notice_type": "Presolicitation",
        "set_aside": "None",
        "naics_code": "541715",
        "psc_code": "AC11",
        "response_date": "",
        "published_date": "2024-10-01",
        "modified_date": "2026-02-18",
        "place_of_performance": "Rome, NY",
        "estimated_value": "",
        "contacts": [],
        "attachments": [],
        "sam_url": "https://sam.gov/opp/c15d90848a894cb9a8144230ef6dcb6f/view",
        "opp_id": "c15d90848a894cb9a8144230ef6dcb6f",
    },
    {
        "notice_id": "FA461026DTO01",
        "title": "Artificial Intelligence / Machine Learning - Industry Day (Virtual Only)",
        "description": "US Space Force - Space Systems Command S6 is hosting a virtual Industry Day on Feb 24, 2026 (0900-1500 PST) to discuss AI/ML for space, acquisition, and Enterprise operations. This is an RFI for market research purposes only. Information gathered may be used in developing acquisition strategy for future solicitations. Meeting ID: 993 341 135 452, Passcode: E2n8P3vm",
        "status": "active",
        "agency": "SPACE SYSTEMS COMMAND",
        "department": "DEPT OF DEFENSE",
        "sub_tier": "DEPT OF THE AIR FORCE",
        "office": "FA4610 30 CONS PK",
        "notice_type": "Sources Sought",
        "set_aside": "None",
        "naics_code": "541715",
        "psc_code": "R425",
        "response_date": "2026-02-24T15:00:00",
        "published_date": "2026-02-20",
        "modified_date": "2026-02-20",
        "place_of_performance": "Vandenberg SFB, CA (Virtual)",
        "estimated_value": "",
        "contacts": [
            {"name": "Alvaro Guzman", "email": "alvaro.guzman.1@spaceforce.mil", "phone": "", "type": "primary"}
        ],
        "attachments": [
            {"name": "RFI -SSC - AI-ML 1.pdf", "url": "", "type": "application/pdf"},
            {"name": "AI_ML Industry Day.pdf", "url": "", "type": "application/pdf"}
        ],
        "sam_url": "https://sam.gov/opp/8c42ae3803bf45f3a45c3d2c41f26ab9/view",
        "opp_id": "8c42ae3803bf45f3a45c3d2c41f26ab9",
    },
    {
        "notice_id": "ASA(ALT)_26-01",
        "title": "Call for Solution - Acquisition Data Nexus (ADN) Initiative",
        "description": "Army Contracting Command - Aberdeen Proving Ground (ACC-APG), Digital Capabilities Contracting Center of Excellence (DC3oE), on behalf of the Assistant Secretary of the Army for Acquisition, Logistics, and Technology [ASA(ALT)], Chief Automation and Data Integration Office (CADIO), is seeking innovative solutions to modernize the Army's Acquisition Data Nexus (ADN). The ADN requirement addresses the Army's need to streamline and automate the integration, routing, and normalization of acquisition data across multiple disconnected systems, such as PMRT, VCE, and ACWS.",
        "status": "active",
        "agency": "DEPT OF THE ARMY",
        "department": "DEPT OF DEFENSE",
        "sub_tier": "DEPT OF THE ARMY",
        "office": "W6QK ACC-APG CONT CT SW SECTOR",
        "notice_type": "Solicitation",
        "set_aside": "",
        "naics_code": "",
        "psc_code": "",
        "response_date": "2026-02-27T13:00:00",
        "published_date": "2026-01-30",
        "modified_date": "2026-02-20",
        "place_of_performance": "",
        "estimated_value": "",
        "contacts": [
            {"name": "", "email": "thomas.j.lueddeke.civ@army.mil", "phone": "", "type": "primary"},
            {"name": "", "email": "kristen.l.weiman.civ@army.mil", "phone": "", "type": "alternative"}
        ],
        "attachments": [],
        "sam_url": "https://sam.gov/opp/98314e282bec40e5ba6c9c5971767b56/view",
        "opp_id": "98314e282bec40e5ba6c9c5971767b56",
    },
]


def seed_database():
    """Seed the database with initial manually collected data."""
    print("Seeding database with initial scan data (Feb 22, 2026)...")

    db = OpportunityDB()

    # Add scan timestamp and scoring
    from src.scanner.scoring import score_opportunity
    from src.scanner.scan import load_config

    config = load_config()
    now = datetime.now(timezone.utc).isoformat()

    for opp in SEED_OPPORTUNITIES:
        opp["scan_timestamp"] = now
        opp["first_seen"] = now
        opp["last_updated"] = opp.get("modified_date", now)
        opp["raw_data"] = {}
        score, rationale = score_opportunity(opp, config)
        opp["fit_score"] = score
        opp["fit_rationale"] = rationale
        opp["recommendation_status"] = "unscored"
        opp["recommendation_date"] = ""
        opp["proposal_status"] = "not_started"

    new, updated = db.upsert_opportunities(SEED_OPPORTUNITIES)
    print(f"  Seeded {new} new, {updated} updated opportunities.")

    # Show scores
    for opp in sorted(SEED_OPPORTUNITIES, key=lambda x: x["fit_score"], reverse=True):
        print(f"  [{opp['fit_score']:3d}] {opp['notice_id']}: {opp['title'][:60]}")

    return db


if __name__ == "__main__":
    seed_database()
