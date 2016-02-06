import click
import pprint
import logging
from didata_cli.utils import flattenDict
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.drivers.dimensiondata import DimensionDataNodeDriver
from libcloud.common.dimensiondata import API_ENDPOINTS, DEFAULT_REGION
from libcloud.utils.py3 import basestring
from dimensiondata.client import DimensionDataClient
from requests.exceptions import HTTPError
from dimensiondata.api.xml_utils import dd_xmltodict
from dimensiondata.exceptions import (BackupPolicyValidationFailure, SingleServerReturnFailMultileServers,
                                      NoDownloadUrlFound, SingleServerReturnFailNoServers)
from libcloud.common.dimensiondata import DimensionDataAPIException
import json
DEFAULT_ENDPOINT = 'https://api-na.dimensiondata.com'

logging.basicConfig(level=logging.CRITICAL)
class DiDataCLIComputeClient(DimensionDataNodeDriver):
    def __init__(self):
        self.verbose = False

    def init_client(self, user, password, region=DEFAULT_REGION):
        super(DiDataCLIComputeClient, self).__init__(user, password, region)

pass_client = click.make_pass_decorator(DiDataCLIComputeClient, ensure=True)

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
    node_list = client.list_nodes(ex_location=datacenterid)
    for node in node_list:
        click.secho("{}".format(node.name), bold=True)
        click.secho("ID: {}".format(node.uuid))
        click.secho("Datacenter: {}".format(node.extra['datacenterId']))
        click.secho("OS: {}".format(node.extra['OS_displayName']))
        click.secho("Private IPv4: {}".format(" - ".join(node.private_ips)))
        if 'ipv6' in node.extra:
            click.secho("Private IPv6: {}".format(node.extra['ipv6']))
        if dumpall:
            click.secho("Public IPs: {}".format(" - ".join(node.public_ips)))
            click.secho("State: {}".format(node.state))
            for key in sorted(node.extra):
                if key == 'cpu':
                    click.echo("CPU Count: {}".format(node.extra[key].cpu_count))
                    click.echo("Cores per Socket: {}".format(node.extra[key].cores_per_socket))
                    click.echo("CPU Performance: {}".format(node.extra[key].performance))
                    continue
                if key not in ['datacenterId', 'status', 'OS_displayName']:
                    click.echo("{}: {}".format(key, node.extra[key]))
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
        response = client.create_node(name, imageid, administratorpassword, description, ex_network_domain=networkdomainid, ex_vlan=vlanid, ex_is_started=autostart)
        click.secho("{}".format(response))
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)

@cli.group()
@pass_client
def backup(config):
    pass

@backup.command()
@click.option('--serverId', help='The server ID to enable backups on')
@click.option('--servicePlan', help='The type of service plan to enroll in', type=click.Choice(['Enterprise', 'Essentials', 'Advanced']))
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def enable(client, serverid, serviceplan, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        dd_http_success(client.enable_backups_for_server(serverid))
    except HTTPError as e:
        dd_http_error(e)

@backup.command()
@click.option('--serverId', help='The server ID to disable backups on')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def disable(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        dd_http_success(client.disable_backups_for_server(serverid))
    except HTTPError as e:
        dd_http_error(e)

@backup.command()
@click.option('--serverId', help='The server ID to disable backups on')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def info(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        response = client.get_backup_info_for_server(serverid)
        new_dict = flattenDict(response)
        for key in sorted(new_dict):
            click.secho("{}: {}".format(key, new_dict[key]))
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='This will list the backup client types availabe for a given server i.e. FA.Linux/MySQL')
@click.option('--serverId', help='The server ID to list client types for')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def list_client_types(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        client_types = client.get_backup_client_types_for_server(serverid)
        click.secho("Available backup client types for {}: ".format(serverid))
        for item in client_types:
            click.secho(item, bold=True)
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='This will list the storage policies availabe for a given server i.e. 7 Years')
@click.option('--serverId', help='The server ID to list storage policies for')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def list_storage_policies(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        storage_policies = client.get_backup_storage_policies_for_server(serverid)
        click.secho("Available storage policies for {}: ".format(serverid))
        for item in storage_policies:
            click.secho(item, bold=True)
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='This will list the backup storage schedules for a given server i.e. 12 AM - 6 AM')
@click.option('--serverId', help='The server ID to list backup schedules for')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def list_schedule_policies(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        schedule_policies = client.get_backup_schedule_policies_for_server(serverid)
        click.secho("Available backup client types for {}: ".format(serverid))
        for item in schedule_policies:
            click.secho(item, bold=True)
    except HTTPError as e:
        dd_http_error(e)

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
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        dd_http_success(client.add_backup_policy_for_server(serverid, clienttype, storagepolicy, schedulepolicy, triggeron, notifyemail))
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='Removes a backup client')
@click.option('--serverId', help='The server ID to list backup schedules for')
@click.option('--policy', required=True, help='The server ID to list backup schedules for')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def remove_client(client, serverid, policy, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        dd_http_success(client.remove_backup_policy_for_server(serverid, policy))
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='Fetch Download URL for Server')
@click.option('--serverId', help='The server ID to list backup schedules for')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def download_url(client, serverid, serverfilteripv6):
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ipv6=serverfilteripv6)
    try:
        click.secho("{}".format(client.get_backup_download_url_for_server(serverid)))
    except HTTPError as e:
        dd_http_error(e)
    except NoDownloadUrlFound:
        click.secho('FAILURE: No backup clients are configured for this server', fg='red', bold=True)


def get_single_server_id_from_filters(client, **kwargs):
    try:
        # fix this line
        if len(kwargs.keys()) == 0 or not kwargs['ipv6']:
            click.secho("No serverId or filters for servers found")
            exit(1)
        return client.get_single_server_id(**kwargs)
    except SingleServerReturnFailMultileServers as e:
        click.secho("FAILURE: Multiple Servers found in filter", fg='red', bold=True)
        for server_id in e.server_id_list:
            click.secho("{}".format(server_id))
        exit(1)
    except SingleServerReturnFailNoServers as noservers:
        click.secho("FAILURE: No servers found with the given filter", fg='red', bold=True)
        exit(1)
    except HTTPError as httperror:
        dd_http_error(httperror)



def dd_http_error(e):
    try:
        if e.response.text.startswith('<'):
            response =  dd_xmltodict(e.response.text)
        else:
            response = json.loads(e.response.text)
        if 'message' in response:
            click.secho("FAILURE: {}".format(response['message']), fg='red', bold=True)
        elif 'Status' in response:
            click.secho("FAILURE: {}".format(response['Status']['resultDetail']), fg='red', bold=True)
        exit(1)
    except Exception:
        raise e

def handle_dd_api_exception(e):
    click.secho("{}".format(e), fg='red', bold=True)

def dd_http_success(response):
    try:
        new_dict = flattenDict(response)
        if 'Status.resultDetail' in new_dict:
            click.secho("{}".format(new_dict['Status.resultDetail']), fg='green', bold=True)
            for key in new_dict:
                if key != 'Status.resultDetail':
                    click.secho("{}: {}".format(key, new_dict[key]))
        elif 'message' in new_dict:
            click.secho("{}".format(new_dict['message']), fg='green', bold=True)
            for key in new_dict:
                if key != 'message':
                    click.secho("{}: {}".format(key, new_dict[key]))

    except Exception as e:
        raise e
