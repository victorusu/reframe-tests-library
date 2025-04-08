# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import os
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


# Instructions provided by Sebastian to run on Alps Daint:
# wget --quiet -O 50c.h5 https://zenodo.org/records/8369645/files/50c.h5
# OMP_NUM_THREADS=64 srun -N1 -c72 --ntasks-per-node=4 -c72 --gpus-per-task=1 ./sphexa-cuda --init evrard --glass 50c.h5 -n 1000 -s 5
class sphexa_mixin(rfm.RegressionMixin):
    '''
    Title: SPH-EXA benchmarks mixin
    Description: This mixin provides functionality to write SPH-EXA benchmarks.
    This mixin implements two different benchmarks: evrard and turbulence.

    Notes:
    * The test must define two ReFrame variables/parameters or instance variables,
    num_particles and num_steps.

    * The test was based on instructions provided by the lead developer,
    Sebastian Keller, including the input file to be downloaded from zenodo.

    * The computer requires network access to run these tests to download
    the input files

    * Since this is a mixin, there is no definition of job parameters.
    These are expected to be set in the test that uses this mixin.
    '''

    #: Parameter encoding the benchmark to run
    #:
    #: :type: :class:`str`
    #: :values: ``['evrard','turbulence']``
    benchmark = parameter([
        'evrard',
        'turbulence',
    ])

    @run_after('init')
    def set_executable(self):
        self.executable = 'sphexa'

    @run_after('init')
    def set_tags(self):
        self.tags |= {'sciapp', 'physics'}

    @run_after('init')
    def set_descr(self):
        self.descr = f'SPH-EXA {self.benchmark} benchmark'

    @run_after('init')
    def _set_num_particles(self):
        self.executable_opts += ['-n', f'{self.num_particles}']

    @run_after('init')
    def _set_num_steps(self):
        self.executable_opts += ['-s', f'{self.num_steps}']

    @run_before('run')
    def set_benchmark_conditions(self):
        bench_fn_name = f'set_benchmark_{util.toalphanum(self.benchmark).lower()}'
        bench_fn = getattr(self, bench_fn_name, None)
        sn.assert_true(
            bench_fn is not None,
            msg=(f'cannot setup benchmark {self.benchmark!r}: '
                 f'please define a member function "{bench_fn_name}()"')
        ).evaluate()
        bench_fn()

    def set_benchmark_evrard(self):
        self.prerun_cmds = [
            f'{hpcutil.ULIMITCMD} -c 0',
            f'{hpcutil.CURLCMD} -LJO https://zenodo.org/records/8369645/files/50c.h5'
        ]
        self.executable_opts = ['--init', f'{self.benchmark}',
                                '--glass', '50c.h5']

    def set_benchmark_turbulence(self):
        self.prerun_cmds = [
            f'{hpcutil.ULIMITCMD} -c 0',
            f'{hpcutil.CURLCMD} -LJO https://zenodo.org/records/8369645/files/50c.h5'
        ]
        self.executable_opts = ['--init', f'{self.benchmark}',
                                '--prop', f'{self.benchmark}',
                                '--glass', '50c.h5']

    @performance_function('s')
    def perf(self):
        # === Total time for iteration(50) 3.45854s
        return sn.extractsingle(r'===\s+Total\s+time\s+for\s+iteration\S+\s+'
                                r'(?P<perf>\S+)s',
                                self.stdout, 'perf', float, -1)

    def assert_sphexa(self, ref_energy):
        # this is an arbritary number I have defined
        ener_thres = 1e-4

        ### Check ### Total energy: -0.616261, (internal: 0.049779, kinetic: 0.00067688, gravitational: -0.666717)
        total_energy = sn.extractsingle(r'Total\s+energy:\s+(?P<energy>\S+),',
                                      self.stdout, 'energy', float,
                                      item=-1)
        ref_total_energy = ref_energy
        thres_total_energy = abs(ener_thres / ref_total_energy)

        nsteps = sn.extractsingle(r'===\s+Total\s+time\s+for\s+iteration'
                                  r'\((?P<nsteps>\S+)\)\s+',
                                self.stdout, 'nsteps', int, item=-1)

        return sn.all([
            sn.assert_reference(total_energy, ref_total_energy,
                                -thres_total_energy, thres_total_energy),
            sn.assert_eq(nsteps, int(self.num_steps),
                         msg=f'The simulation did not run for the expected'
                             f'{self.num_steps} steps'),
        ])

    @deferrable
    def assert_evrard(self):
        return self.assert_sphexa(-0.616261)

    @deferrable
    def assert_turbulence(self):
        return self.assert_sphexa(1000)

    @sanity_function
    def assert_sanity(self):
        '''Assert that the obtained energy meets the benchmark tolerances.'''

        assert_fn_name = (f'assert_{util.toalphanum(self.benchmark).lower()}')
        assert_fn = getattr(self, assert_fn_name, None)
        sn.assert_true(
            assert_fn is not None,
            msg=(f'cannot extract energy from benchmark {self.benchmark!r}: '
                 f'please define a member function "{assert_fn_name}()"')
        ).evaluate()
        return sn.chain(
               sn.assert_not_found('Segmentation fault', self.stderr),
               sn.assert_not_found('std::runtime_error', self.stderr),
               sn.assert_not_found('std::bad_alloc', self.stderr),
               sn.assert_not_found('out of memory', self.stderr),
               assert_fn(),
            )

