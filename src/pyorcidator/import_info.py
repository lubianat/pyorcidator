"""Import ORCID information into Wikidata."""

import webbrowser
from typing import Optional
from urllib.parse import quote

import click
from quickstatements_client import (
    QuickStatementsClient,
    lines_to_new_tab,
    lines_to_url,
    render_lines,
)

from .helper import get_orcid_quickstatements

__all__ = [
    "main",
]


@click.command(name="import")
@click.option("--orcid", prompt=True, help="The ORCID Id to look up")
@click.option(
    "-b",
    "--open-browser",
    is_flag=True,
    help="Automatically open browser with QuickStatements",
)
@click.option(
    "-u",
    "--upload",
    help="Automatically send to QuickStatements API. Give batch name.",
)
@click.option(
    "--batch-name",
    help="QuickStatements batch name.",
)
def main(orcid: str, open_browser: bool, upload: bool, batch_name: Optional[str]):
    """Import ORCID information into Wikidata."""
    lines = get_orcid_quickstatements(orcid)
    print(render_lines(lines))
    print(lines_to_url(lines))
    if open_browser:
        lines_to_new_tab(lines)
    if upload or batch_name is not None:
        client = QuickStatementsClient()
        res = client.post(lines, batch_name=batch_name)
        click.echo(f"Job posted to {res.batch_url}")


if __name__ == "__main__":
    main()
