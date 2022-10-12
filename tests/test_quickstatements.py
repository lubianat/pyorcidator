"""Tests for quickstatements."""

import datetime
import unittest

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
        subject = "Q47475003"
        reference_url = TextQualifier(
            predicate="S854", target=f"https://orcid.org/0000-0003-4423-4370"
        )
        start_date = DateQualifier.start_time(datetime.datetime(year=2021, day=15, month=2))
        position_held = EntityQualifier(predicate="P39", target="Q1706722")
        employment_line = EntityLine(
            subject=subject,
            predicate="P108",  # employer
            target="Q49121",  # Harvard medical school
            qualifiers=[reference_url, start_date, position_held],
        )
        self.assertEqual(
            'Q47475003|P108|Q49121|S854|"https://orcid.org/0000-0003-4423-4370"',
            employment_line.get_line(),
        )

        nickname_line = TextLine(
            subject=subject,
            predicate="P1449",
            text="Charlie",
        )
        self.assertEqual('Q47475003|P1449|"Charlie"', nickname_line.get_line())
