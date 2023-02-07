"""
Parsers provided by aiida_bigdft_new.

Register parsers via the "aiida.parsers" entry point in setup.json.
"""
import os
import re

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import SinglefileData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory
from aiida.common.exceptions import ValidationError

DiffCalculation = CalculationFactory("bigdft_new")


class BigDFTParser(Parser):
    """
    Parser class for parsing output of calculation.
    """

    def __init__(self, node):
        """
        Initialize Parser instance

        Checks that the ProcessNode being passed was produced by a DiffCalculation.

        :param node: ProcessNode of calculation
        :param type node: :class:`aiida.orm.nodes.process.process.ProcessNode`
        """
        super().__init__(node)
        if not issubclass(node.process_class, DiffCalculation):
            raise exceptions.ParsingError("Can only parse DiffCalculation")

    def parse_stderr(self, inputfile):
        """Parse the stderr file to get commong errors, such as OOM or timeout.

        :param i inputfile: stderr file
        :returns: exit code in case of an error, None otherwise
        """
        timeout_messages = {
            'DUE TO TIME LIMIT',                                                # slurm
            'exceeded hard wallclock time',                                     # UGE
            'TERM_RUNLIMIT: job killed',                                        # LFS
            'walltime .* exceeded limit'                                        # PBS/Torque
        }

        oom_messages = {
            '[oO]ut [oO]f [mM]emory',
            'oom-kill',                                                         # generic OOM messages
            'Exceeded .* memory limit',                                         # slurm
            'exceeds job hard limit .*mem.* of queue',                          # UGE
            'TERM_MEMLIMIT: job killed after reaching LSF memory usage limit',  # LFS
            'mem .* exceeded limit',                                            # PBS/Torque
        }
        for message in timeout_messages:
            if re.search(message, inputfile):
                return self.exit_codes.ERROR_OUT_OF_WALLTIME
        for message in oom_messages:
            if re.search(message, inputfile):
                return self.exit_codes.ERROR_OUT_OF_MEMORY
        return

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.

        :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
        """

        error = ExitCode(0)

        stderr = self.node.get_scheduler_stderr()
        if stderr:
            error = self.parse_stderr(stderr)
            if error:
                self.logger.error("Error in stderr: " + error.message)

        output_filename = self.node.get_option('output_filename')
        # jobname = self.node.get_option('jobname')
        # if jobname is not None:
        #     output_filename = "log-" + jobname + ".yaml"
        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [output_filename]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error("Found files '{}', expected to find '{}'".format(
                files_retrieved, files_expected))
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # add output file
        self.logger.info("Parsing '{}'".format(output_filename))
        try:
            with open(output_filename, 'w+') as tmp:
                tmp.write(self.retrieved.get_object_content(output_filename))
                output = SinglefileData(os.path.join(os.getcwd(), output_filename))

        except ValueError:
            self.logger.error("Impossible to parse LogFile".
                              format(output_filename))
            if not error:  # if we already have OOW or OOM, failure here will be handled later
                return self.exit_codes.ERROR_PARSING_FAILED
        try:
            output.store()
            self.logger.info("Successfully parsed LogFile '{}'".
                             format(output_filename))
        except ValidationError:
            self.logger.info("Impossible to store LogFile - ignoring '{}'".
                             format(output_filename))
            if not error:  # if we already have OOW or OOM, failure here will be handled later
                return self.exit_codes.ERROR_PARSING_FAILED

        self.out('logfile', output)

        return error
