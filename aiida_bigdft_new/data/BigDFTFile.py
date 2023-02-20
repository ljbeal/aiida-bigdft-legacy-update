import os

from BigDFT.Logfiles import Logfile
import yaml

from aiida.orm import SinglefileData


class BigDFTFile(SinglefileData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._content = self._open()

    def _open(self):
        try:
            with self.open() as o:
                return yaml.safe_load(o)
        except FileNotFoundError:
            self.logger.warning(f"file {self.filename} could not be opened!")
            return {}

    @property
    def content(self):
        try:
            return self._content
        except AttributeError:
            self._content = self._open()
            return self._content

    def dump_file(self, path=None):
        """
        Dump the stored file to `path`
        defaults to cwd + filename if not provided
        """
        path = path or os.path.join(os.getcwd(), self.filename)

        with self.open() as inp:
            with open(path, "w+") as out:
                out.write(inp.read())


class BigDFTLogfile(BigDFTFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def logfile(self):
        """
        Create and return the BigDFT Logfile object
        """
        return Logfile(dictionary=self.content)
