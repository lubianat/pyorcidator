"""
Tests for the helper module
"""

from pyorcidator.helper import get_date, get_paper_dois, lookup_id


def test_lookup_id():

    tiago = lookup_id("0000-0003-2473-2313", "P496", "LAST")

    assert tiago == "Q90076935"


def test_get_date(sample_orcid_data):
    education_data = sample_orcid_data["activities-summary"]["educations"]["education-summary"]

    test_start_date = get_date(education_data[1])
    test_end_date = get_date(education_data[1], start_or_end="end")

    assert test_start_date == "+2015-08-00T00:00:00Z/10"
    assert test_end_date == "+2017-10-27T00:00:00Z/11"


def test_get_paper_dois(sample_orcid_data):
    test_papers = sample_orcid_data["activities-summary"]["works"]["group"]

    test_dois = get_paper_dois(test_papers)
    assert test_dois[0] == "10.3233/jad-201397"
