import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_data():
    sample_path = Path(__file__).parent.joinpath("sample.json")

    return json.loads(sample_path.read_text())
