"""
SAMgov Pipeline — Main Entry Point

Full pipeline execution:
1. Scan SAM.gov for new/updated opportunities
2. Score and deduplicate results
3. Store with full detail and timestamps
4. Generate today's recommendations (new opportunities only)
5. Generate proposal drafts for top recommendations
6. Produce analytics report
7. Output summary for review

Usage:
    python3 main.py                    # Full pipeline
    python3 main.py --scan-only        # Scan and store only
    python3 main.py --analyze-only     # Analytics only
    python3 main.py --propose NOTICE_ID  # Generate proposal for specific notice
    python3 main.py --export           # Export all data to CSV
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scanner.scan import run_scan_and_save, load_config
from src.storage.db import OpportunityDB
from src.analytics.analyze import generate_analytics_report
from src.proposal.generate import generate_for_notice


def run_full_pipeline(verbose: bool = True) -> dict:
    """Execute the full pipeline."""
    results = {}

    # Step 1: Scan
    if verbose:
        print("=" * 60)
        print("STEP 1: Scanning SAM.gov")
        print("=" * 60)
    scan_summary = run_scan_and_save(verbose=verbose)
    results["scan"] = scan_summary

    # Step 2: Analytics
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 2: Generating Analytics Report")
        print("=" * 60)
    analytics = generate_analytics_report()
    results["analytics"] = analytics["summary"]

    # Step 3: Generate proposals for top recommendations
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 3: Generating Proposal Drafts")
        print("=" * 60)

    proposals = []
    for rec in scan_summary.get("recommendations", []):
        notice_id = rec["notice_id"]
        if verbose:
            print(f"\n  Generating proposal for: {notice_id}")
        try:
            proposal = generate_for_notice(notice_id)
            proposals.append({
                "notice_id": notice_id,
                "title": rec["title"],
                "todo_count": len(proposal.get("todo_list", [])),
            })
        except Exception as e:
            if verbose:
                print(f"    [ERROR] Failed to generate proposal: {e}")

    results["proposals"] = proposals

    # Step 4: Summary
    if verbose:
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Recommendations: {scan_summary['total_recommendations']}")
        print(f"Proposals generated: {len(proposals)}")
        print(f"Total opportunities tracked: {analytics['summary']['total_opportunities']}")

    # Save pipeline run summary
    summary_dir = PROJECT_ROOT / "data" / "processed"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = summary_dir / f"pipeline_run_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def main():
    parser = argparse.ArgumentParser(description="SAMgov Pipeline")
    parser.add_argument("--scan-only", action="store_true", help="Run scan only")
    parser.add_argument("--analyze-only", action="store_true", help="Run analytics only")
    parser.add_argument("--propose", type=str, help="Generate proposal for notice ID")
    parser.add_argument("--export", action="store_true", help="Export data to CSV")
    parser.add_argument("--stats", action="store_true", help="Show database stats")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    verbose = not args.quiet

    if args.scan_only:
        summary = run_scan_and_save(verbose=verbose)
        print(json.dumps(summary, indent=2, default=str))

    elif args.analyze_only:
        report = generate_analytics_report()
        print(json.dumps(report["summary"], indent=2))

    elif args.propose:
        result = generate_for_notice(args.propose)
        print(f"Proposal generated for: {result['title']}")
        print(f"TODO items: {len(result['todo_list'])}")

    elif args.export:
        db = OpportunityDB()
        path = db.export_csv()
        print(f"Exported to: {path}")

    elif args.stats:
        db = OpportunityDB()
        stats = db.get_stats()
        print(json.dumps(stats, indent=2))

    else:
        run_full_pipeline(verbose=verbose)


if __name__ == "__main__":
    main()
