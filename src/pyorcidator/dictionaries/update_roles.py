"""Update the roles dictionary with from Wikidata."""

import json
from pathlib import Path

import click
from textwrap import dedent

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
@click.option("--parent", default="Q189533")
def main(parent):
    """Update the degrees lookup able from Wikidata."""
    query = dedent(f"""\
        SELECT ?itemLabel ?item
        WHERE {{
          ?item wdt:P279* wd:{parent} .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
    """)
    data = json.loads(DEGREE_PATH.read_text())
    it = (
        (record["itemLabel"]["value"], _removeprefix(record["item"]["value"], "http://www.wikidata.org/entity/"))
        for record in query_wikidata(query)
    )
    data.update(
        (label, qid)
        for label, qid in it
        if label != qid
    )
    DEGREE_PATH.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == '__main__':
    main()
