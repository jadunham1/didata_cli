from didata_cli.cli import cli
from click.testing import CliRunner
import click
import unittest
import os




class DimensionDataCLITestCase(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        config_filename = os.path.join(os.path.dirname(__file__), '..', '.didata_cfg')
        if os.path.isfile(config_filename):
            config = configparser.ConfigParser()
            config.read(config_filename)
            os.environ["DIDATA_USER"] = config.get('default', 'user')
            os.environ["DIDATA_PASSWORD"] = config.get('default', 'password')
        else:
            os.environ["DIDATA_USER"] = 'fakeuser'
            os.environ["DIDATA_PASSWORD"] = 'fakepass'

    def test_cli(self):
        result = self.runner.invoke(cli, ['server'], catch_exceptions=False)
        assert result.exit_code == 0

