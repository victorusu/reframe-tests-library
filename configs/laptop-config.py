# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import reframe.utility.osext as osext


site_configuration = {
    'systems': [
        {
            'name' : 'laptop',
            'descr' : 'laptop vm',
            'hostnames' : ['laptop'],
            'partitions': [
                {
                    'name': 'normal',
                    'descr': 'aarch64',
                    'scheduler': 'slurm',
                    'time_limit': '10m',
                    'environs': [
                        'builtin',
                    ],
                    'features': ['uenv', 'modules'],
                    'max_jobs': 100,
                    'launcher': 'srun',
                    'resources': [
                        {
                            'name': 'memory',
                            'options': ['--mem={mem_per_node}']
                        },
                        {
                            'name': 'project',
                            'options': ['--account={project}']
                        },
                        {
                            'name': 'uenv',
                            'options': ['--uenv={file}:{mount}']
                        },
                        {
                            'name': 'uenv_views',
                            'options': ['--view={views}']
                        },
                    ],
                },
                {
                    'name': 'login',
                    'scheduler': 'local',
                    'time_limit': '10m',
                    'environs': [
                        'builtin',
                    ],
                    'descr': 'Login nodes',
                    'max_jobs': 4,
                    'launcher': 'local'
                },
            ]
        }
    ],
}
