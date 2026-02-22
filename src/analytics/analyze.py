"""
Analytics Framework

Provides trend analysis, pattern detection, and reporting over accumulated
SAM.gov opportunity data. Designed to become more powerful as data accumulates
over weeks and months.

Key analyses:
- Agency posting patterns (which agencies post most frequently)
- NAICS code trends (emerging vs declining categories)
- Seasonal/cyclical patterns in posting volume
- Set-aside distribution analysis
- Score distribution and recommendation effectiveness
- Pipeline health metrics
"""

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.db import OpportunityDB


def generate_analytics_report(
    db: Optional[OpportunityDB] = None,
    output_dir: Optional[Path] = None,
) -> dict:
    """
    Generate a comprehensive analytics report from accumulated data.
    Returns a dict with all analytics results.
    """
    if db is None:
        db = OpportunityDB()
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    opps = db.get_all_opportunities()
    stats = db.get_stats()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": stats,
        "agency_analysis": _analyze_agencies(opps),
        "naics_analysis": _analyze_naics(opps),
        "notice_type_analysis": _analyze_notice_types(opps),
        "set_aside_analysis": _analyze_set_asides(opps),
        "timeline_analysis": _analyze_timeline(opps),
        "score_analysis": _analyze_scores(opps),
        "pipeline_health": _analyze_pipeline(opps, db),
        "top_opportunities": _get_top_opportunities(opps, n=10),
    }

    # Save report
    report_path = output_dir / f"analytics_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Generate markdown summary
    md_path = output_dir / f"analytics_{datetime.now().strftime('%Y-%m-%d')}.md"
    _write_markdown_report(report, md_path)

    return report


def _analyze_agencies(opps: list[dict]) -> dict:
    """Analyze which agencies post the most relevant opportunities."""
    agency_counts = Counter()
    agency_scores = defaultdict(list)

    for opp in opps:
        agency = opp.get("sub_tier") or opp.get("department") or "Unknown"
        agency_counts[agency] += 1
        agency_scores[agency].append(opp.get("fit_score", 0))

    # Top agencies by count
    top_by_count = agency_counts.most_common(15)

    # Top agencies by average score
    agency_avg = {}
    for agency, scores in agency_scores.items():
        if len(scores) >= 2:  # Need at least 2 to be meaningful
            agency_avg[agency] = round(sum(scores) / len(scores), 1)
    top_by_score = sorted(agency_avg.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "top_by_volume": [{"agency": a, "count": c} for a, c in top_by_count],
        "top_by_avg_score": [{"agency": a, "avg_score": s} for a, s in top_by_score],
        "total_agencies": len(agency_counts),
    }


def _analyze_naics(opps: list[dict]) -> dict:
    """Analyze NAICS code distribution and trends."""
    naics_counts = Counter()
    naics_scores = defaultdict(list)

    naics_labels = {
        "541511": "Custom Computer Programming",
        "541512": "Computer Systems Design",
        "541513": "Computer Facilities Management",
        "541519": "Other Computer Related Services",
        "541715": "R&D Physical/Engineering Sciences",
        "518210": "Data Processing & Hosting",
        "541330": "Engineering Services",
        "541690": "Other Scientific/Technical Consulting",
        "611420": "Computer Training",
    }

    for opp in opps:
        naics = str(opp.get("naics_code", "")).strip()
        if naics and naics != "(blank)":
            naics_counts[naics] += 1
            naics_scores[naics].append(opp.get("fit_score", 0))

    top_naics = []
    for code, count in naics_counts.most_common(15):
        scores = naics_scores[code]
        top_naics.append({
            "code": code,
            "label": naics_labels.get(code, ""),
            "count": count,
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        })

    return {
        "top_naics": top_naics,
        "total_unique_codes": len(naics_counts),
    }


def _analyze_notice_types(opps: list[dict]) -> dict:
    """Analyze distribution of notice types."""
    type_counts = Counter()
    for opp in opps:
        nt = opp.get("notice_type", "Unknown")
        type_counts[nt] += 1

    return {
        "distribution": [{"type": t, "count": c} for t, c in type_counts.most_common()],
    }


def _analyze_set_asides(opps: list[dict]) -> dict:
    """Analyze set-aside distribution."""
    sa_counts = Counter()
    for opp in opps:
        sa = opp.get("set_aside", "None") or "None"
        sa_counts[sa] += 1

    return {
        "distribution": [{"set_aside": s, "count": c} for s, c in sa_counts.most_common()],
        "sdvosb_count": sum(1 for o in opps if "SDVOSB" in str(o.get("set_aside", "")).upper()),
        "small_business_count": sum(
            1 for o in opps
            if any(kw in str(o.get("set_aside", "")).upper()
                   for kw in ["SMALL", "SBA", "8(A)", "HUBZONE", "SDVOSB"])
        ),
    }


def _analyze_timeline(opps: list[dict]) -> dict:
    """Analyze posting timeline and response date distribution."""
    by_week = Counter()
    deadline_dist = {"expired": 0, "this_week": 0, "next_2_weeks": 0,
                     "next_month": 0, "beyond": 0, "unknown": 0}
    now = datetime.now()

    for opp in opps:
        # Published date analysis
        pub = opp.get("published_date", "")
        if pub:
            try:
                pub_date = datetime.fromisoformat(pub[:10])
                week_key = pub_date.strftime("%Y-W%U")
                by_week[week_key] += 1
            except (ValueError, TypeError):
                pass

        # Response date analysis
        resp = opp.get("response_date", "")
        if not resp:
            deadline_dist["unknown"] += 1
            continue
        try:
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y"]:
                try:
                    resp_date = datetime.strptime(resp[:19], fmt)
                    break
                except ValueError:
                    continue
            else:
                deadline_dist["unknown"] += 1
                continue

            days = (resp_date - now).days
            if days < 0:
                deadline_dist["expired"] += 1
            elif days <= 7:
                deadline_dist["this_week"] += 1
            elif days <= 14:
                deadline_dist["next_2_weeks"] += 1
            elif days <= 30:
                deadline_dist["next_month"] += 1
            else:
                deadline_dist["beyond"] += 1
        except Exception:
            deadline_dist["unknown"] += 1

    # Sort weeks
    weekly_volume = sorted(by_week.items())

    return {
        "weekly_posting_volume": [{"week": w, "count": c} for w, c in weekly_volume],
        "deadline_distribution": deadline_dist,
    }


def _analyze_scores(opps: list[dict]) -> dict:
    """Analyze score distribution and trends."""
    scores = [o.get("fit_score", 0) for o in opps]
    if not scores:
        return {"avg_score": 0, "median_score": 0, "distribution": {}}

    scores.sort()
    avg = round(sum(scores) / len(scores), 1)
    median = scores[len(scores) // 2]

    return {
        "avg_score": avg,
        "median_score": median,
        "min_score": min(scores),
        "max_score": max(scores),
        "above_70": len([s for s in scores if s >= 70]),
        "above_50": len([s for s in scores if s >= 50]),
        "total": len(scores),
    }


def _analyze_pipeline(opps: list[dict], db: OpportunityDB) -> dict:
    """Analyze the proposal pipeline health."""
    stats = db.get_stats()
    proposals = stats.get("proposals", {})

    return {
        "total_tracked": stats["total_opportunities"],
        "active_opportunities": stats["active"],
        "recommended_total": stats["recommended"],
        "proposals": proposals,
        "conversion_rate": (
            round(proposals.get("submitted", 0) / max(stats["recommended"], 1) * 100, 1)
        ),
    }


def _get_top_opportunities(opps: list[dict], n: int = 10) -> list[dict]:
    """Get the top N opportunities by score."""
    active = [o for o in opps if o.get("status") == "active"]
    active.sort(key=lambda x: x.get("fit_score", 0), reverse=True)

    return [
        {
            "notice_id": o["notice_id"],
            "title": o.get("title", "")[:100],
            "agency": o.get("agency", ""),
            "fit_score": o.get("fit_score", 0),
            "response_date": o.get("response_date", ""),
            "set_aside": o.get("set_aside", ""),
            "naics_code": o.get("naics_code", ""),
            "proposal_status": o.get("proposal_status", "not_started"),
        }
        for o in active[:n]
    ]


def _write_markdown_report(report: dict, path: Path):
    """Write a human-readable markdown analytics report."""
    lines = []
    lines.append("# SAM.gov Opportunity Analytics Report")
    lines.append(f"\n**Generated:** {report['generated_at'][:10]}")
    lines.append("")

    # Summary
    s = report["summary"]
    lines.append("## Pipeline Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"| :--- | ---: |")
    lines.append(f"| Total Opportunities Tracked | {s['total_opportunities']} |")
    lines.append(f"| Active | {s['active']} |")
    lines.append(f"| Recommended | {s['recommended']} |")
    lines.append(f"| Scans Completed | {s['scan_count']} |")
    lines.append("")

    # Score distribution
    sd = s.get("score_distribution", {})
    lines.append("## Score Distribution")
    lines.append("")
    lines.append("| Range | Count |")
    lines.append("| :--- | ---: |")
    for rng, cnt in sd.items():
        lines.append(f"| {rng} | {cnt} |")
    lines.append("")

    # Top agencies
    aa = report["agency_analysis"]
    lines.append("## Top Agencies by Volume")
    lines.append("")
    lines.append("| Agency | Count |")
    lines.append("| :--- | ---: |")
    for a in aa["top_by_volume"][:10]:
        lines.append(f"| {a['agency'][:60]} | {a['count']} |")
    lines.append("")

    # Top opportunities
    top = report["top_opportunities"]
    lines.append("## Top Opportunities")
    lines.append("")
    lines.append("| Score | Notice ID | Title | Agency | Deadline |")
    lines.append("| ---: | :--- | :--- | :--- | :--- |")
    for o in top:
        lines.append(
            f"| {o['fit_score']} | {o['notice_id']} | {o['title'][:50]} | "
            f"{o['agency'][:30]} | {o['response_date'][:10] if o['response_date'] else 'Open'} |"
        )
    lines.append("")

    # Deadline distribution
    dd = report["timeline_analysis"]["deadline_distribution"]
    lines.append("## Deadline Distribution")
    lines.append("")
    lines.append("| Timeframe | Count |")
    lines.append("| :--- | ---: |")
    for k, v in dd.items():
        lines.append(f"| {k.replace('_', ' ').title()} | {v} |")
    lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    report = generate_analytics_report()
    print(json.dumps(report["summary"], indent=2))
    print(f"\nReport saved to data/processed/")
