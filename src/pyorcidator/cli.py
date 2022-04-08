import click
from . import import_info


@click.group()
def cli():
    """PyORCIDator."""


cli.add_command(import_info.main)

if __name__ == "__main__":
    cli()
