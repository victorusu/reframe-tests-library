# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import os
import sys

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility.udeps as udeps
import reframe.utility as util


# Add the root directory of hpctestslib
prefix = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import mixins.system.fio.mixin as mixin
import util as hpcutil


@rfm.simple_test
class fio_compile_test(rfm.RegressionTest):
    '''
    Check title: Check if we can compile fio
    Check description: Make sure that we can compile fio
    Check rationale: We need to be able to compile different codes at all moments
    '''
    descr = ('Make sure that we can compile fio.')
    executable = './fio'
    executable_opts = ['--version']
    valid_systems = [hpcutil.get_first_local_partition()]
    valid_prog_environs = ['builtin']
    build_system = 'Autotools'

    @run_after('setup')
    def set_num_procs(self):
        proc = self.current_partition.processor
        if proc:
            self.num_cpus_per_task = max(proc.num_cores, 8)
        else:
            self.num_cpus_per_task = 1

    @run_before('compile')
    def set_download_fio_cmds(self):
        self.prebuild_cmds = [
            '_rfm_download_time="$(date +%s%N)"',
            r"/usr/bin/curl -s https://api.github.com/repos/axboe/fio/releases/latest | /bin/grep tarball_url | /bin/awk -F'\"' '{print $4}' | /usr/bin/xargs -I{} /usr/bin/curl -LJ {} -o fio.tar.gz",
            '_rfm_download_time="$(($(date +%s%N)-_rfm_download_time))"',
            'echo "Download time (ns): $_rfm_download_time"',
            '_rfm_extract_time="$(date +%s%N)"',
            fr'/bin/tar xf fio.tar.gz --strip-components=1 -C {self.stagedir}',
            '_rfm_extract_time="$(($(date +%s%N)-_rfm_extract_time))"',
            'echo "Extraction time (ns): $_rfm_extract_time"',
        ]

    @run_before('compile')
    def set_build_opts(self):
        self.build_system.flags_from_environ = False
        self.prebuild_cmds += ['_rfm_build_time="$(date +%s%N)"']
        self.postbuild_cmds += [
            '_rfm_build_time="$(($(date +%s%N)-_rfm_build_time))"',
            'echo "Compilation time (ns): $_rfm_build_time"',
        ]

    @performance_function('s')
    def compilation_time(self):
        return sn.extractsingle(r'Compilation time \(ns\): (\d+)',
                                self.build_stdout, 1, float) * 1.0e-9

    @performance_function('s')
    def download_time(self):
        return sn.extractsingle(r'Download time \(ns\): (\d+)',
                                self.build_stdout, 1, float) * 1.0e-9

    @performance_function('s')
    def extraction_time(self):
        return sn.extractsingle(r'Extraction time \(ns\): (\d+)',
                                self.build_stdout, 1, float) * 1.0e-9

    @sanity_function
    def assert_sanity(self):
        return sn.assert_found(r'fio-\S+', self.stdout)


class fio_base_test(rfm.RunOnlyRegressionTest,
                    hpcutil.GetDepMixin):
    valid_prog_environs = ['builtin']
    num_nodes = parameter(reversed([1, 2, 4, 6]))
    # num_nodes = parameter(reversed([1, 2, 4, 6, 8]))
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower()}_{x["num_cores"]}')
    # partition_cpus = parameter(hpcutil.get_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower()}_{x["num_cores"]}')

    @run_after('init')
    def set_parent(self):
        self.depends_on('fio_compile_test', how=udeps.by_env)

    @run_after('init')
    def setup_job_parameters(self):
        self.valid_systems = [self.partition_cpus['fullname']]
        self.num_cpus_per_task = self.partition_cpus['num_cores']
        self.num_tasks_per_node = self.partition_cpus['max_num_cores'] // self.num_cpus_per_task
        self.num_tasks = self.num_nodes * self.num_tasks_per_node

    @run_before('run')
    def set_executable_path(self):
        parent = self.mygetdep('fio_compile_test')
        self.executable = os.path.join(parent.stagedir, parent.executable)


@rfm.simple_test
class fio_no_latency_hiding_check(fio_base_test, mixin.fio_no_latency_hiding_regime_mixin):
    pass


@rfm.simple_test
class fio_balanced_regime_check(fio_base_test, mixin.fio_balanced_regime_mixin):
    pass


@rfm.simple_test
class fio_saturation_regime_check(fio_base_test, mixin.fio_saturation_regime_mixin):
    pass
