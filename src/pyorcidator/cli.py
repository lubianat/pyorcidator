import click

from pyorcidator import import_info, import_info_from_list, run_for_event


@click.group()
def cli():
    """PyORCIDator."""


cli.add_command(import_info.main)
cli.add_command(import_info_from_list.main)
cli.add_command(run_for_event.import_orcids_from_event)
if __name__ == "__main__":
    cli()
