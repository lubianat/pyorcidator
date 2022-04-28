from .helper import *


@click.command(name="import_list")
@click.option(
    "--orcid_list",
    prompt="Path to list of ORCIDs",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="The path for a txt file containing one ORCID per line",
)
@click.pass_context
def main(ctx: click.Context, orcid_list: str):
    list_of_orcids = orcid_list.read_text().split("\n")
    qs = ""
    for orcid in list_of_orcids:
        qs = qs + render_orcid_qs(orcid)
    create_qs_url(qs, ctx.obj["open_browser"])


if __name__ == "__main__":
    main()
