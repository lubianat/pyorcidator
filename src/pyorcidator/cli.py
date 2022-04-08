import click

from . import import_info, import_info_from_list


@click.group()
def cli():
    """PyORCIDator."""


cli.add_command(import_info.main)
cli.add_command(import_info_from_list.main)

if __name__ == "__main__":
    cli()
