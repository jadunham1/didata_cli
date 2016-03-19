from didata_cli.cli import cli
from click.testing import CliRunner
import unittest
try:
    from unittest.mock import patch
except:
    from mock import patch
import os
from tests.utils import load_dd_obj
from libcloud.common.dimensiondata import DimensionDataAPIException


@patch('didata_cli.cli.DimensionDataNodeDriver')
class DimensionDataCLITestCase(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        os.environ["DIDATA_USER"] = 'fakeuser'
        os.environ["DIDATA_PASSWORD"] = 'fakepass'

    def test_server_help(self, node_client):
        result = self.runner.invoke(cli, ['server'], catch_exceptions=False)
        assert result.exit_code == 0

    def test_server_list(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('node_list.json')
        result = self.runner.invoke(cli, ['server', 'list'])
        self.assertIn('Private IPv4: 172.16.2.8', result.output)
        self.assertEqual(result.exit_code, 0)

    def test_server_list_idsonly(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('node_list.json')
        result = self.runner.invoke(cli, ['server', 'list', '--idsonly'])
        self.assertNotIn('Private IPv4: 172.16.2.8', result.output)
        self.assertIn('b4ea8995-43a1-4b56-b751-4107b5671713', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_create_node(self, node_client):
        node_client.return_value.create_node.return_value = load_dd_obj('create_node.json')
        result = self.runner.invoke(cli,
                                    ['server', 'create', '--name', 'didata_cli_test',
                                     '--imageId', '294cad61-0857-4124-8ff6-45f4e6643646',
                                     '--administratorPassword', 'fakepassword',
                                     '--description', 'fakedescription',
                                     '--networkDomainId', 'b53b2ad4-ca8b-4abd-9140-72d6b137a6b4',
                                     '--vlanId', 'f04e4e2c-a52e-45d3-8037-9f1b1e234c05'])
        self.assertIn('8aeff10c-c918-4021-b2ce-93e4a209418b', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_create_node_APIException(self, node_client):
        node_client.return_value.create_node.side_effect = DimensionDataAPIException(
            code='REASON 541', msg='Unable to create node', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'create', '--name', 'didata_cli_test',
                                     '--imageId', '294cad61-0857-4124-8ff6-45f4e6643646',
                                     '--administratorPassword', 'fakepassword',
                                     '--description', 'fakedescription',
                                     '--networkDomainId', 'b53b2ad4-ca8b-4abd-9140-72d6b137a6b4',
                                     '--vlanId', 'f04e4e2c-a52e-45d3-8037-9f1b1e234c05'])
        self.assertIn('REASON 541', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_info(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        result = self.runner.invoke(cli,
                                    ['server', 'info',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('ID: 8aeff10c-c918-4021-b2ce-93e4a209418b', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_update_ram(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_reconfigure_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'update_ram',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b',
                                     '--ramInGB', '8'])
        self.assertIn('changed to 8GB', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_update_ram_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_reconfigure_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'update_ram',
                                     '--serverFilterIpv6', '::1',
                                     '--ramInGB', '8'])
        self.assertIn('changed to 8GB', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_update_ram_APIException(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_reconfigure_node.side_effect = DimensionDataAPIException(
            code='REASON 540', msg='No RAM Left', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'update_ram',
                                     '--serverFilterIpv6', '::1',
                                     '--ramInGB', '8'])
        self.assertIn('REASON 540', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_update_cpu_count(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_reconfigure_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'update_cpu_count',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b',
                                     '--cpuCount', '4'])
        self.assertIn('CPU Count changing to 4', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_update_cpu_count_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_reconfigure_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'update_cpu_count',
                                     '--serverFilterIpv6', '::1',
                                     '--cpuCount', '4'])
        self.assertIn('CPU Count changing to 4', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_update_cpu_count_APIException(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_reconfigure_node.side_effect = DimensionDataAPIException(
            code='REASON 539', msg='No CPU Left', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'update_cpu_count',
                                     '--serverFilterIpv6', '::1',
                                     '--cpuCount', '4'])
        self.assertIn('REASON 539', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_destroy(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.destroy_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'destroy',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('is being destroyed', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_destroy_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.destroy_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'destroy',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('is being destroyed', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_destroy_return_False(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.destroy_node.return_value = False
        result = self.runner.invoke(cli,
                                    ['server', 'destroy',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('Something went wrong with attempting to destroy', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_destroy_APIException(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.destroy_node.side_effect = DimensionDataAPIException(
            code='REASON 538', msg='Cannot destroy server', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'destroy',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('REASON 538', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_reboot(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.reboot_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'reboot',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('is being rebooted', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_reboot_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.reboot_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'reboot',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('is being rebooted', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_reboot_return_False(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.reboot_node.return_value = False
        result = self.runner.invoke(cli,
                                    ['server', 'reboot',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('Something went wrong with attempting to reboot', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_reboot_APIException(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.reboot_node.side_effect = DimensionDataAPIException(
            code='REASON 537', msg='Cannot reboot server', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'reboot',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('REASON 537', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_reboot_hard(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_reset.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'reboot_hard',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('is being rebooted', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_reboot_hard_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_reset.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'reboot_hard',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('is being rebooted', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_reboot_hard_return_False(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_reset.return_value = False
        result = self.runner.invoke(cli,
                                    ['server', 'reboot_hard',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('Something went wrong with attempting to reboot', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_reboot_hard_APIException(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_reset.side_effect = DimensionDataAPIException(
            code='REASON 536', msg='Cannot reboot_hard server', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'reboot_hard',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('REASON 536', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_shutdown(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_shutdown_graceful.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('is shutting down gracefully', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_shutdown_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_shutdown_graceful.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('is shutting down gracefully', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_shutdown_return_False(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_shutdown_graceful.return_value = False
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('Something went wrong when attempting to shutdown', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_shutdown_APIException(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_shutdown_graceful.side_effect = DimensionDataAPIException(
            code='REASON 535', msg='Cannot shutdown server', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('REASON 535', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_shutdown_hard(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_power_off.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown_hard',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('is shutting down hard', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_shutdown_hard_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_power_off.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown_hard',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('is shutting down hard', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_shutdown_hard_return_False(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_power_off.return_value = False
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown_hard',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('Something went wrong when attempting to shutdown', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_shutdown_hard_APIException(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_power_off.side_effect = DimensionDataAPIException(
            code='REASON 534', msg='Cannot shutdown_hard server', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'shutdown_hard',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('REASON 534', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_start(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_start_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'start',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('is starting', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_start_server_filters(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_start_node.return_value = True
        result = self.runner.invoke(cli,
                                    ['server', 'start',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('is starting', result.output)
        self.assertTrue(result.exit_code == 0)

    def test_server_start_return_False(self, node_client):
        node_client.return_value.list_nodes.return_value = load_dd_obj('single_node_list.json')
        node_client.return_value.ex_start_node.return_value = False
        result = self.runner.invoke(cli,
                                    ['server', 'start',
                                     '--serverFilterIpv6', '::1'])
        self.assertIn('Something went wrong when attempting to start', result.output)
        self.assertTrue(result.exit_code == 1)

    def test_server_start_APIException(self, node_client):
        node_client.return_value.ex_get_node_by_id.return_value = load_dd_obj('node.json')
        node_client.return_value.ex_start_node.side_effect = DimensionDataAPIException(
            code='REASON 533', msg='Cannot start server', driver=None)
        result = self.runner.invoke(cli,
                                    ['server', 'start',
                                     '--serverId', '8aeff10c-c918-4021-b2ce-93e4a209418b'])
        self.assertIn('REASON 533', result.output)
        self.assertTrue(result.exit_code == 1)
