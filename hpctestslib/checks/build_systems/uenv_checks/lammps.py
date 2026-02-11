# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import datetime
import os
import sys

import reframe as rfm
import reframe.core.runtime as rt
import reframe.utility.sanity as sn
import reframe.utility.udeps as udeps
import reframe.utility as util


# Add the root directory of hpctestslib
prefix = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import checks.build_systems.uenv_checks.definitions as uenv
import checks.build_systems.uenv_checks.benchmarks as uenv_benchmarks
import mixins.sciapp.lammps.mixin as lammps
import util as hpcutil


@rfm.simple_test
class lammps_uenv_check(rfm.RunOnlyRegressionTest,
                        lammps.lammps_mixin,
                        uenv_benchmarks.uenv_mixin):
    '''
    Title: LAMMPS uenv benchmarks
    Description: This check performs a strong experiment up to 16 nodes
    that checks the uenv-compiled version of LAMMPS.

    Notes:
    * This check triggers two distinct classes of tests, each handling the
    existence of the uenv differently. The first class consists of tests that
    rely on a pre-existing uenv; if the required uenv has not been built yet,
    these tests are automatically skipped to prevent failures due to missing
    dependencies. The second class, on the other hand, is designed to build the
    uenv before executing the test. However, if the uenv already exists, these
    tests are skipped to avoid redundant builds. As a result, due to the
    mutually exclusive nature of these test conditions, one of these classes
    will always be skipped during execution, ensuring that tests are run only
    in the appropriate context.

    * Additionally, This check initiates four distinct uenv tests, categorized
    based on the method used to interact with the uenv. Two of these tests focus
    on the SPANK plugin version of uenv, with the key difference being whether
    the uenv view is enabled or not. One test runs with the uenv view enabled,
    while the other runs without it. Similarly, the remaining two tests are
    based on executing the uenv run command, again differing only in whether
    the uenv view is enabled. By covering both the SPANK plugin and the run
    command with and without the uenv view, these tests ensure comprehensive
    validation of uenv behavior across different configurations.

    * The valid programming environment is the builtin one.

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    uenv = parameter(list(filter(lambda x: x['name'].startswith('lammps'), uenv.UENV_SOFTWARE)), fmt=lambda x: x['name'])

    num_nodes = parameter(reversed([1, 2, 4, 6, 8]))
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower()}_{x["num_cores"]}')
    use_multithreading = False
    valid_prog_environs = ['builtin']
    maintainers = ['@victorusu']

    @run_after('init')
    def set_tags(self):
        self.tags |= {'uenv'}

    @run_after('init')
    def setup_job_parameters(self):
        req_feats = ['uenv']
        pwcreq = [self.partition_cpus['fullname']]
        pwfreq = hpcutil.get_partitions_with_feature_set(set(req_feats))
        partitions = [p for p in pwfreq if p in pwcreq]

        self.valid_systems = partitions
        self.num_tasks_per_node = self.partition_cpus['num_cores']
        self.num_cpus_per_task = self.partition_cpus['max_num_cores'] // self.num_tasks_per_node
        self.num_tasks = self.num_nodes * self.num_tasks_per_node
