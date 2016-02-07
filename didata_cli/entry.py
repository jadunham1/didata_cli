import click
import pprint
import logging
from didata_cli.utils import flattenDict
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.drivers.dimensiondata import DimensionDataNodeDriver
from libcloud.backup.drivers.dimensiondata import DimensionDataBackupDriver
from libcloud.backup.base import BackupTarget
from libcloud.common.dimensiondata import API_ENDPOINTS, DEFAULT_REGION
from libcloud.common.dimensiondata import DimensionDataAPIException
import json
DEFAULT_ENDPOINT = 'https://api-na.dimensiondata.com'

logging.basicConfig(level=logging.CRITICAL)
class DiDataCLIClient(object):
    def __init__(self):
        self.verbose = False

    def init_client(self, user, password, region=DEFAULT_REGION):
        self.node = DimensionDataNodeDriver(user, password, region)
        self.backup = DimensionDataBackupDriver(user, password, region)

pass_client = click.make_pass_decorator(DiDataCLIClient, ensure=True)

@click.group()
@click.option('--verbose', is_flag=True)
@click.option('--user', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--region', default=DEFAULT_REGION)
@pass_client
def cli(client, verbose, user, password, region):
    client.init_client(user, password, region)
    if verbose:
        click.echo('Verbose mode enabled')

@cli.group()
@pass_client
def server(client):
    pass

@server.command()
@click.option('--datacenterId', help="Filter by datacenter Id")
@click.option('--dumpall', is_flag=True, default=False, help="Dump all attributes about the server")
@pass_client
def list(client, datacenterid, dumpall):
    node_list = client.node.list_nodes(ex_location=datacenterid)
    for node in node_list:
        click.secho("{0}".format(node.name), bold=True)
        click.secho("ID: {0}".format(node.uuid))
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


@server.command()
@click.option('--name', required=True, help="The name of the server")
@click.option('--description', required=True, help="The description of the server")
@click.option('--imageId', required=True, help="The image id for the server")
@click.option('--autostart', is_flag=True, default=False, help="Bool flag for if you want to autostart")
@click.option('--administratorPassword', required=True, help="The administrator password")
@click.option('--networkDomainId', required=True, type=click.UNPROCESSED, help="The network domain Id to deploy on")
@click.option('--vlanId', required=True, help="The vlan Id to deploy on")
@pass_client
def create(client, name, description, imageid, autostart, administratorpassword, networkdomainid, vlanid):
    try:
        response = client.node.create_node(name, imageid, administratorpassword, description, ex_network_domain=networkdomainid, ex_vlan=vlanid, ex_is_started=autostart)
        click.secho("{0}".format(response))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@cli.group()
@pass_client
def backup(config):
    pass

@backup.command()
@click.option('--serverId', help='The server ID to enable backups on')
@click.option('--servicePlan', required=True, help='The type of service plan to enroll in', type=click.Choice(['Enterprise', 'Essentials', 'Advanced']))
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def enable(client, serverid, serviceplan, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    try:
        extra = {'service_plan': serviceplan }
        response = client.backup.create_target(serverid, serverid, extra=extra)
        click.secho("Backups enabled for {0}.  Service plan: {1}".format(serverid, serviceplan), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@backup.command()
@click.option('--serverId', help='The server ID to disable backups on')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def disable(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    try:
        response = client.backup.delete_target(BackupTarget(serverid, serverid, serverid, None, DimensionDataBackupDriver))
        if response is True:
            click.secho("Backups disabled for {0}".format(serverid), fg='green', bold=True)
        else:
            click.secho("Backups not disabled for {0}".format(serverid, fg='red', bold=True))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@backup.command()
@click.option('--serverId', help='The server ID to disable backups on')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def info(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    try:
        details = client.backup.ex_get_backup_details_for_target(serverid)
        click.secho("Backup Details for {0}".format(serverid))
        click.secho("Service Plan: {0}".format(details.service_plan[0]))
        if len(details.clients) > 0:
            click.secho("Clients:")
            for backup_client in details.clients:
                click.secho("")
                click.secho("{0}".format(backup_client.type), bold=True)
                click.secho("Description: {0}".format(backup_client.description))
                click.secho("Schedule: {0}".format(backup_client.schedule_policy))
                click.secho("Retention: {0}".format(backup_client.storage_policy))
                click.secho("DownloadURL: {0}".format(backup_client.download_url))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@backup.command(help='Adds a backup client')
@click.option('--serverId', help='The server ID to list backup schedules for')
@click.option('--clientType', required=True, help='The server ID to list backup schedules for')
@click.option('--storagePolicy', required=True, help='The server ID to list backup schedules for')
@click.option('--schedulePolicy', required=True, help='The server ID to list backup schedules for')
@click.option('--triggerOn', help='The server ID to list backup schedules for')
@click.option('--notifyEmail', help='The server ID to list backup schedules for')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def add_client(client, serverid, clienttype, storagepolicy, schedulepolicy, triggeron, notifyemail, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    try:
        response = client.backup.ex_add_client_to_target(BackupTarget(serverid, serverid, serverid, None, DimensionDataBackupDriver), clienttype, storagepolicy, schedulepolicy, triggeron, notifyemail)
        if response is True:
            click.secho("Backups disabled for {0}".format(serverid), fg='green', bold=True)
        else:
            click.secho("Backups not disabled for {0}".format(serverid, fg='red', bold=True))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@backup.command(help='Fetch Download URL for Server')
@click.option('--serverId', help='The server ID to list backup schedules for')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def download_url(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    try:
        details = client.backup.ex_get_backup_details_for_target(serverid)
        if len(details.clients) < 1:
            click.secho("No clients configured so there is no backup url", fg='red', bold=True)
            exit(1)
        click.secho("{0}".format(details.clients[0].download_url))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


def get_single_server_id_from_filters(client, **kwargs):
    try:
        # fix this line
        if len(kwargs.keys()) == 0 or not kwargs['ex_ipv6']:
            click.secho("No serverId or filters for servers found")
            exit(1)
        node_list = client.node.list_nodes(**kwargs)
        if len(node_list) > 1:
            click.secho("Too many nodes found in filter", fg='red', bold=True)
            exit(1)
        if len(node_list) == 0:
            click.secho("No nodes found with fitler", fg='red', bold=True)
            exit(1)
        return node_list[0].id
    except HTTPError as httperror:
        dd_http_error(httperror)



def dd_http_error(e):
    try:
        if e.response.text.startswith('<'):
            response =  dd_xmltodict(e.response.text)
        else:
            response = json.loads(e.response.text)
        if 'message' in response:
            click.secho("FAILURE: {0}".format(response['message']), fg='red', bold=True)
        elif 'Status' in response:
            click.secho("FAILURE: {0}".format(response['Status']['resultDetail']), fg='red', bold=True)
        exit(1)
    except Exception:
        raise e

def handle_dd_api_exception(e):
    click.secho("{0}".format(e), fg='red', bold=True)

def dd_http_success(response):
    try:
        new_dict = flattenDict(response)
        if 'Status.resultDetail' in new_dict:
            click.secho("{0}".format(new_dict['Status.resultDetail']), fg='green', bold=True)
            for key in new_dict:
                if key != 'Status.resultDetail':
                    click.secho("{0}: {}".format(key, new_dict[key]))
        elif 'message' in new_dict:
            click.secho("{0}".format(new_dict['message']), fg='green', bold=True)
            for key in new_dict:
                if key != 'message':
                    click.secho("{0}: {1}".format(key, new_dict[key]))

    except Exception as e:
        raise e
