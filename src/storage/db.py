"""
Opportunity Storage Layer

JSON-file-based database for storing all scanned opportunities with:
- Full detail capture (every field from SAM.gov)
- Timestamped records (first_seen, last_updated, scan history)
- Version tracking when opportunities are amended
- Deduplication-aware upsert logic
- Recommendation history tracking
- Export to CSV/Excel
"""

import json
import csv
import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Main database files
OPPORTUNITIES_DB = DATA_DIR / "opportunities.json"
RECOMMENDATION_HISTORY = DATA_DIR / "recommendation_history.json"
SCAN_LOG = DATA_DIR / "scan_log.json"


class OpportunityDB:
    """JSON-file-based opportunity database with full history tracking."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or OPPORTUNITIES_DB
        self.rec_history_path = RECOMMENDATION_HISTORY
        self.scan_log_path = SCAN_LOG
        self._ensure_dirs()
        self.opportunities = self._load_db()
        self.rec_history = self._load_rec_history()

    def _ensure_dirs(self):
        """Create data directories if they don't exist."""
        for d in [DATA_DIR, RAW_DIR, PROCESSED_DIR, DATA_DIR / "recommendations"]:
            d.mkdir(parents=True, exist_ok=True)

    def _load_db(self) -> dict:
        """Load the opportunities database. Keyed by notice_id."""
        if self.db_path.exists():
            with open(self.db_path, "r") as f:
                return json.load(f)
        return {}

    def _save_db(self):
        """Save the opportunities database atomically."""
        tmp = self.db_path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self.opportunities, f, indent=2, default=str)
        shutil.move(str(tmp), str(self.db_path))

    def _load_rec_history(self) -> dict:
        """Load recommendation history. Keyed by notice_id -> list of dates."""
        if self.rec_history_path.exists():
            with open(self.rec_history_path, "r") as f:
                return json.load(f)
        return {}

    def _save_rec_history(self):
        """Save recommendation history."""
        with open(self.rec_history_path, "w") as f:
            json.dump(self.rec_history, f, indent=2, default=str)

    def upsert_opportunities(self, opps: list[dict]) -> tuple[int, int]:
        """
        Insert or update opportunities.
        Returns (new_count, updated_count).
        Preserves first_seen, updates last_updated, tracks scan history.
        """
        new_count = 0
        updated_count = 0
        now = datetime.now(timezone.utc).isoformat()

        for opp in opps:
            nid = opp.get("notice_id", "")
            if not nid:
                continue

            if nid in self.opportunities:
                # Update existing — preserve first_seen, update timestamps
                existing = self.opportunities[nid]
                opp["first_seen"] = existing.get("first_seen", now)

                # Track scan history
                scan_history = existing.get("scan_history", [])
                scan_history.append({
                    "timestamp": now,
                    "fit_score": opp.get("fit_score", 0),
                    "status": opp.get("status", "active"),
                })
                opp["scan_history"] = scan_history

                # Preserve proposal status and recommendation history
                opp["proposal_status"] = existing.get("proposal_status", "not_started")
                opp["recommendation_status"] = existing.get("recommendation_status", "unscored")
                opp["recommendation_date"] = existing.get("recommendation_date", "")

                # Check if content changed (amendment detection)
                old_desc = existing.get("description", "")
                new_desc = opp.get("description", "")
                if old_desc != new_desc and old_desc:
                    amendments = existing.get("amendments", [])
                    amendments.append({
                        "date": now,
                        "previous_modified": existing.get("modified_date", ""),
                        "new_modified": opp.get("modified_date", ""),
                    })
                    opp["amendments"] = amendments
                    opp["was_amended"] = True
                else:
                    opp["amendments"] = existing.get("amendments", [])
                    opp["was_amended"] = False

                self.opportunities[nid] = opp
                updated_count += 1
            else:
                # New opportunity
                opp["first_seen"] = now
                opp["scan_history"] = [{
                    "timestamp": now,
                    "fit_score": opp.get("fit_score", 0),
                    "status": "active",
                }]
                opp["amendments"] = []
                opp["was_amended"] = False
                self.opportunities[nid] = opp
                new_count += 1

        # Save raw scan data with timestamp
        self._save_raw_scan(opps)
        self._save_db()
        self._log_scan(len(opps), new_count, updated_count)

        return new_count, updated_count

    def _save_raw_scan(self, opps: list[dict]):
        """Save raw scan data with timestamp for historical analysis."""
        now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        raw_file = RAW_DIR / f"scan_{now}.json"
        # Save without raw_data to keep file sizes manageable
        clean = []
        for o in opps:
            c = {k: v for k, v in o.items() if k != "raw_data"}
            clean.append(c)
        with open(raw_file, "w") as f:
            json.dump(clean, f, indent=2, default=str)

    def _log_scan(self, total: int, new: int, updated: int):
        """Log scan metadata."""
        log = []
        if self.scan_log_path.exists():
            with open(self.scan_log_path, "r") as f:
                log = json.load(f)
        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_scanned": total,
            "new_opportunities": new,
            "updated_opportunities": updated,
            "total_in_db": len(self.opportunities),
        })
        with open(self.scan_log_path, "w") as f:
            json.dump(log, f, indent=2, default=str)

    def get_recommendations(
        self,
        min_score: int = 70,
        max_results: int = 3,
        cooldown_days: int = 14,
    ) -> list[dict]:
        """
        Get today's recommendations.
        Rules:
        1. Only active opportunities
        2. Score >= min_score
        3. Not recommended within cooldown_days
        4. Prefer new or recently amended opportunities
        5. Sort by score descending
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=cooldown_days)
        candidates = []

        for nid, opp in self.opportunities.items():
            # Must be active
            if opp.get("status") != "active":
                continue

            # Must meet score threshold
            if opp.get("fit_score", 0) < min_score:
                continue

            # Check cooldown
            last_rec_dates = self.rec_history.get(nid, [])
            if last_rec_dates:
                last_rec = datetime.fromisoformat(last_rec_dates[-1])
                if last_rec.tzinfo is None:
                    last_rec = last_rec.replace(tzinfo=timezone.utc)
                if last_rec > cutoff:
                    continue

            # Priority boost for new or amended
            priority = opp.get("fit_score", 0)
            if len(opp.get("scan_history", [])) <= 1:
                priority += 10  # New opportunity bonus
            if opp.get("was_amended"):
                priority += 5  # Recently amended bonus

            candidates.append((priority, opp))

        # Sort by priority descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Take top N
        results = []
        today = now.isoformat()
        for _, opp in candidates[:max_results]:
            nid = opp["notice_id"]
            # Record recommendation
            if nid not in self.rec_history:
                self.rec_history[nid] = []
            self.rec_history[nid].append(today)
            opp["recommendation_status"] = "recommended"
            opp["recommendation_date"] = today
            results.append(opp)

        self._save_rec_history()
        self._save_db()
        return results

    def get_opportunity(self, notice_id: str) -> Optional[dict]:
        """Get a single opportunity by notice ID."""
        return self.opportunities.get(notice_id)

    def get_all_opportunities(self, status: Optional[str] = None) -> list[dict]:
        """Get all opportunities, optionally filtered by status."""
        opps = list(self.opportunities.values())
        if status:
            opps = [o for o in opps if o.get("status") == status]
        return sorted(opps, key=lambda x: x.get("fit_score", 0), reverse=True)

    def update_proposal_status(self, notice_id: str, status: str, notes: str = ""):
        """Update the proposal status for an opportunity."""
        if notice_id in self.opportunities:
            self.opportunities[notice_id]["proposal_status"] = status
            self.opportunities[notice_id]["proposal_notes"] = notes
            self.opportunities[notice_id]["proposal_updated"] = (
                datetime.now(timezone.utc).isoformat()
            )
            self._save_db()

    def export_csv(self, output_path: Optional[Path] = None) -> Path:
        """Export all opportunities to CSV."""
        if output_path is None:
            output_path = PROCESSED_DIR / f"opportunities_{datetime.now().strftime('%Y-%m-%d')}.csv"

        fields = [
            "notice_id", "title", "agency", "department", "sub_tier", "office",
            "notice_type", "set_aside", "naics_code", "psc_code",
            "response_date", "published_date", "modified_date",
            "estimated_value", "place_of_performance",
            "fit_score", "fit_rationale",
            "recommendation_status", "proposal_status",
            "first_seen", "last_updated", "sam_url",
        ]

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for opp in self.get_all_opportunities():
                writer.writerow(opp)

        return output_path

    def get_stats(self) -> dict:
        """Get database statistics."""
        opps = list(self.opportunities.values())
        active = [o for o in opps if o.get("status") == "active"]
        recommended = [o for o in opps if o.get("recommendation_status") == "recommended"]
        proposals = {
            "not_started": len([o for o in opps if o.get("proposal_status") == "not_started"]),
            "in_progress": len([o for o in opps if o.get("proposal_status") == "in_progress"]),
            "submitted": len([o for o in opps if o.get("proposal_status") == "submitted"]),
            "won": len([o for o in opps if o.get("proposal_status") == "won"]),
            "lost": len([o for o in opps if o.get("proposal_status") == "lost"]),
        }

        # Score distribution
        scores = [o.get("fit_score", 0) for o in active]
        score_dist = {
            "90-100": len([s for s in scores if 90 <= s <= 100]),
            "70-89": len([s for s in scores if 70 <= s < 90]),
            "50-69": len([s for s in scores if 50 <= s < 70]),
            "0-49": len([s for s in scores if s < 50]),
        }

        return {
            "total_opportunities": len(opps),
            "active": len(active),
            "recommended": len(recommended),
            "proposals": proposals,
            "score_distribution": score_dist,
            "scan_count": len(self._load_scan_log()),
        }

    def _load_scan_log(self) -> list:
        if self.scan_log_path.exists():
            with open(self.scan_log_path, "r") as f:
                return json.load(f)
        return []
