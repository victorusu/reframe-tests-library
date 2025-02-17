# Copyright 2016-2025 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# ReFrame Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import itertools
import os

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility.udeps as udeps

from reframe.core.schedulers.slurm import SlurmJobScheduler, SqueueJobScheduler


SLEEPCMD='/bin/sleep'
SACCTCMD = '/usr/bin/sacct'


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


ACCOUNTS = {
    'root' : 1,
    'a-cscs-css-8' : 0.57
}


@rfm.simple_test
class slurm_submit_job_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Sleep
    Check description: Sleep for a given amount of time.
    Check rationale: Tests if the workload manager accepts jobs, by submitting a job that sleeps for a few seconds.
    '''

    sleep_time_in_sec = parameter([2])
    project = parameter(list(ACCOUNTS.keys()))
    replica = parameter(range(0, 1))

    descr = ('Sleep for a given amount of time.')
    rationale = variable(str, value='Tests if the workload manager accepts jobs, by submitting a job that sleeps for a few seconds.')
    executable = SLEEPCMD
    # run only when slurm is the workload manager
    # valid_systems = [r'%scheduler=slurm']
    valid_systems = [r'*:normal']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_project_account(self):
        self.extra_resources = {
            'project': {
                'project': self.project
            }
        }

    @run_after('init')
    def set_executable_opts(self):
        self.executable_opts = [str(self.sleep_time_in_sec)]

    @sanity_function
    def assert_sanity(self):
        return sn.all([
            sn.assert_eq(os.stat(sn.evaluate(self.stdout)).st_size, 0,
                         msg=f'file {self.stdout} is not empty'),
            sn.assert_eq(os.stat(sn.evaluate(self.stderr)).st_size, 0,
                         msg=f'file {self.stderr} is not empty'),
            ])


@rfm.simple_test
class slurm_fairshare_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Slurm FairShare Check
    Check description: Check the fairshare values of all tests that it depends on. If the tests have different projects, then it compares the ratio between the projects. Otherwise, the fairshare value is compared against a threshold.
    Check rationale: Slurm fairshare configuration has to be validated in order to make sure that it is achieving the Business Goals.
    '''

    descr = ('Check the fairshare values of all tests that it depends on. If the tests have different projects, then it compares the ratio between the projects. Otherwise, the fairshare value is compared against a threshold.')
    rationale = variable(str, value='Slurm fairshare configuration has to be validated in order to make sure that it is achieving the Business Goals.')
    executable = SLEEPCMD
    executable_opts = ['10']

    sacct = SACCTCMD
    # run in the local scheduler
    # valid_systems = [r'%scheduler=local']
    valid_systems = [r'*:login']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parents(self):
        variants = slurm_submit_job_check.get_variant_nums()
        for v in variants:
            self.depends_on(slurm_submit_job_check.variant_name(v), how=udeps.by_env)

    def mygetdep(self, target, environ):
        '''
        Creating our own getdep because it is very difficult to depend on the
        original one when there are two different partitions
        '''
        for d in self._case().deps:
            mask = int(d.check.unique_name == target)
            mask |= (int(d.environ.name == environ) | int(environ == '*')) << 1
            if mask == 3:
                return d.check

    @run_before('run')
    def collect_parent_ids(self):
        variants = slurm_submit_job_check.get_variant_nums()
        self.jobids = []
        for v in variants:
            parent = self.mygetdep(slurm_submit_job_check.variant_name(v), environ=self.current_environ.name)
            jobid = parent.job.jobid
            self.jobids.append(jobid)
            self.prerun_cmds.append(f'{self.sacct} -j {jobid} -o '
                                    r'Account%100,JobID%20,Priority%20 -n -u$USER')

    @sanity_function
    def assert_sanity(self):
        values = sn.findall(r'(?P<account>\S+)\s+(?P<jobid>\d+)\s+(?P<priority>\d+)\s?$', self.stdout)
        sn.evaluate(sn.assert_true(values,
                                   msg='Unable to find the jobs information'))

        found_jobs = {}
        accounts = set()
        priorities = {}
        for v in values:
            account = v.group('account')
            jobid = v.group('jobid')
            prio = v.group('priority')
            found_jobs[jobid] = {
                'prio' : prio,
                'account' : account,
            }
            accounts.add(account)
            if account in priorities:
                n = priorities[account]['num'] + 1
                p = priorities[account]['prio'] + float(prio)
                a = p / n
                priorities[account] = {
                    'num' : p,
                    'prio' : n,
                    'ave' : a,
                }
            else:
                priorities[account] = {
                    'num' : 1,
                    'prio' : float(prio),
                    'ave' : float(prio),
                }

        jobids_set = set(self.jobids)
        found_jobs_set = set(found_jobs.keys())
        diff_jobid_set = jobids_set.difference(found_jobs_set)

        ref_accounts = set(ACCOUNTS.keys())
        diff_account_set = accounts.difference(ref_accounts)

        account_combinations = itertools.combinations(ACCOUNTS.keys(), 2)

        ratios = []
        for comb in account_combinations:
            acc_a, acc_b = comb
            if acc_a > acc_b:
                ref_ratio = ACCOUNTS[acc_a] / ACCOUNTS[acc_b]
                ratio = priorities[acc_a]['ave'] / priorities[acc_b]['ave']
            else:
                ref_ratio = ACCOUNTS[acc_b] / ACCOUNTS[acc_a]
                ratio = priorities[acc_b]['ave'] / priorities[acc_a]['ave']
            ratios.append(
                sn.assert_reference(ratio, ref_ratio, -0.2, 0.2,
                                    msg=f'{acc_a} and {acc_b} priorities ratio {ratio:.2f}'
                                        f'is not within the threshold of 20% from {ref_ratio:.2f}'))

        return sn.all([
            sn.assert_false(diff_jobid_set,
                                        msg='Unable to find information for '
                                        f'jobids: {diff_jobid_set}'),
            sn.assert_false(diff_account_set,
                         msg='Unable to find information for accounts '
                             f'{diff_account_set}'),
            ] + ratios)
