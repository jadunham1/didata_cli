import click
import pprint
import logging
from didata_cli.utils import flattenDict
from dimensiondata.client import DimensionDataClient
from requests.exceptions import HTTPError
from dimensiondata.api.xml_utils import dd_xmltodict
from dimensiondata.exceptions import (BackupPolicyValidationFailure, SingleServerReturnFailMultileServers,
                                      NoDownloadUrlFound, SingleServerReturnFailNoServers)
import json
DEFAULT_ENDPOINT = 'https://api-na.dimensiondata.com'

logging.basicConfig(level=logging.CRITICAL)
class DiDataCLIClient(DimensionDataClient):
    def __init__(self):
        self.verbose = False

    def init_client(self, user, password, endpoint=DEFAULT_ENDPOINT):
        super(DimensionDataClient, self).__init__(user, password, endpoint)

pass_client = click.make_pass_decorator(DiDataCLIClient, ensure=True)

@click.group()
@click.option('--verbose', is_flag=True)
@click.option('--user', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@pass_client
def cli(client, verbose, user, password):
    client.init_client(user, password)
    if verbose:
        click.echo('Verbose mode enabled')

@cli.group()
@pass_client
def server(client):
    pass

@server.command()
@click.option('--id', help="Filter by server id")
@click.option('--datacenterId', help="Filter by datacenter Id")
@click.option('--networkDomainId', help="Filter by network domain Id")
@click.option('--networkId', help="Filter by network id")
@click.option('--vlanId', help="Filter by vlan id")
@click.option('--sourceImageId', help="Filter by source image id")
@click.option('--deployed', help="Filter by deployed state")
@click.option('--name', help="Filter by server name")
@click.option('--createTime', help="Filter by creation time")
@click.option('--state', help="Filter by state")
@click.option('--started', help="Filter by started")
@click.option('--operatingSystemId', help="Filter by operating system id")
@click.option('--ipv6', help="Filter by ipv6")
@click.option('--privateIpv4', help="Filter by private ipv4")
@click.option('--dumpall', is_flag=True, default=False, help="Dump all attributes about the server")
@pass_client
def list(client, id, datacenterid, networkdomainid, networkid,
         vlanid, sourceimageid, deployed, name,
         createtime, state, started, operatingsystemid,
         ipv6, privateipv4, dumpall):
    click.echo("Finding servers")
    servers = client.get_servers(id=id, datacenterId=datacenterid,
                                 networkDomainId=networkdomainid, vlanId=vlanid,
                                 networkId=networkid, sourceImageId=sourceimageid,
                                 deployed=deployed, name=name, createTime=createtime,
                                 state=state, started=started,
                                 operatingSystemId=operatingsystemid, ipv6=ipv6,
                                 privateIpv4=privateipv4)
    for server in servers:
        click.secho("{}".format(server['name']), bold=True)
        if dumpall:
            new_dict = flattenDict(server)
            for key in sorted(new_dict):
                click.secho("{}: {}".format(key, new_dict[key]))
            click.secho("")
            continue
        mcp=1
        if('networkInfo' in server):
            mcp=2

        if('id' in server):
            click.secho("Server Id: {}".format(server['id']))
        if('datacenterId' in server):
            click.secho("Datacenter: {}".format(server['datacenterId']))

        if(mcp == 2):
            if('ipv6' in server['networkInfo']['primaryNic']):
                click.secho("IPv6: {}".format(server['networkInfo']['primaryNic']['ipv6']))
            if('privateIpv4' in server['networkInfo']['primaryNic']):
                click.secho("Private IPv4: {}".format(server['networkInfo']['primaryNic']['privateIpv4']))
        elif(mcp == 1):
            if('privateIpv4' in server['nic']):
                click.secho("Private IPv4: {}".format(server['nic']['privateIpv4']))
        if('displayName' in server['operatingSystem']):
            click.secho("OS: {}".format(server['operatingSystem']['displayName']))
        click.secho("")


@cli.group()
@pass_client
def backup(config):
    pass

@backup.command()
@click.option('--serverId', required=True, help='The server ID to enable backups on')
@click.option('--servicePlan', help='The type of service plan to enroll in', type=click.Choice(['Enterprise', 'Essentials', 'Advanced']))
@pass_client
def enable(client, serverid, serviceplan):
    try:
        dd_http_success(client.enable_backups_for_server(serverid))
    except HTTPError as e:
        dd_http_error(e)

@backup.command()
@click.option('--serverId', required=True, help='The server ID to disable backups on')
@pass_client
def disable(client, serverid):
    try:
        dd_http_success(client.disable_backups_for_server(serverid))
    except HTTPError as e:
        dd_http_error(e)

@backup.command()
@click.option('--serverId', required=True, help='The server ID to disable backups on')
@pass_client
def info(client, serverid):
    try:
        response = client.get_backup_info_for_server(serverid)
        new_dict = flattenDict(response)
        for key in sorted(new_dict):
            click.secho("{}: {}".format(key, new_dict[key]))
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='This will list the backup client types availabe for a given server i.e. FA.Linux/MySQL')
@click.option('--serverId', required=True, help='The server ID to list client types for')
@pass_client
def list_client_types(client, serverid):
    try:
        client_types = client.get_backup_client_types_for_server(serverid)
        click.secho("Available backup client types for {}: ".format(serverid))
        for item in client_types:
            click.secho(item, bold=True)
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='This will list the storage policies availabe for a given server i.e. 7 Years')
@click.option('--serverId', required=True, help='The server ID to list storage policies for')
@pass_client
def list_storage_policies(client, serverid):
    try:
        storage_policies = client.get_backup_storage_policies_for_server(serverid)
        click.secho("Available storage policies for {}: ".format(serverid))
        for item in storage_policies:
            click.secho(item, bold=True)
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='This will list the backup storage schedules for a given server i.e. 12 AM - 6 AM')
@click.option('--serverId', required=True, help='The server ID to list backup schedules for')
@pass_client
def list_schedule_policies(client, serverid):
    try:
        schedule_policies = client.get_backup_schedule_policies_for_server(serverid)
        click.secho("Available backup client types for {}: ".format(serverid))
        for item in schedule_policies:
            click.secho(item, bold=True)
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='Adds a backup client')
@click.option('--serverId', required=True, help='The server ID to list backup schedules for')
@click.option('--clientType', required=True, help='The server ID to list backup schedules for')
@click.option('--storagePolicy', required=True, help='The server ID to list backup schedules for')
@click.option('--schedulePolicy', required=True, help='The server ID to list backup schedules for')
@click.option('--triggerOn', help='The server ID to list backup schedules for')
@click.option('--notifyEmail', help='The server ID to list backup schedules for')
@pass_client
def add_client(client, serverid, clienttype, storagepolicy, schedulepolicy, triggeron, notifyemail):
    try:
        dd_http_success(client.add_backup_policy_for_server(serverid, clienttype, storagepolicy, schedulepolicy, triggeron, notifyemail))
    except HTTPError as e:
        dd_http_error(e)

@backup.command(help='Removes a backup client')
@click.option('--serverId', required=True, help='The server ID to list backup schedules for')
@click.option('--policy', required=True, help='The server ID to list backup schedules for')
@pass_client
def remove_client(client, serverid, policy):
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

def dd_http_success(response):
    try:
        new_dict = flattenDict(response)
        click.secho("{}".format(new_dict['Status.resultDetail']), fg='green', bold=True)
        for key in new_dict:
            if key != 'Status.resultDetail':
                click.secho("{}: {}".format(key, new_dict[key]))
    except Exception as e:
        raise e
