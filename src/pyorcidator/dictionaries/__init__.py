""" Loads all JSON files into a single mother dict"""

import json
import logging
from pathlib import Path
from typing import Dict, Mapping

__all__ = [
    "dicts",
    "stem_to_path",
]

logger = logging.getLogger(__name__)

HERE = Path(__file__).parent.resolve()
ROLE_PATH = HERE.joinpath("role.json")
INSTITUTIONS_PATH = HERE.joinpath("institutions.json")

JSON_PATHS = sorted(HERE.glob("*.json"))
for path in JSON_PATHS:
    logger.info("loading PyORCIDator data from %", path)

dicts: Mapping[str, Dict[str, str]] = {
    path.stem: json.loads(path.read_text()) for path in JSON_PATHS
}
stem_to_path: Mapping[str, Path] = {path.stem: path for path in JSON_PATHS}
