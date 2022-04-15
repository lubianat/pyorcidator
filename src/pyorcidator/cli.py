import click

from . import import_info, import_info_from_list


@click.group()
@click.option(
    "--open-browser",
    is_flag=True,
    help="Automatically open browser with QuickStatements",
)
@click.pass_context
def cli(ctx: click.Context, open_browser: bool):
    """PyORCIDator."""
    ctx.obj = {"open_browser": open_browser}


cli.add_command(import_info.main)
cli.add_command(import_info_from_list.main)

if __name__ == "__main__":
    cli()
