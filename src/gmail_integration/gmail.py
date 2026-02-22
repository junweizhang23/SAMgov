"""
Gmail Integration Module

Integrates with Gmail via MCP (Model Context Protocol) for:
- Sending proposal drafts and capability statements
- Tracking sent proposals and responses
- Linking opportunities to email threads

Note: This module is designed to be called from the Manus agent context
where the Gmail MCP server is available. For standalone usage, it provides
helper functions to format emails and track correspondence.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.db import OpportunityDB

# Email tracking database
EMAIL_TRACKING_FILE = PROJECT_ROOT / "data" / "email_tracking.json"


class GmailIntegration:
    """Gmail integration for proposal sending and tracking."""

    def __init__(self):
        self.tracking = self._load_tracking()

    def _load_tracking(self) -> dict:
        """Load email tracking data."""
        if EMAIL_TRACKING_FILE.exists():
            with open(EMAIL_TRACKING_FILE, "r") as f:
                return json.load(f)
        return {"sent": [], "threads": {}}

    def _save_tracking(self):
        """Save email tracking data."""
        EMAIL_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EMAIL_TRACKING_FILE, "w") as f:
            json.dump(self.tracking, f, indent=2, default=str)

    def format_introduction_email(self, opp: dict) -> dict:
        """
        Format an introduction email to the contracting officer.
        Returns a dict ready for gmail_send_messages MCP tool.
        """
        contacts = opp.get("contacts", [])
        if not contacts:
            return None

        to_email = contacts[0].get("email", "")
        if not to_email:
            return None

        notice_id = opp.get("notice_id", "")
        title = opp.get("title", "")
        agency = opp.get("agency", "")

        subject = f"Interest in {notice_id} - {title[:60]}"

        content = f"""Dear Contracting Officer,

I am writing to express our interest in {notice_id}: {title}.

We are a Service-Disabled Veteran-Owned Small Business (SDVOSB) with deep expertise in artificial intelligence, machine learning, and software engineering. Our principal holds a PhD in Applied Mathematics with specialization in AI/ML and brings extensive experience from both the private sector and military service (Air Force Reserve).

Our core capabilities include:
- AI/ML system design and implementation
- Software development and cloud architecture
- Data analytics and visualization
- Research and development in applied mathematics

We would welcome the opportunity to discuss how our capabilities align with your requirements. Please let us know if there are any questions or if additional information would be helpful.

Respectfully,
Alfred
SDVOSB Principal
"""

        return {
            "to": [to_email],
            "subject": subject,
            "content": content,
            "notice_id": notice_id,
        }

    def format_proposal_email(self, opp: dict, proposal_path: str = "") -> dict:
        """
        Format a proposal submission email.
        Returns a dict ready for gmail_send_messages MCP tool.
        """
        contacts = opp.get("contacts", [])
        if not contacts:
            return None

        to_email = contacts[0].get("email", "")
        if not to_email:
            return None

        notice_id = opp.get("notice_id", "")
        title = opp.get("title", "")

        subject = f"Proposal Submission - {notice_id}: {title[:50]}"

        content = f"""Dear Contracting Officer,

Please find attached our proposal in response to {notice_id}: {title}.

We are a Service-Disabled Veteran-Owned Small Business (SDVOSB) and are pleased to submit this response for your consideration. Our team brings specialized expertise in artificial intelligence, machine learning, and software engineering that directly addresses the requirements outlined in this solicitation.

Should you have any questions or require additional information, please do not hesitate to contact us.

Respectfully,
Alfred
SDVOSB Principal
"""

        email = {
            "to": [to_email],
            "subject": subject,
            "content": content,
            "notice_id": notice_id,
        }

        if proposal_path and os.path.exists(proposal_path):
            email["attachments"] = [proposal_path]

        return email

    def record_sent_email(self, notice_id: str, email_type: str, to: str, subject: str):
        """Record that an email was sent for tracking."""
        record = {
            "notice_id": notice_id,
            "type": email_type,
            "to": to,
            "subject": subject,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
        }
        self.tracking["sent"].append(record)
        self._save_tracking()

        # Update opportunity proposal status
        db = OpportunityDB()
        if email_type == "proposal":
            db.update_proposal_status(notice_id, "submitted")
        elif email_type == "introduction":
            db.update_proposal_status(notice_id, "contacted")

    def search_responses(self, notice_id: str) -> str:
        """
        Generate a Gmail search query to find responses related to a notice.
        This query can be used with the gmail_search_messages MCP tool.
        """
        return f"subject:{notice_id} OR subject:\"Re:\" {notice_id}"

    def get_tracking_summary(self) -> dict:
        """Get a summary of all email tracking data."""
        sent = self.tracking.get("sent", [])
        by_type = {}
        by_notice = {}

        for s in sent:
            t = s.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

            nid = s.get("notice_id", "unknown")
            if nid not in by_notice:
                by_notice[nid] = []
            by_notice[nid].append(s)

        return {
            "total_sent": len(sent),
            "by_type": by_type,
            "by_notice": by_notice,
        }

    def generate_mcp_command(self, email: dict) -> str:
        """
        Generate the manus-mcp-cli command to send an email.
        This is for reference/documentation; actual sending should be done
        through the Manus agent's MCP integration.
        """
        messages = [{
            "to": email["to"],
            "subject": email["subject"],
            "content": email["content"],
        }]

        if "attachments" in email:
            messages[0]["attachments"] = email["attachments"]

        input_json = json.dumps({"messages": messages})
        return f'manus-mcp-cli tool call gmail_send_messages --server gmail --input \'{input_json}\''
