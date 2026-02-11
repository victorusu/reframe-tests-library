# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
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
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import util as hpcutil
import mixins.prgenv.mixin as helloworld


@rfm.simple_test
class hello_world_check(rfm.RegressionTest,
                        helloworld.helloworld_mixin):
    '''
    Title: Hello, World check
    Description: This is an example Hello, World check

    Notes:
    * * The test assumes that the C, C++ and Fortran compilers are available in the environment.

    * The valid programming environment is the builtin one.

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    maintainers = ['@victorusu']
    use_multithreading = False
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower() if x and "name" in x else ""}{"_" + x["num_cores"] if x and "num_cores" in x else ""}')
    valid_prog_environs = ['builtin']
    num_nodes = parameter([1])
    # repetitions = parameter(range(0, 1000))

    @run_after('init')
    def setup_job_parameters(self):
        self.num_cpus_per_task = 1
        self.num_tasks = 1
        self.num_tasks_per_node = 1

        if self.partition_cpus:
            self.valid_systems = [self.partition_cpus['fullname']]
            self.num_cpus_per_task = self.partition_cpus['num_cores']
            self.num_tasks_per_node = self.partition_cpus['max_num_cores'] // self.num_cpus_per_task
            self.num_tasks = self.num_nodes * self.num_tasks_per_node
