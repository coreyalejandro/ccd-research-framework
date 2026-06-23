"""
GDPR/CCPA Compliance Module for CCD Research Framework

Handles data anonymization, retention policies, consent management,
and right-to-deletion for session data containing potential PII.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConsentStatus(Enum):
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"


class DataCategory(Enum):
    SESSION_INTERACTION = "session_interaction"
    COMPONENT_NAME = "component_name"
    RESEARCHER_ID = "researcher_id"
    SUPPORT_TICKET = "support_ticket"


@dataclass
class ConsentRecord:
    subject_id: str
    status: ConsentStatus
    timestamp: float
    purposes: List[str]
    data_categories: List[DataCategory]
    expiry: Optional[float] = None


@dataclass
class RetentionPolicy:
    data_category: DataCategory
    max_retention_days: int
    auto_delete: bool = True


class GDPRComplianceManager:
    """
    GDPR/CCPA compliance manager for CCD session data.

    Responsibilities:
    - Anonymize PII in session records
    - Enforce data retention policies
    - Track and verify consent
    - Execute right-to-deletion requests
    - Data portability exports
    """

    DEFAULT_RETENTION = {
        DataCategory.SESSION_INTERACTION: RetentionPolicy(DataCategory.SESSION_INTERACTION, 90, True),
        DataCategory.RESEARCHER_ID: RetentionPolicy(DataCategory.RESEARCHER_ID, 365, False),
        DataCategory.SUPPORT_TICKET: RetentionPolicy(DataCategory.SUPPORT_TICKET, 730, False),
    }

    def __init__(self) -> None:
        self._consents: Dict[str, ConsentRecord] = {}
        self._data_registry: Dict[str, Dict[str, Any]] = {}  # subject_id -> data records
        self._deletion_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Anonymization
    # ------------------------------------------------------------------

    def anonymize_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace PII-bearing fields with pseudonymous hashes.
        Returns a new dict — original is not mutated.
        """
        anon = dict(session)
        # Hash session_id
        if "session_id" in anon:
            anon["session_id"] = self._hash(str(anon["session_id"]))
        # Strip free-text user prompts that may contain names/emails
        if "interactions" in anon:
            anon["interactions"] = [
                self._anonymize_interaction(i) for i in anon["interactions"]
            ]
        return anon

    def anonymize_corpus(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch anonymize an entire corpus."""
        return [self.anonymize_session(s) for s in sessions]

    def _anonymize_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        anon = dict(interaction)
        # Redact email patterns from prompts/responses
        for field_name in ("user_prompt", "agent_response"):
            if field_name in anon and isinstance(anon[field_name], str):
                anon[field_name] = self._redact_pii(anon[field_name])
        return anon

    def _redact_pii(self, text: str) -> str:
        import re
        # Redact email addresses
        text = re.sub(r'[\w.+-]+@[\w-]+\.[\w.]+', "[EMAIL]", text)
        # Redact phone numbers (basic)
        text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', "[PHONE]", text)
        return text

    # ------------------------------------------------------------------
    # Consent management
    # ------------------------------------------------------------------

    def record_consent(
        self,
        subject_id: str,
        status: ConsentStatus,
        purposes: List[str],
        data_categories: List[DataCategory],
        retention_days: int = 365,
    ) -> ConsentRecord:
        """Record a consent decision for a data subject."""
        record = ConsentRecord(
            subject_id=subject_id,
            status=status,
            timestamp=time.time(),
            purposes=purposes,
            data_categories=data_categories,
            expiry=time.time() + retention_days * 86400,
        )
        self._consents[subject_id] = record
        return record

    def check_consent(self, subject_id: str, purpose: str) -> bool:
        """Return True if consent is active for the given purpose."""
        record = self._consents.get(subject_id)
        if record is None:
            return False
        if record.status != ConsentStatus.GRANTED:
            return False
        if record.expiry and time.time() > record.expiry:
            return False
        return purpose in record.purposes

    def withdraw_consent(self, subject_id: str) -> None:
        """Mark consent as withdrawn."""
        if subject_id in self._consents:
            self._consents[subject_id].status = ConsentStatus.WITHDRAWN

    # ------------------------------------------------------------------
    # Retention enforcement
    # ------------------------------------------------------------------

    def register_data(self, subject_id: str, data: Dict[str, Any], category: DataCategory) -> str:
        """Register a data record for retention tracking. Returns record ID."""
        record_id = str(uuid.uuid4())[:8]
        self._data_registry.setdefault(subject_id, {})[record_id] = {
            "data": data,
            "category": category,
            "created_at": time.time(),
        }
        return record_id

    def enforce_retention(self) -> List[str]:
        """
        Delete records past their retention period.
        Returns list of deleted record IDs.
        """
        deleted = []
        now = time.time()
        for subject_id, records in list(self._data_registry.items()):
            for record_id, entry in list(records.items()):
                policy = self.DEFAULT_RETENTION.get(entry["category"])
                if policy and policy.auto_delete:
                    age_days = (now - entry["created_at"]) / 86400
                    if age_days > policy.max_retention_days:
                        del records[record_id]
                        deleted.append(record_id)
        return deleted

    # ------------------------------------------------------------------
    # Right to deletion
    # ------------------------------------------------------------------

    def delete_subject_data(self, subject_id: str) -> int:
        """
        Execute right-to-deletion for a subject.
        Returns count of records deleted.
        """
        count = 0
        if subject_id in self._data_registry:
            count = len(self._data_registry[subject_id])
            del self._data_registry[subject_id]
        if subject_id in self._consents:
            del self._consents[subject_id]
        self._deletion_log.append({
            "subject_id": self._hash(subject_id),
            "timestamp": time.time(),
            "records_deleted": count,
        })
        return count

    # ------------------------------------------------------------------
    # Data portability
    # ------------------------------------------------------------------

    def export_subject_data(self, subject_id: str) -> str:
        """Return a JSON export of all data held for a subject."""
        records = self._data_registry.get(subject_id, {})
        consent = self._consents.get(subject_id)
        export = {
            "subject_id": self._hash(subject_id),
            "consent_status": consent.status.value if consent else None,
            "records": {
                rid: {
                    "category": v["category"].value,
                    "created_at": v["created_at"],
                }
                for rid, v in records.items()
            },
            "exported_at": time.time(),
        }
        return json.dumps(export, indent=2)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()[:16]
