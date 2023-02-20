#!/usr/bin/env python
"""Run a test calculation on localhost.

Usage: ./example_01.py
"""
from os import path

import click

from aiida import cmdline, engine
from aiida.engine import run, submit
from aiida.orm import StructureData

from aiida_bigdft_new import helpers
from aiida_bigdft_new.calculations import BigDFTCalculation
from aiida_bigdft_new.data import BigDFTParameters

INPUT_DIR = path.join(path.dirname(path.realpath(__file__)), "input_files")


def test_run(bigdft_new_code):
    """Run a calculation on the localhost computer.

    Uses test helpers to create AiiDA Code on the fly.
    """
    if not bigdft_new_code:
        # get code
        computer = helpers.get_computer()
        bigdft_new_code = helpers.get_code(entry_point="bigdft_new", computer=computer)

    alat = 4  # angstrom
    cell = [
        [
            alat,
            0,
            0,
        ],
        [
            0,
            alat,
            0,
        ],
        [
            0,
            0,
            alat,
        ],
    ]
    s = StructureData(cell=cell)
    s.append_atom(position=(alat / 2, alat / 2, alat / 2), symbols="Ti")
    s.append_atom(position=(alat / 2, alat / 2, 0), symbols="O")
    s.append_atom(position=(alat / 2, 0, alat / 2), symbols="O")

    inputs = {
        "code": bigdft_new_code,
        "structure": s,
        "metadata": {
            "options": {
                "jobname": "TiO2",
                "max_wallclock_seconds": 3600,
                "queue_name": "mono",
            }
        },
    }

    bigdft_parameters = {}
    bigdft_parameters["dft"] = {"ixc": "LDA", "itermax": "5"}
    bigdft_parameters["output"] = {"orbitals": "binary"}

    inputs["parameters"] = BigDFTParameters(bigdft_parameters)

    result = submit(BigDFTCalculation, **inputs)

    return result


@click.command()
@cmdline.utils.decorators.with_dbenv()
@cmdline.params.options.CODE()
def cli(code):
    """Run example.

    Example usage: $ ./example_01.py --code diff@localhost

    Alternative (creates diff@localhost-test code): $ ./example_01.py

    Help: $ ./example_01.py --help
    """
    test_run(code)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
