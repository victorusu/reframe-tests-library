# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import glob
import grp
import pwd
import os
import stat

import reframe as rfm
import reframe.core.runtime as rt
import reframe.utility.osext as osext

from collections.abc import MutableMapping
from contextlib import AbstractContextManager

from reframe.core.schedulers.slurm import SlurmJobScheduler, SqueueJobScheduler
from reframe.utility.osext import cray_cdt_version

from reframe.core.exceptions import ReframeError


class WrongUserError(ReframeError):
    '''Raised when the test expects an user that is not the one running reframe .'''

AIDECMD='/usr/sbin/aide'
AUTHSELECTCMD='/usr/bin/authselect'
AWKCMD='/usr/bin/awk'
BLKIDCMD='/usr/sbin/blkid'
CATCMD='/usr/bin/cat'
CHAGECMD='/usr/bin/chage'
CHGRPCMD='/usr/bin/chgrp'
CHMODCMD='/usr/bin/chmod'
CHOWNCMD='/usr/bin/chown'
CPCMD = '/bin/cp'
CURLCMD = '/usr/bin/curl'
DNFCMD='/usr/bin/dnf'
ECHOCMD = '/bin/echo'
FINDCMD='/usr/bin/find'
FINDMNTCMD='/usr/bin/findmnt'
FIPSCHECKCMD='/usr/bin/fipscheck'
FIPSMODESETUPCMD='/usr/bin/fips-mode-setup'
FIREWALLDCMD='/usr/bin/firewall-cmd'
GETCONFCMD='/usr/bin/getconf'
GETENTCMD='/usr/bin/getent'
GPGCMD='/usr/bin/gpg'
GREPCMD='/usr/bin/grep'
GRUBBYCMD='/sbin/grubby'
IPCMD='/usr/sbin/ip'
LSCMD='/usr/bin/ls'
LSMODCMD='/sbin/lsmod'
MOUNTCMD='/usr/bin/mount'
NEWALIASESCMD='/usr/bin/newaliases'
NMCLICMD='/usr/bin/nmcli'
PSCMD='/bin/ps'
RMCMD='/usr/bin/rm'
RPMCMD='/usr/bin/rpm'
SEDCMD = '/bin/sed'
SEMANAGECMD='/usr/sbin/semanage'
SSHDCMD='/usr/sbin/sshd'
SSHKEYGENCMD='/usr/bin/ssh-keygen'
SYSCTLCMD='/usr/sbin/sysctl'
SYSTEMCTLCMD='/usr/bin/systemctl'
TARCMD = '/bin/tar'
ULIMITCMD = '/bin/ulimit'
UNAMECMD='/bin/uname'
UPDATECRYPTOPOLICIESCMD='/usr/bin/update-crypto-policies'


def get_first_local_partition():
    for p in rt.runtime().system.partitions:
        if p.scheduler.is_local:
            return p.fullname
    return ''


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
    yield {}


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
    yield {}


def get_partitions_with_feature_set(feature_set=set(), avoid_local=True):
    for p in rt.runtime().system.partitions:
        if p.scheduler.is_local and avoid_local:
            continue

        sfeat = set(p.features)
        if feature_set.difference(sfeat):
            continue

        yield(p.fullname)
    yield {}


def is_cray():
    return cray_cdt_version()


# taken from https://www.freecodecamp.org/news/how-to-flatten-a-dictionary-in-python-in-4-different-ways/
def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str ='\t') -> MutableMapping:
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_all_files_in_paths(paths, extensions=None, recursive=False):
    def _get_file(file, extensions):
        if extensions:
            ext = pathlib.Path(file).suffix
            if isinstance(extensions, list):
                if ext in extensions:
                    return file
            else:
                if ext == extensions:
                    return file
        else:
            return file

        return None
    files = []
    for path in paths:
        if os.path.isfile(path):
            p = _get_file(path, extensions)
            if p:
                files.append(p)
        else:
            for (dirpath, _, filenames) in os.walk(path):
                for f in filenames:
                    p = _get_file(os.path.join(dirpath, f), extensions)
                    if p:
                        files.append(p)
                if not recursive:
                    break

    return files


class SkipIfNotLocal(rfm.RegressionTestPlugin):
    @run_before('run')
    def skip_if_not_local(self):
        self.skip_if(not self.is_local,
                     msg="Skipping the test because it is not local")


# class SkipIfNotRoot(rfm.RegressionTestPlugin):
#     @run_after('init')
#     def skip_if_not_root(self):
#         self.skip_if(os.getuid() != 0,
#                      msg='Skipping test because it has not been executed as root')


# class SkipIfRoot(rfm.RegressionTestPlugin):
#     @run_after('init')
#     def skip_if_root(self):
#         self.skip_if(os.getuid() == 0,
#                      msg='Skipping test because it has been executed as root')


class SkipIfNotRoot(rfm.RegressionTestPlugin):
    @run_after('init')
    def skip_if_not_root(self):
        if os.getuid() != 0:
            raise WrongUserError('ReFrame has not been executed as root')


class SkipIfCmdNotFound(rfm.RegressionTestPlugin):
    @run_after('init')
    def skip_if_cmd_not_found(self):
        try:
            cmd_status = osext.run_command(f'{self.executable}')
        except FileNotFoundError:
            self.skip(f'{self.executable} command not found')


class SkipIfNotSlurm(rfm.RegressionTestPlugin):
    @run_after('setup')
    def skip_if_not_slurm(self):
        sched = self.current_partition.scheduler
        is_slurm = (isinstance(sched, SlurmJobScheduler) or
                    isinstance(sched, SqueueJobScheduler))
        if not is_slurm:
            self.skip('The scheduler is not Slurm')


class GetDepMixin(rfm.RegressionTestPlugin):
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


class info_protection(AbstractContextManager):
    '''
    Check if there are any information stored in the disk that should not
    '''

    def __init__(self, rfmclss):
        self.rfmclss = rfmclss

    def __enter__(self):
        # return self.rfmclss
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            with osext.change_dir(sn.evaluate(self.rfmclss.stagedir)):
                open(sn.evaluate(self.rfmclss.stdout), 'w').close()
                open(sn.evaluate(self.rfmclss.stderr), 'w').close()
                for f in self.rfmclss.keep_files:
                    open(f, 'w').close()

        return False