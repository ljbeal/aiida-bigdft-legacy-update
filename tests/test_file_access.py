import os

import yaml
from aiida.orm import load_node

from aiida_bigdft_new.data.BigDFTFile import BigDFTFile


def test_saveload_file():

    test_data = {'test': 7}
    path = os.path.join(os.getcwd(), 'test.yaml')

    with open(path, 'w+') as o:
        yaml.dump(test_data, o)

    filenode = BigDFTFile(path)

    assert filenode.content == test_data

    # now store and reload the node
    filenode.store()

    reloaded = load_node(filenode.pk)

    assert reloaded.content == test_data
