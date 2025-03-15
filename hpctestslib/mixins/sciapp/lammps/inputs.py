# Copyright 2025 ETHZ/CSCS
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


LJ_CUTOFF = [
'variable	x index 1',
'variable	y index 1',
'variable	z index 1',
'',
'variable	xx equal 20*$x',
'variable	yy equal 20*$y',
'variable	zz equal 20*$z',
'',
'units		lj',
'atom_style	atomic',
'',
'lattice		fcc 0.8442',
'region		box block 0 ${xx} 0 ${yy} 0 ${zz}',
'create_box	1 box',
'create_atoms	1 box',
'mass		1 1.0',
'',
'velocity	all create 1.44 87287 loop geom',
'',
'pair_style	lj/cut 2.5',
'pair_coeff	1 1 1.0 1.0 2.5',
'',
'neighbor	0.3 bin',
'neigh_modify	delay 0 every 20 check no',
'',
'fix		1 all nve',
'',
'run		100',
]

CU_EAM = [
'variable	x index 1',
'variable	y index 1',
'variable	z index 1',
'',
'variable	xx equal 20*$x',
'variable	yy equal 20*$y',
'variable	zz equal 20*$z',
'',
'units		metal',
'atom_style	atomic',
'',
'lattice		fcc 3.615',
'region		box block 0 ${xx} 0 ${yy} 0 ${zz}',
'create_box	1 box',
'create_atoms	1 box',
'',
'pair_style	eam',
'pair_coeff	1 1 Cu_u3.eam',
'',
'velocity	all create 1600.0 376847 loop geom',
'',
'neighbor	1.0 bin',
'neigh_modify    every 1 delay 5 check yes',
'',
'fix		1 all nve',
'',
'timestep	0.005',
'thermo		50',
'',
'run		100',
]