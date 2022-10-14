"""Update the fields of work dictionary with data from Wikidata."""

import click

from pyorcidator.dictionaries import FIELDS_PATH
from pyorcidator.dictionaries.utils import update_curation_dictionary

ANCESTORS = {
    "Q11862829": "academic discipline",
}


@click.command(name="update-fields")
def main():
    """Update the institutions lookup table from Wikidata."""
    update_curation_dictionary(
        parents=sorted(ANCESTORS),
        path=FIELDS_PATH,
        clause="?item wdt:P31/wdt:P279* ?ancestor .",
    )


if __name__ == "__main__":
    main()
