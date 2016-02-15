from didata_cli.utils import flattenDict


def test_flatten_dict():
    data = {'a': {'b': 1}, 'c': 3}
    flattenDict(data)
