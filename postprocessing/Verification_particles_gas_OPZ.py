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

GOST = True



style_Q = '-'
style_F = '--'

line_width = 2

verify_sources = [verify_FLUENT, verify_QUBIQ]
number_of_sources = sum(verify_sources)

path_verification = r'D:\YASIM\VORON\2026_01_OPZ\verification_hot'
dir_verification = 'run'

if verify_QUBIQ:
    path_qubiq_particles_01 = r'D:\YASIM\VORON\2026_01_OPZ\results_hot\qubiq\3mm_pmfr_0.005_RANS\points_averaged_QUBIQ.csv'
if verify_gas:
    path_qubiq_gas_01 = r'D:\YASIM\VORON\2026_01_OPZ\results_hot\qubiq\3mm_pmfr_0.005_RANS\data_averaged_QUBIQ_3D.csv'

if verify_FLUENT:
    path_fluent_particles_01 = r'D:\YASIM\VORON\2026_01_OPZ\results_hot\fluent\3mm_pmfr_0.005_SST\points_averaged_FLUENT.csv'
if verify_gas:
    path_fluent_gas_01 = r'D:\YASIM\VORON\2026_01_OPZ\results_hot\fluent\3mm_pmfr_0.005_SST\data_averaged_FLUENT_3D.csv'


# y_limits = {
#     'Temperature': [2000, 2100],
#     'Pressure': [500000, 503000],
#     'Velocity': [0, 20],
#     'Y_Air': [0, 1],
#     'Y_CP': [0, 1],
#     'turbulent_kinetic_energy': [0, 0.3],
#     'specific_dissipation_rate': [0, 4000]
# }

y_limits = {
    'Temperature': [2000, 2800],
    'Pressure': [500000, 504000],
    'Velocity': [0, 25],
    'Y_Air': [0, 1],
    'Y_CP': [0, 1],
    'turbulent_kinetic_energy': [0, 0.5],
    'specific_dissipation_rate': [0, 5000]
}

x_limit = 1
# x_limit = 0.4

path_verification_current_run = ''.join((path_verification, '/', dir_verification))
Path(path_verification_current_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_verification_current_run)

if verify_FLUENT:
    df_fluent_particles_01 = pd.read_csv(path_fluent_particles_01, index_col='CoordinateX')

if verify_gas:
    df_fluent_gas_01 = pd.read_csv(path_fluent_gas_01, index_col='CoordinateX')

if verify_QUBIQ:
    df_qubiq_particles_01 = pd.read_csv(path_qubiq_particles_01, index_col='CoordinateX')

if verify_gas:
    df_qubiq_gas_01 = pd.read_csv(path_qubiq_gas_01, index_col='CoordinateX')


# n_particles = 2000
# ts_scale_factor = 1
#
if verify_FLUENT:
    df_fluent_particles_01['Diameter'] = df_fluent_particles_01['Diameter']*1e6

if verify_QUBIQ:
    df_qubiq_particles_01['Diameter'] = df_qubiq_particles_01['Diameter']*1e6

x_t_label = r'$X,\ м$'

# x_t_label = r'$\tau,\ с$'
y_Cp_label = r'$Cp\ (\frac{Дж}{кг \cdot К})$'
y_H_label = r'$H\ (\frac{Дж}{кг})$'


# plot_result(['p_density'], ['-'], [r'$плотность частицы\ \left[\frac{кг}{м^3}\right]$'], r'$\rho\ \left(\frac{кг}{м^3}\right)$', '04_p_density')



# colors = plt.cm.tab10.colors[:len(section_names)]
colors = plt.cm.tab10.colors[:10]

# plot_result('01_ptot', x_label, r'$p*,\ Па$', (data, section_names, styles, section_names_for_plot, y_limits, colors), GOST=GOST, x_limits=x_limits, swap_axes=False)

y_limits_default = None

pic_base_name = 'xaverage'




# ЧАСТИЦЫ
if verify_QUBIQ and verify_FLUENT:
    plot_result('01_p_D', x_t_label, r'$d,\ мкм$', (df_qubiq_particles_01, ['Diameter'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], [0, 15], colors, [0, 80], [0.4], [0.1], [0.1]),
                                                   (df_fluent_particles_01, ['Diameter'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)
    plot_result('02_p_T', x_t_label, r'$T,\ K$', (df_qubiq_particles_01, ['Temperature'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits_default, colors, [400, 430], [0.4], [0.1], [-0.1]),
                                                 (df_fluent_particles_01, ['Temperature'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [400, 430], [0.2], [0.1], [-0.1]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)




# ГАЗ
if verify_gas:
    plot_result(f"{pic_base_name}_gas_temperature", x_t_label, r'$T,\ K$', (df_qubiq_gas_01, ['Temperature'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['Temperature'], colors, [0, 80], [0.4], [0.1], [0.1]),
                                                                           (df_fluent_gas_01, ['Temperature'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)
    plot_result(f"{pic_base_name}_gas_pressure", x_t_label, r'$p,\ Па$', (df_qubiq_gas_01, ['Pressure'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['Pressure'], colors, [0, 80], [0.4], [0.1], [0.1]),
                                                                         (df_fluent_gas_01, ['Pressure'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)
    plot_result(f"{pic_base_name}_gas_velocity", x_t_label, r'$\upsilon,\ м/с$', (df_qubiq_gas_01, ['Velocity'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['Velocity'], colors, [0, 80], [0.4], [0.1], [0.1]),
                                                                                 (df_fluent_gas_01, ['Velocity'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)
    plot_result(f"{pic_base_name}_gas_Y", x_t_label, r'$Y$', (df_qubiq_gas_01, ['Y_Air', 'Y_CP'], [style_Q, style_Q], ['СПК «ГиперКуб-ГРАФ» - массовая доля воздуха', 'СПК «ГиперКуб-ГРАФ» - массовая доля ПС'], y_limits['Y_Air'], colors, [0, 80], [0.1, 0.3], [0.1, 0.1], [-0.2, 0.2]),
                                                             (df_fluent_gas_01, ['Y_Air', 'Y_CP'], [style_F, style_F], ['ПК «ANSYS Fluent» - массовая доля воздуха', 'ПК «ANSYS Fluent» - массовая доля ПС'], y_limits_default, colors, [0, 80], [0.1, 0.3], [0.1, 0.1], [-0.2, 0.2]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)
    plot_result(f"{pic_base_name}_turbulent_kinetic_energy", x_t_label, r'$k,\ \frac{\text{м}^2}{\text{с}^2}$', (df_qubiq_gas_01, ['turbulent_kinetic_energy'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['turbulent_kinetic_energy'], colors, [0, 80], [0.4], [0.1], [0.1]),
                                                                                                                (df_fluent_gas_01, ['turbulent_kinetic_energy'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)
    plot_result(f"{pic_base_name}_specific_dissipation_rate", x_t_label, r'$omega,\ \frac{1}{\text{с}}$', (df_qubiq_gas_01, ['specific_dissipation_rate'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['specific_dissipation_rate'], colors, [0, 80], [0.4], [0.1], [0.1]),
                                                                                                          (df_fluent_gas_01, ['specific_dissipation_rate'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit], swap_axes=False)









print('debug')







