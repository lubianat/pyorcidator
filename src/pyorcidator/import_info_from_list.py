from pathlib import Path
from urllib.parse import quote

import click

from .helper import *


@click.command(name="import_list")
@click.option(
    "--orcid_list",
    prompt="Path to list of ORCIDs",
    type=click.Path(),
    help="The path for a txt file containing one ORCID per line",
)
def main(orcid_list: str):
    p = Path(orcid_list)
    list_of_orcids = p.read_text().split("\n")
    qs = ""
    for orcid in list_of_orcids:
        qs = qs + render_orcid_qs(orcid)
    quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
    url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
    print(qs)
    print(url)


if __name__ == "__main__":
    main()
