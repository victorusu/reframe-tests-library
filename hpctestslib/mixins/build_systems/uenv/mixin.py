# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import os
import sys

import reframe as rfm

from string import Template


# Add the root directory of hpctestslib
prefix = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


import checks.build_systems.uenv_checks.definitions as uenv


class build_uenv_mixin(rfm.RegressionTestPlugin):
    def uenv2string(self, uenv_dict, uenv_version=None):
        swname = uenv_dict['swname']
        swver = uenv_dict['swver']
        system = uenv_dict['system']
        arch = uenv_dict['arch']
        if uenv_version:
            return f'{swname}/{swver}:{uenv_version}@{system}%{arch}'
        return f'{swname}/{swver}@{system}%{arch}'

    def get_uenv_name_from_software(self, software, uenv_version=None):
        self.skip_if_no_procinfo()
        # uenv = os.path.basename(software)
        uenv_name = software['name']
        env_parts = uenv_name.split('@', maxsplit=1)
        swname = env_parts[0]
        swver = env_parts[1] if len(env_parts) > 1 else 'latest'

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


class enable_uenv_mixin(build_uenv_mixin):
    def enable_uenv_options(self, uenv_path, mntpoint=None, views=None):
        if not self.extra_resources:
            self.extra_resources = {
                    'uenv' : {
                    'file': uenv_path,
                    'mount' : mntpoint if mntpoint else '/user-environment'
                },
            }
        else:
            self.extra_resources.update({
                    'uenv' : {
                    'file': uenv_path,
                    'mount' : mntpoint if mntpoint else '/user-environment'
                },
            })
        if views:
            self.extra_resources['uenv_views'] = {
                'views': views
            }


class recipes_creation_mixin(rfm.RegressionTestPlugin):
    def read_recipe_file(self, recipes_file):
        with open(recipes_file, 'r') as f:
            return Template(f.read())

    def dump_recipe_file(self, sw, template, filename):
        with open(filename, 'w') as f:
            f.write(template.safe_substitute(
                name=sw['name'].replace('@', '_'),
                bootstrap=sw['bootstrap'],
                gcc=sw['gcc'],
                spack=sw['spack'],
                descr=sw['descr'],
                spec=sw['spec'],
                envname=sw['envname'],
                mpi=sw['mpi'],
                variants=sw['variants'],
            ))

    def create_uenv_recipe(self, uenv, validate_uenv=True):
        if validate_uenv:
            self.validate_uenv_software_fields(uenv)
        srcdir = os.path.join(self.stagedir, 'recipe')
        recipe_files = os.listdir(srcdir)

        output_path = os.path.join(self.stagedir, uenv['name'])
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        elif not os.path.isdir(output_path):
            raise ValueError(f'The recipes path {output_path} is not a directory')

        for re in recipe_files:
            template = self.read_recipe_file(os.path.join(srcdir, re))
            filename = os.path.join(output_path, re)
            self.dump_recipe_file(uenv, template, filename)

    def validate_uenv_software_fields(self, software):
        # for software in uenv_software_list:
        if 'name' not in software:
            raise ValueError(f'Found software without a name entry')

        if 'bootstrap' not in software:
            software['bootstrap'] = uenv.UENV_DEFAULT_COMPILER
            major_version = uenv.UENV_DEFAULT_COMPILER.split('.')
            if len(major_version) > 1:
                software['bootstrap'] = ''.join(major_version[:-1])

        if 'gcc' not in software:
            software['gcc'] = uenv.UENV_DEFAULT_COMPILER

        if 'spack' not in software:
            software['spack'] = uenv.DEFAULT_SPACK

        if 'descr' not in software:
            software['descr'] = software['name']

        if 'spec' not in software:
            software['spec'] = ''

        if isinstance(software['spec'], str):
            software['spec'] = '  - ' + software['name'] + ' ' + software['spec']
        elif isinstance(software['spec'], list):
            software['spec'] = '\n'.join(['  - ' + spec for spec in software['spec']])

        if 'variants' not in software:
            software['variants'] = ['+mpi']

        if 'mpi' not in software:
            software['mpi'] = ['spec: cray-mpich']

        if isinstance(software['mpi'], str):
            mpi = software['mpi']
            if not mpi.startswith('spec:'):
                software['mpi'] = ['spec: ' + mpi]
            else:
                software['mpi'] = [mpi]

        if 'cuda' in software:
            if isinstance(software['cuda'], bool):
                if software['cuda']:
                    software['cuda'] = 'cuda'

            if 'cuda_arch' not in software:
                software['cuda_arch'] = 'cuda_arch=90'

            if isinstance(software['variants'], str):
                variants = software['variants'].split('\n')
                if '+cuda' not in variants:
                    software['variants'] = software['variants'] + '\n - +cuda'
                if software['cuda_arch'] not in variants:
                    software['variants'] = software['variants'] + '\n - ' + software['cuda_arch']
            elif isinstance(software['variants'], list):
                if '+cuda' not in software['variants']:
                    software['variants'] = software['variants'] + ['+cuda']
                if software['cuda_arch'] not in software['variants']:
                    software['variants'] = software['variants'] + [software['cuda_arch']]

            software['mpi'] = software['mpi'] + ['gpu: cuda']

        if isinstance(software['variants'], str):
            software['variants'] = '  - ' + software['name'] + ' ' + software['variants']
        elif isinstance(software['variants'], list):
            software['variants'] = '\n'.join(['  - ' + v for v in software['variants']])

        software['mpi'] = '\n    '.join(software['mpi'])

        if 'envname' not in software:
            sname = software['name'].split('@', maxsplit=1)
            envname = sname[0]
            software['envname'] = envname
            if len(sname) != 2:
                software['name'] = software['name'] + '@latest'

        # this should be the last thing in the function
        if 'cuda' in software:
            name = software['name']
            if 'cuda' not in name:
                software['name'] = software['name'] + software['cuda'].replace('@', '')

        name_opts = software['name'].split('@', maxsplit=1)
        if len(name_opts) > 1:
            suffix = name_opts[-1]
            if 'gcc' not in suffix:
                software['name'] = software['name'] + software['gcc'].replace('@', '')
