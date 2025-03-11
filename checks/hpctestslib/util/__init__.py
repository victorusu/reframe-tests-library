# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import reframe as rfm
import reframe.core.runtime as rt

from reframe.core.schedulers.slurm import SlurmJobScheduler, SqueueJobScheduler
from reframe.utility.osext import cray_cdt_version


ECHOCMD = '/bin/echo'
CPCMD = '/bin/cp'
CURLCMD = '/usr/bin/curl'
TARCMD = '/bin/tar'
SEDCMD = '/bin/sed'
ULIMITCMD = '/bin/ulimit'


def get_first_local_partition():
    for p in rt.runtime().system.partitions:
        if p.scheduler.is_local:
            return p.fullname


def get_max_cpus_per_part(avoid_local=True):
    for p in rt.runtime().system.partitions:
        if p.scheduler.is_local and avoid_local:
            continue

        yield ({
            'name' : p.name,
            'fullname' : p.fullname,
            'max_num_cores' : p.processor.num_cores,
            'num_cores' : p.processor.num_cores,
            'num_sockets' : p.processor.num_sockets,
        })


def get_cpus_per_part(avoid_local=True):
    for p in rt.runtime().system.partitions:
        if p.scheduler.is_local and avoid_local:
            continue

        nthr = 1
        while nthr < p.processor.num_cores:
            yield ({
                'name' : p.name,
                'fullname' : p.fullname,
                'max_num_cores' : p.processor.num_cores,
                'num_cores' : nthr,
                'num_sockets' : p.processor.num_sockets,
            })
            nthr <<= 1

        yield ({
            'name' : p.name,
            'fullname' : p.fullname,
            'max_num_cores' : p.processor.num_cores,
            'num_cores' : nthr,
            'num_sockets' : p.processor.num_sockets,
        })


def get_partitions_with_feature_set(feature_set=set(), avoid_local=True):
    for p in rt.runtime().system.partitions:
        if p.scheduler.is_local and avoid_local:
            continue

        sfeat = set(p.features)
        if feature_set.difference(sfeat):
            continue

        yield(p.fullname)


def is_cray():
    return cray_cdt_version()


class SkipIfNotLocal(rfm.RegressionMixin):
    @run_before('run')
    def skip_if_not_local(self):
        self.skip_if(not self.is_local,
                     msg="Skipping the test because it is not local")


class SkipIfNotSlurm(rfm.RegressionMixin):
    @run_after('setup')
    def skip_if_not_slurm(self):
        sched = self.current_partition.scheduler
        is_slurm = (isinstance(sched, SlurmJobScheduler) or
                    isinstance(sched, SqueueJobScheduler))
        if not is_slurm:
            self.skip('The scheduler is not Slurm')


class GetDepMixin(rfm.RegressionMixin):
    def mygetdep(self, target, environ=None):
        '''
        Creating our own getdep because it is very difficult to depend on the
        original one when there are two different partitions
        '''
        if environ is None:
            environ = self.current_environ.name

        for d in self._case().deps:
            mask = int(d.check.unique_name == target)
            mask |= (int(d.environ.name == environ) | int(environ == '*')) << 1
            if mask == 3:
                return d.check