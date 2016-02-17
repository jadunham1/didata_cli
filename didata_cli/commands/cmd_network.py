import click
from didata_cli.cli import pass_client
from libcloud.common.dimensiondata import DimensionDataAPIException, DimensionDataNetworkDomain
from libcloud.common.dimensiondata import DimensionDataVlan
from didata_cli.utils import handle_dd_api_exception


@click.group()
@pass_client
def cli(client):
    pass


@cli.command()
@click.option('--datacenterId', type=click.UNPROCESSED, help="Filter by datacenter Id")
@click.option('--networkDomainId', type=click.UNPROCESSED, help="Filter by network domain")
@pass_client
def list_vlans(client, datacenterid, networkdomainid):
    try:
        if networkdomainid is not None:
            networkdomainid = DimensionDataNetworkDomain(networkdomainid, None, None, None, None, None)
        vlans = client.node.ex_list_vlans(
            location=datacenterid,
            network_domain=networkdomainid
        )
        for vlan in vlans:
            click.secho("{0}".format(vlan.name), bold=True)
            click.secho("ID: {0}".format(vlan.id))
            click.secho("Description: {0}".format(vlan.description))
            click.secho("IPv4 Range: {0}/{1}".format(vlan.private_ipv4_range_address, vlan.private_ipv4_range_size))
            click.secho("IPv6 Range: {0}/{1}".format(vlan.ipv6_range_address, vlan.ipv6_range_size))
            click.secho("")
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--networkDomainId', required=True, type=click.UNPROCESSED, help="Network domain to create VLAN under")
@click.option('--name', required=True, type=click.UNPROCESSED, help="Name of the VLAN")
@click.option('--baseIpv4Address', required=True, type=click.UNPROCESSED, help="Base IPv4 Address")
@click.option('--description', type=click.UNPROCESSED, help="Description of the VLAN")
@click.option('--prefixSize', type=click.UNPROCESSED, help="Prefix Size", default='24')
@pass_client
def create_vlan(client, networkdomainid, name, baseipv4address, description, prefixsize):
    try:
        networkdomainid = DimensionDataNetworkDomain(networkdomainid, None, None, None, None, None)
        vlan = client.node.ex_create_vlan(networkdomainid, name, baseipv4address, description, prefixsize)
        click.secho("Successfully created VLAN {0}".format(vlan.id), bold=True, fg='green')
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--vlanId', required=True, help="ID of the vlan to remove")
@pass_client
def delete_vlan(client, vlanid):
    try:
        client.node.ex_delete_vlan(
            DimensionDataVlan(
                vlanid, None, None, None, None, None, None, None, None, None, None, None
            )
        )
        click.secho("Vlan {0} deleted.".format(vlanid), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


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
@click.option('--description', help="Description for the network domain")
@pass_client
def create_network_domain(client, datacenterid, name, serviceplan, description):
    try:
        client.node.ex_create_network_domain(datacenterid, name, serviceplan, description=description)
        click.secho("Network Domain {0} created in {1}".format(name, datacenterid), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--networkDomainId', required=True, help="ID of the network domain to remove")
@pass_client
def delete_network_domain(client, networkdomainid):
    try:
        client.node.ex_delete_network_domain(
            DimensionDataNetworkDomain(
                networkdomainid, None, None, None, None, None
            )
        )
        click.secho("Network Domain {0} deleted.".format(networkdomainid), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--datacenterId', required=True, type=click.UNPROCESSED, help="Location for the network")
@click.option('--name', required=True, help="Name for the network")
@click.option('--servicePlan', required=True, help="Service plan")
@pass_client
def create_network(client, datacenterid, name):
    try:
        client.node.ex_create_network(datacenterid, name)
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
@click.option('--networkId', required=True, help="ID of the network to remove")
@pass_client
def delete_network(client, networkid):
    try:
        client.node.ex_delete_network(networkid)
        click.secho("Network {0} deleted.".format(id), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)
