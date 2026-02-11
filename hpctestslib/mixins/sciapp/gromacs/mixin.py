# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


# import datetime
import os
import re
import sys

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility as util

# Add the root directory of hpctestslib
prefix = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import util as hpcutil


GITHUB_INPUT_URL = 'https://api.github.com/repos/victorusu/GROMACS_Benchmark_Suite/tarball/refs/tags/1.0.0' # noqa: E501


class gromacs_mixin(rfm.RegressionTestPlugin):
    '''
    Title: GROMACS benchmarks mixin
    Description: This mixin provides functionality to write GROMACS benchmarks.
    This mixin implements six different benchmarks:
    * HECBioSim/Crambin
    * HECBioSim/Glutamine-Binding-Protein
    * HECBioSim/hEGFRDimer
    * HECBioSim/hEGFRDimerSmallerPL
    * HECBioSim/hEGFRDimerPair
    * HECBioSim/hEGFRtetramerPair

    Notes:
    * The mixin assumes the use of MPI version of the code (gmx_mpi).

    * The mixin was based on the HECBioSim
    (https://www.hecbiosim.ac.uk/access-hpc/benchmarks) input files.
    They are stored on GitHub for improved download reliability.

    * The computer requires network access to run these tests to download
    the input files

    * The mixin supports CPU and GPU-accelerated non-bonded calculations

    * Since this is a mixin, there is no definition of job parameters.
    These are expected to be set in the test that uses this mixin.
    '''

    #: Parameter encoding the name of the benchmark to run
    #:
    #: :type: :class:`str`
    #: :values: ``['HECBioSim/Crambin', 'HECBioSim/Glutamine-Binding-Protein', 'HECBioSim/hEGFRDimer', 'HECBioSim/hEGFRDimerSmallerPL', 'HECBioSim/hEGFRDimerPair', 'HECBioSim/hEGFRtetramerPair']``
    benchmark = parameter([
        'HECBioSim/Crambin',
        'HECBioSim/Glutamine-Binding-Protein',
        'HECBioSim/hEGFRDimer',
        'HECBioSim/hEGFRDimerSmallerPL',
        'HECBioSim/hEGFRDimerPair',
        'HECBioSim/hEGFRtetramerPair'
    ])

    #: Parameter encoding the implementation of the non-bonded calculations
    #:
    #: :type: :class:`str`
    #: :values: ``['cpu', 'gpu']``
    nb_impl = parameter(['cpu', 'gpu'])

    @run_after('init')
    def set_executable(self):
        self.executable = 'gmx_mpi mdrun'

    @run_after('init')
    def set_tags(self):
        self.tags |= {'sciapp', 'chemistry'}

    @run_after('init')
    def set_descr(self):
        self.descr = f'GROMACS {self.benchmark} benchmark'

    @run_after('init')
    def set_keep_files(self):
        self.keep_files = ['md.log']

    @run_after('init')
    def set_kernel_impl(self):
        self.executable_opts += ['-v', '-nb', self.nb_impl]

    @run_after('init')
    def set_ntomp(self):
        if self.num_cpus_per_task:
            self.executable_opts += ['-ntomp', self.num_cpus_per_task]

    @run_before('run')
    def set_inputfile(self):
        input_file = os.path.join(self.benchmark, 'benchmark.tpr')
        self.executable_opts += [f'-s {input_file}']

    @run_before('run')
    def download_inputfile_from_github(self):
        self.prerun_cmds += [
            fr'{hpcutil.CURLCMD} -LJ {GITHUB_INPUT_URL} -o inputs.tar.gz',
            fr'{hpcutil.TARCMD} xf inputs.tar.gz --strip-components=1 '
            fr'-C {self.stagedir}'
        ]

    @performance_function('ns/day')
    def perf(self):
        return sn.extractsingle(r'Performance:\s+(?P<perf>\S+)',
                                'md.log', 'perf', float)

    @deferrable
    def assert_hecbiosim_crambin(self):
        energy = sn.extractsingle(r'\s+Potential\s+Kinetic En\.\s+Total Energy'
                                r'\s+Conserved En\.\s+Temperature\n'
                                r'(\s+\S+){2}\s+(?P<energy>\S+)(\s+\S+){2}\n'
                                r'\s+Pressure \(bar\)\s+Constr\. rmsd',
                                'md.log', 'energy', float, item=-1)
        ref_energy = -204107.0
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_hecbiosim_glutamine_binding_protein(self):
        energy = sn.extractsingle(r'\s+Potential\s+Kinetic En\.\s+Total Energy'
                                r'\s+Conserved En\.\s+Temperature\n'
                                r'(\s+\S+){2}\s+(?P<energy>\S+)(\s+\S+){2}\n'
                                r'\s+Pressure \(bar\)\s+Constr\. rmsd',
                                'md.log', 'energy', float, item=-1)
        ref_energy = -724598.0
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_hecbiosim_hegfrdimer(self):
        energy = sn.extractsingle(r'\s+Potential\s+Kinetic En\.\s+Total Energy'
                                r'\s+Conserved En\.\s+Temperature\n'
                                r'(\s+\S+){2}\s+(?P<energy>\S+)(\s+\S+){2}\n'
                                r'\s+Pressure \(bar\)\s+Constr\. rmsd',
                                'md.log', 'energy', float, item=-1)
        ref_energy = -3.32892e+06
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_hecbiosim_hegfrdimersmallerpl(self):
        energy = sn.extractsingle(r'\s+Potential\s+Kinetic En\.\s+Total Energy'
                                r'\s+Conserved En\.\s+Temperature\n'
                                r'(\s+\S+){2}\s+(?P<energy>\S+)(\s+\S+){2}\n'
                                r'\s+Pressure \(bar\)\s+Constr\. rmsd',
                                'md.log', 'energy', float, item=-1)
        ref_energy = -3.27080e+06
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_hecbiosim_hegfrdimerpair(self):
        energy = sn.extractsingle(r'\s+Potential\s+Kinetic En\.\s+Total Energy'
                                r'\s+Conserved En\.\s+Temperature\n'
                                r'(\s+\S+){2}\s+(?P<energy>\S+)(\s+\S+){2}\n'
                                r'\s+Pressure \(bar\)\s+Constr\. rmsd',
                                'md.log', 'energy', float, item=-1)
        ref_energy = -1.20733e+07
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_hecbiosim_hegfrtetramerpair(self):
        energy = sn.extractsingle(r'\s+Potential\s+Kinetic En\.\s+Total Energy'
                                r'\s+Conserved En\.\s+Temperature\n'
                                r'(\s+\S+){2}\s+(?P<energy>\S+)(\s+\S+){2}\n'
                                r'\s+Pressure \(bar\)\s+Constr\. rmsd',
                                'md.log', 'energy', float, item=-1)
        ref_energy = -2.09831e+07
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @sanity_function
    def assert_sanity(self):
        '''Assert that the obtained energy meets the benchmark tolerances.'''

        assert_fn_name = f'assert_{util.toalphanum(self.benchmark).lower()}'
        assert_fn = getattr(self, assert_fn_name, None)
        sn.assert_true(
            assert_fn is not None,
            msg=(f'cannot extract energy from benchmark {self.benchmark!r}: '
                 f'please define a member function "{assert_fn_name}()"')
        ).evaluate()

        return sn.chain(
                sn.assert_found('Finished mdrun', 'md.log'),
                sn.assert_not_found('Segmentation fault', self.stderr),
                assert_fn(),
            )
