"""
Calculations provided by aiida_bigdft_new.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
import os
from pprint import pprint

from BigDFT.Atoms import Atom
from BigDFT.Fragments import Fragment
from BigDFT.Inputfiles import Inputfile
import BigDFT.Systems
from BigDFT.Systems import System
from BigDFT.UnitCells import UnitCell
import yaml

from aiida.common import datastructures
from aiida.engine import CalcJob
import aiida.orm
from aiida.orm import Bool, SinglefileData, Str, StructureData, to_aiida_type

from aiida_bigdft_new.data import BigDFTParameters
from aiida_bigdft_new.data.BigDFTFile import BigDFTFile, BigDFTLogfile


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
        spec.inputs["metadata"]["options"]["parser_name"].default = "bigdft_new"

        # inputs
        # structure input. Either AiiDA structuredata, or direct posinp file
        spec.input("structure", valid_type=StructureData)
        spec.input(
            "posinp",
            valid_type=Str,
            default=lambda: Str(BigDFTCalculation._posinp),
            help="structure xyz file",
        )
        spec.input("metadata.options.jobname", valid_type=str, required=False)
        spec.input(
            "parameters",
            valid_type=BigDFTParameters,
            help="Command line parameters for BigDFT",
        )

        spec.input(
            "dry_run",
            valid_type=Bool,
            default=lambda: Bool(False),
            help="Stops calculation after posinp writing if True",
            serializer=to_aiida_type,
        )

        # outputs
        spec.input(
            "metadata.options.output_filename",
            valid_type=str,
            default=BigDFTCalculation._logfile,
        )
        spec.output("logfile", valid_type=BigDFTLogfile, help="BigDFT Logfile")
        spec.output("timefile", valid_type=BigDFTFile, help="BigDFT timing file")

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
            "ERROR_OUT_OF_WALLTIME",
            message="Calculation did not finish because of a walltime issue.",
        )
        spec.exit_code(
            401,
            "ERROR_OUT_OF_MEMORY",
            message="Calculation did not finish because of memory limit.",
        )

    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        print("preparing for submission")

        inpdict = Inputfile()
        inpdict.update(self.inputs.parameters.get_dict())

        # structure = check_ortho(self.inputs.structure)
        structure = self.inputs.structure

        inpdict.update({"posinp": structure_to_posinp(structure)})

        self.logger.info("inp dict is")
        self.logger.info(inpdict)

        with open(self._inpfile, "w+") as o:
            self.logger.info(f"writing inputfile {self._inpfile}")
            yaml.dump(dict(inpdict), o)

        if self.inputs.dry_run:
            self.logger.warning("dry_run is true, exiting early")
            codeinfo = datastructures.CodeInfo()
            codeinfo.code_uuid = self.inputs.code.uuid

            calcinfo = datastructures.CalcInfo()
            calcinfo.codes_info = [codeinfo]

            return calcinfo

        inpfile = SinglefileData(os.path.join(os.getcwd(), self._inpfile)).store()

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
            f"./data/{BigDFTCalculation._timefile}",
            "forces_posinp.yaml",
            # "forces_posinp.xyz",
            # "final_posinp.yaml",
            # "final_posinp.xyz",
            ["./debug/bigdft-err*", ".", 2],
        ]

        return calcinfo


def structure_to_system(
    structure: aiida.orm.StructureData, coerce=False
) -> BigDFT.Systems.System:
    """
    Creates a BigDFT System from input aiida StructureData

    This method adds a fragment to the position section,
    though can be safely ignored.
    """
    print(f"creating bigdft System from {structure.get_description()}")

    if structure.cell_angles != [90.0, 90.0, 90.0] and not coerce:
        raise ValueError("non orthorhombic cells are not supported")

    as_ase = structure.get_ase()

    frag = Fragment()
    for atom in as_ase:
        # print(f'appending {sym} at {loc}')
        sym = atom.symbol
        loc = atom.position

        frag.append(Atom({sym: loc, "sym": sym, "units": "angstroem"}))

    sys = System()
    sys.cell = UnitCell(as_ase.cell.tolist(), units="angstroem")
    sys["FRA:0"] = frag

    return sys


def structure_to_posinp(structure: aiida.orm.StructureData) -> dict:
    """
    Creates a posinp file from input aiida StructureData
    """

    def process_line(line: str) -> [str, list]:
        """
        xyz position lines are in the format
        at x.x y.y z.z
        split, and convert
        """
        at_sym = line.split()[0]
        at_loc = [float(p) for p in line.split()[1:]]
        return at_sym, at_loc

    # print(f'creating bigdft System from {structure.get_description()}')

    string = structure._prepare_xyz()[0].decode().split("\n")

    # natoms = string[0]
    # cell = [float(v) for v in structure.cell_lengths]
    # pbc = structure.pbc

    posinp = {"units": "angstroem"}

    positions = []
    for sym, loc in [process_line(line) for line in string[2:]]:
        # print(f'appending {sym} at {loc}')
        # frag.append(Atom({sym: loc, 'sym': sym, 'units': 'angstroem'}))

        positions.append({sym: loc})

    posinp["positions"] = positions
    posinp["abc"] = structure.get_ase().cell.tolist()

    return posinp
