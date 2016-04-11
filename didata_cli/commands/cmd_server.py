import click
from didata_cli.cli import pass_client
from libcloud.common.dimensiondata import DimensionDataAPIException
from didata_cli.utils import handle_dd_api_exception, get_single_server_id_from_filters


@click.group()
@pass_client
def cli(client):
    pass


def _print_node_info(node):
    click.secho("Name: {0}".format(node.name), bold=True)
    click.secho("ID: {0}".format(node.id))
    click.secho("Private IPv4: {0}".format(" - ".join(node.private_ips)))
    if 'ipv6' in node.extra:
        click.secho("Private IPv6: {0}".format(node.extra['ipv6']))
    click.secho("Public IPs: {0}".format(" - ".join(node.public_ips)))
    click.secho("State: {0}".format(node.state))
    for key in sorted(node.extra):
        if key == 'cpu':
            click.echo("CPU Count: {0}".format(node.extra[key].cpu_count))
            click.echo("Cores per Socket: {0}".format(node.extra[key].cores_per_socket))
            click.echo("CPU Performance: {0}".format(node.extra[key].performance))
            continue
        if key == 'disks':
            for disk in node.extra[key]:
                click.secho("Disk {0}:".format(disk.scsi_id))
                click.secho("  Size: {0}GB".format(disk.size_gb))
                click.secho("  Speed: {0}".format(disk.speed))
                click.secho("  State: {0}".format(disk.state))
            continue
        # skip this key, it is similar to node.status
        if key == 'status':
            continue
        click.echo("{0}: {1}".format(key, node.extra[key]))
    click.secho("")


@cli.command()
@click.option('--serverId', required=True, help="The server ID to get info for")
@pass_client
def info(client, serverid):
    node = client.node.ex_get_node_by_id(serverid)
    _print_node_info(node)


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
@click.option('--idsonly', is_flag=True, default=False, help="Only dump server ids")
@pass_client
def list(client, datacenterid, networkdomainid, networkid,
         vlanid, sourceimageid, deployed, name,
         state, started, ipv6, privateipv4, idsonly):
    node_list = client.node.list_nodes(ex_location=datacenterid, ex_name=name, ex_network=networkid,
                                       ex_network_domain=networkdomainid, ex_vlan=vlanid,
                                       ex_image=sourceimageid, ex_deployed=deployed, ex_started=started,
                                       ex_state=state, ex_ipv6=ipv6, ex_ipv4=privateipv4)
    for node in node_list:
        if idsonly:
            click.secho(node.id)
        else:
            _print_node_info(node)


@cli.command()
@click.option('--serverId', help="The server ID to add a disk on")
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@click.option('--size', required=True, type=click.INT, help="The size of the disk (in GB) to add")
@click.option('--speed', default='STANDARD', type=click.Choice(['STANDARD', 'ECONOMY', 'HIGHPERFORMANCE']))
@pass_client
def add_disk(client, serverid, serverfilteripv6, size, speed):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_add_storage_to_node(node, size, speed)
        if response is True:
            click.secho("Adding disk {0} {1}GB to {2}".format(speed, size, serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong attempting to add disk to {0}".format(serverid), fg='red', bold=True)
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', help="The server ID to add a disk on")
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@click.option('--diskId', required=True, type=click.INT, help="The size of the disk (in GB) to add")
@pass_client
def remove_disk(client, serverid, serverfilteripv6, diskid):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)

    # See if we can find the disk to remove
    disk_to_remove = _find_disk_id_from_node(node, diskid)

    try:
        response = client.node.ex_remove_storage_from_node(node, disk_to_remove.id)
        if response is True:
            click.secho("Removed disk {0} from {1}".format(disk_to_remove.id, serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong attempting to remove disk {0} from {1}".format(disk_to_remove.id,
                                                                                             serverid),
                        fg='red', bold=True)
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', help="The server ID to add a disk on")
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@click.option('--diskId', required=True, type=click.INT, help="The size of the disk (in GB) to add")
@click.option('--size', type=click.INT, help="The size of the disk (in GB) to add")
@click.option('--speed', type=click.Choice(['STANDARD', 'ECONOMY', 'HIGHPERFORMANCE']))
@pass_client
def modify_disk(client, serverid, serverfilteripv6, diskid, size, speed):
    # Validate parameters, wish click had exculsion
    if size is not None and speed is not None:
        click.secho("Only one modify disk operation can happen at a time.  Please choose either --speed or --size",
                    fg='red', bold=True)
        exit(1)
    elif size is None and speed is None:
        click.secho("Must choose one of --speed or --size to change", fg='red', bold=True)
        exit(1)

    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)

    # See if we can find the disk to modify
    disk_to_modify = _find_disk_id_from_node(node, diskid)

    try:
        if speed is not None:
            response = client.node.ex_change_storage_speed(node, disk_to_modify.id, speed)
        else:
            response = client.node.ex_change_storage_size(node, disk_to_modify.id, size)
        if response is True:
            click.secho("Successfully modified disk {0} from {1}".format(disk_to_modify.scsi_id, serverid),
                        fg='green', bold=True)
        else:
            click.secho("Something went wrong attemping to modify disk {0} from {1}".format(disk_to_modify.id,
                                                                                            serverid),
                        fg='red', bold=True)
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--name', required=True, help="The name of the server")
@click.option('--description', required=True, help="The description of the server")
@click.option('--imageId', required=True, type=click.UNPROCESSED, help="The image id for the server")
@click.option('--autostart', is_flag=True, default=False, help="Bool flag for if you want to autostart")
@click.option('--administratorPassword', required=True, type=click.UNPROCESSED, help="The administrator password")
@click.option('--networkDomainId', required=True, type=click.UNPROCESSED, help="The network domain Id to deploy on")
@click.option('--vlanId', required=True, type=click.UNPROCESSED, help="The vlan Id to deploy on")
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
            exit(1)
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
            exit(1)
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
            exit(1)
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
            exit(1)
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
            exit(1)
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
            click.secho("Something went wrong when attempting to shutdown {0}".format(serverid))
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


def _find_disk_id_from_node(node, diskid):
    found_disk = None
    for disk in node.extra['disks']:
        if disk.scsi_id == diskid:
            found_disk = disk
            break
    if found_disk is None:
        click.secho("No disk with id {0} in server {1}".format(diskid, node.id), fg='red', bold=True)
        exit(1)
    return found_disk
