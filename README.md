# SAMgov — Government Contract Intelligence Pipeline

A comprehensive system for scanning, analyzing, and responding to federal contract opportunities on SAM.gov. Designed for a Service-Disabled Veteran-Owned Small Business (SDVOSB) with deep expertise in AI/ML, software development, and data analytics.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAMgov Pipeline Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Scanner  │──▶│ Storage  │──▶│Analytics │──▶│ Proposal │    │
│  │ Engine   │   │  Layer   │   │Framework │   │Generator │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       │              │              │              │             │
│       ▼              ▼              ▼              ▼             │
│  SAM.gov API    JSON/CSV DB    Trend Reports   Draft Emails     │
│  Web Scraping   Timestamped    Fit Scoring     TODO Lists       │
│  Dedup Logic    Full Records   Recommendations Gmail Send       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Scanner Engine (`src/scanner/`)
- Automated SAM.gov opportunity scanning via public API and web scraping
- Multi-keyword search across AI/ML, software dev, cloud, data analytics
- Deduplication logic: tracks seen opportunities and only surfaces new or updated ones
- Configurable search profiles and NAICS code filters

### 2. Storage Layer (`src/storage/`)
- Timestamped JSON records for every scanned opportunity
- Full data capture: notice ID, title, agency, dates, contacts, description, attachments, set-aside, NAICS, PSC, amounts
- Historical tracking with version diffs when opportunities are amended
- Export to CSV/Excel for external analysis

### 3. Analytics Framework (`src/analytics/`)
- Opportunity scoring based on configurable fit criteria (technical, agency, size, set-aside)
- Trend analysis over accumulated data (agency patterns, NAICS trends, seasonal cycles)
- Deduplication-aware recommendation engine (never recommends the same opportunity twice)
- Weekly/monthly summary reports

### 4. Proposal Generator (`src/proposal/`)
- Auto-generates draft proposal outlines based on opportunity requirements
- Creates actionable TODO lists with deadlines
- Produces structured response documents

### 5. Gmail Integration (`src/gmail_integration/`)
- Sends proposal drafts via Gmail MCP
- Tracks sent proposals and responses
- Links opportunities to email threads

## Data Structure

Each opportunity record contains:
```json
{
  "notice_id": "DARPA-PA-25-07-02",
  "title": "CLARA - Compositional Learning-And-Reasoning for AI",
  "scan_timestamp": "2026-02-22T15:00:00Z",
  "first_seen": "2026-02-22T15:00:00Z",
  "last_updated": "2026-02-22T15:00:00Z",
  "status": "active",
  "agency": "DARPA",
  "department": "DEPT OF DEFENSE",
  "sub_tier": "DEFENSE ADVANCED RESEARCH PROJECTS AGENCY",
  "office": "DEF ADVANCED RESEARCH PROJECTS AGCY",
  "notice_type": "Solicitation",
  "set_aside": "None",
  "naics_code": "541715",
  "psc_code": "AC11",
  "response_date": "2026-04-10T16:00:00Z",
  "published_date": "2026-02-10",
  "place_of_performance": "",
  "estimated_value": "$2,000,000",
  "description": "...",
  "contacts": [...],
  "attachments": [...],
  "sam_url": "https://sam.gov/opp/...",
  "fit_score": 95,
  "fit_rationale": "...",
  "recommendation_status": "recommended",
  "recommendation_date": "2026-02-22",
  "proposal_status": "not_started"
}
```

## Configuration

Edit `config/profile.json` to customize:
- Search keywords and NAICS codes
- Agency preferences
- Fit scoring weights
- Recommendation rules

## Usage

```bash
# Run daily scan
python3 src/scanner/scan.py

# Generate analytics report
python3 src/analytics/analyze.py

# Generate proposal for a specific opportunity
python3 src/proposal/generate.py --notice-id DARPA-PA-25-07-02

# Full pipeline
python3 main.py
```

## License

Private — All rights reserved.
