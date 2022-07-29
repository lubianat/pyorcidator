""" Loads all JSON files into a single mother dict"""

import json
from pathlib import Path

__all__ = [
    "dicts",
]

HERE = Path(__file__).parent.resolve()
for path in HERE.glob("*.json"):
    print(path)

dicts = {path.stem: json.loads(path.read_text()) for path in HERE.glob("*.json")}
