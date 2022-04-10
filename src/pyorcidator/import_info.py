import webbrowser
from urllib.parse import quote

import click
from pathlib import Path

from .helper import *


@click.command(name="import")
@click.option("--orcid", prompt=True, help="The ORCID Id to look up")
@click.option(
    "--open-browser",
    is_flag=True,
    help="Automatically open browser with QuickStatements",
)
def main(orcid: str, open_browser: bool):
    qs = render_orcid_qs(orcid)
    quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
    url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
    print(qs)
    print(url)
    if open_browser:
        webbrowser.open_new_tab(url)


if __name__ == "__main__":
    main()
