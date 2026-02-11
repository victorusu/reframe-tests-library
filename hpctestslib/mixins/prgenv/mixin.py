# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


# import datetime
import os

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility as util

from reframe.core.exceptions import SanityError

# import mixin as nwchem
import mixins.prgenv.inputs as inputs


class helloworld_mixin(rfm.RegressionTestPlugin):
    '''
    Title: STRESS-NG benchmarks mixin
    Description: This mixin provides functionality to write STRESS-NG benchmarks.
    This mixin implements 256 different benchmarks.

    Notes:
    * This is not an MPI code, thus this mixin assumes the use of MPI with
    a single rank

    * The mixin was based on the https://github.com/ColinIanKing/stress-ng.git.

    * The computer does not requires network access to run these tests

    * The mixin supports several CPU, memory, networks, disk benchmarks

    * Since this is a mixin, there is no definition of job parameters.
    These are expected to be set in the test that uses this mixin.
    '''

    #: Parameter encoding the name of the benchmark to run
    #:
    #: :type: :class:`str`
    #: :values: ``['mpi', 'openmp', 'serial']``
    benchmark = parameter(['mpi', 'openmp', 'serial'])
    # benchmark = parameter(['openmp', 'serial'])
    lang = parameter(['c', 'cpp', 'f90'])
    # lang = parameter(['c'])

    @run_after('init')
    def set_build_opts(self):
        self.build_system = 'SingleSource'
        self.prebuild_cmds = ['_rfm_build_time="$(date +%s%N)"']
        self.postbuild_cmds = [
            '_rfm_build_time="$(($(date +%s%N)-_rfm_build_time))"',
            'echo "Compilations time (ns): $_rfm_build_time"',
        ]

    @run_after('init')
    def set_executable(self):
        self.executable = './helloworld'

    @run_after('init')
    def set_tags(self):
        self.tags |= {'prgenv', 'helloworld'}

    @run_after('init')
    def set_descr(self):
        self.descr = f'Hello, World {self.benchmark} benchmark'

    @run_before('compile')
    def create_inpufile(self):
        try:
            content = getattr(inputs, util.toalphanum(self.lang).upper(), None)
        except Exception as e:
            self.skip(e)

        input_filename = f'helloworld.{self.lang}'
        self.sourcepath = input_filename
        input_filename = os.path.join(sn.evaluate(self.stagedir),
                                      input_filename)

        with open(input_filename, 'w') as f:
            f.write(content)

    @run_before('compile')
    def set_openmp_flags_and_env(self):
        if self.benchmark not in ['openmp', 'mpi+openmp']:
            return

        self.build_system.cflags = self.current_environ.extras.get(
            'c_openmp_flags', ['-fopenmp'])
        self.build_system.cxxflags = self.build_system.cflags
        self.build_system.fflags = self.current_environ.extras.get(
            'f_openmp_flags', self.build_system.cflags )

        # On SLURM there is no need to set OMP_NUM_THREADS if one defines
        # num_cpus_per_task, but adding for completeness and portability
        self.env_vars['OMP_NUM_THREADS'] = self.num_cpus_per_task

    @run_before('compile')
    def set_mpi_flags_and_env(self):
        if self.benchmark not in ['mpi', 'mpi+openmp']:
            return

        self.build_system.cppflags += ['-DUSE_MPI']

    @sanity_function
    def assert_hello_world(self):
        result = sn.findall(r'Hello, World from thread\s*(\d+) out '
                            r'of\s*(\d+)\s*from rank\s*(\d+) out of'
                            r'\s*(\d+)', self.stdout)

        num_tasks = sn.getattr(self, 'num_tasks')
        num_cpus_per_task = sn.getattr(self, 'num_cpus_per_task')

        if self.benchmark == 'serial':
            num_tasks = 1
            num_cpus_per_task = 1
        if not num_tasks:
            raise SanityError('num_tasks is not defined for this test. Cannot validate sanity')
        if not num_cpus_per_task:
            raise SanityError('num_cpus_per_task is not defined for this test. Cannot validate sanity')

        def tid(match):
            return int(match.group(1))

        def num_threads(match):
            return int(match.group(2))

        def rank(match):
            return int(match.group(3))

        def num_ranks(match):
            return int(match.group(4))

        return sn.all(sn.chain(
                [sn.assert_eq(sn.count(result), num_tasks*num_cpus_per_task)],
                sn.map(lambda x: sn.assert_lt(tid(x), num_threads(x)), result),
                sn.map(lambda x: sn.assert_lt(rank(x), num_ranks(x)), result),
                sn.map(
                    lambda x: sn.assert_lt(tid(x), num_cpus_per_task), result
                ),
                sn.map(
                    lambda x: sn.assert_eq(num_threads(x), num_cpus_per_task),
                    result
                ),
                sn.map(lambda x: sn.assert_lt(rank(x), num_tasks), result),
                sn.map(
                    lambda x: sn.assert_eq(num_ranks(x), num_tasks), result
                ),
            )
        )

    @performance_function('s')
    def compilation_time(self):
        return sn.extractsingle(r'Compilations time \(ns\): (\d+)',
                                self.build_stdout, 1, float) * 1.0e-9
