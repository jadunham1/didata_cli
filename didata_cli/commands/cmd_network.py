import click
from didata_cli.cli import pass_client
from libcloud.common.dimensiondata import DimensionDataAPIException
from didata_cli.utils import handle_dd_api_exception, get_single_server_id_from_filters
from libcloud.common.dimensiondata import DimensionDataAPIException


@click.group()
@pass_client
def cli(client):
    pass

@cli.command()
@click.option('--datacenterId', type=click.UNPROCESSED, help="Filter by datacenter Id")
@pass_client
def list_network_domains(client, datacenterid):
    try:
        network_domains = client.node.ex_list_network_domains(location=datacenterid)
        for network_domain in network_domains:
            click.secho("{0}".format(network_domain.name), bold=True)
            click.secho("ID: {0}".format(network_domain.id))
            click.secho("Description: {0}".format(network_domain.description))
            click.secho("Plan: {0}".format(network_domain.plan))
            click.secho("Location: {0}".format(network_domain.location.id))
            click.secho("Status: {0}".format(network_domain.status))
            click.secho("")
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@cli.command()
@click.option('--datacenterId', required=True, type=click.UNPROCESSED, help="Location for the network domain")
@click.option('--name', required=True, help="Name for the network")
@click.option('--servicePlan', required=True, help="Service plan")
@pass_client
def create_network(client, datacenterid, name):
    try:
        network = client.node.ex_create_network(datacenterid, name)
        click.secho("Network {0} created in {1}".format(name, datacenterid), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@cli.command()
@click.option('--datacenterId', type=click.UNPROCESSED, help="Filter by datacenter Id")
@pass_client
def list_networks(client, datacenterid):
    try:
        networks = client.node.ex_list_networks(location=datacenterid)
        for network in networks:
            click.secho("{0}".format(network.name), bold=True)
            click.secho("ID: {0}".format(network.id))
            click.secho("Description: {0}".format(network.description))
            click.secho("PrivateNet: {0}".format(network.private_net))
            click.secho("Location: {0}".format(network.location.id))
            click.secho("")
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@cli.command()
@click.option('--datacenterId', required=True, type=click.UNPROCESSED, help="Location for the network")
@click.option('--name', required=True, help="Name for the network")
@pass_client
def create_network(client, datacenterid, name):
    try:
        network = client.node.ex_create_network(datacenterid, name)
        click.secho("Network {0} created in {1}".format(name, datacenterid), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@cli.command()
@click.option('--networkId', required=True, help="ID of the network to remove")
@pass_client
def delete_network(client, networkid):
    try:
        network = client.node.ex_delete_network(networkid)
        click.secho("Network {0} deleted.".format(id), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


