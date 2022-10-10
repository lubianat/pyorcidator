"""Update degrees from wikidata."""

import json
from pathlib import Path

import click

from pyorcidator.dictionaries import DEGREE_PATH
from pyorcidator.wikidata_lookup import query_wikidata

HERE = Path(__file__).parent.resolve()
QUERY = """\
SELECT DISTINCT ?label ?item
WHERE {
  ?item wdt:P279* wd:Q3529618 .
  ?item rdfs:label ?label .
}
"""


def _removeprefix(s: str, prefix: str) -> str:
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


@click.command(name="update-degrees")
def main():
    """Update the degrees lookup able from Wikidata."""
    data = json.loads(DEGREE_PATH.read_text())
    data.update(
        (record["label"]["value"], _removeprefix(record["item"]["value"], "http://www.wikidata.org/entity/"))
        for record in query_wikidata(QUERY)
    )
    DEGREE_PATH.write_text(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))


if __name__ == '__main__':
    main()
