# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


# import datetime
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
import mixins.sciapp.lammps.mixin as lammps


@rfm.simple_test
class lammps_strong_scaling_check(rfm.RunOnlyRegressionTest,
                                  lammps.lammps_mixin):
    '''
    Title: LAMMPS strong scaling benchmarks
    Description: This is an example strong scaling test up to 16 nodes.

    Notes:
    * The test assumes that the LAMMPS binary is available in the environment.

    * The valid programming environment is the builtin one.

    * Since the mixin supports Kokkos, it assumes that the LAMMPS module provide
    a Kokkos accelerated version of the code

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    maintainers = ['@victorusu']
    use_multithreading = False

    num_nodes = parameter(reversed([1, 2, 4, 6, 8, 12, 16]))
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower()}_{x["num_cores"]}')
    loadbalancing = parameter(['yes', 'no'])
    use_multithreading = False
    valid_prog_environs = ['builtin']

    @run_after('init')
    def setup_job_parameters(self):
        self.valid_systems = [self.partition_cpus['fullname']]
        self.num_cpus_per_task = self.partition_cpus['num_cores']
        self.num_tasks_per_node = self.partition_cpus['max_num_cores'] // self.num_cpus_per_task
        self.num_tasks = self.num_nodes * self.num_tasks_per_node


@rfm.simple_test
class lammps_modules_strong_scaling_check(lammps_strong_scaling_check):
    '''
    Title: LAMMPS strong scaling benchmarks
    Description: This is an example strong scaling test up to 16 nodes.

    Notes:
    * The test assumes that the LAMMPS can be loaded by the environment module
    named LAMMPS that is available on the system.

    * The valid programming environment is the builtin one.

    * Since the mixin supports Kokkos, it assumes that the LAMMPS module provide
    a Kokkos accelerated version of the code

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    modules = ['LAMMPS']

    @run_after('init')
    def set_tags(self):
        self.tags |= {'modules'}
