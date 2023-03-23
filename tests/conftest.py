import json
from pathlib import Path

import pytest

from pyorcidator.helper import get_external_ids, get_orcid_data


@pytest.fixture
def sample_orcid_data():
    sample_path = Path(__file__).parent.joinpath("sample.json")

    return json.loads(sample_path.read_text())


@pytest.fixture()
def wikidata_api_result():
    sample_path = Path(__file__).parent.joinpath("wikidata_api_result.json")

    return json.loads(sample_path.read_text())


@pytest.fixture
def orcid_w_external_links():
    orcid = "0000-0002-0791-1347"  #   Selja Seppälä
    data = get_orcid_data(orcid)
    ids = get_external_ids(data)

    return ids


@pytest.fixture
def orcid_w_other_external_links():
    # Useful for testing twitter and github with no https in URL
    orcid = "0000-0003-4423-4370"  # Charlie Hoyt
    data = get_orcid_data(orcid)
    ids = get_external_ids(data)

    return ids
