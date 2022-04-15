import click

from .helper import *


@click.command(name="import")
@click.option("--orcid", prompt=True, help="The ORCID ID to look up")
@click.pass_context
def main(ctx: click.Context, orcid: str):
    qs = render_orcid_qs(orcid)
    create_qs_url(qs, ctx.obj["open_browser"])


if __name__ == "__main__":
    main()
