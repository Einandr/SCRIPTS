import pandas as pd
import fileinput, glob, os
import re
import math
import matplotlib.pyplot as plt
import numpy as np
import pylab
from pathlib import Path

from utils import plot_result

verify_FLUENT = True
verify_QUBIQ = True
verify_gas = True

GOST = False



style_S = '-'
style_F = '-'
style_Q = '--'
line_width = 2

verify_sources = [verify_FLUENT, verify_QUBIQ]
number_of_sources = sum(verify_sources)

path_verification = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_VERIFICATION'
dir_verification = 'run'

if verify_FLUENT:
    path_fluent_particles_01 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_FLUENT\RESULTS\points_averaged_FLUENT_D0_G0_Y0_steady.csv'
    if verify_gas:
        path_fluent_gas_01 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_FLUENT\RESULTS\data_averaged_QUBIQ_D0_G0_Y0_steady.csv'

if verify_QUBIQ:
    path_qubiq_particles_01 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_FLUENT\RESULTS\points_averaged_QUBIQ_D0_G0_Y0_steady.csv'
    path_qubiq_particles_02 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_FLUENT\RESULTS\points_averaged_QUBIQ_D0_G0_Y0_transient.csv'
    if verify_gas:
        path_qubiq_gas_01 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_FLUENT\RESULTS\data_averaged_QUBIQ_D0_G0_Y0_steady.csv'
        path_qubiq_gas_02 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_FLUENT\RESULTS\data_averaged_QUBIQ_D0_G0_Y0_transient.csv'

# x_limit = 1
x_limit = 0.4

path_verification_current_run = ''.join((path_verification, '/', dir_verification))
Path(path_verification_current_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_verification_current_run)

if verify_FLUENT:
    df_fluent_particles_01 = pd.read_csv(path_fluent_particles_01, index_col='CoordinateX')
    if verify_gas:
        df_fluent_gas_01 = pd.read_csv(path_fluent_gas_01, index_col='CoordinateX')

if verify_QUBIQ:
    df_qubiq_particles_01 = pd.read_csv(path_qubiq_particles_01, index_col='CoordinateX')
    df_qubiq_particles_02 = pd.read_csv(path_qubiq_particles_02, index_col='CoordinateX')
    if verify_gas:
        df_qubiq_gas_01 = pd.read_csv(path_qubiq_gas_01, index_col='CoordinateX')
        df_qubiq_gas_02 = pd.read_csv(path_qubiq_gas_02, index_col='CoordinateX')


# n_particles = 2000
# ts_scale_factor = 1
#
# if verify_FLUENT:
#     df_fluent['Diameter'] = df_fluent['Diameter']*1e6
#
# if verify_QUBIQ:
#     df_qubiq_particles['Diameter'] = df_qubiq_particles['Diameter']*1e6

# if verify_SCRIPT:
#     df_script['p_Q[J]'] = df_script['p_Q[J]']*1e6*ts_scale_factor
#     df_script['p_dQ_vol_evap[J]'] = df_script['p_dQ_vol_evap[J]']*1e6*ts_scale_factor
#     df_script['p_dQ_comb_mass[J]'] = df_script['p_dQ_comb_mass[J]']*1e6*ts_scale_factor
#     df_script['p_dQ_comb_prelim[J]'] = df_script['p_dQ_comb_prelim[J]']*1e6*ts_scale_factor
#     df_script['p_dQ_comb_final[J]'] = df_script['p_dQ_comb_final[J]']*1e6*ts_scale_factor
#     df_script['p_dQ_convection[J]'] = df_script['p_dQ_convection[J]']*1e6*ts_scale_factor
#
#     df_script['g_dQ[J]'] = df_script['g_dQ[J]']*1e6*ts_scale_factor/n_particles
#     df_script['g_dQ_GV_mass[J]'] = df_script['g_dQ_GV_mass[J]']*1e6*ts_scale_factor
#     df_script['g_dQ_CPCF_mass[J]'] = df_script['g_dQ_CPCF_mass[J]']*1e6*ts_scale_factor
#     df_script['g_dQ_oxidizer_mass[J]'] = df_script['g_dQ_oxidizer_mass[J]']*1e6*ts_scale_factor
#     df_script['g_dQ_convection[J]'] = df_script['g_dQ_convection[J]']*1e6*ts_scale_factor
#     df_script['g_dQ_final_combustion[J]'] = df_script['g_dQ_final_combustion[J]']*1e6*ts_scale_factor
#     df_script['g_dQ_from_particle_limits[J]'] = df_script['g_dQ_from_particle_limits[J]']*1e6*ts_scale_factor
#     df_script['g_pressure[Pa]'] = 500000

# if verify_QUBIQ:
#     df_qubiq_particles['diameter'] = df_qubiq_particles['diameter']*1e6*ts_scale_factor
    # df_qubiq_particles['mass_volatile'] = df_qubiq_particles['mass'] * df_qubiq_particles['Y1']
    # df_qubiq_particles['mass_combustible'] = df_qubiq_particles['mass'] * df_qubiq_particles['Y2']
    # df_qubiq_particles['mass_inert'] = df_qubiq_particles['mass'] * df_qubiq_particles['Y3']

x_t_label = r'$X,\ м$'

# x_t_label = r'$\tau,\ с$'
y_Cp_label = r'$Cp\ (\frac{Дж}{кг \cdot К})$'
y_H_label = r'$H\ (\frac{Дж}{кг})$'


# plot_result(['p_density'], ['-'], [r'$плотность частицы\ \left[\frac{кг}{м^3}\right]$'], r'$\rho\ \left(\frac{кг}{м^3}\right)$', '04_p_density')

# QUBIQ - FLUENT
if verify_QUBIQ and verify_FLUENT:
    plot_result('01_p_D', x_t_label, r'$d,\ мкм$', (df_fluent_particles_01, ['Diameter'], [style_F], ['Fluent ST - диаметр частицы'], [0, 80], [0.2], [0.1], [0.1]),
                                                   (df_qubiq_particles_01, ['Diameter'], [style_Q], ['QUBIQ ST - диаметр частицы'], [0, 80], [0.4], [0.1], [0.1]),
                                                   (df_qubiq_particles_02, ['Diameter'], [style_Q], ['QUBIQ TR - диаметр частицы'], [0, 80], [0.4], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit])
    plot_result('02_p_T',x_t_label, r'$T,\ K$', (df_fluent_particles_01, ['Temperature'], [style_F], ['Fluent ST - температура частицы'], [400, 430], [0.2], [0.1], [-0.1]),
                                                (df_qubiq_particles_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура частицы'], [400, 430], [0.4], [0.1], [-0.1]),
                                                (df_qubiq_particles_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура частицы'], [400, 430], [0.4], [0.1], [-0.1]), GOST=GOST, x_limits=[0, x_limit])



    # plot_result('01_p_diameter', r'$d\ (мкм)$', ((df_fluent, ['p_diameter'], [style_F], ['Fluent - диаметр частицы'], [0, 80], [0.2], [0.1], [0.1]),
    #                                              (df_qubiq_particles, ['diameter'], [style_Q], ['QUBIQ - диаметр частицы'], [0, 80], [0.4], [0.1], [0.1])))
    # plot_result('02_p_mass', r'$m\ (кг)$', ((df_fluent, ['p_mass'], [style_F], [r'Fluent - масса частицы'], [0, 1.6e-10], [0.2], [0.1], [0.1]),
    #                                         (df_qubiq_particles, ['mass'], [style_Q], ['QUBIQ - масса частицы'], [0, 1.6e-10], [0.4], [0.1], [0.1])))
    # plot_result('03_p_mass_all', r'$m\ (кг)$', ((df_script, ['p_mass[kg]', 'p_mass_volatile[kg]', 'p_mass_combustible[kg]', 'p_mass_inert[kg]'], ['.', '-', '-', '-'], ['Скрипт - масса частицы', 'Скрипт - масса летучего компонента частицы', 'Скрипт - масса горючего компонента частицы', 'Скрипт - масса инертного компонента частицы']),
    #                                             (df_fluent, ['p_mass', 'p_mass_volatile', 'p_mass_combustible', 'p_mass_inert'], ['.', '-', '-', '-'], ['Fluent - масса частицы', 'Fluent - масса горючего летучего частицы', 'Fluent - масса горючего компонента частицы', 'Fluent - масса инертного компонента частицы'])))
    # plot_result('03_p_density', r'$\rho\ \left(\frac{кг}{м^3}\right)$', ((df_fluent, ['p_density'], [style_F], [r'Fluent - плотность частицы'], [550, 690], [0.2], [0.1], [-0.1]),
    #                                                                      (df_qubiq_particles, ['density'], [style_Q], ['QUBIQ - плотность частицы'], [550, 690], [0.4], [0.1], [-0.1])))
    # plot_result('04_pT', r'$T\ (K)$', ((df_fluent, ['p_temperature'], [style_F], [r'Fluent - температура частицы'], [290, 430], [0.2], [0.1], [-0.1]),
    #                                    (df_qubiq_particles, ['temperature'], [style_Q], ['QUBIQ - температура частицы'], [290, 430], [0.4], [0.1], [-0.1])))
    # plot_result('06_gT', r'$T\ (K)$', ((df_script, ['g_temperature[K]'], ['-'], ['QUBIQ - температура газа']),
    #                                    (df_fluent, ['g_temperature'], ['-'], [r'Fluent - температура газа'])))
    # plot_result('06_pT_gT', r'$T\ (K)$', ((df_script, ['p_temperature[K]', 'g_temperature[K]'], ['-', '-'], ['Скрипт - температура частицы', 'Скрипт - температура газа']),
    #                                       (df_fluent, ['p_temperature', 'g_temperature'], ['-', '-'], ['Fluent - температура частицы', 'Fluent - температура газа'])))
    # plot_result('07_pY', r'$Y$', ((df_script, ['p_Y_volatile', 'p_Y_combustible', 'p_Y_inert'], ['-', '-', '-'], ['Скрипт - массовая доля летучих', 'Скрипт - массовая доля горючих', 'Скрипт - массовая доля инертных']),
    #                               (df_fluent, ['p_Y_volatile', 'p_Y_combustible', 'p_Y_inert'], ['-', '-', '-'], ['Fluent - массовая доля летучих', 'Fluent - массовая доля горючих', 'Fluent - массовая доля инертных'])))
    # plot_result('08_gY', r'$Y$', ((df_script, ['g_Y_oxidizer', 'g_Y_volatile', 'g_Y_nitrogen', 'g_Y_CPCF'], ['o-', 'o-', 'o-', 'o-'], ['Скрипт - массовая доля O2', 'Скрипт - массовая доля летучего', 'Скрипт - массовая доля N2', 'Скрипт - массовая доля конечных продуктов окисления']),
    #                               (df_fluent, ['g_Y_O2', 'g_Y_GV', 'g_Y_N2', 'g_Y_CPCF'], ['-', '-', '-', '-'], ['Fluent - массовая доля O2', 'Fluent - массовая доля летучего', 'Fluent - массовая доля N2', 'Fluent - массовая доля конечных продуктов окисления'])))
    # plot_result('09_Gvol_Gcomb', r'$G\ \left(\frac{kg}{m^2 \cdot c}\right)$', ((df_script, ['G_vol[kg/m^2/s]', 'G_comb[kg/m^2/s]'], ['o-', 'o-'], ['Скрипт - массовый поток летучего', 'Скрипт - массовый поток горючего']),
    #                                                                            (df_fluent, ['G_vol', 'G_comb'], ['-', '-'], ['Fluent - массовый поток летучего', 'Fluent - массовый поток горючего'])))
    # plot_result('10_Theta', r'$\theta$', ((df_script, ['theta_vol', 'theta_comb'], ['-', '-'], ['Скрипт - к-т вдува летучего', 'Скрипт - к-т вдува горючего']),
    #                                       (df_fluent, ['theta_vol', 'theta_comb'], ['-', '-'], ['Fluent - к-т вдува летучего', 'Fluent - к-т вдува горючего'])))
    # plot_result('11_Y_surf', r'$Y_surf$', ((df_script, ['Y_surf_vol', 'Y_surf_comb'], ['o-', 'o-'], ['Скрипт - концентрация летучего GV у поверхности', 'Скрипт - концентрация О2 у поверхности']),
    #                                        (df_fluent, ['Y_surf_vol', 'Y_surf_comb'], ['-', '-'], ['Fluent - концентрация летучего GV у поверхности', 'Fluent - концентрация О2 у поверхности'])))
    # plot_result('12_pQ', r'$Q\ \left(Дж\right)$', ((df_script, ['p_dQ_vol_evap[J]', 'p_dQ_comb_mass[J]', 'p_dQ_comb_prelim[J]', 'p_dQ_comb_final[J]', 'p_dQ_convection[J]'], ['.', '.', '.', '.', '.'], ['Скрипт - p_dQ_vol_evap', 'Скрипт - p_dQ_comb_mass', 'Скрипт - p_dQ_comb_prelim', 'Скрипт - p_dQ_comb_final', 'Скрипт - p_dQ_convection']),
    #                                                (df_fluent, ['p_dQ_vol_evap', 'p_dQ_comb_mass', 'p_dQ_comb_prelim', 'p_dQ_comb_final', 'p_dQ_convection'], ['-', '-', '-', '-', '-'], ['Fluent - p_dQ_vol_evap', 'Fluent - p_dQ_comb_mass', 'Fluent - p_dQ_comb_prelim', 'Fluent - p_dQ_comb_final', 'Fluent - p_dQ_convection'])))
    # plot_result('13_gQ', r'$Q\ \left(Дж\right)$', ((df_script, ['g_dQ[J]', 'g_dQ_GV_mass[J]', 'g_dQ_CPCF_mass[J]', 'g_dQ_oxidizer_mass[J]', 'g_dQ_convection[J]', 'g_dQ_final_combustion[J]', 'g_dQ_from_particle_limits[J]'], ['.', '.', '.', '.', '.', '.', '.'], ['Скрипт - g_dQ', 'Скрипт - g_dQ_GV_mass', 'Скрипт - g_dQ_CPCF_mass', 'Скрипт - g_dQ_oxidizer_mass', 'Скрипт - g_dQ_convection', 'Скрипт - g_dQ_final_combustion', 'Скрипт - g_dQ_from_particle_limits']),
    #                                                (df_fluent, ['g_dQ', 'g_dQ_GV_mass', 'g_dQ_CPCF_mass', 'g_dQ_oxidizer_mass', 'g_dQ_convection', 'g_dQ_final_combustion', 'g_dQ_from_particle_limits'], ['-', '-', '-', '-', '-', '-', '-'], ['Fluent - g_dQ', 'Fluent - g_dQ_GV_mass', 'Fluent - g_dQ_CPCF_mass', 'Fluent - g_dQ_oxidizer_mass', 'Fluent - g_dQ_convection', 'Fluent - g_dQ_final_combustion', 'Fluent - g_dQ_from_particle_limits'])))
    # plot_result('14_pH', r'$H\ \left(\frac{Дж}{кг}\right)$', ((df_script, ['p_enthalpy[J/kg]'], ['-'], ['Скрипт - энтальпия частицы']),
    #                                                           (df_fluent, ['p_enthalpy'], ['-'], ['Fluent - энтальпия частицы'])))
    # plot_result('15_gH', r'$H\ \left(\frac{Дж}{кг}\right)$', ((df_script, ['g_enthalpy[J/kg]'], ['-'], ['Скрипт - энтальпия газа']),
    #                                                           (df_fluent, ['g_enthalpy'], ['-'], ['Fluent - энтальпия газа'])))
    # plot_result('16_dH', r'$dH\ \left(\frac{Дж}{кг}\right)$', ((df_script, ['dH_vol_evap[J/kg]', 'dH_comb_preliminary[J/kg]', 'dH_comb_final[J/kg]'], ['.', '.', '.'], ['Скрипт - тепловой эффект испарения', 'Скрипт - тепловой эффект сгорания первичных', 'Скрипт - тепловой эффект сгорания конечных']),
    #                                                           (df_fluent, ['dH_vol_evap', 'dH_comb_preliminary', 'dH_comb_final'], ['-', '-', '-'], ['Fluent - тепловой эффект испарения', 'Fluent - тепловой эффект сгорания первичных', 'Fluent - тепловой эффект сгорания конечных'])))
    # plot_result('17_k_comb', r'$H\ \left(\frac{с}{м}\right)$', ((df_script, ['k_comb[s/m]'], ['.'], ['Скрипт - k_comb']),
    #                                                             (df_fluent, ['k_comb'], ['-'], ['Fluent - k_comb'])))
    # plot_result('18_Y_comb', r'$Y$', ((df_script, ['Y_surf_comb', 'g_Y_oxidizer'], ['.', '.'], ['Скрипт - массовая доля O2 на поверхности', 'Скрипт - массовая доля O2']),
    #                                   (df_fluent, ['Y_surf_comb', 'g_Y_O2'], ['-', '-'], ['Fluent - массовая доля O2 на поверхности', 'Fluent - массовая доля O2'])))






# ГАЗ ТОЛЬКО
# if verify_QUBIQ and verify_FLUENT and verify_gas:
#     plot_result('05_gT', r'$T\ (K)$', ((df_fluent_gas_01, ['g_temperature'], [style_F], ['Fluent ST - температура газа'], [1800, 2000], [0.2], [0.1], [0.1]),
#                                        (df_qubiq_gas_01, ['temperature'], [style_Q], ['QUBIQ ST - температура газа'], [1800, 2000], [0.4], [0.1], [0.1]),
#                                        (df_qubiq_gas_02, ['temperature'], [style_Q], ['QUBIQ TR - температура газа'], [1800, 2000], [0.4], [0.1], [0.1])))
#     plot_result('06_pT_gT', r'$T\ (K)$', ((df_fluent, ['p_temperature', 'g_temperature'], [style_F, style_F], ['Fluent - температура частицы', 'Fluent - температура газа'], [1950, 1975], [0.2, 0.4], [0.1, 0.1], [-0.05, 0.01]),
#                                           (df_qubiq_particles, ['temperature'], [style_Q], [r'QUBIQ - температура частицы'], [1950, 1975], [0.1], [0.1], [-0.05]),
#                                           (df_qubiq_gas, ['temperature'], [style_Q], ['QUBIQ - температура газа'], [1950, 1975], [0.3], [0.1], [0.1])))
#     plot_result('08_gY', r'$Y$', ((df_fluent, ['g_Y_vap', 'g_Y_O2', 'g_Y_N2'], [style_F, style_F, style_F], ['Fluent - массовая доля н-гептана', 'Fluent - массовая доля O2', 'Fluent - массовая доля N2'], [0, 1], [0.1, 0.3, 0.5], [0.1, 0.1, 0.1], [0.2, 2, -0.2]),
#                                   (df_qubiq_gas, ['mass_fractions_C7H16_nheptane', 'mass_fractions_O2', 'mass_fractions_N2'], [style_Q, style_Q, style_Q], ['QUBIQ - массовая доля н-гептана', 'QUBIQ - массовая доля O2', 'QUBIQ - массовая доля N2'], [0, 1], [0.15, 0.35, 0.55], [0.1, 0.1, 0.1], [0.2, 30, -0.2])))
#     plot_result('06_gP', r'$P\ (Па)$', ((df_fluent, ['g_pressure'], [style_F], ['Fluent - давление газа'], [0, 1500000], [0.2], [0.1], [0.0005]),
#                                         (df_qubiq_gas, ['pressure'], [style_Q], ['QUBIQ - давление газа'], [0, 1500000], [0.3], [0.1], [0.0005])))



# ГАЗ и ЧАСТИЦЫ
if verify_gas:
    plot_result('03_gT', x_t_label, r'$T,\ K$', (df_fluent_gas_01, ['Temperature'], [style_F], ['Fluent ST - температура газа'], [1350, 2000], [0.2], [0.1], [0.1]),
                                                (df_qubiq_gas_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура газа'], [1350, 2000], [0.4], [0.1], [0.1]),
                                                (df_qubiq_gas_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура газа'], [1350, 2000], [0.4], [0.1], [0.1]))
    plot_result('04_pT_gT', x_t_label, r'$T\ (K)$', (df_fluent_particles_01, ['Temperature'], [style_F], ['Fluent ST - температура частицы'], [0, 2000], [0.2], [0.1], [0.5]),
                                                    (df_fluent_gas_01, ['Temperature'], [style_F], ['Fluent ST - температура газа'], [0, 2000], [0.4], [0.1], [-0.2]),
                                                    (df_qubiq_particles_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура частицы'], [0, 2000], [0.1], [0.1], [0.5]),
                                                    (df_qubiq_particles_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура частицы'], [0, 2000], [0.1], [0.1], [0.5]),
                                                    (df_qubiq_gas_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура газа'], [0, 2000], [0.3], [0.1], [-0.2]),
                                                    (df_qubiq_gas_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура газа'], [0, 2000], [0.3], [0.1], [-0.2]))
    plot_result('05_gY', x_t_label, r'$Y$', (df_fluent_gas_01, ['Y_c7h16', 'Y_o2', 'Y_n2'], [style_F, style_F, style_F], ['Fluent ST - массовая доля н-гептана', 'Fluent ST - массовая доля O2', 'Fluent ST - массовая доля N2'], [0, 0.8], [0.1, 0.3, 0.5], [0.1, 0.1, 0.1], [-0.2, 0.2, -0.2]),
                                            (df_qubiq_gas_01, ['Y_c7h16', 'Y_o2', 'Y_n2'], [style_Q, style_Q, style_Q], ['QUBIQ ST - массовая доля н-гептана', 'QUBIQ ST - массовая доля O2', 'QUBIQ ST - массовая доля N2'], [0, 0.8], [0.15, 0.35, 0.55], [0.1, 0.1, 0.1], [-0.2, 0.2, -0.2]),
                                            (df_qubiq_gas_02, ['Y_c7h16', 'Y_o2', 'Y_n2'], [style_Q, style_Q, style_Q], ['QUBIQ TR - массовая доля н-гептана', 'QUBIQ TR - массовая доля O2', 'QUBIQ TR - массовая доля N2'], [0, 0.8], [0.15, 0.35, 0.55], [0.1, 0.1, 0.1], [-0.2, 0.2, -0.2]))
    plot_result('06_gP', x_t_label, r'$P,\ Па$', (df_fluent_gas_01, ['Pressure'], [style_F], ['Fluent ST - давление газа'], [497000, 502000], [0.2], [0.1], [0.0005]),
                                                 (df_qubiq_gas_01, ['Pressure'], [style_Q], ['QUBIQ ST - давление газа'], [497000, 502000], [0.3], [0.1], [0.0005]),
                                                 (df_qubiq_gas_02, ['Pressure'], [style_Q], ['QUBIQ TR - давление газа'], [497000, 502000], [0.3], [0.1], [0.0005]))
    plot_result('07_gRho', x_t_label, r'$\rho,\ \frac{кг}{м^3}$', (df_fluent_gas_01, ['Density'], [style_F], ['Fluent ST - плотность газа'], [0.8, 1.5], [0.2], [0.1], [0.0005]),
                                                                  (df_qubiq_gas_01, ['Density'], [style_Q], ['QUBIQ ST - плотность газа'], [0.8, 1.5], [0.3], [0.1], [0.0005]),
                                                                  (df_qubiq_gas_02, ['Density'], [style_Q], ['QUBIQ TR - плотность газа'], [0.8, 1.5], [0.3], [0.1], [0.0005]))
    plot_result('08_gV', x_t_label, r'$v\ \frac{м}{с}$', (df_fluent_gas_01, ['Velocity'], [style_F], ['Fluent ST - скорость газа'], [40, 60], [0.2], [0.1], [0.0005]),
                                                         (df_qubiq_gas_01, ['Velocity'], [style_Q], ['QUBIQ ST - скорость газа'], [40, 60], [0.3], [0.1], [0.0005]),
                                                         (df_qubiq_gas_02, ['Velocity'], [style_Q], ['QUBIQ TR - скорость газа'], [40, 60], [0.3], [0.1], [0.0005]))








print('debug')







