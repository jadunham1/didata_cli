import click
from didata_cli.cli import pass_client
from libcloud.common.dimensiondata import DimensionDataAPIException
from didata_cli.utils import handle_dd_api_exception


@click.group()
@pass_client
def cli(client):
    pass


@cli.command()
@click.option('--datacenterId', type=click.UNPROCESSED, help="Filter by datacenter Id")
@pass_client
def list(client, datacenterid):
    try:
        locations = client.node.list_locations(ex_id=datacenterid)
        for location in locations:
            click.secho("{0}".format(location.name), bold=True)
            click.secho("ID: {0}".format(location.id))
            click.secho("Description: {0}".format(location.country))
            click.secho("")
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)
