# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import reframe.utility.osext as osext

# https://tbrindus.ca/correct-ld-preload-hooking-libc/
# https://thehackernews.com/2025/02/new-linux-malware-auto-color-grants.html?m=1
# https://unit42.paloaltonetworks.com/new-linux-backdoor-auto-color/

# libcext.so.2
# /var/log/cross/auto-color
# /etc/ld.preload

# cat /proc/net/tcp
# 0 instead of sl

# /tmp/cross/config-err-XXXXXXXX
# /var/log/cross/config-err-XXXXXXXX


# bwrap --dev-bind / / --tmpfs /tmp

# additivefoam
# amr-wind
# arborx
# cabana
# chombo
# ecp-data-vis-sdk
# exaca
# filo
# heffte
# hydrogen
# lammps
# lbann
# nek5000
# nektools
# parsplice
# qmcpack
# redset
# shuffile
# upcxx
# aluminum
# amrex
# axl
# chai
# dihydrogen
# er
# exawind
# gasnet
# hiptt
# kvtree
# latte
# nalu-wind
# nekrs
# nwchem
# py-warpx
# rankstr
# rmgdft
# warpx


site_configuration = {
    'systems': [
        {
            'name' : 'rocky',
            'descr' : 'rocky vm',
            'hostnames' : ['rocky'],
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
