from dataclasses import dataclass
from typing import Optional

__all__ = [
    "EducationEntry",
]


@dataclass
class EducationEntry:
    """Class for capturing the info for an education entry on ORCID."""

    institution: str
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
