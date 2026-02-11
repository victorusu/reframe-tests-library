# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


import os
import re
import sys

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility as util

from string import Template

# TODO: Fix this. This is not a great idea
CPP = r"""#include <limits.h>
#include <stdio.h>
#ifdef _OPENMP
#include <omp.h>
#endif
#ifdef USE_MPI
#include "mpi.h"
#endif
#include <unistd.h>

int main(int argc, char *argv[]) {
  int rank = 0, size = 1;
  int mpiversion, mpisubversion;
  int resultlen = -1;
#ifdef USE_MPI
  char mpilibversion[MPI_MAX_LIBRARY_VERSION_STRING];
  int namelen;
  char processor_name[MPI_MAX_PROCESSOR_NAME];
#else
  char processor_name[HOST_NAME_MAX + 1];
  if (gethostname(processor_name, sizeof(processor_name)) != 0) {
          perror("gethostname");
          return 1;
  }
#endif
  int tid = 0, nthreads = 1;

#ifdef USE_MPI
  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  MPI_Get_processor_name(processor_name, &namelen);
  if (rank == 0) {
    MPI_Get_version(&mpiversion, &mpisubversion);
    MPI_Get_library_version(mpilibversion, &resultlen);
    printf("# MPI-%d.%d = %s\n", mpiversion, mpisubversion, mpilibversion);
  }
#endif

#pragma omp parallel default(shared) private(tid)
  {
#ifdef _OPENMP
    nthreads = omp_get_num_threads();
    tid = omp_get_thread_num();
#endif
    printf(
        "Hello, World from thread %d out of %d from rank %d out of %d %s\n", tid, nthreads, rank, size, processor_name);
  }

#ifdef USE_MPI
  MPI_Finalize();
#endif

  return 0;
}
"""

# TODO: Fix this. This is not a great idea
C = CPP

# TODO: Fix this. This is not a great idea
F90  = r"""program hello_world_mpi_openmp
#ifdef _OPENMP
    use omp_lib
#endif
#ifdef USE_MPI
    use mpi
   !include mpif.h
#endif
   implicit none

   integer :: rank=0, size=1, tid=0, nthreads=1
   integer :: ierr, i, j, k
   integer :: mpiversion=0, mpisubversion=0
   integer :: resultlen = -1

#ifdef USE_MPI
   character(len=MPI_MAX_PROCESSOR_NAME) :: processor_name
   character(len=MPI_MAX_LIBRARY_VERSION_STRING) :: mpilibversion
   !integer, dimension(MPI_STATUS_SIZE) :: status
   call MPI_INIT(ierr)
   call MPI_COMM_RANK(MPI_COMM_WORLD, rank, ierr)
   call MPI_COMM_SIZE(MPI_COMM_WORLD, size, ierr)
   call MPI_Get_processor_name(processor_name, resultlen, ierr)
   if (rank .eq. 0) then
        call MPI_Get_version(mpiversion, mpisubversion, iErr)
        call MPI_Get_library_version(mpilibversion, resultlen, ierr)
        write (*, (A6,I1,A1,I1)) # MPI-, mpiversion, ., mpisubversion
        print *,trim(mpilibversion)
   endif
#else
   character(len=3) :: processor_name = nid
#endif

!$OMP PARALLEL PRIVATE(tid, nthreads)
#ifdef _OPENMP
   if (rank .eq. 0) then
       print *, # OMP-, _OPENMP
   endif
   tid = omp_get_thread_num()
   nthreads = omp_get_num_threads()
#else
   tid = 0
   nthreads = 1
#endif
   write(*, (A24,1X,I3,A7,I3,1X,A12,1X,I3,1X,A6,I3,1X,A10)) &
       "Hello, World from thread ", &
       tid, "out of", nthreads, &
       "from rank", rank, "out of", size, trim(processor_name)
   ! flush(6)
!$OMP END PARALLEL

#ifdef USE_MPI
   call MPI_FINALIZE(ierr)
#endif

end program hello_world_mpi_openmp
"""
