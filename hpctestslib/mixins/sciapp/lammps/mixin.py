# Copyright 2025 ETHZ/CSCS
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


class lammps_mixin(rfm.RegressionMixin):
    '''
    Title: LAMMPS benchmarks mixin
    Description: This mixin provides functionality to write LAMMPS benchmarks.
    This mixin implements twelve different benchmarks:
    * adp
    * comb
    * eam
    * eim
    * fene
    * gb
    * lj
    * peri
    * protein
    * spce
    * sw
    * tersoff

    The benchmarks have been taken from the official
    LAMMPS documentation (https://www.lammps.org/bench.html).

    Notes:
    * The mixin the num_steps instance variable. If you want to change that,
    please change the sanity functions appropriately.

    * The test supports the default implementaion of the pairlist potentials
    and also attempts to set explicitly the Kokkos one.
    But not all benchmarks support Kokkos. Check the skip_some_kokkos_benchmarks
    function.

    * The computer requires network access to run these tests to download
    the input files directly from LAMMPS website

    * Since this is a mixin, there is no definition of job parameters.
    These are expected to be set in the test that uses this mixin.
    '''

    #: Parameter defining name of the benchmark to run
    #:
    #: :type: :class:`str`
    #: :values: ``['adp', 'comb', 'eam', 'eim', 'fene', 'gb', 'lj', 'peri', 'protein', 'spce', 'sw', 'tersoff']``
    benchmark = parameter([
        'adp',
        'comb',
        'eam',
        # 'eff', # can be added to the binary
        'eim',
        'fene',
        'gb',
        'lj',
        # 'meam', # can be added to the binary
        'peri',
        'protein',
        'spce',
        'sw',
        'tersoff',
    ])
    #: Parameter encoding the name of the benchmark to run
    #:
    #: :type: :class:`str`
    #: :values: ``['adp', 'comb', 'eam', 'eim', 'fene', 'gb', 'lj', 'peri', 'protein', 'spce', 'sw', 'tersoff']``
    kokkos = parameter([True, False])
    # any change to num steps need to be reflected on the assert functions
    num_steps = 100000

    @run_after('init')
    def set_executable(self):
        self.executable = 'lmp'

    @run_after('init')
    def set_tags(self):
        self.tags |= {'sciapp', 'chemistry'}

    @run_after('init')
    def set_descr(self):
        self.descr = f'LAMMP {self.benchmark} benchmark'

    @run_after('init')
    def check_num_steps(self):
        # the spce benchmark fails with kokkos after 75'000 steps
        if self.benchmark == 'spce' and self.kokkos:
            self.num_steps = min(self.num_steps, 75000)
        # the comb benchmark is too slow
        if self.benchmark == 'comb':
            self.num_steps = min(self.num_steps, 500)

    @run_after('init')
    def skip_some_kokkos_benchmarks(self):
        '''
        The peri bechmark does not work with kokkos
        ERROR: KOKKOS package requires a Kokkos-enabled atom_style
        '''
        self.skip_if(self.kokkos and self.benchmark in ['peri', 'gb'],
                     msg='This benchmark cannot be executed with kokkos')

    @run_before('run', always_last=True)
    def set_omp_num_threads(self):
        if 'OMP_NUM_THREADS' not in self.env_vars:
            self.env_vars['OMP_NUM_THREADS'] = self.num_cpus_per_task

    @run_before('run')
    def set_inputfile(self):
        self.executable_opts += [f'-i in.{self.benchmark}']

    @run_before('run')
    def set_kokkos(self):
        if self.kokkos:
            self.executable_opts += ['-k', 'on', '-pk', 'kokkos', '-sf', 'kk']

    @run_before('run')
    def set_download_inputfile_from_lammps_website(self):
        self.prerun_cmds += [
            fr'{hpcutil.CURLCMD} -LJO https://www.lammps.org/bench/bench_{self.benchmark}.tar.gz', # noqa: E501
            fr'{hpcutil.TARCMD} xf bench_{self.benchmark}.tar.gz --strip-components=1 -C {self.stagedir}', # noqa: E501
            fr"{hpcutil.SEDCMD} -i -e 's/^run.*100/run\t\t{self.num_steps}/g' in.{self.benchmark}" # noqa: E501
        ]

    @performance_function('s')
    def time_run(self):
        walltime = r'Total wall time: (?P<hour>\S+):(?P<min>\S+):(?P<sec>\S+)'
        hour = sn.extractsingle(walltime, self.stdout, 'hour', int)
        min = sn.extractsingle(walltime, self.stdout, 'min', int)
        sec = sn.extractsingle(walltime, self.stdout, 'sec', int)
        return (hour * 3600) + (min * 60) + sec

    @deferrable
    def assert_adp(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -135742.9
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])


    @deferrable
    def assert_comb(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<pot>\S+)\s+'
                                  r'(?P<vdw>\S+)\s+(?P<coul>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -6.8036753
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_eam(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -106640.77
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_eim(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<energy>\S+)\s+'
                                  r'(?P<pxx>\S+)\s+(?P<pyy>\S+)\s+(?P<pzz>\S+)'
                                  r'\s+(?P<temp>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -97216
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_fene(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = 22.469024
        if self.kokkos:
            ref_energy = 22.474714
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_gb(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = 3.4067608
        if self.kokkos:
            ref_energy = 4.6365424

        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_lj(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -4.6223453
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_peri(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = 449656900.0
        if self.kokkos:
            ref_energy = 9.4142265e+08
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_protein(self):
        energy = sn.extractsingle(fr'.*Step\s+{self.num_steps}.*\nTotEng\s+=\s+'
                                  r'(?P<energy>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -25723.2099
        if self.kokkos:
            ref_energy = -25329.5229

        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_spce(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -111318.84
        if self.kokkos:
            ref_energy = -110915.58

        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_sw(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -134631.82
        thres_energy = 0.001
        return sn.all([
            sn.assert_reference(energy, ref_energy, -thres_energy, thres_energy)
        ])

    @deferrable
    def assert_tersoff(self):
        energy = sn.extractsingle(fr'^\s+{self.num_steps}\s+(?P<temp>\S+)\s+'
                                  r'(?P<epair>\S+)\s+(?P<emol>\S+)\s+'
                                  r'(?P<energy>\S+)\s+(?P<press>\S+)',
                                  self.stdout, 'energy', float, item=-1)
        ref_energy = -144034.65
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
                sn.assert_found('Total wall time', self.stdout),
                sn.assert_not_found('Segmentation fault', self.stderr),
                assert_fn(),
            )
