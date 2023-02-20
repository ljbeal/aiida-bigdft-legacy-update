"""
Tests that the inbuilt file objects funciton after database store and load
"""

import os

import yaml

from aiida.orm import load_node

from aiida_bigdft_new.data.BigDFTFile import BigDFTFile


def test_saveload_file():
    """
    Write out a basic yaml, then test BigDFTFile features
    """

    test_data = {"test": 7}
    path = os.path.join(os.getcwd(), "test.yaml")

    with open(path, "w+", encoding="utf8") as o:
        yaml.dump(test_data, o)

    filenode = BigDFTFile(path)

    assert filenode.content == test_data

    # now store and reload the node
    filenode.store()

    reloaded = load_node(filenode.pk)

    assert reloaded.content == test_data
