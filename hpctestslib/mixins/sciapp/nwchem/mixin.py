# Copyright 2025-2026 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause


# import datetime
import os
import re
import sys

import reframe as rfm
import reframe.utility.sanity as sn
import reframe.utility as util

# Add the root directory of hpctestslib
prefix = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir, os.pardir])
)
if not prefix in sys.path:
    sys.path = [prefix] + sys.path


# import mixin as nwchem
import mixins.sciapp.nwchem.inputs as inputs


class nwchem_mixin(rfm.RegressionTestPlugin):
    '''
    Title: NHChem benchmarks mixin
    Description: This mixin provides functionality to write NHChem benchmarks.
    This mixin implements twelve different benchmarks:
    * bf_tddft_freq
    * cf3coo-_cosmo
    * heme6a1
    * water_dimer
    * glucose
    * glucose_ccsd
    * glucose_cosmo
    * glucose_dft
    * glucose_freq
    * glucose_opt
    * glucose_qmd
    * glucose_tddft

    The first four benchmarks listed above have been taken from the official
    NHChem documentation (https://nwchemgit.github.io). The remainder 8
    glucose-based benchmarks, I created myself.
    Who doesn't like to run some SCF on sugar, hum? (:

    Notes:
    * The computer does not require network access to run these tests because
    the input files are constructed before the simulations are executed.

    * Since this is a mixin, there is no definition of job parameters.
    These are expected to be set in the test that uses this mixin.

    * This mixin does not support, yet, any accelerated version of NWChem
    '''

    #: Parameter encoding the name of the benchmark to run
    #:
    #: :type: :class:`str`
    #: :values: ``['bf_tddft_freq', 'cf3coo-_cosmo', 'glucose', 'glucose_ccsd', 'glucose_cosmo', 'glucose_dft', 'glucose_freq', 'glucose_opt', 'glucose_qmd', 'glucose_tddft', 'heme6a1', 'water_dimer']``
    benchmark = parameter([
        'bf_tddft_freq',
        # 'cf3coo-_cosmo',
        'glucose',
        # 'glucose_ccsd',
        # 'glucose_cosmo',
        # 'glucose_dft',
        # 'glucose_freq',
        # 'glucose_opt',
        # 'glucose_qmd',
        # # 'glucose_tce', # TODO: run this simulation and add it to the list of values above
        # 'glucose_tddft',
        'heme6a1',
        # 'water_dimer',
    ])

    @run_after('init')
    def set_executable(self):
        self.executable = 'nwchem'

    @run_after('init')
    def set_tags(self):
        self.tags |= {'sciapp', 'chemistry'}


    @run_after('init')
    def set_descr(self):
        self.descr = f'NWCHEM {self.benchmark} benchmark'

    @run_before('run')
    def set_input_file(self):
        self.executable_opts += [f'{self.benchmark}.nw']

    @run_before('run')
    def set_keep_files(self):
        self.keep_files += [f'{self.benchmark}.nw']

    @run_before('run')
    def create_inpufile(self):
        create_fn_name = f'input_{util.toalphanum(self.benchmark).lower()}'
        create_input_fn = getattr(self, create_fn_name, None)
        sn.assert_true(
            create_input_fn is not None,
            msg=(f'cannot create input file for benchmark {self.benchmark!r}: '
                 f'please define a member function "{create_fn_name}()"')
        ).evaluate()

        input_file = os.path.join(sn.evaluate(self.stagedir),
                                  f'{self.benchmark}.nw')
        create_input_fn(input_file)

    def input_bf_tddft_freq(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='bf_tddft_freq',
                title='CIS/6-31G* BF optimization frequencies',
                geometry='\n'.join(inputs.BF),
                basis='\n'.join(inputs.BS_631GS),
                computation='\n'.join(inputs.CISTDDFTOPTFREQ),
            ))

    def input_cf3coo__cosmo(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='cf3coo__cosmo',
                title='M06-2X solvation free energy for CF3COO- in water',
                geometry='\n'.join(inputs.CF3COO_),
                basis='\n'.join(inputs.BS_631GS),
                computation='\n'.join(inputs.nwchem.COSMO),
            ))

    def input_glucose(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose',
                title='Hartree-Fock SCF Calculation on Alpha-D-Glucose',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.HFSCF),
            ))

    def input_glucose_ccsd(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose_ccsd',
                title='CCSD Calculation on Alpha-D-Glucose',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.CCSD),
            ))

    def input_glucose_cosmo(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose_cosmo',
                title='DFT M06-2x Calculation on Alpha-D-Glucose in COSMO water',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.COSMO),
            ))

    def input_glucose_dft(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose_dft',
                title='DFT PBE0 Calculation on Alpha-D-Glucose',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.PBEDFT),
            ))

    def input_glucose_freq(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose_freq',
                title='Hartree-Fock Opt and Freq Calculation on Alpha-D-Glucose',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.HFSCFOPTFREQ),
            ))

    def input_glucose_opt(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose_opt',
                title='Hartree-Fock Opt Calculation on Alpha-D-Glucose',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.HFSCFOPT),
            ))

    def input_glucose_qmd(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose_qmd',
                title='PBE0 QMD Calculation on Alpha-D-Glucose',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.PBEQMD),
            ))

    # # TODO: uncomment this function
    # def input_glucose_tce(self, input_file):
    #     with open(input_file, 'w') as f:
    #         f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
    #             name='glucose_tce',
    #             title='CISD Calculation on Alpha-D-Glucose',
    #             geometry='\n'.join(inputs.GLUCOSE),
    #             basis='\n'.join(inputs.BS_631GSS),
    #             computation='\n'.join(inputs.CISD),
    #         ))

    def input_glucose_tddft(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='glucose_tddft',
                title='TDDFT Calculation on Alpha-D-Glucose',
                geometry='\n'.join(inputs.GLUCOSE),
                basis='\n'.join(inputs.BS_631GSS),
                computation='\n'.join(inputs.TDDFT),
            ))

    def input_heme6a1(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='heme6a1',
                title='SCF based on Fragments Calculation on heme-H2O complex',
                geometry='\n'.join(inputs.HEME),
                basis='\n'.join(inputs.HEMEBS),
                computation='\n'.join(inputs.HEMETASK),
            ))

    def input_water_dimer(self, input_file):
        with open(input_file, 'w') as f:
            f.write(inputs.INPUT_FILE_TEMPLATE.safe_substitute(
                name='waterdimer',
                title='SCF based on Fragments Calculation on water dimer',
                geometry='\n'.join(inputs.WATERDIMER),
                basis='\n'.join(inputs.BS_321G),
                computation='\n'.join(inputs.WATERDIMERTASK),
            ))

    @performance_function('s')
    def perf(self):
        # Total times  cpu:        2.0s     wall:        3.6s
        return sn.extractsingle(r'Total\s+times\s+cpu:\s+\S+s\s+wall:\s+'
                                r'(?P<perf>\S+)s',
                                self.stdout, 'perf', float, -1)

    @deferrable
    def assert_bf_tddft_freq(self):
        # Convergence on energy requested:  1.00D-06
        ener_thres = sn.extractsingle(r'Convergence\s+on\s+energy\s+'
                                      r'requested:\s+(?P<thres>\S+)',
                                      self.stdout, 'thres',
                                      item=-1)

        ener_thres = sn.evaluate(ener_thres).replace('D', 'E')
        ener_thres = float(ener_thres)

        # Total DFT energy =     -124.098908887656
        total_dft_energy_start = sn.extractsingle(r'Total\s+DFT\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=0)
        ref_total_dft_energy_start = -124.098908887656
        thres_total_dft_energy_start = abs(ener_thres / ref_total_dft_energy_start)

        # Total DFT energy =     -124.100428853875
        total_dft_energy_end = sn.extractsingle(r'Total\s+DFT\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_dft_energy_end = -124.100428853875
        thres_total_dft_energy_end = abs(ener_thres / ref_total_dft_energy_end)

        # Ground state a1       -124.098908887656 a.u.
        ground_state_a1_start = sn.extractsingle(r'Ground\s+state\s+a1\s+'
                                                r'(?P<energy>\S+)',
                                                self.stdout, 'energy', float,
                                                item=0)
        ref_ground_state_a1_start = -124.098908887656
        thres_ground_state_a1_start = abs(ener_thres / ref_ground_state_a1_start)

        # Excited state energy =   -123.838371032320
        exc_state_ener_start = sn.extractsingle(r'Excited\s+state\s+energy\s+='
                                                r'\s+(?P<energy>\S+)',
                                                self.stdout, 'energy', float,
                                                item=0)
        ref_exc_state_ener_start = -123.838371032320
        thres_exc_state_ener_start = abs(ener_thres / ref_exc_state_ener_start)

        # Excited state energy =   -123.853064317425
        exc_state_ener_end = sn.extractsingle(r'Excited\s+state\s+energy\s+='
                                                r'\s+(?P<energy>\S+)',
                                                self.stdout, 'energy', float,
                                                item=-1)
        ref_exc_state_ener_end = -123.853064317425
        thres_exc_state_ener_end = abs(ener_thres / ref_exc_state_ener_end)

        # Total Entropy                    =   48.055 cal/mol-K
        total_entropy = sn.extractsingle(r'Total\s+Entropy\s+=\s+'
                                                r'(?P<energy>\S+)',
                                                self.stdout, 'energy', float,
                                                item=-1)
        ref_total_entropy = 48.055
        thres_total_entropy = abs(1E-3 / ref_total_entropy)

        return sn.all([
            sn.assert_reference(total_dft_energy_start, ref_total_dft_energy_start,
                                -thres_total_dft_energy_start, thres_total_dft_energy_start),
            sn.assert_reference(total_dft_energy_end, ref_total_dft_energy_end,
                                -thres_total_dft_energy_end, thres_total_dft_energy_end),
            sn.assert_reference(ground_state_a1_start, ref_ground_state_a1_start,
                                -thres_ground_state_a1_start, thres_ground_state_a1_start),
            sn.assert_eq(total_dft_energy_start, ground_state_a1_start,
                         msg=f'First ground state energy {total_dft_energy_start} different from the DFT energy {ground_state_a1_start}'),
            sn.assert_reference(exc_state_ener_start, ref_exc_state_ener_start,
                                -thres_exc_state_ener_start, thres_exc_state_ener_start),
            sn.assert_reference(exc_state_ener_end, ref_exc_state_ener_end,
                                -thres_exc_state_ener_end, thres_exc_state_ener_end),
            sn.assert_found('Vibrational analysis via the FX method', self.stdout),
            sn.assert_found('Linear Molecule', self.stdout),
            sn.assert_reference(total_entropy, ref_total_entropy,
                                -thres_total_entropy, thres_total_entropy),
        ])

    @deferrable
    def assert_cf3coo__cosmo(self):
        # Convergence on energy requested:  1.00D-06
        ener_thres = sn.extractsingle(r'Convergence\s+on\s+energy\s+'
                                      r'requested:\s+(?P<thres>\S+)',
                                      self.stdout, 'thres',
                                      item=-1)

        ener_thres = sn.evaluate(ener_thres).replace('D', 'E')
        ener_thres = float(ener_thres)

        # Total DFT energy =     -526.161913505093
        total_dft_energy = sn.extractsingle(r'Total\s+DFT\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_dft_energy = -526.161913505093
        thres_total_dft_energy = abs(ener_thres / ref_total_dft_energy)

        # COSMO energy =       10.391162812557
        cosmo_energy = sn.extractsingle(r'COSMO\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_cosmo_energy = 10.391162812557
        thres_cosmo_energy = abs(ener_thres / ref_cosmo_energy)

        #  delta internal energy  =         0.002297456656
        delta_internal_ener = sn.extractsingle(r'delta\s+internal\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_delta_internal_ener = 0.002297456656
        thres_delta_internal_ener = abs(ener_thres / ref_delta_internal_ener)

        # dielectric constant -eps-     =  78.40
        dielectric_const = sn.extractsingle(r'dielectric\s+constant\s+-eps-\s+=\s+'
                                            r'(?P<const>\S+)',
                                            self.stdout, 'const', float)
        ref_dielectric_const = 78.40

        return sn.all([
            sn.assert_reference(total_dft_energy, ref_total_dft_energy,
                                -thres_total_dft_energy, thres_total_dft_energy),
            sn.assert_reference(cosmo_energy, ref_cosmo_energy,
                                -thres_cosmo_energy, thres_cosmo_energy),
            sn.assert_reference(delta_internal_ener, ref_delta_internal_ener,
                                -thres_delta_internal_ener, thres_delta_internal_ener),
            sn.assert_eq(dielectric_const, ref_dielectric_const,
                         msg=f'Dielectric constant is not {ref_dielectric_const}')
        ])

    @deferrable
    def assert_glucose(self):
        # Convergence threshold     :          1.000E-06
        ener_thres = sn.extractsingle(r'Convergence\s+threshold\s+:\s+'
                                      r'(?P<thres>\S+)',
                                      self.stdout, 'thres', float,
                                      item=-1)


        # Total SCF energy =   -683.365261303407
        total_scf_energy = sn.extractsingle(r'Total\s+SCF\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_scf_energy = -683.365261303407
        thres_total_scf_energy = abs(ener_thres / ref_total_scf_energy)

        # One-electron energy =   -2607.299805379243
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -2607.299805379243
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Two-electron energy =     1084.575687920973
        two_e_energy = sn.extractsingle(r'Two-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_two_e_energy = 1084.575687920973
        thres_two_e_energy = abs(ener_thres / ref_two_e_energy)

        # Nuclear repulsion energy =     839.358856154863
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 839.358856154863
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        return sn.all([
            sn.assert_reference(total_scf_energy, ref_total_scf_energy,
                                -thres_total_scf_energy, thres_total_scf_energy),
            sn.assert_reference(one_e_energy, ref_one_e_energy,
                                -thres_one_e_energy, thres_one_e_energy),
            sn.assert_reference(two_e_energy, ref_two_e_energy,
                                -thres_two_e_energy, thres_two_e_energy),
            sn.assert_reference(nuc_rep_energy, ref_nuc_rep_energy,
                                -thres_nuc_rep_energy, thres_nuc_rep_energy),
        ])

    @deferrable
    def assert_glucose_ccsd(self):
        return True

    # TODO: check the unused variables in this function
    @deferrable
    def assert_glucose_cosmo(self):
        # Convergence on energy requested:  1.00D-06
        ener_thres = sn.extractsingle(r'Convergence\s+on\s+energy\s+'
                                      r'requested:\s+(?P<thres>\S+)',
                                      self.stdout, 'thres',
                                      item=-1)

        ener_thres = sn.evaluate(ener_thres).replace('D', 'E')
        ener_thres = float(ener_thres)

        # Total DFT energy =      -686.949838350192
        total_dft_energy = sn.extractsingle(r'Total\s+DFT\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_dft_energy = -686.949838350192
        thres_total_dft_energy = abs(ener_thres / ref_total_dft_energy)

        # One-electron energy =   -2608.958022321022
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -2608.958022321022
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Coulomb energy =     1170.814029607174
        coul_energy = sn.extractsingle(r'Coulomb\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_coul_energy = 1170.814029607174
        thres_coul_energy = abs(ener_thres / ref_coul_energy)

        # Exchange-Corr. energy =      -88.647358711313
        exchange_corr = sn.extractsingle(r'Exchange-Corr.\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_exchange_corr = -88.647358711313
        thres_exchange_corr = abs(ener_thres / ref_exchange_corr)

        # Nuclear repulsion energy =     839.358856154863
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 839.358856154863
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        # COSMO energy =       0.482656920106
        cosmo_energy = sn.extractsingle(r'COSMO\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_cosmo_energy = 0.482656920106
        thres_cosmo_energy = abs(ener_thres / ref_cosmo_energy)

        #  delta internal energy  =         0.007176549622
        delta_internal_ener = sn.extractsingle(r'delta\s+internal\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_delta_internal_ener = 0.007176549622
        thres_delta_internal_ener = abs(ener_thres / ref_delta_internal_ener)

        # dielectric constant -eps-     =  78.40
        dielectric_const = sn.extractsingle(r'dielectric\s+constant\s+-eps-\s+=\s+'
                                            r'(?P<const>\S+)',
                                            self.stdout, 'const', float)
        ref_dielectric_const = 78.40

        return sn.all([
            sn.assert_reference(total_dft_energy, ref_total_dft_energy,
                                -thres_total_dft_energy, thres_total_dft_energy),
            sn.assert_reference(cosmo_energy, ref_cosmo_energy,
                                -thres_cosmo_energy, thres_cosmo_energy),
            sn.assert_reference(delta_internal_ener, ref_delta_internal_ener,
                                -thres_delta_internal_ener, thres_delta_internal_ener),
            sn.assert_eq(dielectric_const, ref_dielectric_const,
                         msg=f'Dielectric constant is not {ref_dielectric_const}')
        ])

    @deferrable
    def assert_glucose_dft(self):
        # Convergence on energy requested:  1.00D-06
        ener_thres = sn.extractsingle(r'Convergence\s+on\s+energy\s+'
                                      r'requested:\s+(?P<thres>\S+)',
                                      self.stdout, 'thres',
                                      item=-1)

        ener_thres = sn.evaluate(ener_thres).replace('D', 'E')
        ener_thres = float(ener_thres)

        # Total DFT energy =      -686.440956331395
        total_dft_energy = sn.extractsingle(r'Total\s+DFT\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_dft_energy = -686.440956331395
        thres_total_dft_energy = abs(ener_thres / ref_total_dft_energy)

        # One-electron energy =   -2608.477645956119
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -2608.477645956119
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Coulomb energy =     1170.815188573782
        coul_energy = sn.extractsingle(r'Coulomb\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_coul_energy = 1170.815188573782
        thres_coul_energy = abs(ener_thres / ref_coul_energy)

        # Exchange-Corr. energy =      -88.137355103922
        exchange_corr = sn.extractsingle(r'Exchange-Corr.\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_exchange_corr = -88.137355103922
        thres_exchange_corr = abs(ener_thres / ref_exchange_corr)

        # Nuclear repulsion energy =     839.358856154863
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 839.358856154863
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        return sn.all([
            sn.assert_reference(total_dft_energy, ref_total_dft_energy,
                                -thres_total_dft_energy, thres_total_dft_energy),
            sn.assert_reference(one_e_energy, ref_one_e_energy,
                                -thres_one_e_energy, thres_one_e_energy),
            sn.assert_reference(coul_energy, ref_coul_energy,
                                -thres_coul_energy, thres_coul_energy),
            sn.assert_reference(exchange_corr, ref_exchange_corr,
                                -thres_exchange_corr, thres_exchange_corr),
            sn.assert_reference(nuc_rep_energy, ref_nuc_rep_energy,
                                -thres_nuc_rep_energy, thres_nuc_rep_energy),
        ])

    @deferrable
    def assert_glucose_freq(self):
        # Convergence threshold     :          1.000E-06
        ener_thres = sn.extractsingle(r'Convergence\s+threshold\s+:\s+'
                                      r'(?P<thres>\S+)',
                                      self.stdout, 'thres', float,
                                      item=-1)


        # Total SCF energy =   -683.365261303407
        total_scf_energy = sn.extractsingle(r'Total\s+SCF\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_scf_energy = -683.365261303407
        thres_total_scf_energy = abs(ener_thres / ref_total_scf_energy)

        # One-electron energy =   -2607.299805379243
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -2607.299805379243
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Two-electron energy =     1084.575687920973
        two_e_energy = sn.extractsingle(r'Two-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_two_e_energy = 1084.575687920973
        thres_two_e_energy = abs(ener_thres / ref_two_e_energy)

        # Nuclear repulsion energy =     839.358856154863
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 839.358856154863
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        # I know, I know we are not in a minimum.
        # All the frequencies have to be positive, but I am not doing science
        # with this geometry. I just need to find out if NWChem is working properly
        # My Quantum Chemistry professors would kill me now. Shame on me!
        #  Frequency         -1.38       -1.20       -0.78        0.26        0.77        1.19
        #  Frequency         78.38       96.46      126.19      162.41      225.58      260.42
        #  Frequency        267.43      280.50      291.72      339.60      362.98      394.08
        #  Frequency        405.54      425.18      443.16      464.15      467.51      500.26
        #  Frequency        589.80      610.48      654.83      702.71      847.50      932.39
        #  Frequency       1003.80     1082.06     1142.41     1159.06     1171.65     1175.01
        #  Frequency       1200.90     1222.77     1240.50     1260.34     1266.25     1270.83
        #  Frequency       1288.70     1341.32     1361.10     1383.99     1387.67     1417.83
        #  Frequency       1439.52     1491.89     1504.18     1512.77     1530.78     1537.09
        #  Frequency       1558.28     1564.57     1581.33     1588.00     1605.82     1641.42
        #  Frequency       3117.82     3156.14     3204.08     3221.96     3239.87     3265.77
        #  Frequency       3269.19     4144.68     4158.18     4163.37     4165.07     4180.19
        frequencies = sn.findall(r'^\s+Frequency\s+(?P<all>(?:\s+(?P<one>\S+))'
                                 r'{6})$',
                                self.stdout)

        freqs_one = re.findall(r"(?P<one>\S+)",
                               sn.evaluate(frequencies[0]).group("all"))

        freqs_last = re.findall(r"(?P<one>\S+)",
                               sn.evaluate(frequencies[-1]).group("all"))

        # We could check all numbers, but a few checks should suffice
        ref_freqs_one = set(['-1.38', '-1.20', '-0.78', '0.26', '0.77', '1.19'])
        ref_freqs_last = set(['3269.19', '4144.68', '4158.18', '4163.37', '4165.07', '4180.19'])

        diff_freqs_one = ref_freqs_one.difference(set(freqs_one))
        diff_freqs_last = ref_freqs_last.difference(set(freqs_last))

        return sn.all([
            sn.assert_reference(total_scf_energy, ref_total_scf_energy,
                                -thres_total_scf_energy, thres_total_scf_energy),
            sn.assert_reference(one_e_energy, ref_one_e_energy,
                                -thres_one_e_energy, thres_one_e_energy),
            sn.assert_reference(two_e_energy, ref_two_e_energy,
                                -thres_two_e_energy, thres_two_e_energy),
            sn.assert_reference(nuc_rep_energy, ref_nuc_rep_energy,
                                -thres_nuc_rep_energy, thres_nuc_rep_energy),
            sn.assert_eq(sn.count(frequencies), 12,
                         msg='Could not find all the 72 frequencies'),
            sn.assert_false(diff_freqs_one,
                            msg=f'Found frequencies {diff_freqs_one} that were '
                                 'not supposed to be there'),
            sn.assert_false(diff_freqs_last,
                            msg=f'Found frequencies {diff_freqs_last} that were '
                                 'not supposed to be there'),
        ])

    @deferrable
    def assert_glucose_opt(self):
        # Convergence threshold     :          1.000E-06
        ener_thres = sn.extractsingle(r'Convergence\s+threshold\s+:\s+'
                                      r'(?P<thres>\S+)',
                                      self.stdout, 'thres', float,
                                      item=-1)

        # Total SCF energy =   -683.365261338948
        total_scf_energy = sn.extractsingle(r'Total\s+SCF\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_scf_energy = -683.365261338948
        thres_total_scf_energy = abs(ener_thres / ref_total_scf_energy)

        # One-electron energy =   -2607.302073824297
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -2607.302073824297
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Two-electron energy =     1084.576726849307
        two_e_energy = sn.extractsingle(r'Two-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_two_e_energy = 1084.576726849307
        thres_two_e_energy = abs(ener_thres / ref_two_e_energy)

        # Nuclear repulsion energy =     839.360085636041
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 839.360085636041
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        return sn.all([
            sn.assert_reference(total_scf_energy, ref_total_scf_energy,
                                -thres_total_scf_energy, thres_total_scf_energy),
            sn.assert_reference(one_e_energy, ref_one_e_energy,
                                -thres_one_e_energy, thres_one_e_energy),
            sn.assert_reference(two_e_energy, ref_two_e_energy,
                                -thres_two_e_energy, thres_two_e_energy),
            sn.assert_reference(nuc_rep_energy, ref_nuc_rep_energy,
                                -thres_nuc_rep_energy, thres_nuc_rep_energy),
        ])

    @deferrable
    def assert_glucose_qmd(self):
        # Convergence on energy requested:  1.00D-06
        ener_thres = sn.extractsingle(r'Convergence\s+on\s+energy\s+'
                                      r'requested:\s+(?P<thres>\S+)',
                                      self.stdout, 'thres',
                                      item=-1)

        ener_thres = sn.evaluate(ener_thres).replace('D', 'E')
        ener_thres = float(ener_thres)

        # Total DFT energy =      -686.440956335001
        total_dft_energy = sn.extractsingle(r'Total\s+DFT\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_dft_energy = -686.440956335001
        thres_total_dft_energy = abs(ener_thres / ref_total_dft_energy)

        # One-electron energy =   -2608.477631366763
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -2608.477631366763
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Coulomb energy =     1170.815171236917
        coul_energy = sn.extractsingle(r'Coulomb\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_coul_energy = 1170.815171236917
        thres_coul_energy = abs(ener_thres / ref_coul_energy)

        # Exchange-Corr. energy =      -88.137352360019
        exchange_corr = sn.extractsingle(r'Exchange-Corr.\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_exchange_corr = -88.137352360019
        thres_exchange_corr = abs(ener_thres / ref_exchange_corr)

        # Nuclear repulsion energy =     839.358856154863
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 839.358856154863
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        # this is an arbritary number I have defined
        qmd_prop_prec = 1e-4

        # Kin. energy (a.u.):        1            0.020377
        kin_ene_step1 = sn.extractsingle(r'Kin.\s+energy\s+\(a.u.\)):\s+1\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_kin_ene_step1 = 0.020377
        thres_kin_ene_step1 = abs(qmd_prop_prec / ref_kin_ene_step1)

        # Pot. energy (a.u.):        1         -686.441152
        pot_ene_step1 = sn.extractsingle(r'Pot.\s+energy\s+\(a.u.\)):\s+1\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_pot_ene_step1 = -686.441152
        thres_pot_ene_step1 = abs(qmd_prop_prec / ref_pot_ene_step1)

        # Tot. energy (a.u.):        1         -686.420775
        tot_ene_step1 = sn.extractsingle(r'Tot.\s+energy\s+\(a.u.\)):\s+1\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_tot_ene_step1 = -686.420775
        thres_tot_ene_step1 = abs(qmd_prop_prec / ref_tot_ene_step1)

        # Kin. energy (a.u.):        2            0.020121
        kin_ene_step2 = sn.extractsingle(r'Kin.\s+energy\s+\(a.u.\)):\s+2\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_kin_ene_step2 = 0.020121
        thres_kin_ene_step2 = abs(qmd_prop_prec / ref_kin_ene_step2)

        # Pot. energy (a.u.):        2         -686.441302
        pot_ene_step2 = sn.extractsingle(r'Pot.\s+energy\s+\(a.u.\)):\s+2\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_pot_ene_step2 = -686.441302
        thres_pot_ene_step2 = abs(qmd_prop_prec / ref_pot_ene_step2)

        # Tot. energy (a.u.):        2         -686.421181
        tot_ene_step2 = sn.extractsingle(r'Tot.\s+energy\s+\(a.u.\)):\s+2\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_tot_ene_step2 = -686.421181
        thres_tot_ene_step2 = abs(qmd_prop_prec / ref_tot_ene_step2)

        return sn.all([
            sn.assert_reference(total_dft_energy, ref_total_dft_energy,
                                -thres_total_dft_energy, thres_total_dft_energy),
            sn.assert_reference(one_e_energy, ref_one_e_energy,
                                -thres_one_e_energy, thres_one_e_energy),
            sn.assert_reference(coul_energy, ref_coul_energy,
                                -thres_coul_energy, thres_coul_energy),
            sn.assert_reference(exchange_corr, ref_exchange_corr,
                                -thres_exchange_corr, thres_exchange_corr),
            sn.assert_reference(nuc_rep_energy, ref_nuc_rep_energy,
                                -thres_nuc_rep_energy, thres_nuc_rep_energy),
            sn.assert_reference(kin_ene_step1, ref_kin_ene_step1,
                                -thres_kin_ene_step1, thres_kin_ene_step1),
            sn.assert_reference(pot_ene_step1, ref_pot_ene_step1,
                                -thres_pot_ene_step1, thres_pot_ene_step1),
            sn.assert_reference(tot_ene_step1, ref_tot_ene_step1,
                                -thres_tot_ene_step1, thres_tot_ene_step1),
            sn.assert_reference(kin_ene_step2, ref_kin_ene_step2,
                                -thres_kin_ene_step2, thres_kin_ene_step2),
            sn.assert_reference(pot_ene_step2, ref_pot_ene_step2,
                                -thres_pot_ene_step2, thres_pot_ene_step2),
            sn.assert_reference(tot_ene_step2, ref_tot_ene_step2,
                                -thres_tot_ene_step2, thres_tot_ene_step2),
        ])

    # # TODO: write the sanity function
    # @deferrable
    # def assert_glucose_tce(self):
    #     return True

    @deferrable
    def assert_glucose_tddft(self):
        # Convergence on energy requested:  1.00D-06
        ener_thres = sn.extractsingle(r'Convergence\s+on\s+energy\s+'
                                      r'requested:\s+(?P<thres>\S+)',
                                      self.stdout, 'thres',
                                      item=-1)

        ener_thres = sn.evaluate(ener_thres).replace('D', 'E')
        ener_thres = float(ener_thres)

        # Total DFT energy =      -681.838002892225
        total_dft_energy = sn.extractsingle(r'Total\s+DFT\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_dft_energy = -681.838002892225
        thres_total_dft_energy = abs(ener_thres / ref_total_dft_energy)

        # One-electron energy =   -2608.211733648903
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -2608.211733648903
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Coulomb energy =     1170.306810114574
        coul_energy = sn.extractsingle(r'Coulomb\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_coul_energy = 1170.306810114574
        thres_coul_energy = abs(ener_thres / ref_coul_energy)

        # Exchange-Corr. energy =      -83.291935512760
        exchange_corr = sn.extractsingle(r'Exchange-Corr.\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_exchange_corr = -83.291935512760
        thres_exchange_corr = abs(ener_thres / ref_exchange_corr)

        # Nuclear repulsion energy =     839.358856154863
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 839.358856154863
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        # this is an arbritary number I have defined
        tddft_prec = 1e-3

        # Root   1 singlet a              0.221049320 a.u.                6.0151 eV
        root_one_ene = sn.extractsingle(r'Root\s+1\s+singlet\s+a\s+\S+\s+\S+\s+'
                                        r'(?P<energy>\S+)\s+eV',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_root_one_ene = 6.0151
        thres_root_one_ene = abs(tddft_prec / ref_root_one_ene)

        # Root   2 singlet a              0.232001505 a.u.                6.3131 eV
        root_two_ene = sn.extractsingle(r'Root\s+2\s+singlet\s+a\s+\S+\s+\S+\s+'
                                         r'(?P<energy>\S+)\s+eV',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_root_two_ene = 6.3131
        thres_root_two_ene = abs(tddft_prec / ref_root_two_ene)

        # Root   3 singlet a              0.238526339 a.u.                6.4906 eV
        root_three_ene = sn.extractsingle(r'Root\s+3\s+singlet\s+a\s+\S+\s+\S+\s+'
                                         r'(?P<energy>\S+)\s+eV',
                                        self.stdout, 'energy', float,
                                        item=0)
        ref_root_three_ene = 6.4906
        thres_root_three_ene = abs(tddft_prec / ref_root_three_ene)

        return sn.all([
            sn.assert_reference(total_dft_energy, ref_total_dft_energy,
                                -thres_total_dft_energy, thres_total_dft_energy),
            sn.assert_reference(one_e_energy, ref_one_e_energy,
                                -thres_one_e_energy, thres_one_e_energy),
            sn.assert_reference(coul_energy, ref_coul_energy,
                                -thres_coul_energy, thres_coul_energy),
            sn.assert_reference(exchange_corr, ref_exchange_corr,
                                -thres_exchange_corr, thres_exchange_corr),
            sn.assert_reference(nuc_rep_energy, ref_nuc_rep_energy,
                                -thres_nuc_rep_energy, thres_nuc_rep_energy),
            sn.assert_reference(root_one_ene, ref_root_one_ene,
                                -thres_root_one_ene, thres_root_one_ene),
            sn.assert_reference(root_two_ene, ref_root_two_ene,
                                -thres_root_two_ene, thres_root_two_ene),
            sn.assert_reference(root_three_ene, ref_root_three_ene,
                                -thres_root_three_ene, thres_root_three_ene),
        ])

    @deferrable
    def assert_heme6a1(self):
        # Convergence threshold     :          1.000E-02
        ener_thres = sn.extractsingle(r'Convergence\s+threshold\s+:\s+'
                                      r'(?P<thres>\S+)',
                                      self.stdout, 'thres', float,
                                      item=-1)

        # Total SCF energy =  -2545.183109542068
        total_scf_energy = sn.extractsingle(r'Total\s+SCF\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_scf_energy = -2545.183109542068
        thres_total_scf_energy = abs(ener_thres / ref_total_scf_energy)

        # wavefunction    = RHF
        wave_fnc_type_start = sn.extractsingle(r'wavefunction\s+=\s+'
                                               r'(?P<wavefn>\S+)',
                                               self.stdout, 'wavefn',
                                               item=0)

        # wavefunction    = ROHF
        wave_fnc_type_end = sn.extractsingle(r'wavefunction\s+=\s+'
                                             r'(?P<wavefn>\S+)',
                                             self.stdout, 'wavefn',
                                             item=-1)

        return sn.all([
            sn.assert_reference(total_scf_energy, ref_total_scf_energy,
                                -thres_total_scf_energy, thres_total_scf_energy),
            sn.assert_eq(wave_fnc_type_start, 'RHF',
                         msg='Wavefunction for the first method is not RHF'),
            sn.assert_eq(wave_fnc_type_end, 'ROHF',
                         msg='Wavefunction for the last method is not ROHF'),
            sn.assert_found('Final ROHF results', self.stdout),
            sn.assert_found('Final eigenvalues', self.stdout),
        ])

    @deferrable
    def assert_water_dimer(self):
        # Convergence threshold     :          1.000E-04
        ener_thres = sn.extractsingle(r'Convergence\s+threshold\s+:\s+'
                                      r'(?P<thres>\S+)',
                                      self.stdout, 'thres', float,
                                      item=-1)

        # Total SCF energy =   -151.187952037914
        total_scf_energy = sn.extractsingle(r'Total\s+SCF\s+energy\s+=\s+'
                                            r'(?P<energy>\S+)',
                                            self.stdout, 'energy', float,
                                            item=-1)
        ref_total_scf_energy = -151.1879
        thres_total_scf_energy = abs(ener_thres / ref_total_scf_energy)

        # One-electron energy =   -283.055720556525
        one_e_energy = sn.extractsingle(r'One-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_one_e_energy = -283.0557
        thres_one_e_energy = abs(ener_thres / ref_one_e_energy)

        # Two-electron energy =     94.692634711216
        two_e_energy = sn.extractsingle(r'Two-electron\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_two_e_energy = 94.6926
        thres_two_e_energy = abs(ener_thres / ref_two_e_energy)

        # Nuclear repulsion energy =     37.175133807395
        nuc_rep_energy = sn.extractsingle(r'Nuclear\s+repulsion\s+energy\s+=\s+'
                                        r'(?P<energy>\S+)',
                                        self.stdout, 'energy', float,
                                        item=-1)
        ref_nuc_rep_energy = 37.1751
        thres_nuc_rep_energy = abs(ener_thres / ref_nuc_rep_energy)

        return sn.all([
            sn.assert_reference(total_scf_energy, ref_total_scf_energy,
                                -thres_total_scf_energy, thres_total_scf_energy),
            sn.assert_reference(one_e_energy, ref_one_e_energy,
                                -thres_one_e_energy, thres_one_e_energy),
            sn.assert_reference(two_e_energy, ref_two_e_energy,
                                -thres_two_e_energy, thres_two_e_energy),
            sn.assert_reference(nuc_rep_energy, ref_nuc_rep_energy,
                                -thres_nuc_rep_energy, thres_nuc_rep_energy),
        ])

    @sanity_function
    def assert_sanity(self):
        '''Assert that the obtained energy meets the benchmark tolerances.'''

        assert_fn_name = f'assert_{util.toalphanum(self.benchmark).lower()}'
        assert_fn = getattr(self, assert_fn_name, None)
        sn.assert_true(
            assert_fn is not None,
            msg=(f'cannot extract energy from benchmark {self.benchmark!r}: '
                 f'please define a member function "{assert_fn_name}()"')
        ).evaluate()
        return sn.chain(
               sn.assert_found('CITATION', self.stdout),
               sn.assert_not_found('Segmentation fault', self.stderr),
               assert_fn(),
            )
