# Copyright 2025 ETHZ/CSCS
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import reframe as rfm


UENV_DEFAULT_COMPILER = 'gcc@13'
DEFAULT_SPACK = 'v0.23.1'

UENV2BUILD = []
UENV_SOFTWARE = [
    {
        'name' : 'prgenv-gnu@24.11',
        'descr' : 'programming environment',
        'gcc' : 'gcc@13',
        'spec' : [
            'boost +chrono +filesystem +iostreams +mpi +python +regex +serialization +shared +system +timer',
            'cmake',
            'fftw',
            'fmt',
            'gsl',
            'hdf5+cxx+hl+fortran',
            'kokkos +aggressive_vectorization cxxstd=17 +openmp +pic +serial +shared +tuning',
            'kokkos-kernels +blas +execspace_openmp +execspace_serial +lapack +openmp scalars=float,double,complex_float,complex_double +serial +shared +superlu',
            'kokkos-tools +mpi +papi',
            'libtree',
            'lua',
            'lz4',
            'meson',
            'netlib-scalapack',
            'ninja',
            'openblas threads=openmp',
            'osu-micro-benchmarks@5.9',
            'python@3.12',
            'superlu',
            'zlib-ng',
        ],
    },
    {
        'name' : 'prgenv-gnu@24.11cuda12.4',
        'descr' : 'programming environment with cuda12.4',
        'gcc' : 'gcc@13',
        'cuda' : True,
        'spec' : [
            'boost +chrono +filesystem +iostreams +mpi +python +regex +serialization +shared +system +timer',
            'cmake',
            'cuda@12.4',
            'fftw',
            'fmt',
            'gsl',
            'hdf5+cxx+hl+fortran',
            'kokkos +aggressive_vectorization cxxstd=17 +openmp +pic +serial +shared +tuning',
            'kokkos-kernels +blas +execspace_openmp +execspace_serial +lapack +openmp scalars=float,double,complex_float,complex_double +serial +shared +superlu',
            'kokkos-tools +mpi +papi',
            'libtree',
            'lua',
            'lz4',
            'meson',
            'netlib-scalapack',
            'ninja',
            'openblas threads=openmp',
            'osu-micro-benchmarks@5.9',
            'python@3.12',
            'superlu',
            'zlib-ng',
        ],

    },
    {
        'name' : 'gromacs@2024.3',
        'descr' : 'GROMACS',
        'spec' : '+openmp +mpi +hwloc +cycle_subcounters',
    },
    {
        'name' : 'gromacs@2024.3cuda12.4',
        'descr' : 'GROMACS with CUDA',
        'cuda' : True,
        'spec' : [
            'gromacs@2024.3 +cuda +openmp +mpi +hwloc +cycle_subcounters',
            'cuda@12.4'
        ],
    },
    {
        'name' : 'nwchem@7.2.3',
        'descr' : 'NWChem',
        'spec' : 'armci=mpi3 +elpa +fftw3 +openmp +extratce'
    },
    {
        'name' : 'lammps@20240829.1',
        'descr' : 'LAMMPS',
        'spec' : '+asphere +body +class2 +colloid +compress +coreshell +dipole +ffmpeg +granular +jpeg +kim +kokkos +kspace +lib +manybody +mc +misc +molecule +mpi +openmp +openmp-package +opt +peri +png +poems +python +qeq +replica +rigid +shock +srd +tools +voronoi lammps_sizes=smallbig +ipo'
    },
    {
        'name' : 'lammps@20240829.1cuda12.4',
        'descr' : 'LAMMPS with CUDA',
        'cuda' : True,
        'spec' : [
            'lammps@20240829.1 +asphere +body +class2 +colloid +compress +coreshell +dipole +ffmpeg +granular +jpeg +kim +kokkos +kspace +lib +manybody +mc +misc +molecule +mpi +openmp +openmp-package +opt +peri +png +poems +python +qeq +replica +rigid +shock +srd +tools +voronoi lammps_sizes=smallbig +ipo',
            'cuda@12.4'
        ]
    },
    {
        'name' : 'sphexa@0.93.1',
        'descr' : 'SPH-EXA',
        'spack' : 'develop'
    },
    {
        'name' : 'sphexa@0.93.1cuda12.4',
        'descr' : 'SPH-EXA',
        'spack' : 'develop',
        'cuda' : True,
        'spec' : [
            'sphexa@0.93.1',
            'cuda@12.4'
        ],
    },
    {
        'name' : 'stress-ng@0.12.06',
        'descr' : 'STRESS-NG',
    },
]
