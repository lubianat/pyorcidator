"""Update the roles dictionary with from Wikidata."""

import click

from pyorcidator.dictionaries import ROLE_PATH
from pyorcidator.dictionaries.utils import update_curation_dictionary

QUERY = """\
SELECT DISTINCT ?label ?item
WHERE {
  ?item wdt:P279* wd:Q3529618 .
  ?item rdfs:label ?label .
}
"""
ANCESTORS = {
    "Q189533": "academic degree",
}


@click.command(name="update-degrees")
def main():
    """Update the degrees lookup able from Wikidata."""
    update_curation_dictionary(parents=sorted(ANCESTORS), path=ROLE_PATH)


if __name__ == "__main__":
    main()
