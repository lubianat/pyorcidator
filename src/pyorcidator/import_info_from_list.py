from pathlib import Path

import click

from .helper import *


@click.command(name="import_list")
@click.option(
    "--orcid_list",
    prompt="Path to list of ORCIDs",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="The path for a txt file containing one ORCID per line",
)
@click.option(
    "--open-browser",
    is_flag=True,
    help="Automatically open browser with QuickStatements",
)
def main(orcid_list: str, open_browser: bool):
    list_of_orcids = orcid_list.read_text().split("\n")
    qs = ""
    for orcid in list_of_orcids:
        qs = qs + render_orcid_qs(orcid)
    create_qs_url(qs, open_browser)


if __name__ == "__main__":
    main()
