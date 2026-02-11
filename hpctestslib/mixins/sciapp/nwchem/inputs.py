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


INPUT_FILE_TEMPLATE = Template(
'start $name\n'
'\n'
'# Memory allocation\n'
'memory 2048 mb\n'
'\n'
'# Title\n'
'title "$title"\n'
'\n'
'# Geometry\n'
'$geometry\n'
'\n'
'# Basis set\n'
'$basis\n'
'\n'
'# Computation\n'
'$computation\n'
)

GLUCOSE = [
'geometry units angstroms noautosym nocenter',
'  C       8.47473660    13.29351591    37.45155696',
'  C       8.62932868    12.65410329    38.83071622',
'  C       8.96538020    13.71981308    39.86076322',
'  C      10.15374335    14.56052759    39.41879530',
'  C       9.90302949    15.10567904    38.01342070',
'  C      11.11886291    15.82220989    37.44985956',
'  O       7.35253333    14.11043771    37.41855240',
'  O       7.42721037    12.00664540    39.13929906',
'  O       9.17639033    13.15210628    41.13622370',
'  O      10.35304193    15.63471478    40.28943738',
'  O       9.60015703    14.03259559    37.15017161',
'  O      10.87501900    16.41679929    36.21023778',
'  H       8.40939727    12.52393251    36.69098463',
'  H       9.44699731    11.93422179    38.77406224',
'  H       8.11038020    14.37290662    39.97922779',
'  H      11.04362414    13.92514412    39.38769707',
'  H       9.06387450    15.79348129    38.05821331',
'  H      11.46168766    16.54987399    38.17996538',
'  H      11.91081375    15.10024417    37.29146700',
'  H       6.62467712    13.63204800    37.78691540',
'  H       7.40443689    11.81148528    40.06351047',
'  H       9.92059954    12.56935082    41.11090771',
'  H      10.28110622    15.32842153    41.18022023',
'  H      10.21397219    17.08374304    36.29779890',
'end',
]

CF3COO_ = [
'charge -1',
'geometry nocenter',
'  C    0.512211   0.000000  -0.012117',
'  C   -1.061796   0.000000  -0.036672',
'  O   -1.547400   1.150225  -0.006609',
'  O   -1.547182  -1.150320  -0.006608',
'  F    1.061911   1.087605  -0.610341',
'  F    1.061963  -1.086426  -0.612313',
'  F    0.993255  -0.001122   1.266928',
'  symmetry c1',
'end',
]

BF = [
'geometry',
'  b 0.0 0.0 0.0',
'  f 0.0 0.0 1.2',
'  symmetry c2v # enforcing abelian symmetry',
'end',
]

HEME = [
'geometry full-system',
'  symmetry cs',
'  H     0.438   -0.002    4.549',
'  C     0.443   -0.001    3.457',
'  C     0.451   -1.251    2.828',
'  C     0.452    1.250    2.828',
'  H     0.455    2.652    4.586',
'  H     0.461   -2.649    4.586',
'  N1    0.455   -1.461    1.441',
'  N1    0.458    1.458    1.443',
'  C     0.460    2.530    3.505',
'  C     0.462   -2.530    3.506',
'  C     0.478    2.844    1.249',
'  C     0.478    3.510    2.534',
'  C     0.478   -2.848    1.248',
'  C     0.480   -3.513    2.536',
'  C     0.484    3.480    0.000',
'  C     0.485   -3.484    0.000',
'  H     0.489    4.590    2.664',
'  H     0.496   -4.592    2.669',
'  H     0.498    4.573    0.000',
'  H     0.503   -4.577    0.000',
'  H    -4.925    1.235    0.000',
'  H    -4.729   -1.338    0.000',
'  C    -3.987    0.685    0.000',
'  N    -3.930   -0.703    0.000',
'  C    -2.678    1.111    0.000',
'  C    -2.622   -1.076    0.000',
'  H    -2.284    2.126    0.000',
'  H    -2.277   -2.108    0.000',
'  N    -1.838    0.007    0.000',
'  Fe    0.307    0.000    0.000',
'  O     2.673   -0.009    0.000',
'  H     3.238   -0.804    0.000',
'  H     3.254    0.777    0.000',
'end',
'geometry ring-only',
'  symmetry cs',
'  H     0.438   -0.002    4.549',
'  C     0.443   -0.001    3.457',
'  C     0.451   -1.251    2.828',
'  C     0.452    1.250    2.828',
'  H     0.455    2.652    4.586',
'  H     0.461   -2.649    4.586',
'  N1    0.455   -1.461    1.441',
'  N1    0.458    1.458    1.443',
'  C     0.460    2.530    3.505',
'  C     0.462   -2.530    3.506',
'  C     0.478    2.844    1.249',
'  C     0.478    3.510    2.534',
'  C     0.478   -2.848    1.248',
'  C     0.480   -3.513    2.536',
'  C     0.484    3.480    0.000',
'  C     0.485   -3.484    0.000',
'  H     0.489    4.590    2.664',
'  H     0.496   -4.592    2.669',
'  Bq    0.307    0.0      0.0    charge 2  # simulate the iron',
'end',
'geometry imid-only',
'  symmetry cs',
'  H     0.498    4.573    0.000',
'  H     0.503   -4.577    0.000',
'  H    -4.925    1.235    0.000',
'  H    -4.729   -1.338    0.000',
'  C    -3.987    0.685    0.000',
'  N    -3.930   -0.703    0.000',
'  C    -2.678    1.111    0.000',
'  C    -2.622   -1.076    0.000',
'  H    -2.284    2.126    0.000',
'  H    -2.277   -2.108    0.000',
'  N    -1.838    0.007    0.000',
'end',
'geometry fe-only',
'  symmetry cs',
'  Fe    .307    0.000    0.000',
'end',
'geometry water-only',
'  symmetry cs',
'  O     2.673   -0.009    0.000',
'  H     3.238   -0.804    0.000',
'  H     3.254    0.777    0.000',
'end',
]

WATERDIMER = [
'geometry dimer',
'  O   -0.595   1.165  -0.048',
'  H    0.110   1.812  -0.170',
'  H   -1.452   1.598  -0.154',
'  O    0.724  -1.284   0.034',
'  H    0.175  -2.013   0.348',
'  H    0.177  -0.480   0.010',
'end',
'geometry h2o1',
'  O   -0.595   1.165  -0.048',
'  H    0.110   1.812  -0.170',
'  H   -1.452   1.598  -0.154',
'end',
'geometry h2o2',
'  O    0.724  -1.284   0.034',
'  H    0.175  -2.013   0.348',
'  H    0.177  -0.480   0.010',
'end',
]

BS_321G = [
'basis',
'  * library 3-21G',
'end',
]

BS_631GS = [
'basis',
' * library 6-31g*',
'end',
]

BS_631GSS = [
'basis',
'  * library 6-31G**',
'end',
]

HEMEBS = [
'basis',
'  O   library 6-31g*',
'  N   library 6-31g*',
'  C   library 6-31g*',
'  H   library 6-31g*',
'  Fe  library "Ahlrichs pVDZ"',
'end',
]

WATERDIMERTASK = [
'set geometry h2o1',
'scf; vectors input atomic output h2o1.movecs; end',
'task scf',
'set geometry h2o2',
'scf; vectors input atomic output h2o2.movecs; end',
'task scf',
'set geometry dimer',
'scf',
'vectors input fragment h2o1.movecs h2o2.movecs \\',
        'output dimer.movecs',
'end',
'task scf',
]

HEMETASK = [
'scf; thresh 1e-2; end',
'set geometry ring-only',
'scf; vectors atomic swap 80 81 output ring.mo; end',
'task scf',
'set geometry water-only',
'scf; vectors atomic output water.mo; end',
'task scf',
'set geometry imid-only',
'scf; vectors atomic output imid.mo; end',
'task scf',
'charge 3',
'set geometry fe-only',
'scf; sextet; vectors atomic output fe.mo; end',
'task scf',
'unset scf:*     # This restores the defaults',
'charge 1',
'set geometry full-system',
'scf',
'  sextet',
'  vectors fragment ring.mo imid.mo fe.mo water.mo',
'  maxiter 50',
'end',
'task scf',
]

COSMO = [
'dft',
  'xc m06-2x',
'end',
'',
'cosmo',
  'do_cosmo_smd true',
  'solvent water',
'end',
'task dft energy',
]

TDDFTFREQ = [
'dft',
'  xc hfexch',
'end',
'',
'tddft',
'  cis',
'  nroots 3',
'  notriplet',
'  target 1',
'  civecs',
'  grad',
'    root 1',
'  end',
'end',
'task tddft optimize',
'task tddft frequencies',
]

TDDFT = [
'tddft',
'  cis',
'  nroots 3',
'  notriplet',
'  target 1',
'  civecs',
'  grad',
'    root 1',
'  end',
'end',
'',
'task tddft energy',
]

CISTDDFTOPTFREQ = [
'dft',
'  xc hfexch',
'end',
'',
'tddft',
'  cis',
'  nroots 3',
'  notriplet',
'  target 1',
'  civecs',
'  grad',
'    root 1',
'  end',
'end',
'',
'task tddft optimize',
'task tddft frequencies',
]

PBEDFT = [
'dft',
'  direct',
'  xc pbe0',
'  iterations 200',
'end',
'',
'set dft:pstat t',
'set dft:staticguess t',
'task dft energy',
]

PBEQMD = [
'dft',
  'xc pbe0',
'end',
'',
'qmd',
  'nstep_nucl  2',
  'dt_nucl     10.0',
  'targ_temp   200.0',
  'com_step    10',
  'thermostat  svr 100.0',
  'print_xyz   5',
'end',
'',
'task dft qmd',
]

HFSCF = [
'scf',
'  singlet',
'  rhf',
'  maxiter 200',
'  direct',
'  thresh 1.0e-6',
'end',
'',
'task scf',
]

HFSCFOPT = [
'scf',
'  singlet',
'  rhf',
'  maxiter 200',
'  direct',
'  thresh 1.0e-6',
'end',
'',
'task scf optimize',
]

HFSCFOPTFREQ = [
'scf',
'  singlet',
'  rhf',
'  maxiter 200',
'  direct',
'  thresh 1.0e-6',
'end',
'',
'task scf optimize',
'task scf freq',
]

CCSD = [
'scf',
'  thresh 1.0e-8',
'  tol2e 1.0e-12',
'  singlet',
'  rhf',
'  maxiter 200',
'end',

'tce',
' freeze core',
' ccsd',
' nroots 3',
' thresh 1.0d-6',
'end',

'set tce:thresheom 1.0d-4',
'set tce:threshl 1.0d-3',
'task tce energy',
]

CISD = [
'scf',
'  thresh 1.0e-8',
'  tol2e 1.0e-12',
'  singlet',
'  rhf',
'  maxiter 200',
'end',
'',
'tce',
'  thresh 1.0d-5',
'  maxiter 200',
'  mbpt2',
'end',
'',
'task tce energy',
]
