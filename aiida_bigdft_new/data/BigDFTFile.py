import os

import yaml
from BigDFT.Logfiles import Logfile
from aiida.orm import SinglefileData


__all__ = ('BigDFTFile',)


class BigDFTFile(SinglefileData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._content = self._open()

    def _open(self):
        try:
            with self.open() as o:
                return yaml.safe_load(o)
        except FileNotFoundError:
            pass

    @property
    def content(self):
        return self._content

    def dump_file(self, path=None):
        """
        Dump the stored file to `path`
        defaults to cwd + filename if not provided
        """
        path = path or os.path.join(os.getcwd(), self.filename)

        with self.open() as inp:
            with open(path, 'w+') as out:
                out.write(inp.read())


class BigDFTLogfile(BigDFTFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def logfile(self):
        return Logfile(dictionary=self.content)
