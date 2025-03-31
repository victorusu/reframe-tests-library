# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


# import datetime
import os
import re
import sys

import reframe as rfm
import reframe.utility.sanity as sn


class stress_ng_mixin(rfm.RegressionMixin):
    '''
    Title: STRESS-NG benchmarks mixin
    Description: This mixin provides functionality to write STRESS-NG benchmarks.
    This mixin implements 256 different benchmarks.

    Notes:
    * This is not an MPI code, thus this mixin assumes the use of MPI with
    a single rank

    * The mixin was based on the https://github.com/ColinIanKing/stress-ng.git.

    * The computer does not requires network access to run these tests

    * The mixin supports several CPU, memory, networks, disk benchmarks

    * Since this is a mixin, there is no definition of job parameters.
    These are expected to be set in the test that uses this mixin.
    '''

    #: Parameter encoding the name of the benchmark to run
    #:
    #: :type: :class:`str`
    #: :values: ``[too long]``
    benchmark = parameter([
        'af-alg',
        'affinity',
        'alarm',
        'atomic',
        'bad-altstack',
        'besselmath',
        'bigheap',
        'bitonicsort',
        'bitops',
        'branch',
        'brk',
        'bsearch',
        'bubblesort',
        'cache',
        'cachehammer',
        'cacheline',
        'chattr',
        'chdir',
        'chmod',
        'chown',
        'clock',
        'clone',
        'close',
        'context',
        'copy-file',
        'cpu',
        'cpu-sched',
        'crypt',
        'daemon',
        'dekker',
        'dev-shm',
        'dir',
        'dirmany',
        'dnotify',
        'dynlib',
        'enosys',
        'epoll',
        'eventfd',
        'exec',
        'exit-group',
        'expmath',
        'fallocate',
        'far-branch',
        'fault',
        'fcntl',
        'fd-fork',
        'fd-race',
        'fiemap',
        'fifo',
        'file-ioctl',
        'filename',
        'flipflop',
        'flock',
        'flushcache',
        'fma',
        'fork',
        'forkheavy',
        'fp',
        'fp-error',
        'fractal',
        'fsize',
        'fstat',
        'full',
        'funccall',
        'funcret',
        'futex',
        'get',
        'getdent',
        'getrandom',
        'goto',
        'handle',
        'hash',
        'hdd',
        'hrtimers',
        'hsearch',
        'hyperbolic',
        'icache',
        'inode-flags',
        'inotify',
        'insertionsort',
        'intmath',
        'io-uring',
        'iomix',
        'ioprio',
        'itimer',
        'kcmp',
        'kill',
        'klog',
        'landlock',
        'lease',
        'link',
        'list',
        'loadavg',
        'locka',
        'lockbus',
        'lockf',
        'lockmix',
        'lockofd',
        'logmath',
        'longjmp',
        'lsearch',
        'madvise',
        'malloc',
        'matrix',
        'matrix-3d',
        'mcontend',
        'membarrier',
        'memcpy',
        'memfd',
        'memrate',
        'memthrash',
        'mergesort',
        'metamix',
        'min-nanosleep',
        'mincore',
        'mknod',
        'mlock',
        'mmap',
        'mmapaddr',
        'mmapfiles',
        'mmapfixed',
        'mmapfork',
        'mmaphuge',
        'mmapmany',
        'mmaptorture',
        'monte-carlo',
        'mprotect',
        'mq',
        'mremap',
        'msg',
        'msync',
        'msyncmany',
        'mtx',
        'munmap',
        'mutex',
        'nanosleep',
        'netdev',
        'nice',
        'nop',
        'null', # --fd-fork-file file     select file to dup [ null, random, stdin, stdout, zero ]
        'numa',
        'opcode',
        'open',
        'pagemove',
        'pageswap',
        'personality',
        'pidfd',
        'ping-sock',
        'pipe',
        'pipeherd',
        'pkey',
        'poll',
        'powmath',
        'prctl',
        'prefetch',
        'prio-inv',
        'priv-instr',
        'procfs',
        'pseek',
        'pthread',
        'ptr-chase',
        'ptrace',
        'pty',
        'qsort',
        'race-sched',
        'radixsort',
        'randlist',
        'readahead',
        'reboot',
        'regex',
        'regs',
        'remap',
        'rename',
        'resched',
        'resources',
        'revio',
        'ring-pipe',
        'rlimit',
        'rmap',
        'rotate',
        'rseq',
        'rtc',
        'schedmix',
        'schedpolicy',
        'seal',
        'secretmem',
        'seek',
        'sem',
        'sem-sysv',
        'sendfile',
        'session',
        'set',
        'shellsort',
        'shm',
        'shm-sysv',
        'skiplist',
        'sleep',
        'sock',
        'sockabuse',
        'sockdiag',
        'sockfd',
        'sockmany',
        'sockpair',
        'sparsematrix',
        'spawn',
        'spinmem',
        'splice',
        'stack',
        'stackmmap',
        'str',
        'stream',
        'switch',
        'symlink',
        'sync-file',
        'syncload',
        'sysbadaddr',
        'syscall',
        'sysfs',
        'sysinfo',
        'tee',
        'time-warp',
        'timer',
        'timerfd',
        'tlb-shootdown',
        'tmpfs',
        'touch',
        'tree',
        'trig',
        'tsearch',
        'udp-flood',
        'unlink',
        'unshare',
        'urandom',
        'utime',
        'vdso',
        'veccmp',
        'vecfp',
        'vecmath',
        'vecshuf',
        'vecwide',
        'vfork',
        'vforkmany',
        'vm',
        'vm-addr',
        'vm-rw',
        'vm-segv',
        'vm-splice',
        'vma',
        'vnni',
        'wait',
        'waitcpu',
        'workload',
        'xattr',
        'yield',
        'zero',
        'zombie',
    ])
    benchmark_time = 10

    @run_after('init')
    def set_executable(self):
        self.executable = 'stress-ng'

    @run_after('init')
    def set_tags(self):
        self.tags |= {'system', 'stress', 'perf'}

    @run_after('init')
    def set_descr(self):
        self.descr = f'STRESS-NG {self.benchmark} benchmark'

    @run_before('run')
    def set_benchmark_opts(self):
        self.skip_if_no_procinfo()
        procs = self.current_partition.processor.num_cores
        if self.benchmark == 'cacheline':
            # to fully exercise a 64 byte cache line, 32 instances are required'
            procs = max(procs, 32)

        self.executable_opts += ['-t', f'{self.benchmark_time}',
                                '--verify', '--metrics-brief',
                                f'--{self.benchmark}', f'{procs}',
                                ]

        if self.benchmark == 'syscall':
            self.executable_opts += [
                # setting to display the top 1'000 fastest syscalls
                # this makes sure that we will display everything that stress-ng
                # chooses to share with us
                '--syscall-top', '1000'
            ]
        elif self.benchmark == 'cache':
            self.executable_opts += [
                '--cache-enable-all'
            ]

    def _extract_bogos(self):
        return sn.extractsingle(fr'stress-ng:.*metrc.*{self.benchmark}\s+(?P<ops>\S+)\s+'
                                r'(?P<rtime>\S+)\s+(?P<utime>\S+)\s+'
                                r'(?P<stime>\S+)\s+(?P<ropss>\S+)\s+',
                                self.stdout, 'ropss', float)

    def _extract_exectime(self):
        return sn.extractsingle(r'stress-ng:.*successful\srun\scompleted\sin\s'
                                r'(?P<time>\S+)\ssec',
                                self.stdout, 'time', float, item=-1)

    def _extract_hashes(self, name):
        return sn.extractsingle(fr'stress-ng:.*hash:\s+{name}\s+'
                                 r'(?P<value>\S+)\s+(?P<chi>\S+)\n',
                                    self.stdout, 'value', float)

    def _extract_min_nanosleep(self, size):
        return sn.extractsingle(fr'stress-ng:.*\s+{size}\s+(?P<min>\S+)'
                                r'\s+(?P<max>\S+)\s+(?P<avg>\S+)\s+\n',
                                self.stdout, 'avg', float)

    def _extract_syscalls(self, name):
        return sn.extractsingle(fr'stress-ng:.*syscall:\s+{name}\s+'
                                    r'(?P<avg>\S+)\s+(?P<min>\S+)\s+'
                                    r'(?P<max>\S+)\n',
                                    self.stdout, 'avg', float)

    @run_before('performance')
    def set_perf_vars(self):
        make_perf_fn = sn.make_performance_function
        self.perf_variables['exec_time'] = make_perf_fn(self._extract_exectime, 's')
        self.perf_variables['real_ops_s'] = make_perf_fn(self._extract_bogos, 'bogo ops/s')
        if self.benchmark == 'syscall':
            # it seems too much to performance check all the syscalls? nah! let's measure all!
            stdout = os.path.join(self.stagedir, sn.evaluate(self.stdout))
            syscalls=sn.extractall(r'stress-ng:.*syscall:\s+(?P<name>\S+)\s+'
                                    r'(?P<avg>\S+)\s+(?P<min>\S+)\s+'
                                    r'(?P<max>\S+)\n',
                                    stdout, 'name')
            for name in syscalls:
                self.perf_variables[name] = make_perf_fn(self._extract_syscalls(name), 'ns')
        elif self.benchmark == 'hash':
            # it seems too much to performance check all the hashes? nah! let's measure all!
            stdout = os.path.join(self.stagedir, sn.evaluate(self.stdout))
            hashes=sn.extractall(r'stress-ng:.*hash:\s+(?P<name>\S+)\s+'
                                 r'(?P<value>\S+)\s+(?P<chi>\S+)\n',
                                    stdout, 'name')
            for name in hashes:
                self.perf_variables[name] = make_perf_fn(self._extract_hashes(name), 'hashes/sec')
        elif self.benchmark == 'min-nanosleep':
            # it seems too much to performance check all the hashes? nah! let's measure all!
            stdout = os.path.join(self.stagedir, sn.evaluate(self.stdout))
            sizes=sn.extractall(r'stress-ng:.*\s+(?P<size>\d+)\s+(?P<min>\d+)'
                                r'\s+(?P<max>\d+)\s+(?P<avg>\S+)\s+\n',
                                stdout, 'size')
            for size in sizes:
                self.perf_variables[size] = make_perf_fn(self._extract_min_nanosleep(size), 'ns')

    @sanity_function
    def assert_sanity(self):
        time = sn.extractsingle(r'stress-ng:.*successful\srun\scompleted\sin\s'
                                r'(?P<time>\S+)\ssec',
                                self.stdout, 'time', float, item=-1)

        passed = sn.extractsingle(r'stress-ng:.*passed:\s(?P<passed>\d+)',
                                  self.stdout, 'passed', int, item=-1)
        failed = sn.extractsingle(r'stress-ng:.*failed:\s(?P<failed>\d+)',
                                  self.stdout, 'failed', int, item=-1)
        untrusted = sn.extractsingle(r'stress-ng:.*metrics\suntrustworthy:\s'
                                     r'(?P<untrusted>\d+)',
                                     self.stdout, 'untrusted', int, item=-1)
        return sn.all([
            sn.assert_gt(passed, 0,
                         msg='There are not successful metrics'),
            sn.assert_eq(failed, 0,
                         msg=f'There are {failed} failed metrics'),
            sn.assert_eq(untrusted, 0,
                         msg=f'There are {untrusted} untrustworthy metrics'),
            sn.assert_not_found('Segmentation fault', self.stderr),
            sn.assert_found(r'stress-ng:.*successful\srun\scompleted\sin\s'
                            r'(?P<time>\S+)\ssec', self.stdout,
                            msg='The benchmarks did not finish properly'),
        ])
