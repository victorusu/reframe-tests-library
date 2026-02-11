# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import os
import sys

import reframe as rfm
import reframe.core.runtime as rt
import reframe.utility.sanity as sn
import reframe.utility.udeps as udeps
import reframe.utility as util


# Add the root directory of hpctestslib
prefix = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir], *[os.pardir], *[os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import util as hpcutil
import mixins.sciapp.sphexa.mixin as sphexa


@rfm.simple_test
class sphexa_strong_scaling_check(rfm.RunOnlyRegressionTest,
                                sphexa.sphexa_mixin):
    '''
    Title: SPH-EXA strong scaling benchmarks
    Description: This is an example strong scaling test up to 16 nodes.

    Notes:
    * The test assumes that the sphexa executables location is already included
    in the $PATH. Thus, it does not add any full or relative path to the executable
    nor modify the environment to run the code.

    * The executables are expected to be named:
        - sphexa - CPU-only version of the code
        - sphexa-cuda - CUDA accelerated version of the code
        - sphexa-hip - HIP accelerated version of the code

    * The valid programming environment is the builtin one.

    * Any remote partion can execute the CPU version of the code

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function

    * The test assumes that the virtual partitions define the following features
    to run the GPU accelerated version of the code
        - cuda - CUDA accelerated version of the code
        - hip - HIP accelerated version of the code
    '''

    num_nodes = parameter(reversed([1, 2, 4, 6, 8]))
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower()}_{x["num_cores"]}')
    accel = parameter(['cpu', 'cuda', 'hip'])
    use_multithreading = False
    valid_prog_environs = ['builtin']
    num_steps = 50
    num_particles = 50

    @run_after('init', always_last=True)
    def update_executable(self):
        if 'cuda' == self.accel:
            self.executable = self.executable + '-cuda'
        elif 'hip' == self.accel:
            self.executable = self.executable + '-hip'

    @run_after('init')
    def setup_job_parameters(self):
        req_feats = []
        if 'cuda' == self.accel:
            req_feats = ['cuda']
        elif 'hip' == self.accel:
            req_feats = ['hip']
        pwcreq = [self.partition_cpus['fullname']]
        pwfreq = hpcutil.get_partitions_with_feature_set(set(req_feats))
        partitions = [p for p in pwfreq if p in pwcreq]

        self.valid_systems = partitions
        self.num_cpus_per_task = self.partition_cpus['num_cores']
        self.num_tasks_per_node = self.partition_cpus['max_num_cores'] // self.num_cpus_per_task
        self.num_tasks = self.num_nodes * self.num_tasks_per_node


@rfm.simple_test
class sphexa_weak_scaling_check(sphexa_strong_scaling_check):
    '''
    Title: SPH-EXA weak scaling benchmarks
    Description: This is an example weak scaling test up to 16 nodes.

    Notes:
    * The test assumes that the sphexa executables location is already included
    in the $PATH. Thus, it does not add any full or relative path to the executable
    nor modify the environment to run the code.

    * The executables are expected to be named:
        - sphexa - CPU-only version of the code
        - sphexa-cuda - CUDA accelerated version of the code
        - sphexa-hip - HIP accelerated version of the code

    * The valid programming environment is the builtin one.

    * Any remote partion can execute the CPU version of the code

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function

    * The test assumes that the virtual partitions define the following features
    to run the GPU accelerated version of the code
        - cuda - CUDA accelerated version of the code
        - hip - HIP accelerated version of the code
    '''

    @run_after('init')
    def set_num_particles(self):
        self.num_particles = self.num_particles * self.num_nodes
