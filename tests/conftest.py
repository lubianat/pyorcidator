import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_orcid_data():
    sample_path = Path(__file__).parent.joinpath("sample.json")

    return json.loads(sample_path.read_text())


@pytest.fixture()
def wikidata_api_result():
    sample_path = Path(__file__).parent.joinpath("wikidata_api_result.json")

    return json.loads(sample_path.read_text())
