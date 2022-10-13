import datetime
from dataclasses import dataclass
from typing import Optional

__all__ = [
    "AffiliationEntry",
]


@dataclass
class AffiliationEntry:
    """Class for capturing the info for an affiliation (education or employment) entry on ORCID."""

    institution: str
    role: Optional[str] = None
    start_date: Optional[datetime.datetime] = None
    start_date_precision: Optional[int] = None
    end_date: Optional[datetime.datetime] = None
    end_date_precision: Optional[int] = None
