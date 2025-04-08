# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import datetime
import os
import sys

import reframe as rfm
import reframe.core.runtime as rt
import reframe.utility.sanity as sn
import reframe.utility.typecheck as typ
import reframe.utility.udeps as udeps
import reframe.utility as util

from string import Template

from reframe.core.exceptions import DependencyError, SanityError, ReframeError


# Add the root directory of hpctestslib
prefix = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import checks.build_systems.uenv_checks.definitions as uenv
import mixins.build_systems.uenv.mixin as uenv_mixin
import util as hpcutil


@rfm.simple_test
class spack_cmd_not_present_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Check that Spack is not enabled in the environment
    Check description: Make sure that Spack command is not enabled in the environment
    Check rationale: A standalone version of Spack can interfere with uenvs.
    '''
    descr = ('Make sure that Spack command is not enabled in the environment.')
    executable = 'spack'
    executable_opts = ['--version']
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']

    @sanity_function
    def assert_sanity(self):
        return sn.assert_found(r'spack: command not found|spack: No such file or directory', self.stderr),


@rfm.simple_test
class uenv_cmd_present(rfm.RunOnlyRegressionTest):
    '''
    Check title: Check that uenv is enabled in the environment
    Check description: Make sure that uenv is enabled in the environment
    Check rationale: There is no point in testing uenvs if it is not enabled in the environment.
    '''

    descr = ('Make sure that Spack command is not enabled in the environment.')
    executable = 'uenv'
    executable_opts = ['--version']
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']

    @sanity_function
    def assert_sanity(self):
        return sn.assert_found(r'\d+.\d+.\d+', self.stdout)


@rfm.simple_test
class uenv_image_present_check(rfm.RunOnlyRegressionTest,
                               uenv_mixin.build_uenv_mixin,
                               uenv_mixin.recipes_creation_mixin):
    '''
    Check title: Check if the uenv is already present in the user repo
    Check description: We should not build images that already present and we should not run tests that depend on non-built images
    '''

    descr = ('We should not build images that already present and we should not run tests that depend on non-built images')
    uenv = parameter(uenv.UENV_SOFTWARE, fmt=lambda x: x['name'])
    executable = 'uenv'
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        self.depends_on('uenv_cmd_present')

    @run_before('run')
    def set_uenv_image(self):
        # do not add the time in the image removal command because we do not know what is it
        self.validate_uenv_software_fields(self.uenv)
        self.uenv_data = self.get_uenv_name_from_software(self.uenv)
        self.executable_opts = [
            'image', 'ls', self.uenv_data
        ]
        self.postrun_cmds = [
            f'{self.executable} image inspect --format={{meta}} {self.uenv_data}'
        ]


    @sanity_function
    def assert_sanity(self):
        uenvs = sn.findall(r'(?P<name>\S+(:\S+)?)\s+(?P<arch>\S+)\s+'
                           r'(?P<system>\S+)(\s+\S+){3}', self.stdout)
        count = sn.count(uenvs)

        found = sn.extractall(r'(?P<path>\S+)\/meta', self.stdout, 'path')

        self.uenv_path = None
        if found:
            self.uenv_path = os.path.join(sn.evaluate(found[0]), 'store.squashfs')

        self.uenv_installed = False
        try:
            sn.evaluate(sn.assert_not_found(r'no matching uenv', self.stderr))
        except SanityError as e:
            return True

        if count > 1:
            self.uenv_installed = True
            self.uenv_data = sn.evaluate(uenvs)[-1].group('name')

        return True


@rfm.simple_test
class uenv_image_present_response_aggregator_check(rfm.RunOnlyRegressionTest,
                                                   uenv_mixin.recipes_creation_mixin):
    '''
    Check title: Image present aggregator
    Check description: This test collects information about all available user environments and helps the subsequent tests to decide if they need to be skipped
    '''

    descr = ('This test collects information about all available user environments and helps the subsequent tests to decide if they need to be skipped')
    executable = 'uenv'
    executable_opts = ['--version']
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']
    uenvs_installed = []

    @run_after('init')
    def set_parent(self):
        variants = uenv_image_present_check.get_variant_nums()
        for v in variants:
            self.depends_on(uenv_image_present_check.variant_name(v))

    def is_cuda_build(self, uenv):
        if 'cuda' in uenv:
            if uenv['cuda']:
                return True
        return False

    @sanity_function
    def assert_sanity(self):
        variants = uenv_image_present_check.get_variant_nums()

        cuda_partitions = list(hpcutil.get_partitions_with_feature_set(set(['cuda'])))
        part_skipped_uenvs = []
        for v in variants:
            parent = self.getdep(uenv_image_present_check.variant_name(v))
            if parent.uenv_installed:
                self.uenvs_installed.append(parent.uenv)
            else:
                if self.is_cuda_build(parent.uenv):
                    if cuda_partitions:
                        # The parent class should already have updated the environment
                        self.create_uenv_recipe(parent.uenv, validate_uenv=False)
                    else:
                        part_skipped_uenvs.append(parent.uenv)
                else:
                    # TODO: add a gate to restrist non-cuda builds on cuda systems
                    self.create_uenv_recipe(parent.uenv, validate_uenv=False)

        self.skip_if(len(self.uenvs_installed) + len(part_skipped_uenvs) == len(variants),
                     msg=f'All uenvs are already installed')

        return True


@rfm.simple_test
class stackinator_bootstrap_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Stackinator Boostrap
    Check description: Downloads and bootstraps Stackinator
    '''

    descr = ('Downloads and bootstraps Stackinator')
    executable = 'stack-config'
    executable_opts = ['--version']
    sourcesdir = 'https://github.com/eth-cscs/stackinator'
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        self.depends_on('spack_cmd_not_present_check')
        self.depends_on('uenv_cmd_present')
        self.depends_on('uenv_image_present_response_aggregator_check')

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
class uenv_build_cache_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: UENV build cache
    Check description: Checks if the build cache is configured
    '''

    descr = ('Checks if the build cache is configured')
    cache_cfg = variable(str, value='~/.cache-config.yaml')
    executable = hpcutil.ECHOCMD
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']
    use_cache = variable(typ.Bool, value=True)

    @run_after('init')
    def set_parent(self):
        self.depends_on('spack_cmd_not_present_check')
        self.depends_on('uenv_cmd_present')
        self.depends_on('uenv_image_present_response_aggregator_check')

    @run_after('init')
    def normalize_path(self):
        self.cache_cfg = os.path.expandvars(os.path.expanduser(str(self.cache_cfg)))

    # TODO: improve this sanity check
    # It should check for the contents of the self.cache_cfg file
    @sanity_function
    def assert_sanity(self):
        if self.use_cache:
            return sn.all([
                sn.assert_not_found(r'does not exist', self.stdout),
                sn.assert_not_found(r'does not exist', self.stderr),
                sn.assert_true(os.path.exists(self.cache_cfg), msg=f'Cache file {self.cache_cfg} does not exist'),
                sn.assert_not_found(r'spack minimum version is .* - recipe uses .*', self.stdout),
                sn.assert_eq(os.stat(sn.evaluate(self.stderr)).st_size, 0,
                            msg=f'file {self.stderr} is not empty'),
                ])
        else:
            return True


@rfm.simple_test
class cluster_configuration_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Cluster configurations check
    Check description: Downloads the configuration for a given Alps node. The configuration is used by stackinator to build uenvs
    '''

    descr = ('Downloads the configuration for a given Alps node. The configuration is used by stackinator to build uenvs')
    sourcesdir = 'https://github.com/eth-cscs/alps-cluster-config'
    cluster_name = variable(str, value='')
    executable = hpcutil.ECHOCMD
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']
    system_dir = ''

    @run_after('init')
    def set_parent(self):
        self.depends_on('spack_cmd_not_present_check')
        self.depends_on('uenv_cmd_present')
        self.depends_on('uenv_image_present_response_aggregator_check')

    @sanity_function
    def assert_sanity(self):
        cluster_name = self.cluster_name if self.cluster_name else self.current_system.name
        self.system_dir = os.path.join(sn.evaluate(self.stagedir), cluster_name)
        return sn.all([
            sn.assert_true(os.path.isdir(self.system_dir),
                           msg=f'System {cluster_name} is not supported by Alps '
                                 'Cluster Config repo')
            ])


@rfm.simple_test
class bootstrap_uenv_check(rfm.RunOnlyRegressionTest,
                           uenv_mixin.build_uenv_mixin,
                           uenv_mixin.recipes_creation_mixin):
    '''
    Check title: Bootstrap UENVs
    Check description: Bootstraps the uenv to be built and generates the command that should be used to build the uenv
    '''

    descr = ('Bootstraps the uenv to be built and generates the command that should be used to build the uenv')
    sourcesdir = 'https://github.com/eth-cscs/alps-uenv'
    uenv = parameter(uenv.UENV_SOFTWARE, fmt=lambda x: x['name'])
    time_limit = '2h'
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']
    use_shm = variable(typ.Bool, value=True)
    use_cache = variable(typ.Bool, value=True)

    executable = hpcutil.ECHOCMD

    @run_after('init')
    def set_parent(self):
        self.depends_on('uenv_build_cache_check')
        self.depends_on('stackinator_bootstrap_check')
        self.depends_on('cluster_configuration_check')
        self.depends_on('uenv_image_present_response_aggregator_check')

    @run_before('run')
    def is_uenv_installed(self):
        parent = self.getdep('uenv_image_present_response_aggregator_check')
        uenv = self.get_uenv_name_from_software(self.uenv)
        self.validate_uenv_software_fields(self.uenv)
        self.skip_if(self.uenv in parent.uenvs_installed,
                     msg=f'uenv {uenv} is already built')
        self.uenv_recipe_path = os.path.join(parent.stagedir, self.uenv['name'])

    @run_after('init')
    def skip_cuda_builds(self):
        if 'cuda' in self.uenv:
            if self.uenv['cuda']:
                partitions = hpcutil.get_partitions_with_feature_set(['cuda'])
                self.skip_if(not partitions,
                             msg='The system does not have any partitions with '
                                 'CUDA support')

    @run_before('run')
    def set_tmpdir(self):
        import tempfile
        if self.use_shm:
            tempfile.tempdir=f'/dev/shm'
            try:
                self.tmpdir = tempfile.mkdtemp(prefix=self.unique_name)
            except Exception as e:
                raise ReframeError(e)
        else:
            self.tmpdir = self.stagedir

    @run_before('run')
    def set_cmds(self):
        stackinator = self.getdep('stackinator_bootstrap_check')
        cluster_cfg = self.getdep('cluster_configuration_check')
        self.executable = stackinator.executable
        self.executable_opts = [
            '--build',
            self.tmpdir,
            '--recipe',
            self.uenv_recipe_path,
            '--system',
            cluster_cfg.system_dir,
        ]
        if self.use_cache:
            cache_cfg = self.getdep('uenv_build_cache_check')
            self.executable_opts += [
                '--cache',
                cache_cfg.cache_cfg
            ]

    @sanity_function
    def assert_sanity(self):
        # return False
        return sn.all([
            sn.assert_not_found(r'does not exist', self.stdout),
            sn.assert_not_found(r'does not exist', self.stderr),
            sn.assert_not_found(r'spack minimum version is .* - recipe uses .*',
                                self.stdout),
            sn.assert_not_found(r"the mount point '/user-environment' must exist",
                                self.stdout),
            sn.assert_not_found(r'see log.* for more information', self.stdout),
            sn.assert_found(r'Configuration finished, run the following to '
                            r'build the environment', self.stdout),
            sn.assert_eq(os.stat(sn.evaluate(self.stderr)).st_size, 0,
                         msg=f'file {self.stderr} is not empty'),
            ])


@rfm.simple_test
class build_uenv_check(rfm.RunOnlyRegressionTest):
    '''
    Check title: Build uenv check
    Check description: Builds the uenv using the command provided by the uenv bootstrap test
    '''

    descr = ('Builds the uenv using the command provided by the uenv bootstrap test')
    uenv = parameter(uenv.UENV_SOFTWARE, fmt=lambda x: x['name'])
    time_limit = '2h'
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']

    @run_after('init')
    def set_parent(self):
        variants = bootstrap_uenv_check.get_variant_nums(uenv=self.uenv)
        if len(variants) != 1:
            raise DependencyError(f'{self.name} depends on more than one '
                                  'version of bootstrap_uenv_check')
        self.depends_on(bootstrap_uenv_check.variant_name(variants[0]))

    @run_after('setup')
    def set_check_invariants(self):
        variants = bootstrap_uenv_check.get_variant_nums(uenv=self.uenv)
        parent = self.getdep(bootstrap_uenv_check.variant_name(variants[0]))
        self.bootstrap_dir = sn.evaluate(parent.stagedir)
        output = os.path.join(self.bootstrap_dir,
                              sn.evaluate(parent.stdout))
        with open(output, 'r') as f:
            found = f.readlines()
        cmds = ['', '']
        if found and len(found) > 1:
            cmds = found[-2:]

        self.executable = hpcutil.ECHOCMD
        self.prerun_cmds = cmds

        self.sqfs_img = 'store.squashfs'
        self.sqfs_path = os.path.join(parent.tmpdir, self.sqfs_img)
        self.postrun_cmds = [
            f'{hpcutil.CPCMD} {self.sqfs_path} {sn.evaluate(self.stagedir)}'
        ]
        self.sqfs_path = os.path.join(sn.evaluate(self.stagedir), self.sqfs_img)

        self.keep_files = [
            self.sqfs_img
        ]

    @run_before('cleanup')
    def remove_tmpdir(self):
        variants = bootstrap_uenv_check.get_variant_nums(uenv=self.uenv)
        parent = self.getdep(bootstrap_uenv_check.variant_name(variants[0]))
        import shutil
        try:
            shutil.rmtree(parent.tmpdir, ignore_errors=True)
        except:
            pass

    @sanity_function
    def assert_sanity(self):
        return sn.all([
            sn.assert_not_found(r'does not exist', self.stdout),
            sn.assert_not_found(r'does not exist', self.stderr),
            sn.assert_not_found(r'command not found', self.stderr),
            sn.assert_true(os.path.exists(self.sqfs_path), msg='The squashfs image was not created'),
            ])


@rfm.simple_test
class update_uenv_check(rfm.RunOnlyRegressionTest,
                        uenv_mixin.build_uenv_mixin,
                        uenv_mixin.recipes_creation_mixin):
    '''
    Check title: Update uenv
    Check description: Adds the recently built uenv to the uenv repo
    '''

    descr = ('Adds the recently built uenv to the uenv repo')
    uenv  = parameter(uenv.UENV_SOFTWARE, fmt=lambda x: x['name'])
    valid_systems = [hpcutil.get_first_local_partition()]
    local = True
    valid_prog_environs = ['builtin']
    executable = 'uenv'
    time_limit = '2h'

    @run_after('init')
    def set_parent(self):
        variants = build_uenv_check.get_variant_nums(uenv=self.uenv)
        if len(variants) != 1:
            raise DependencyError(f'{self.name} depends on more than one version of build_uenv_check')
        self.depends_on(build_uenv_check.variant_name(variants[0]))

    @run_before('run')
    def set_cmds(self):
        now = datetime.datetime.now()
        variants = build_uenv_check.get_variant_nums(uenv=self.uenv)
        parent = self.getdep(build_uenv_check.variant_name(variants[0]))

        # update the uenv name to properly get the uenv_data info
        self.validate_uenv_software_fields(self.uenv)
        self.uenv_data = self.get_uenv_name_from_software(self.uenv, uenv_version=f'{now:%Y%m%d.%H%M%S%z}')
        self.executable_opts = [
            'image', 'add', self.uenv_data, parent.sqfs_path,
        ]
        self.postrun_cmds = [
            f'{self.executable} image inspect --format={{meta}} {self.uenv_data}'
        ]

    @sanity_function
    def assert_sanity(self):
        found = sn.extractall(r'(?P<path>\S+)\/meta', self.stdout, 'path')

        self.uenv_path = ''
        if found:
            self.uenv_path = os.path.join(sn.evaluate(found[0]), 'store.squashfs')

        return sn.all([
            sn.assert_true(found, msg='Image was not added to the repository'),
            sn.assert_found(r'the uenv .* was added to', self.stdout),
            sn.assert_not_found(r'does not exist', self.stdout),
            sn.assert_not_found(r'does not exist', self.stderr),
            sn.assert_not_found(r'command not found', self.stderr),
            ])


class uenv_mixin(uenv_mixin.enable_uenv_mixin, hpcutil.GetDepMixin):
    '''
    Check title: uenv mixin
    Check description: This mixin encompasses a set of functionalities to test uenvs based on the previous tests with and without views and the use of the SPANK plugin
    '''
    uenv = parameter([])

    status = parameter(['justbuilt', 'alreadypresent'])
    uenv_views = parameter([True, False])
    uenv_spank = parameter([True, False])

    @run_after('init')
    def set_uenv_name(self):
        if 'name' in self.uenv:
            self.uenv_name = self.uenv['name']
        else:
            raise ValueError(f'name not defined in {self.uenv}')

    @run_after('init')
    def set_view_name(self):
        self.view_name = self.uenv['name'].split('@')[0].split('/')[0]

    @run_after('init')
    def set_parent(self):
        if self.status == 'alreadypresent':
            variants = uenv_image_present_check.get_variant_nums(uenv=self.uenv)
            if not variants:
                raise DependencyError(f'{self.name} does not depend on any uenv_image_present_check test')
            elif len(variants) > 1:
                raise DependencyError(f'{self.name} depends on more than one version of uenv_image_present_check {variants}')
            self.depends_on(uenv_image_present_check.variant_name(variants[0]), how=udeps.by_env)
        elif self.status == 'justbuilt':
            variants = update_uenv_check.get_variant_nums(uenv=self.uenv)
            if not variants:
                raise DependencyError(f'{self.name} does not depend on any update_uenv_check test')
            elif len(variants) > 1:
                raise DependencyError(f'{self.name} depends on more than one version of update_uenv_check {variants}')
            self.depends_on(update_uenv_check.variant_name(variants[0]), how=udeps.by_env)
        else:
            raise ValueError(f'Unknown status {self.status}')

    @run_after('setup')
    def get_parent(self):
        if self.status == 'alreadypresent':
            variants = uenv_image_present_check.get_variant_nums(uenv=self.uenv)
            self.parent = self.mygetdep(uenv_image_present_check.variant_name(variants[0]))
            self.skip_if(not self.parent.uenv_installed, msg=f'{self.parent.uenv_data} is not installed')
        elif self.status == 'justbuilt':
            variants = update_uenv_check.get_variant_nums(uenv=self.uenv)
            self.parent = self.mygetdep(update_uenv_check.variant_name(variants[0]))

    @run_before('run')
    def update_executable(self):
        if not self.uenv_views:
            self.executable = os.path.join(f'/user-environment/env/{self.view_name}/bin', self.executable)

        if not self.uenv_spank:
            if self.uenv_views:
                self.executable = f'uenv run {self.parent.uenv_data} --view={self.view_name} -- {self.executable}'
            else:
                self.executable = f'uenv run {self.parent.uenv_data} -- {self.executable}'

    @run_before('run')
    def enable_uenv(self):
        if self.uenv_spank:
            if self.uenv_views:
                self.enable_uenv_options(uenv_path=self.parent.uenv_path, views=self.view_name)
            else:
                self.enable_uenv_options(uenv_path=self.parent.uenv_path)

