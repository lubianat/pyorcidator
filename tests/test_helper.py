"""
Tests for the helper module
"""

from pyorcidator.helper import (
    get_date,
    get_external_ids,
    get_orcid_data,
    get_organization_list,
    get_paper_dois,
    lookup_id,
    process_keyword_entries,
    process_paper_entries,
    render_orcid_qs,
)


def test_lookup_id():
    tiago = lookup_id("0000-0003-2473-2313", "P496", "LAST")
    assert tiago == "Q90076935"


def test_get_paper_dois(sample_orcid_data):
    test_papers = sample_orcid_data["activities-summary"]["works"]["group"]

    test_dois = get_paper_dois(test_papers)
    assert "10.3233/jad-201397" in test_dois


def test_process_paper_entries(sample_orcid_data):

    test_papers = sample_orcid_data["activities-summary"]["works"]["group"]
    test_dois = get_paper_dois(test_papers)

    entries = process_paper_entries(
        orcid="0000-0003-4423-4370",
        researcher_qid="Q47475003",
        paper_dois=test_dois,
        property_id="P50",
    )

    entries_qids = [entry.subject for entry in entries]

    assert len(entries) == 31
    assert entries_qids[1:3] == ["Q63709723", "Q82511885"]


def test_get_org_list(sample_orcid_data):
    employment_data = sample_orcid_data["activities-summary"]["employments"]["employment-summary"]

    data = get_organization_list(employment_data)

    # Q152171 = "University of Bonn" on the sample dataset
    # Returns QID because this instance has a GRID disambiguator
    assert data == [
        "Harvard Medical School",
        "Enveda Biosciences",
        "Q152171",
        "Fraunhofer SCAI",
    ]


def test_get_field_of_work(sample_orcid_data):

    keyword_data = sample_orcid_data["person"]["keywords"]["keyword"]

    fields = process_keyword_entries(
        orcid="0000-0003-4423-4370",
        researcher_qid="Q47475003",
        keyword_data=keyword_data,
        property_id="P101",
    )

    assert len(fields) == 5
    assert fields[1].target == "Q114662947"


def test_get_loop_id(sample_orcid_data):
    goal = "827476"
    result = get_external_ids(sample_orcid_data)
    assert result["Loop profile"] == goal


def test_render_orcid_runs():
    render_orcid_qs("0000-0003-4423-4370")


def test_get_github(orcid_w_external_links):
    """Test getting a github link."""
    assert orcid_w_external_links["github"] == "seljaseppala"


def test_get_twitter(orcid_w_other_external_links):
    """Test getting a twitter link."""
    assert orcid_w_other_external_links["twitter"] == "egonwillighagen"


def test_get_github_no_https(orcid_w_other_external_links):
    """Test getting a github link with no https."""
    assert orcid_w_other_external_links["github"] == "egonw"


def test_get_scopus(orcid_w_external_links):
    """Test getting a scopus ID."""
    assert orcid_w_external_links["Scopus Author ID"] == "56352777000"
