import click

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
    create_qs_url(qs, open_browser)


if __name__ == "__main__":
    main()
