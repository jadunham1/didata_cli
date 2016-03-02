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
@click.option('--networkDomainId', type=click.UNPROCESSED, help="Filter by network domain Id")
@click.option('--networkId', type=click.UNPROCESSED, help="Filter by network id")
@click.option('--vlanId', type=click.UNPROCESSED, help="Filter by vlan id")
@click.option('--sourceImageId', type=click.UNPROCESSED, help="Filter by source image id")
@click.option('--deployed', help="Filter by deployed state")
@click.option('--name', help="Filter by server name")
@click.option('--state', help="Filter by state")
@click.option('--started', help="Filter by started")
@click.option('--ipv6', help="Filter by ipv6")
@click.option('--privateIpv4', help="Filter by private ipv4")
@click.option('--dumpall', is_flag=True, default=False, help="Dump all attributes about the server")
@click.option('--idsonly', is_flag=True, default=False, help="Only dump server ids")
@pass_client
def list(client, datacenterid, networkdomainid, networkid,
         vlanid, sourceimageid, deployed, name,
         state, started,
         ipv6, privateipv4, dumpall, idsonly):
    node_list = client.node.list_nodes(ex_location=datacenterid, ex_name=name, ex_network=networkid,
                                       ex_network_domain=networkdomainid, ex_vlan=vlanid,
                                       ex_image=sourceimageid, ex_deployed=deployed, ex_started=started,
                                       ex_state=state, ex_ipv6=ipv6, ex_ipv4=privateipv4)
    for node in node_list:
        if idsonly:
            click.secho(node.id)
        else:
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
                    if key not in ['datacenterId', 'OS_displayName']:
                        click.echo("{0}: {1}".format(key, node.extra[key]))
            click.secho("")


@cli.command()
@click.option('--name', required=True, help="The name of the server")
@click.option('--description', required=True, help="The description of the server")
@click.option('--imageId', type=click.UNPROCESSED, required=True, help="The image id for the server")
@click.option('--autostart', is_flag=True, default=False, help="Bool flag for if you want to autostart")
@click.option('--administratorPassword', type=click.UNPROCESSED, help="The administrator password")
@click.option('--networkDomainId', required=True, type=click.UNPROCESSED, help="The network domain Id to deploy on")
@click.option('--vlanId', type=click.UNPROCESSED, help="The vlan Id to deploy on")
@click.option('--primaryIpv4', help="The IPv4 Address for the hosts primary nic")
@click.option('--additionalVlan', help="Addtional nic on a specific VLAN", multiple=True)
@click.option('--additionalIPv4', help="Addtional nic with a specific IPv4 Address", multiple=True)
@pass_client
def create(client, name, description, imageid, autostart, administratorpassword, networkdomainid, vlanid, primaryipv4, additionalvlan, additionalipv4):
    try:
        # libcloud takes either None or a Tuple/List
        # Click multiples get initialed as tuples so if they are empty we should make them null
        if not additionalvlan:
            additionalvlan = None
        if not additionalipv4:
            additionalipv4 = None
        response = client.node.create_node(name, imageid, administratorpassword,
                                           description, ex_network_domain=networkdomainid, ex_primary_ipv4=primaryipv4,
                                           ex_vlan=vlanid, ex_is_started=autostart,
                                           ex_additional_nics_ipv4=additionalipv4,
                                           ex_additional_nics_vlan=additionalvlan)
        click.secho("Node starting up: {0}.  IPv6: {1}".format(response.id, response.extra['ipv6']),
                    fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to destroy')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@click.option('--ramInGB', required=True, help='Amount of RAM to change the server to', type=int)
@pass_client
def update_ram(client, serverid, serverfilteripv6, ramingb):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        client.node.ex_reconfigure_node(node, ramingb, None, None, None)
        click.secho("Server {0} ram is being changed to {1}GB".format(serverid, ramingb), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to destroy')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@click.option('--cpuCount', required=True, help='# of CPUs to change to', type=int)
@pass_client
def update_cpu_count(client, serverid, serverfilteripv6, cpucount):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        client.node.ex_reconfigure_node(node, None, cpucount, None, None)
        click.secho("Server {0} CPU Count changing to {1}".format(serverid, cpucount), fg='green', bold=True)
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
