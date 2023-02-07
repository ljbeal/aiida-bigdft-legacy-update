[![Build Status][ci-badge]][ci-link]
[![Coverage Status][cov-badge]][cov-link]
[![Docs status][docs-badge]][docs-link]
[![PyPI version][pypi-badge]][pypi-link]

# aiida-bigdft-new

Temporary Repository for migration of [aiida-bigdft-plugin](https://github.com/ljbeal/aiida-bigdft-plugin) to python 3 and aiida 2.0

## Installation

```shell
pip install aiida-bigdft-new
verdi quicksetup  # better to set up a new profile
verdi plugin list aiida.calculations  # should now show your calclulation plugins
```


## Usage

Here goes a complete example of how to submit a test calculation using this plugin.

A quick demo of how to submit a calculation:
```shell
verdi daemon start     # make sure the daemon is running
cd examples
./example_01.py        # run test calculation
verdi process list -a  # check record of calculation
```

The plugin also includes verdi commands to inspect its data types:
```shell
verdi data bigdft_new list
verdi data bigdft_new export <PK>
```

## Development

```shell
git clone https://github.com/ljbeal/aiida-bigdft-new .
cd aiida-bigdft-new
pip install --upgrade pip
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

See the [developer guide](http://aiida-bigdft-new.readthedocs.io/en/latest/developer_guide/index.html) for more information.

## License

MIT
## Contact

louis.j.beal@gmail.com


[ci-badge]: https://github.com/ljbeal/aiida-bigdft-new/workflows/ci/badge.svg?branch=master
[ci-link]: https://github.com/ljbeal/aiida-bigdft-new/actions
[cov-badge]: https://coveralls.io/repos/github/ljbeal/aiida-bigdft-new/badge.svg?branch=master
[cov-link]: https://coveralls.io/github/ljbeal/aiida-bigdft-new?branch=master
[docs-badge]: https://readthedocs.org/projects/aiida-bigdft-new/badge
[docs-link]: http://aiida-bigdft-new.readthedocs.io/
[pypi-badge]: https://badge.fury.io/py/aiida-bigdft-new.svg
[pypi-link]: https://badge.fury.io/py/aiida-bigdft-new
