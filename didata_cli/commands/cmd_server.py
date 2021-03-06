import click
from didata_cli.cli import pass_client
from libcloud.common.dimensiondata import DimensionDataAPIException
from didata_cli.utils import handle_dd_api_exception, get_single_server_id_from_filters


@click.group()
@pass_client
def cli(client):
    pass


@cli.command()
@click.option('--datacenterId', type=click.UNPROCESSED, help="Filter by datacenter Id")
@click.option('--networkDomainId', help="Filter by network domain Id")
@click.option('--networkId', help="Filter by network id")
@click.option('--vlanId', help="Filter by vlan id")
@click.option('--sourceImageId', help="Filter by source image id")
@click.option('--deployed', help="Filter by deployed state")
@click.option('--name', help="Filter by server name")
@click.option('--state', help="Filter by state")
@click.option('--started', help="Filter by started")
@click.option('--ipv6', help="Filter by ipv6")
@click.option('--privateIpv4', help="Filter by private ipv4")
@click.option('--dumpall', is_flag=True, default=False, help="Dump all attributes about the server")
@pass_client
def list(client, datacenterid, networkdomainid, networkid,
         vlanid, sourceimageid, deployed, name,
         state, started,
         ipv6, privateipv4, dumpall):
    node_list = client.node.list_nodes(ex_location=datacenterid, ex_name=name, ex_network=networkid,
                                       ex_network_domain=networkdomainid, ex_vlan=vlanid,
                                       ex_image=sourceimageid, ex_deployed=deployed, ex_started=started,
                                       ex_state=state, ex_ipv6=ipv6, ex_ipv4=privateipv4)
    for node in node_list:
        click.secho("{0}".format(node.name), bold=True)
        click.secho("ID: {0}".format(node.id))
        click.secho("Datacenter: {0}".format(node.extra['datacenterId']))
        click.secho("OS: {0}".format(node.extra['OS_displayName']))
        click.secho("Private IPv4: {0}".format(" - ".join(node.private_ips)))
        if 'ipv6' in node.extra:
            click.secho("Private IPv6: {0}".format(node.extra['ipv6']))
        if dumpall:
            click.secho("Public IPs: {0}".format(" - ".join(node.public_ips)))
            click.secho("State: {0}".format(node.state))
            for key in sorted(node.extra):
                if key == 'cpu':
                    click.echo("CPU Count: {0}".format(node.extra[key].cpu_count))
                    click.echo("Cores per Socket: {0}".format(node.extra[key].cores_per_socket))
                    click.echo("CPU Performance: {0}".format(node.extra[key].performance))
                    continue
                if key not in ['datacenterId', 'status', 'OS_displayName']:
                    click.echo("{0}: {1}".format(key, node.extra[key]))
        click.secho("")


@cli.command()
@click.option('--name', required=True, help="The name of the server")
@click.option('--description', required=True, help="The description of the server")
@click.option('--imageId', required=True, help="The image id for the server")
@click.option('--autostart', is_flag=True, default=False, help="Bool flag for if you want to autostart")
@click.option('--administratorPassword', required=True, type=click.UNPROCESSED, help="The administrator password")
@click.option('--networkDomainId', required=True, type=click.UNPROCESSED, help="The network domain Id to deploy on")
@click.option('--vlanId', required=True, help="The vlan Id to deploy on")
@pass_client
def create(client, name, description, imageid, autostart, administratorpassword, networkdomainid, vlanid):
    try:
        response = client.node.create_node(name, imageid, administratorpassword,
                                           description, ex_network_domain=networkdomainid,
                                           ex_vlan=vlanid, ex_is_started=autostart)
        click.secho("Node starting up: {0}.  IPv6: {1}".format(response.id, response.extra['ipv6']),
                    fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to destroy')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def destroy(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.destroy_node(node)
        if response is True:
            click.secho("Server {0} is being destroyed".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong with attempting to destroy {0}".format(serverid))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to reboot')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def reboot(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.reboot_node(node)
        if response is True:
            click.secho("Server {0} is being rebooted".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong with attempting to reboot {0}".format(serverid))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to reboot')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def reboot_hard(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_reset(node)
        if response is True:
            click.secho("Server {0} is being rebooted".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong with attempting to reboot {0}".format(serverid))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to start')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def start(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_start_node(node)
        if response is True:
            click.secho("Server {0} is starting".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong when attempting to start {0}".format(serverid))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to shutdown')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def shutdown(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_shutdown_graceful(node)
        if response is True:
            click.secho("Server {0} is shutting down gracefully".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong when attempting to shutdown {0}".format(serverid))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to shutdown')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def shutdown_hard(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_power_off(node)
        if response is True:
            click.secho("Server {0} is shutting down hard".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong when attempting to shut down {0}".format(serverid))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)
