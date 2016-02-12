import click
from libcloud.common.dimensiondata import DimensionDataAPIException


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
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


def handle_dd_api_exception(e):
    click.secho("{0}".format(e), fg='red', bold=True)
    exit(1)


def flattenDict(d, result=None):
    if result is None:
        result = {}
    for key in d:
        value = d[key]
        if isinstance(value, dict):
            value1 = {}
            for keyIn in value:
                value1[".".join([key, keyIn])] = value[keyIn]
            flattenDict(value1, result)
        elif isinstance(value, (tuple, list)):
            for indexB, element in enumerate(value):
                if isinstance(element, dict):
                    value1 = {}
                    index = 0
                    for keyIn in element:
                        value1[".".join([key, keyIn])] = value[indexB][keyIn]
                        index += 1
                    for keyA in value1:
                        flattenDict(value1, result)
        else:
            result[key] = value
    return result
