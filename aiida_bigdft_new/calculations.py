"""
Calculations provided by aiida_bigdft_new.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
import os

import yaml
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import SinglefileData, Str, StructureData

from BigDFT.Inputfiles import Inputfile

from aiida_bigdft_new.data import BigDFTParameters
from aiida_bigdft_new.utils.preprocess import check_orthorhombic


class BigDFTCalculation(CalcJob):
    """
    AiiDA calculation plugin wrapping the BigDFT executable.
    """

    _posinp = "posinp.xyz"
    _inpfile = "input.yaml"
    _logfile = "log.yaml"
    _timefile = "time.yaml"

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        super().define(spec)

        # set default values for AiiDA options
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }
        spec.inputs["metadata"]["options"][
            "parser_name"].default = "bigdft_new"

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
        spec.output(
            "logfile",
            valid_type=SinglefileData,
            help="BigDFT Logfile"
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

        def structure_to_posinp(structure):
            def process_line(line):
                at = line.split()[0]
                pos = [float(p) for p in line.split()[1:]]

                return {at: pos}

            string = structure._prepare_xyz()[0].decode().split('\n')

            # natoms = string[0]
            cell = [float(v) for v in structure.cell_lengths]
            # pbc = structure.pbc

            pos = [process_line(l) for l in string[2:]]

            return {'posinp':
                        {'cell': cell,
                         'positions': pos,
                         'units': 'angstroem'
                         }
                    }

        print('preparing for submission')

        inpdict = Inputfile()
        inpdict.update(self.inputs.parameters.get_dict())

        structure = check_orthorhombic(self.inputs.structure)

        inpdict.update(structure_to_posinp(structure))

        print('inp dict is')
        print(inpdict)

        with open(self._inpfile, 'w+') as o:
            yaml.dump(dict(inpdict), o)

        inpfile = SinglefileData(
            os.path.join(os.getcwd(), self._inpfile)).store()

        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [
            (
                inpfile.uuid,
                inpfile.filename,
                inpfile.filename,
            ),
        ]
        calcinfo.retrieve_list = [
            self.metadata.options.output_filename,
            f'./data/{BigDFTCalculation._timefile}',
            "forces_posinp.yaml",
            # "forces_posinp.xyz",
            # "final_posinp.yaml",
            # "final_posinp.xyz",
            ["./debug/bigdft-err*", ".", 2]
        ]

        return calcinfo
