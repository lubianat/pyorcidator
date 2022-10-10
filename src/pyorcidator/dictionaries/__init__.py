""" Loads all JSON files into a single mother dict"""

import json
import logging
from pathlib import Path
from typing import Mapping

__all__ = [
    "dicts",
    "stem_to_path",
]

logger = logging.getLogger(__name__)

HERE = Path(__file__).parent.resolve()
DEGREE_PATH = HERE.joinpath("degree.json")

JSON_PATHS = HERE.glob("*.json")
for path in JSON_PATHS:
    logger.info("loading PyORCIDator data from %", path)

dicts = {path.stem: json.loads(path.read_text()) for path in JSON_PATHS}
stem_to_path: Mapping[str, Path] = {path.stem: path for path in JSON_PATHS}
