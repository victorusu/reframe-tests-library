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
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import util as hpcutil
import mixins.sciapp.nwchem.mixin as nwchem


@rfm.simple_test
class nwchem_strong_scaling_check(rfm.RunOnlyRegressionTest,
                                  nwchem.nwchem_mixin):
    '''
    Title: NHChem strong scaling benchmarks
    Description: This is an example strong scaling test up to 16 nodes.

    Notes:
    * The test assumes that the NWChem can be loaded by the environment module
    named NWChem that is available on the system.

    * The valid programming environment is the builtin one.

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    maintainers = ['@victorusu']
    use_multithreading = False

    num_nodes = parameter(reversed([1, 2, 4, 6, 8]))
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower() if x and "name" in x else ""}{"_" + x["num_cores"] if x and "num_cores" in x else ""}')
    use_multithreading = False
    valid_prog_environs = ['builtin']

    @run_after('init')
    def setup_job_parameters(self):
        self.valid_systems = [self.partition_cpus['fullname']]
        self.num_cpus_per_task = self.partition_cpus['num_cores']
        self.num_tasks_per_node = self.partition_cpus['max_num_cores'] // self.num_cpus_per_task
        self.num_tasks = self.num_nodes * self.num_tasks_per_node


@rfm.simple_test
class nwchem_modules_strong_scaling_check(nwchem_strong_scaling_check):
    '''
    Title: NHChem strong scaling benchmarks
    Description: This is an example strong scaling test up to 16 nodes.

    Notes:
    * The test assumes that the NWChem can be loaded by the environment module
    named NWChem that is available on the system.

    * The valid programming environment is the builtin one.

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    modules = ['NHChem']

    @run_after('init')
    def set_tags(self):
        self.tags |= {'modules'}
