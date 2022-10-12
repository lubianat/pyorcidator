"""Tests for quickstatements."""

import datetime
import unittest

from pyorcidator.helper import get_orcid_quickstatements
from pyorcidator.quickstatements import (
    DateQualifier,
    EntityLine,
    EntityQualifier,
    TextLine,
    TextQualifier,
)


class TestQuickStatements(unittest.TestCase):
    """Tests for quickstatements."""

    def test_quickstatements(self):
        """Test quick statements."""
        subject_qid = "Q47475003"  # Charles Tapley Hoyt
        subject_orcid = "0000-0003-4423-4370"
        reference_url_qualifier = TextQualifier(
            predicate="S854", target=f"https://orcid.org/0000-0003-4423-4370"
        )
        start_date = datetime.datetime(year=2021, day=15, month=2)
        start_date_qualifier = DateQualifier.start_time(start_date)
        position_held_qualifier = EntityQualifier(predicate="P39", target="Q1706722")
        employment_line = EntityLine(
            subject=subject_qid,
            predicate="P108",  # employer
            target="Q49121",  # Harvard medical school
            qualifiers=[reference_url_qualifier, start_date_qualifier, position_held_qualifier],
        )
        self.assertEqual(
            'Q47475003|P108|Q49121|S854|"https://orcid.org/0000-0003-4423-4370"|S580|+2021-02-15T00:00:00Z|P39|Q1706722',
            employment_line.get_line(),
        )

        nickname_line = TextLine(
            subject=subject_qid,
            predicate="P1449",
            target="Charlie",
        )
        self.assertEqual('Q47475003|P1449|"Charlie"', nickname_line.get_line())

        lines = get_orcid_quickstatements(subject_orcid)
        # self.assertTrue(any(
        #     line == nickname_line
        #     for line in lines
        # ))

        harvard_line = next(
            line for line in lines if line.predicate == "P108" and line.target == "Q49121"
        )
        self.assertLess(0, len(harvard_line.qualifiers))
        self.assertTrue(
            any(qualifier.predicate == "S580" for qualifier in harvard_line.qualifiers),
            msg="No start time qualifier found",
        )
        self.assertTrue(
            any(
                qualifier.predicate == "S580" and qualifier.target == start_date
                for qualifier in harvard_line.qualifiers
            )
        )
