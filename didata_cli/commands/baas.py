import click
from didata_cli.entry import pass_prearguments

@didata_cli.cli.group()
@pass_prearguments
def backup(config):
   click.secho("In backups")

@backup.command()
@click.option('--new_string', default='Hello')
@pass_prearguments
def list(config, new_string):
   click.echo(new_string)

