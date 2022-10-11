"""Update the roles dictionary with from Wikidata."""

import json
from pathlib import Path
from typing import Union, Collection

from textwrap import dedent

from ..wikidata_lookup import query_wikidata

__all__ = [
    "update",
]


def _removeprefix(s: str, prefix: str) -> str:
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


def update(
    parents: Union[str, Collection[str]],
    path: Path,
    clause: str = "?item wdt:P279* ?ancestor .",
) -> None:
    if isinstance(parents, str):
        values = f"wd:{parents}"
    else:
        values = " ".join(f"wd:{v}" for v in parents)
    query = dedent(
        f"""\
        SELECT ?itemLabel ?item
        WHERE {{
            VALUES ?ancestor {{ {values} }}
            {clause}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
    """
    )
    print(query)
    data = json.loads(path.read_text()) if path.is_file() else {}
    it = (
        (
            record["itemLabel"]["value"].strip().replace("  ", " "),
            _removeprefix(record["item"]["value"], "http://www.wikidata.org/entity/"),
        )
        for record in query_wikidata(query)
    )
    data.update((label, qid) for label, qid in it if label != qid)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
