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


import checks.build_systems.uenv_checks.definitions as uenv
import checks.build_systems.uenv_checks.benchmarks as uenv_benchmarks
import mixins.system.stress_ng.mixin as stress_ng
import util as hpcutil


@rfm.simple_test
class stress_ng_uenv_check(rfm.RunOnlyRegressionTest,
                           stress_ng.stress_ng_mixin,
                           uenv_benchmarks.uenv_mixin):
    '''
    Title: STRESS-NG benchmarks
    Description: This is an example STRESS-NG tests

    Notes:
    * The test assumes that the STRESS-NG binary is available in the environment.

    * The valid programming environment is the builtin one.

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    uenv = parameter(list(filter(lambda x: x['name'].startswith('stress-ng'), uenv.UENV_SOFTWARE)), fmt=lambda x: x['name'])

    maintainers = ['@victorusu']
    use_multithreading = False
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower() if x and "name" in x else ""}{"_" + x["num_cores"] if x and "num_cores" in x else ""}')
    valid_prog_environs = ['builtin']

    @run_after('init')
    def setup_job_parameters(self):
        self.skip_if_no_procinfo()
        self.valid_systems = [self.partition_cpus['fullname']]
        self.num_cpus_per_task = self.partition_cpus['max_num_cores']
        self.num_tasks = 1
