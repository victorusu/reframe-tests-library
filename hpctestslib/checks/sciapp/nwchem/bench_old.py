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
import checks.sciapp.nwchem.mixin as nwchem
import checks.build_systems.uenv.benchmarks as uenv


@rfm.simple_test
class nwchem_modules_strong_scaling_check(rfm.RunOnlyRegressionTest,
                                           nwchem.nwchem_mixin):
    '''
    Title: NHChem strong scaling benchmarks
    Description: This is an example strong scaling test up to 16 nodes.

    Notes:
    * The test assumes that the NWChem can be loaded by the environment module
    named NWChem that is available on the system.

    * The valid programming environment is the builtin one.

    * Since the mixin supports CPU and GPU-accelerated non-bonded calculations,
    it assumes that the NWChem module provide a GPU accelerated version of
    the code

    * In order to enable the execution of the code in non-remote partitions,
    pass the parameter avoid_local=False to the hpcutil.get_max_cpus_per_part()
    function
    '''
    modules = ['NHChem']
    maintainers = ['@victorusu']
    use_multithreading = False

    num_nodes = parameter(reversed([1, 2, 4, 6, 8, 12, 16]))
    partition_cpus = parameter(hpcutil.get_max_cpus_per_part(), fmt=lambda x: f'{util.toalphanum(x["name"]).lower()}_{x["num_cores"]}')
    use_multithreading = False
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_tags(self):
        self.tags |= {'modules'}

    @run_after('init')
    def setup_job_parameters(self):
        self.valid_systems = [self.partition_cpus['fullname']]
        self.num_cpus_per_task = self.partition_cpus['num_cores']
        self.num_tasks_per_node = self.partition_cpus['max_num_cores'] // self.num_cpus_per_task
        self.num_tasks = self.num_nodes * self.num_tasks_per_node


# @rfm.simple_test
# class nwchem_spack_compilation_check(rfm.RegressionTest):
#     '''
#     Check title: TBD
#     Check description: TBD
#     Check rationale: TBD
#     '''
#     build_system = 'CustomBuild'
#     sourcesdir = 'https://github.com/spack/spack.git'
#     executable = 'nwchem'
#     build_time_limit = '6h'
#     nwchem = parameter(['nwchem armci=mpi3 +elpa +fftw3 +openmp +extratce'])
#     mpi_impl = parameter(['mpich', 'openmpi', 'cray-mpich', 'mvapich2', 'mvapich2x', 'intel-mpi', 'intel-oneapi-mpi'])
#     blas_impl = parameter(['openblas', 'intel-mkl', 'intel-oneapi-mkl'])
#     lapack_impl = parameter(['netlib-scalapack', 'intel-mkl', 'intel-oneapi-mkl'])

#     maintainers = ['@victorusu']

#     num_nodes = 1
#     valid_systems = [hpcutil.get_first_local_partition()]
#     valid_prog_environs = ['builtin']

#     @run_after('init')
#     def set_tags(self):
#         self.tags |= {'compile'}

#     @run_after('setup')
#     def set_env_vars(self):
#         spackbin = os.path.join(self.stagedir, 'bin')
#         self.env_vars = {
#             'PATH' : f'{spackbin}:$PATH'
#         }

#     @run_before('compile')
#     def prepare_build(self):
#         self.skip_if_no_procinfo()
#         proc = self.current_partition.processor
#         self.build_system.commands = [
#             'spack env create -d . --with-view software',
#             f'spack -e . add {self.nwchem}',
#             f'spack -e . add {self.mpi_impl}',
#             f'spack -e . add {self.blas_impl}',
#             f'spack -e . add {self.lapack_impl}',
#             'spack -e . concretize',
#             'spack -e . env depfile -o Makefile',
#             f'make -j{proc.num_cpus_per_socket}',
#         ]

#     @sanity_function
#     def assert_sanity(self):
#         return sn.all([
#             sn.assert_found(r'Unable to open nwchem.nw', self.stdout),
#             sn.assert_found(r'nwchem: failed to open the input file',
#                             self.stdout),
#             sn.assert_found(r'There is an error in the input file', self.stdout)
#         ])


# class nwchem_download(rfm.RunOnlyRegressionTest):
#     '''
#     Download NWChem source code.
#     '''

#     tarfile = variable(str, value='')

#     descr = 'Fetch NWChem source code'
#     executable = hpcutil.CURLCMD
#     tarfile = 'src.tar.bz2'
#     prerun_cmds = [
#         r"tarurl=$(curl -s https://api.github.com/repos/nwchemgit/nwchem/releases/latest | grep browser_download_url | grep '\-srconly'  | grep bz2 | grep -v md5 | awk '{print $2}' | tr -d \")"
#     ]
#     local = True
#     maintainers = ['@victorusu']

#     @run_after('init')
#     def set_executable_opts(self):
#         self.executable_opts = [
#             '-LJ',
#             '${tarurl}',
#             '-o',
#             self.tarfile
#         ]

#     @sanity_function
#     def validate_download(self):
#         return sn.assert_eq(self.job.exitcode, 0)


# # @rfm.simple_test
# class nwchem_compile_check(rfm.RegressionTest):
#     '''
#     Check title: TBD
#     Check description: TBD
#     Check rationale: TBD
#     '''
#     build_system = 'Make'
#     sourcepath = 'src'
#     nwchem_source = fixture(nwchem_download, scope='session')
#     executable = 'nwchem'
#     build_time_limit = '6h'
#     nwchem = parameter(['nwchem armci=mpi3 +elpa +fftw3 +openmp +extratce'])
#     mpi_impl = parameter(['mpich', 'openmpi', 'cray-mpich', 'mvapich2', 'mvapich2x', 'intel-mpi', 'intel-oneapi-mpi'])
#     blas_impl = parameter(['openblas', 'intel-mkl', 'intel-oneapi-mkl'])
#     lapack_impl = parameter(['netlib-scalapack', 'intel-mkl', 'intel-oneapi-mkl'])

#     maintainers = ['@victorusu']

#     num_nodes = 1
#     valid_systems = [hpcutil.get_first_local_partition()]
#     valid_prog_environs = ['*']

#     @run_after('init')
#     def set_tags(self):
#         self.tags |= {'compile'}

#     @run_after('setup')
#     def set_env_vars(self):
#         self.env_vars = {
#             'NWCHEM_TOP' : self.stagedir,
#             'NWCHEM_MODULES' : 'all',
#             'NWCHEM_LONG_PATHS' : 'Y',
#             'NWCHEM_TARGET' : 'LINUX64',
#             'MSG_COMMS' : 'MPI',
#             'armci_network' : 'MPI-MT',
#             'LARGE_FILES' : 'Y',
#             'USE_NOFSCHECK' : 'Y',
#             'CCSDTLR' : 'Y',
#             'CCSDTQ' : 'Y',
#             'MRCC_METHODS' : 'Y',
#             'EACCSD' : 'Y',
#             'IPCCSD' : 'Y',
#             'USE_NOIO' : 'Y',
#             'NWCHEM_BASIS_LIBRARY' : '/user-environment/env/nwchem/share/nwchem/libraries/',
#         }

#     @run_before('compile')
#     def prepare_build(self):
#         self.skip_if_no_procinfo()
#         proc = self.current_partition.processor
#         self.build_system.max_concurrency = proc.num_cpus_per_socket

#         tarfile = os.path.join(self.nwchem_source.stagedir,
#                                self.nwchem_source.tarfile)
#         self.prebuild_cmds = [
#             f'tar xf {tarfile} --strip-components=1 -C {self.stagedir}'
#         ]

#         # # TODO: Use Ninja generator
#         # self.build_system.config_opts = [
#         #     # Puts executables under exe/local_cuda/
#         #     '-DCP2K_ENABLE_REGTESTS=ON',
#         #     '-DCP2K_USE_LIBXC=ON',
#         #     '-DCP2K_USE_LIBINT2=ON',
#         #     '-DCP2K_USE_SPGLIB=ON',
#         #     '-DCP2K_USE_ELPA=ON',
#         #     '-DCP2K_USE_SPLA=ON',
#         #     '-DCP2K_USE_SIRIUS=ON',
#         #     '-DCP2K_USE_COSMA=ON',
#         #     '-DCP2K_USE_PLUMED=ON',
#         # ]

#         # if self.uarch == 'gh200':
#         #     self.build_system.config_opts += [
#         #         '-DCP2K_USE_ACCEL=CUDA',
#         #         '-DCP2K_WITH_GPU=H100',
#         #     ]

#     @sanity_function
#     def assert_sanity(self):
#         return sn.all[
#             sn.assert_found(r'Unable to open nwchem.nw', self.stdout),
#             sn.assert_found(r'nwchem: failed to open the input file',
#                             self.stdout),
#             sn.assert_found(r'There is an error in the input file', self.stdout)
#         ]