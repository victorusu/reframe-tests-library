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
import reframe.utility as util


def normalize_units(value: float, unit: str, table: dict) -> float:
    if unit not in table:
        raise ValueError(f"Unsupported unit: {unit}")
    return value * table[unit]

BW_MULTIPLIERS = {
    'KiB/s': 1024,
    'MiB/s': 1024**2,
    'GiB/s': 1024**3,
    'TiB/s': 1024**4,
    'PiB/s': 1024**5,
}

IO_MULTIPLIERS = {
    'KiB': 1024,
    'MiB': 1024**2,
    'GiB': 1024**3,
    'TiB': 1024**4,
    'PiB': 1024**5,
}

TIME_MULTIPLIERS = {
    'msec': 1,
    'sec': 1000,
    's': 1000,
}

class fio_mixin(rfm.RegressionMixin):
    '''
    Title: FIO benchmarks mixin
    Description: This mixin provides functionality to write FIO benchmarks.

    Notes:
    * This is not an MPI code, thus this mixin aggregates or gets the maximum
    value of some performance indicators. Note the FIO provides other performance
    metrics, but we are considering only those that can be easily aggregated, e.g.
    bandwidth, io size, and (max)runtime.
    We have on propose ignored latency because a proper analysis requires proper
    statistics to be meaningful.

    * The mixin was based on the https://github.com/axboe/fio.

    * The computer does not requires network access to run these tests

    * The mixin supports sequential and random read and write. I have on propose
    ignore random read & write. This is because we tend to not use it as metric
    for system performance.

    * Since this is a mixin, there is no definition of job parameters.
    These are expected to be set in the test that uses this mixin.
    Please note that this mixin expects the test to define a instance variable
    named num_nodes. This is used for sanity and performance checking
    '''

    benchmark =  parameter(['read', 'write', 'randread', 'randwrite'])
    block_size = parameter(['4k', '8k', '16k', '32k', '64k', '128k', '256k', '512k', '1M', '2M', '4M'])
    num_jobs = parameter([1, 2, 4])
    runtime = variable(int, value=60)
    engine = variable(str, value='io_uring')

    @run_after('init')
    def set_executable(self):
        self.executable = 'fio'

    @run_after('init')
    def set_tags(self):
        self.tags |= {'system', 'stress', 'perf', 'io', 'fio'}

    @run_after('init')
    def set_descr(self):
        self.descr = f'Flexible I/O Tester {self.benchmark} benchmark'

    # Setting file_size to be depend on the other parameters
    # iodepth could be defined as a variable e.g.
    # file_size = parameter(['1G', '2G', '4G', '8G'])
    @run_after('init')
    def set_filesize(self):
        # Using formula: file_size ≥ 1000 × block_size × num_jobs
        # Produces approximately the following table if
        # num_jobs = parameter([1, 2, 4])
        #
        # bs=4k → 4G
        # bs=1M → 1–4G
        # bs=32M → 32–128G

        # This is an approximation
        bs = self.block_size.replace('k', '000').replace('M', '000000')
        self.file_size = 1000 * int(bs) * self.num_jobs

    @run_before('run')
    def set_fio_options(self):
        if self.benchmark.startswith('rand'):
            self.test_name = self.benchmark
        else:
            self.test_name = 'seq' + self.benchmark

        self.executable_opts += [
            f'--name={self.test_name}',
            f'--rw={self.benchmark}',
            f'--bs={self.block_size}',
            f'--numjobs={self.num_jobs}',
            f'--iodepth={self.iodepth}',
            f'--size={self.file_size}',
            f'--runtime={self.runtime}',
            f'--ioengine={self.engine}',
            '--group_reporting',
            '--direct=1',
            '--time_based=1'
        ]

    def aggregate_bw(self, bw_list, output_unit='MiB/s'):
        total_bytes_per_sec = sum([
            normalize_units(float(value.group('bw')), value.group('unit'),
                            BW_MULTIPLIERS) for value in bw_list
        ])
        factor = BW_MULTIPLIERS[output_unit]
        return total_bytes_per_sec / factor, output_unit

    def aggregate_io(self, io_list, output_unit='MiB'):
        total_bytes = sum(
            normalize_units(float(value.group('io')), value.group('unit'),
                            IO_MULTIPLIERS) for value in io_list
        )
        factor = IO_MULTIPLIERS[output_unit]
        return total_bytes / factor, output_unit

    def get_max_time(self, time_list, output_unit='s'):
        runs_time = [
            normalize_units(float(value.group('time')), value.group('unit'),
                            TIME_MULTIPLIERS) for value in time_list
        ]

        max_run = max(runs_time)
        factor = TIME_MULTIPLIERS[output_unit]
        return max_run / factor, output_unit

    def _extract_read_group_bw(self):
        found_bws = sn.findall(r'READ:\s*bw=(?P<bw>[\d.]+)(?P<unit>[A-Za-z\/]+)',
                               self.stdout)
        bw_sum, _ = self.aggregate_bw(found_bws)
        return bw_sum

    def _extract_read_group_io(self):
        found_ios = sn.findall(r'READ:.*io=(?P<io>[\d.]+)(?P<unit>[A-Za-z\/]+)',
                               self.stdout)
        io_sum, _ = self.aggregate_io(found_ios)
        return io_sum

    def _extract_read_group_time(self):
        found_times = sn.findall(r'READ:.*run=[\d.]+-(?P<time>[\d.]+)(?P<unit>[A-Za-z\/]+)',
                                self.stdout)
        time_max, _ = self.get_max_time(found_times)
        return time_max

    def _extract_write_group_bw(self):
        found_bws = sn.findall(r'WRITE:\s*bw=(?P<bw>[\d.]+)(?P<unit>[A-Za-z\/]+)',
                               self.stdout)
        bw_sum, _ = self.aggregate_bw(found_bws)
        return bw_sum

    def _extract_write_group_io(self):
        found_ios = sn.findall(r'WRITE:.*io=(?P<io>[\d.]+)(?P<unit>[A-Za-z\/]+)',
                               self.stdout)
        io_sum, _ = self.aggregate_io(found_ios)
        return io_sum

    def _extract_write_group_time(self):
        found_times = sn.findall(r'WRITE:.*run=[\d.]+-(?P<time>[\d.]+)(?P<unit>[A-Za-z\/]+)',
                                self.stdout)
        time_max, _ = self.get_max_time(found_times)
        return time_max

    @run_before('performance')
    def set_perf_vars(self):
        make_perf_fn = sn.make_performance_function
        bw = 'aggregated_bw' if self.num_nodes > 1 else 'bw'
        io = 'aggregated_io' if self.num_nodes > 1 else 'io'
        rn = 'max_time' if self.num_nodes > 1 else 'time'
        if 'read' in self.benchmark:
            self.perf_variables[bw] = make_perf_fn(self._extract_read_group_bw, 'MiB/s')
            self.perf_variables[io] = make_perf_fn(self._extract_read_group_io, 'MiB')
            self.perf_variables[rn] = make_perf_fn(self._extract_read_group_time, 's')
        else:
            self.perf_variables[bw] = make_perf_fn(self._extract_write_group_bw, 'MiB/s')
            self.perf_variables[io] = make_perf_fn(self._extract_write_group_io, 'MiB')
            self.perf_variables[rn] = make_perf_fn(self._extract_write_group_time, 's')

    @deferrable
    def assert_all_reads(self):
        reads = sn.findall(r'READ:', self.stdout)
        return sn.assert_eq(sn.count(reads), self.num_nodes,
                            msg=f'Could not find all the READ lines in output')

    @deferrable
    def assert_all_writes(self):
        writes = sn.findall(r'WRITE:', self.stdout)
        return sn.assert_eq(sn.count(writes), self.num_nodes,
                            msg=f'Could not find all the WRITE lines in output')

    @sanity_function
    def assert_sanity(self):
        if 'read' in self.benchmark:
            assert_fn_name = 'assert_all_reads'
        else:
            assert_fn_name = 'assert_all_writes'

        assert_fn = getattr(self, assert_fn_name, None)

        sn.assert_true(
            assert_fn is not None,
            msg=(f'cannot extract all metrics from {self.benchmark!r}: '
                 f'please define a member function "{assert_fn_name}()"')
        ).evaluate()

        return sn.chain(
                sn.assert_found(r'Starting \d+ process', self.stdout),
                sn.assert_found(r'Run status group 0 \(all jobs\)', self.stdout),
                assert_fn(),
            )


class fio_no_latency_hiding_regime_mixin(fio_mixin):
    '''
    Title: FIO no latency hiding benchmarks mixin
    Description: This mixin provides functionality to write FIO benchmarks without
    latency hiding.
    The question we are trying to answer is: "How quickly does the system respond?"
    This is mostly relevant for databases, control-plane IO, journaling.

    Notes:
    * To enforce the latency regime we do
        block_size <= 16k (small blocks)
        num_jobs = 1 (no concurrency)
        iodepth = 1 (single I/O operation in flight)
            This implies in Submit → wait → complete → next I/O
    * In this scenario, there is no latency hiding
    * For small block sizes (4k-32k) and larger iodepth one is effectively
    measuring queue saturation, not per-IO behavior
    * In this case, latency becomes dominated by device queueing,
    scheduler batching, and the results are hard to compare across devices
    * Technically, the benchmarks should be only randread.
    But we are doing write and sequential as well.
    '''
    block_size = parameter(['4k', '8k', '16k', '32k'])
    num_jobs = parameter([1])
    iodepth = parameter([1])

    @run_after('init')
    def set_descr(self):
        self.descr = f'Flexible I/O Tester {self.benchmark} no latency hiding benchmark'


class fio_balanced_regime_mixin(fio_mixin):
    '''
    Title: FIO latency benchmarks mixin
    Description: This mixin provides functionality to write FIO benchmarks with
    latency hiding.
    The question we are trying to answer is:
    "How does the system behave under realistic scientific workloads?"
    This is the most defensible choice for HPC benchmarks.

    Notes:
    * In this context we perform a medium-to-large I/O:
        block_size > 32k <= 1 M
        num_jobs >= 1 with and without concurrency
        iodepth > 1 (multiple I/O operation in flight)
    * In this scenario, there is latency hiding
    * These block sizes tend to be large enough to avoid metadata noise,
    but small enough to expose scheduling and queueing.
    (this statement is based on my limited experience)
    '''
    block_size = parameter(['64k', '128k', '256k', '512k', '1M'])
    num_jobs = parameter([1, 2])
    iodepth = parameter([8])

    @run_after('init')
    def set_descr(self):
        self.descr = f'Flexible I/O Tester {self.benchmark} balanced workloads benchmark'


class fio_saturation_regime_mixin(fio_mixin):
    '''
    Title: FIO latency benchmarks mixin
    Description: This mixin provides functionality to write FIO benchmarks with
    latency hiding and that can be throughput-bound (bandwidth ceiling).
    The question we are trying to answer is:
    "How fast can the system move data?"
    This is what vendors often quote.

    Notes:
    * In this context we perform a medium-to-large I/O:
        block_size >= 1 M
        num_jobs >> 1 with concurrency
        iodepth >> 1 (multiple I/O operation in flight)
    * In this scenario, results are strongly influenced by the kernel readahead,
    page cache depending on the file_size (that's why we compute the file size
    based on the iodepth and num_jobs), and the device max request size.
    (this statement is based on my limited experience)
    * This is rarely representative of real workloads
    '''

    block_size = parameter(['1M', '2M', '4M'])
    num_jobs = parameter([2, 4])
    iodepth = parameter([16, 32])
