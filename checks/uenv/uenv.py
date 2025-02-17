# Copyright 2016-2025 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# ReFrame Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import datetime
import os
import time

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility as util

from string import Template

from reframe.core.exceptions import DependencyError, SanityError

# # reframe.core.launcher.JobLauncher
# from reframe.core.launcher import JobLauncher

# from reframe.core.schedulers import getlauncher
from reframe.core.schedulers.slurm import SlurmJobScheduler, SqueueJobScheduler


from hpctestlib.sciapps.amber.nve import amber_nve_check
from hpctestlib.sciapps.gromacs.benchmarks import gromacs_check

ECHOCMD = '/bin/echo'
CPCMD = '/bin/cp'
SLEEPCMD='/bin/sleep'
SACCTCMD = '/usr/bin/sacct'
RMCMD = '/bin/rm'
GITCMD = '/usr/bin/git'


UENV2BUILD = []

SOFTWARE = [
    {
        'name' : 'gromacs@2024.3',
        'descr' : 'GROMACS',
        'spec' : '+openmp +mpi +hwloc +cycle_subcounters'
    },
    {
        'name' : 'nwchem@7.2.3',
        'descr' : 'NWChem',
        'spec' : 'armci=mpi3 +elpa +fftw3 +openmp'
    },
    {
        'name' : 'lammps@20240829.1',
        'descr' : 'LAMMPS',
        'spec' : '+asphere +body +class2 +colloid +compress +coreshell +dipole +ffmpeg +granular +jpeg +kim +kokkos +kspace +lib +manybody +mc +misc +molecule +mpi +openmp +openmp-package +opt +peri +png +poems +python +qeq +replica +rigid +shock +srd +tools +voronoi lammps_sizes=smallbig +ipo'
    },
]

DEFAULT_COMPILER = 'gcc@12.3'
DEFAULT_SPACK = 'v0.23.0'


def validate_software_fields(software):
    if 'name' not in software:
        raise ValueError(f'Found software without a name entry')

    if 'envname' not in software:
        sname = software['name'].split('@', maxsplit=2)
        envname = sname[0]
        software['envname'] = envname

    if 'bootstrap' not in software:
        software['bootstrap'] = DEFAULT_COMPILER
        major_version = DEFAULT_COMPILER.split('.')
        if len(major_version) > 1:
            software['bootstrap'] = ''.join(major_version[:-1])

    if 'gcc' not in software:
        software['gcc'] = DEFAULT_COMPILER

    if 'spack' not in software:
        software['spack'] = DEFAULT_SPACK

    if 'descr' not in software:
        software['descr'] = software['name']

    if 'spec' not in software:
        software['spec'] = ''


def read_recipe_file(recipes_file):
    with open(recipes_file, 'r') as f:
        return Template(f.read())


def dump_recipe_file(sw, template, filename):
    with open(filename, 'w') as f:
        f.write(template.safe_substitute(
            name=sw['name'],
            bootstrap=sw['bootstrap'],
            gcc=sw['gcc'],
            spack=sw['spack'],
            descr=sw['descr'],
            spec=sw['spec'],
            envname=sw['envname']
        ))


def create_uenv_recipes(software_list, output_path, recipes_dir = 'src/recipe'):
    ret = []
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    elif not os.path.isdir(output_path):
        raise ValueError(f'The provided path {output_path} is not a directory')

    if os.path.isabs(recipes_dir):
        recipes_files = os.listdir(recipes_dir)
    else:
        srcdir = os.path.join(os.path.dirname(__file__), recipes_dir)
        recipes_files = os.listdir(srcdir)

    if not recipes_files:
        raise ValueError(f'The provided recipes dir {recipes_dir} is empty')

    for sw in software_list:
        validate_software_fields(sw)
        recipe_folder = os.path.join(output_path, sw['name'])
        if not os.path.exists(recipe_folder):
            os.mkdir(recipe_folder)

        for re in recipes_files:
            template = read_recipe_file(os.path.join(recipes_dir, re))
            filename = os.path.join(recipe_folder, re)
            dump_recipe_file(sw, template, filename)
        ret.append(recipe_folder)

    return ret


UENV2BUILD = create_uenv_recipes(SOFTWARE, '/users/hvictor/myrecipes')


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


class UENV(rfm.RegressionMixin):

    def uenv2string(self, uenv_dict, uenv_version=None):
        swname = uenv_dict['swname']
        swver = uenv_dict['swver']
        system = uenv_dict['system']
        arch = uenv_dict['arch']
        if uenv_version:
            return f'{swname}/{swver}:{uenv_version}@{system}%{arch}'
        return f'{swname}/{swver}@{system}%{arch}'

    def get_uenv_from_uenv2build(self, uenv2build, uenv_version=None):
        uenv = os.path.basename(uenv2build)
        env_parts = uenv.split('@', maxsplit=2)
        swname = env_parts[0]
        swver = env_parts[1] if len(env_parts) > 0 else 'latest'

        proc = self.current_partition.processor
        if proc:
            arch = proc.arch
        else:
            arch = 'unknown'

        uenv_dict = {
            'swname' : swname,
            'swver' : swver,
            # 'version' : version,
            'system' : self.current_system.name,
            'arch' : arch
        }
        return self.uenv2string(uenv_dict=uenv_dict, uenv_version=uenv_version)


@rfm.simple_test
class spack_cmd_not_present_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Check that Spack is not enabled in the environment
    Check description: Make sure that Spack command is not enabled in the environment
    Check rationale: A standalone version of Spack can interfere with uenvs.
    '''

    descr = ('Make sure that Spack command is not enabled in the environment.')
    rationale = variable(str, value='A standalone version of Spack can interfere with uenvs.')
    executable = 'spack'
    executable_opts = ['--version']
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @sanity_function
    def assert_sanity(self):
        return sn.assert_found(r'spack: command not found', self.stderr)


@rfm.simple_test
class uenv_cmd_present(rfm.RunOnlyRegressionTest):
    '''
    Check title: Check that uenv is enabled in the environment
    Check description: Make sure that uenv is enabled in the environment
    Check rationale: There is no point in testing uenvs if it is not enabled in the environment.
    '''

    descr = ('Make sure that Spack command is not enabled in the environment.')
    rationale = variable(str, value='A standalone version of Spack can interfere with uenvs.')
    executable = 'uenv'
    executable_opts = ['--version']
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @sanity_function
    def assert_sanity(self):
        return sn.assert_found(r'\d+.\d+.\d+', self.stdout)


@rfm.simple_test
class uenv_image_present_check(rfm.RunOnlyRegressionTest, UENV):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    uenv2build = parameter(UENV2BUILD)
    executable = 'uenv'
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        self.depends_on('uenv_cmd_present')

    @run_before('run')
    def set_uenv_image(self):
        # do not add the time in the image removal command because we do not know what is it
        self.uenv = self.get_uenv_from_uenv2build(self.uenv2build)
        self.executable_opts = [
            'image', 'ls', self.uenv
        ]

    @sanity_function
    def assert_sanity(self):
        uenvs = sn.findall(r'(?P<name>\S+(:\S+)?)\s+(?P<arch>\S+)\s+(?P<system>\S+)', self.stdout)
        count = sn.count(uenvs)

        self.uenv_installed = False
        try:
            sn.evaluate(sn.assert_not_found(r'no matching uenv', self.stderr))
        except SanityError as e:
            return True

        if count > 1:
            self.uenv_installed = True

        return True


@rfm.simple_test
class stackinator_bootstrap_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Stackinator Boostrap
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    executable = 'stack-config'
    executable_opts = ['--version']
    sourcesdir = 'https://github.com/eth-cscs/stackinator'
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        self.depends_on('spack_cmd_not_present_check')
        self.depends_on('uenv_cmd_present')

    @run_before('run')
    def set_prerun_cmds(self):
        self.prerun_cmds = [os.path.join(sn.evaluate(self.stagedir), 'bootstrap.sh')]

    @run_before('run')
    def update_executable_path(self):
        self.executable = os.path.join(os.path.join(sn.evaluate(self.stagedir),
                                                    'bin'), self.executable)

    @sanity_function
    def assert_sanity(self):
        return sn.assert_found(r'stackinator version\s+\d+.\d+.\d+', self.stdout)


@rfm.simple_test
class cluster_configuration_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    sourcesdir = 'https://github.com/eth-cscs/alps-cluster-config'
    cluster_name =  variable(str, value='')
    executable = ECHOCMD
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @sanity_function
    def assert_sanity(self):
        cluster_name = self.cluster_name if self.cluster_name else self.current_system.name
        self.system_dir = os.path.join(sn.evaluate(self.stagedir), cluster_name)
        return sn.all([
            sn.assert_true(os.path.isdir(self.system_dir), msg=f'System {cluster_name} is not supported by Alps Cluster Config repo')
            ])


@rfm.simple_test
class uenv_build_cache_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: UENV build cache
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    cache_cfg = variable(str, value='~/.cache-config.yaml')
    executable = ECHOCMD
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        self.depends_on('spack_cmd_not_present_check')
        self.depends_on('uenv_cmd_present')

    @run_after('init')
    def normalize_path(self):
        self.cache_cfg = os.path.expandvars(os.path.expanduser(str(self.cache_cfg)))


    # TODO: improve this sanity check
    # It should check for the contents of the self.cache_cfg file
    @sanity_function
    def assert_sanity(self):
        return sn.all([
            sn.assert_not_found(r'does not exist', self.stdout),
            sn.assert_not_found(r'does not exist', self.stderr),
            sn.assert_true(os.path.exists(self.cache_cfg), msg=f'Cache file {self.cache_cfg} does not exist'),
            sn.assert_not_found(r'spack minimum version is .* - recipe uses .*', self.stdout),
            sn.assert_eq(os.stat(sn.evaluate(self.stderr)).st_size, 0,
                         msg=f'file {self.stderr} is not empty'),
            ])


@rfm.simple_test
class uenv_image_present_auxiliar_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    uenv2build = parameter(UENV2BUILD)
    executable = 'uenv'
    executable_opts = ['--version']
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        variants = uenv_image_present_check.get_variant_nums(uenv2build=self.uenv2build)
        if len(variants) != 1:
            raise DependencyError(f'build_uenv_check %{self.uenv2build} depends on more than one version of uenv_image_present_check')
        self.depends_on(uenv_image_present_check.variant_name(variants[0]))

    @sanity_function
    def assert_sanity(self):
        variants = uenv_image_present_check.get_variant_nums(uenv2build=self.uenv2build)
        parent = self.getdep(uenv_image_present_check.variant_name(variants[0]))

        self.skip_if(parent.uenv_installed, msg=f'uenv {parent.uenv} is already installed')
        return True


@rfm.simple_test
class bootstrap_uenv_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    sourcesdir = 'https://github.com/eth-cscs/alps-uenv'
    uenv2build = parameter(UENV2BUILD)
    time_limit = '2h'
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        variants = uenv_image_present_auxiliar_check.get_variant_nums(uenv2build=self.uenv2build)
        if len(variants) != 1:
            raise DependencyError(f'build_uenv_check %{self.uenv2build} depends on more than one version of uenv_image_present_auxiliar_check')
        self.depends_on(uenv_image_present_auxiliar_check.variant_name(variants[0]))
        self.depends_on('uenv_build_cache_check')
        self.depends_on('stackinator_bootstrap_check')
        self.depends_on('cluster_configuration_check')

    @run_after('init')
    def set_recipes_path(self):
        if not os.path.isabs(self.uenv2build):
            self.recipes = os.path.normpath(
                    os.path.join('recipes', self.uenv2build)
                )
        else:
            self.recipes = os.path.normpath(self.uenv2build)

    @run_before('run')
    def set_cmds(self):
        stackinator = self.getdep('stackinator_bootstrap_check')
        cluster_cfg = self.getdep('cluster_configuration_check')
        cache_cfg = self.getdep('uenv_build_cache_check')
        self.executable = stackinator.executable
        self.executable_opts = [
            '--build',
            f'{sn.evaluate(self.stagedir)}',
            '--recipe',
            self.recipes,
            '--system',
            cluster_cfg.system_dir,
            '--cache',
            cache_cfg.cache_cfg
        ]

    @sanity_function
    def assert_sanity(self):
        return sn.all([
            sn.assert_not_found(r'does not exist', self.stdout),
            sn.assert_not_found(r'does not exist', self.stderr),
            sn.assert_not_found(r'spack minimum version is .* - recipe uses .*', self.stdout),
            sn.assert_eq(os.stat(sn.evaluate(self.stderr)).st_size, 0,
                         msg=f'file {self.stderr} is not empty'),
            ])


@rfm.simple_test
class build_uenv_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    uenv2build = parameter(UENV2BUILD)
    time_limit = '2h'
    valid_systems = ['*']
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        variants = bootstrap_uenv_check.get_variant_nums(uenv2build=self.uenv2build)
        if len(variants) != 1:
            raise DependencyError(f'build_uenv_check %{self.uenv2build} depends on more than one version of bootstrap_uenv_check')
        self.depends_on(bootstrap_uenv_check.variant_name(variants[0]))

    @run_after('init')
    def set_recipes_path(self):
        if not os.path.isabs(self.uenv2build):
            self.recipes = os.path.normpath(
                    os.path.join('recipes', self.uenv2build)
                )
        else:
            self.recipes = os.path.normpath(self.uenv2build)

    @run_before('run')
    def set_check_invariants(self):
        variants = bootstrap_uenv_check.get_variant_nums(uenv2build=self.uenv2build)
        parent = self.getdep(bootstrap_uenv_check.variant_name(variants[0]))
        stagedir = sn.evaluate(parent.stagedir)
        output = os.path.join(stagedir,
                              sn.evaluate(parent.stdout))
        with open(output, 'r') as f:
            found = f.readlines()
        cmd = found[-1]
        cmds = cmd.split()
        if len(cmds) > 0:
            self.executable = cmds[0]
            self.executable_opts = cmds[1:]
        else:
            self.executable = ECHOCMD
        self.prerun_cmds = [
            f'cd {parent.stagedir}'
        ]

        self.sqfs_img = 'store.squashfs'
        self.sqfs_path = os.path.join(sn.evaluate(parent.stagedir), self.sqfs_img)
        self.postrun_cmds = [
            f'{CPCMD} {self.sqfs_path} {sn.evaluate(self.stagedir)}'
        ]
        self.sqfs_path = os.path.join(sn.evaluate(self.stagedir), self.sqfs_img)

        self.keep_files = [
            self.sqfs_img
        ]

    @sanity_function
    def assert_sanity(self):
        return sn.all([
            sn.assert_not_found(r'does not exist', self.stdout),
            sn.assert_not_found(r'does not exist', self.stderr),
            sn.assert_not_found(r'command not found', self.stderr),
            sn.assert_true(os.path.exists(self.sqfs_path), msg='The squashfs image was not created'),
            ])


@rfm.simple_test
class update_uenv_check(rfm.RunOnlyRegressionTest, UENV):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    uenv2build = parameter(UENV2BUILD)
    valid_systems = ['*']
    valid_prog_environs = ['builtin']
    executable = 'uenv'

    @run_after('init')
    def set_parent(self):
        variants = build_uenv_check.get_variant_nums(uenv2build=self.uenv2build)
        if len(variants) != 1:
            raise DependencyError(f'update_uenv_check %{self.uenv2build} depends on more than one version of build_uenv_check')
        self.depends_on(build_uenv_check.variant_name(variants[0]))

    @run_before('run')
    def set_cmds(self):
        # should we skip the test? I am not sure
        # self.skip_if_no_procinfo()
        now = datetime.datetime.now()
        self.uenv = self.get_uenv_from_uenv2build(self.uenv2build, uenv_version=f'{now:%Y%m%d.%H%M%S%z}')

        variants = build_uenv_check.get_variant_nums(uenv2build=self.uenv2build)
        parent = self.getdep(build_uenv_check.variant_name(variants[0]))
        self.executable_opts = [
            'image', 'add', self.uenv, parent.sqfs_path,
        ]

    @sanity_function
    def assert_sanity(self):
        return sn.all([
            sn.assert_found(r'the uenv .* was added to', self.stdout),
            sn.assert_not_found(r'does not exist', self.stdout),
            sn.assert_not_found(r'does not exist', self.stderr),
            sn.assert_not_found(r'command not found', self.stderr),
            ])


class gromacs_base_uenv_check(gromacs_check, UENV):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    descr = ('TBD')
    rationale = variable(str, value='TBD')
    uenv2build = parameter(list(filter(lambda x: os.path.basename(x).startswith('gromacs'), UENV2BUILD)))
    valid_systems = ['*']
    valid_prog_environs = ['builtin']
    maintainers = ['@victorusu']
    use_multithreading = False
    # num_nodes = parameter([1, 2])
    num_nodes = parameter([1])
    nb_impl = parameter(['cpu'])
    executable_opts += ['-dlb yes', '-ntomp 1', '-npme -1']

    @run_before('run')
    def append_executable_cmds(self):
        self.executable = f'uenv run {self.parent.uenv} --view=gromacs -- {self.executable}'

    @run_before('run')
    def set_job_parameters(self):
        proc = self.current_partition.processor
        if proc:
            self.num_tasks_per_node = proc.num_cores
            self.num_tasks = self.num_nodes * self.num_tasks_per_node
        else:
            self.num_tasks_per_node = 1
            self.num_tasks = self.num_nodes * self.num_tasks_per_node


@rfm.simple_test
class gromacs_uenv_check(gromacs_base_uenv_check):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    @run_after('init')
    def set_parent(self):
        variants = update_uenv_check.get_variant_nums(uenv2build=self.uenv2build)
        if len(variants) != 1:
            raise DependencyError(f'gromacs_uenv_check %{self.uenv2build} depends on more than one version of update_uenv_check')
        self.depends_on(update_uenv_check.variant_name(variants[0]))

    @run_after('setup')
    def get_parent(self):
        variants = update_uenv_check.get_variant_nums(uenv2build=self.uenv2build)
        self.parent = self.getdep(update_uenv_check.variant_name(variants[0]))


@rfm.simple_test
class gromacs_uenv_stress_check(gromacs_base_uenv_check, UENV):
    '''
    Check title: TBD
    Check description: TBD
    Check rationale: TBD
    '''

    @run_after('init')
    def set_parent(self):
        variants = uenv_image_present_check.get_variant_nums(uenv2build=self.uenv2build)
        if len(variants) != 1:
            raise DependencyError(f'gromacs_uenv_check %{self.uenv2build} depends on more than one version of uenv_image_present_check')
        self.depends_on(uenv_image_present_check.variant_name(variants[0]))

    @run_after('setup')
    def get_parent(self):
        variants = uenv_image_present_check.get_variant_nums(uenv2build=self.uenv2build)
        self.parent = self.getdep(uenv_image_present_check.variant_name(variants[0]))
        self.skip_if(not self.parent.uenv_installed, msg=f'{self.parent.uenv} is not installed')


