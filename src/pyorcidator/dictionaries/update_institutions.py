"""Update the institutions dictionary with from Wikidata."""

import click

from pyorcidator.dictionaries import INSTITUTIONS_PATH
from pyorcidator.dictionaries.utils import update

ANCESTORS = {
    "Q4671277": "academic institution",
}


@click.command(name="update-institutions")
def main():
    """Update the institutions lookup table from Wikidata."""
    update(
        parents=sorted(ANCESTORS),
        path=INSTITUTIONS_PATH,
        clause="?item wdt:P31/wdt:P279* ?ancestor .",
    )


if __name__ == "__main__":
    main()
