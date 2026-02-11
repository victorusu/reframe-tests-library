# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import reframe.utility.osext as osext


site_configuration = {
    'systems': [
        {
            'name' : 'scopi',
            'descr' : 'Piz Scopi vCluster',
            'hostnames' : ['scopi-ln001'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'normal',
                    'descr': 'AMD Zen2',
                    'scheduler': 'squeue',
                    'time_limit': '10m',
                    'environs': [
                        'b',
                        'builtin',
                        'PrgEnv-cray',
                        'PrgEnv-gnu'
                    ],
                    'features': ['remote', 'scontrol', 'uenv'],
                    'max_jobs': 500,
                    'launcher': 'srun',
                    # 'access': [f'--account={osext.osgroup()}'],
                    'access' : ['--account=a-csstaff'],
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
                        'b',
                        'builtin',
                    ],
                    'descr': 'Login nodes',
                    'max_jobs': 4,
                    'launcher': 'local'
                },
            ]
        }
    ],
    'environments': [
        {
            'name': 'b',
            'target_systems': ['scopi', 's'],
            'cc': 'cc',
        },
    ],
}
