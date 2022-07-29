from dataclasses import dataclass


@dataclass
class EducationEntry:
    """Class for capturing the info for an education entry on ORCID."""

    institution: str
    degree: str = None
    start_date: str = None
    end_date: str = None
