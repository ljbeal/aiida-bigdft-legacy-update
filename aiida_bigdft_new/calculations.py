"""
Calculations provided by aiida_bigdft_new.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
import os

from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import SinglefileData, StructureData, Str
from aiida.plugins import DataFactory

from BigDFT.Inputfiles import Inputfile

BigDFTParameters = DataFactory("bigdft_new")


class BigDFTCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the BigDFT executable.
    """

    _posinp = 'posinp.xyz'
    _inpfile = 'input.yaml'
    _logfile = 'log.yaml'
    _timefile = 'time.yaml'

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        super().define(spec)

        # set default values for AiiDA options
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }
        spec.inputs["metadata"]["options"]["parser_name"].default = "bigdft_new"

        # inputs
        # structure input. Either AiiDA structuredata, or direct posinp file
        spec.input(
            "structure",
            valid_type=StructureData
        )
        spec.input(
            "posinp",
            valid_type=Str,
            default=lambda: Str(BigDFTCalculation._posinp),
            help='structure xyz file'
        )
        spec.input(
            "metadata.options.jobname",
            valid_type=str,
            required=False
        )
        spec.input(
            "parameters",
            valid_type=BigDFTParameters,
            help="Command line parameters for BigDFT",
        )

        # outputs
        spec.input(
            "metadata.options.output_filename",
            valid_type=str,
            default=BigDFTCalculation._logfile
        )

        # error codes
        spec.exit_code(
            300,
            "ERROR_MISSING_OUTPUT_FILES",
            message="Calculation did not produce all expected output files.",
        )
        spec.exit_code(
            301,
            "ERROR_PARSING_FAILED",
            message="Parsing error.",
        )
        spec.exit_code(
            400,
            'ERROR_OUT_OF_WALLTIME',
            message='Calculation did not finish because of a walltime issue.'
        )
        spec.exit_code(
            401,
            'ERROR_OUT_OF_MEMORY',
            message='Calculation did not finish because of memory limit.'
        )

    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        def write_posinp(structure):
            # posinp_filename = self.inputs.structurefile.value
            posinp_filename = 'Not Written'
            if self.inputs.structure is not None:
                if self.inputs.structure.cell_angles != [90.0, 90.0, 90.0]:
                    raise ValueError('non orthorhombic cells are not supported')

                print("writing input posinp file")
                posinp_string = self.inputs.structure._prepare_xyz()[0]
                # set bcs at the correct format (periodic only?)
                if self.inputs.structure.pbc == (True, True, True):
                    filestring = posinp_string.split(b'\n')
                    line = "periodic " + str(self.inputs.structure.cell_lengths[0]) + " "\
                           + str(self.inputs.structure.cell_lengths[1]) + " "\
                           + str(self.inputs.structure.cell_lengths[2])
                    filestring[1] = line.encode()
                    posinp_string = b'\n'.join(filestring)

                if "jobname" not in self.inputs.metadata.options:
                    posinp_filename = self._posinp
                else:
                    posinp_filename = self.inputs.metadata.options.jobname + ".xyz"

                # write posinp, open file in correct format
                fmode = 'w+' if isinstance(posinp_string, str) else 'wb+'
                with open(posinp_filename, fmode) as posfile:
                    posfile.write(posinp_string)

            return SinglefileData(os.path.join(os.getcwd(), posinp_filename)).store()

        print('preparing for submission')

        inpdict = Inputfile()
        inpdict.update(self.inputs.parameters.get_dict())

        print('inp dict is')
        print(inpdict)

        posinp_file = write_posinp(self.inputs.structure)
        print('posinp written to', posinp_file)

        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [
            (
                posinp_file.uuid,
                posinp_file.filename,
                posinp_file.filename,
            ),
        ]
        calcinfo.retrieve_list = [self.metadata.options.output_filename]

        return calcinfo
