from .helper import *
from urllib.parse import quote
import click


@click.command(name="import")
@click.option("--orcid", prompt=True, help="The ORCID Id to look up")
def main(orcid: str):
    qs = render_orcid_qs(orcid)
    quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
    url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
    print(qs)
    print(url)


if __name__ == "__main__":
    main()
