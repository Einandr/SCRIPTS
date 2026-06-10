import pandas as pd
import fileinput, glob, os
import re
import math
import matplotlib.pyplot as plt
import numpy as np
import pylab
from pathlib import Path
from scipy.interpolate import interp1d, griddata
from scipy.interpolate import LinearNDInterpolator

from utils import plot_result

verify_FLUENT = False
verify_QUBIQ = True

GOST = True

style_Q = '-'
style_F = '--'

verify_sources = [verify_FLUENT, verify_QUBIQ]
number_of_sources = sum(verify_sources)

path_verification = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_1cell_VERIFICATION'
dir_verification = 'run'

if verify_FLUENT:
    path_fluent_01 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_1cell_FLUENT\post_D0_G0'
    path_fluent_02 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_1cell_FLUENT\post_D0_G0.333'
    path_fluent_03 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_1cell_FLUENT\post_D0_G1'
    file_fluent ='result_Fluent.xlsx'

if verify_QUBIQ:
    path_qubiq_01 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_1cell_QUBIQ\post_D0_G0'
    path_qubiq_02 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_1cell_QUBIQ\post_D0_G0.333'
    path_qubiq_03 = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_1cell_QUBIQ\post_D0_G1'
    file_qubiq_particles = 'qubiq_result_particles.xlsx'

path_verification_current_run = ''.join((path_verification, '/', dir_verification))
Path(path_verification_current_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_verification_current_run)

if verify_FLUENT:
    df_fluent_01 = pd.read_excel(''.join((path_fluent_01, '/', file_fluent)), index_col='p_current_time')
    df_fluent_02 = pd.read_excel(''.join((path_fluent_02, '/', file_fluent)), index_col='p_current_time')
    df_fluent_03 = pd.read_excel(''.join((path_fluent_03, '/', file_fluent)), index_col='p_current_time')

if verify_QUBIQ:
    df_qubiq_particles_01 = pd.read_excel(''.join((path_qubiq_01, '/', file_qubiq_particles)), index_col='time')
    df_qubiq_particles_02 = pd.read_excel(''.join((path_qubiq_02, '/', file_qubiq_particles)), index_col='time')
    df_qubiq_particles_03 = pd.read_excel(''.join((path_qubiq_03, '/', file_qubiq_particles)), index_col='time')


n_particles = 2000
ts_scale_factor = 1

if verify_FLUENT:
    df_fluent_01['p_diameter'] = df_fluent_01['p_diameter']*1e6
    df_fluent_02['p_diameter'] = df_fluent_02['p_diameter'] * 1e6
    df_fluent_03['p_diameter'] = df_fluent_03['p_diameter'] * 1e6

if verify_QUBIQ:
    df_qubiq_particles_01['diameter'] = df_qubiq_particles_01['diameter'] * 1e6 * ts_scale_factor
    df_qubiq_particles_02['diameter'] = df_qubiq_particles_02['diameter'] * 1e6 * ts_scale_factor
    df_qubiq_particles_03['diameter'] = df_qubiq_particles_03['diameter'] * 1e6 * ts_scale_factor

# x_label = r'$X,\ м$'
x_label = r'$\tau,\ с$'




parameters = ['Temperature', 'Y_Air', 'Y_CP']
parameter_labels = [r'$T,\ K$', r'$Y_{Air}$', r'$Y_{CP}$']
parameter_limits = [[2000.0, 2700.0], [0.5, 1], [0, 0.5]]

sections_x = [0.25, 0.5, 0.75, 1.0]
standard_colors = plt.cm.tab10.colors
section_colors = standard_colors[:len(sections_x)]


def make_lines_data(data, parameters, sections):
    section_dfs = []
    for section_x in sections:
        section_data = {'CoordinateY': np.linspace(min(data['CoordinateY']), max(data['CoordinateY']), 100)}
        for parameter in parameters:
            x = data['CoordinateX'].values
            y = data['CoordinateY'].values
            z = data[parameter].values
            interpolator = LinearNDInterpolator(list(zip(x, y)), z)
            points_line = [(section_x, yi) for yi in section_data['CoordinateY']]
            z_line = interpolator(points_line)
            # z_line = np.nan_to_num(z_line, nan=np.nanmean(z_line))
            section_data[parameter] = z_line
        section_df = pd.DataFrame(section_data)
        for parameter in parameters:
            section_df[parameter] = pd.Series(section_df[parameter]).interpolate(method='linear', limit_direction='both')
        section_df.dropna(inplace=True)
        section_df.set_index('CoordinateY', inplace=True, drop=False)
        section_dfs.append(section_df)
    return section_dfs


# if verify_FLUENT:
#     section_dfs_fluent = make_lines_data(df_fluent, parameters, sections_x)
# if verify_QUBIQ:
#     section_dfs_qubiq = make_lines_data(df_qubiq, parameters, sections_x)


pic_base_name = ''
style = style_Q

# for parameter, label, limits in zip(parameters, parameter_labels, parameter_limits):
#     plot_data = []
#
#     # if verify_FLUENT and not verify_QUBIQ:
#     #     section_dfs = section_dfs_fluent
#     # if verify_QUBIQ and not verify_FLUENT:
#     #     section_dfs = section_dfs_qubiq
#     # if verify_FLUENT and verify_QUBIQ:
#     #     section_df =
#
#     # Определяем, какие данные использовать
#     if verify_FLUENT and verify_QUBIQ:
#         section_dfs = list(zip(section_dfs_fluent, section_dfs_qubiq))
#     elif verify_FLUENT:
#         section_dfs = [(df, None) for df in section_dfs_fluent]
#     elif verify_QUBIQ:
#         section_dfs = [(None, df) for df in section_dfs_qubiq]
#
#     # Определение Y лимитов
#     all_values = []
#     # for section_df in section_dfs:
#     #     all_values.extend(section_df[parameter].dropna().values)
#     for fluent_df, qubiq_df in section_dfs:
#         if fluent_df is not None:
#             all_values.extend(fluent_df[parameter].dropna().values)
#         if qubiq_df is not None:
#             all_values.extend(qubiq_df[parameter].dropna().values)
#
#     if not GOST:
#         y_limits = [min(all_values), max(all_values)]
#     else:
#         y_limits = limits
#
#
#     for i, (fluent_df, qubiq_df) in enumerate(section_dfs):
#         section_x = sections_x[i]
#         color = section_colors[i]
#         print('текущий цвет', color)
#
#         if qubiq_df is not None:
#             section_label_qubiq = f'X = {section_x:.2f} м, СПК «ГиперКуб-ГРАФ»'.replace('.', ',')
#             plot_data.append((
#                 qubiq_df,
#                 [parameter],
#                 [style_Q],
#                 [section_label_qubiq],
#                 y_limits,
#                 [color]
#             ))
#
#
#
#         if fluent_df is not None:
#             section_label_fluent = f'X = {section_x:.2f} м, ПК «ANSYS Fluent»'.replace('.', ',')
#             plot_data.append((
#                 fluent_df,
#                 [parameter],
#                 [style_F],
#                 [section_label_fluent],
#                 y_limits,
#                 [color]
#             ))
#
#     print('РАЗМЕР плот даты:', len(plot_data))
#
#
#         # section_label = f'Сечение X = {section_x:.2f} м'.replace('.', ',')
#         # plot_data.append((
#         #     section_df,
#         #     [parameter],
#         #     [style],
#         #     [section_label],
#         #     y_limits
#         # ))
#
#     pic_name = f"{pic_base_name}_{parameter}"
#     # x_limits = [min(section_df['CoordinateY']), max(section_df['CoordinateY'])]
#     x_limits = [-0.05, 0.05]
#     plot_result(pic_name, x_label, label, *plot_data, GOST=GOST, x_limits=x_limits, swap_axes=True)


# QUBIQ - FLUENT

# if verify_QUBIQ and verify_FLUENT:

x_limits = [0, 0.035]



# QUBIQ - FLUENT
if verify_QUBIQ and verify_FLUENT:
    plot_result('01_p_diameter', x_label, r'$d,\ мкм$', (df_fluent_01, ['p_diameter'], [style_F], ['Fluent D0 G0 - диаметр частицы'], [0, 85], [None], [0.9], [-0.3], [-0.1]),
                                                        (df_fluent_02, ['p_diameter'], [style_F], ['Fluent D0 G0.333 - диаметр частицы'], [0, 85], [None], [0.8], [-0.3], [-0.1]),
                                                        (df_fluent_03, ['p_diameter'], [style_F], ['Fluent D0 G1 - диаметр частицы'], [0, 85], [None], [0.7], [-0.2], [-0.1]),
                                                        (df_qubiq_particles_01, ['diameter'], [style_Q], ['QUBIQ D0 G0 - диаметр частицы'], [0, 85], [None], [0.9], [-0.1], [-0.1]),
                                                        (df_qubiq_particles_02, ['diameter'], [style_Q], ['QUBIQ D0 G0.333 - диаметр частицы'], [0, 85], [None], [0.9], [-0.1], [-0.1]),
                                                        (df_qubiq_particles_03, ['diameter'], [style_Q], ['QUBIQ D0 G1 - диаметр частицы'], [0, 85], [None], [0.9], [-0.1], [-0.1]), GOST=GOST, x_limits=x_limits, swap_axes=False)

    plot_result('02_p_mass', x_label, r'$m,\ кг$', (df_fluent_01, ['p_mass'], [style_F], ['Fluent D0 G0 - масса частицы'], [0, 1.6e-10], [None], [0.6], [0.1], [0.1]),
                                                   (df_fluent_02, ['p_mass'], [style_F], ['Fluent D0 G0.333 - масса частицы'], [0, 1.6e-10], [None], [0.3], [-0.1], [-0.1]),
                                                   (df_fluent_03, ['p_mass'], [style_F], ['Fluent D0 G1 - масса частицы'], [0, 1.6e-10], [None], [0.2], [-0.1], [-0.1]),
                                                   (df_qubiq_particles_01, ['mass'], [style_Q], ['QUBIQ D0 G0 - масса частицы'], [0, 1.6e-10], [None], [0.8], [0.05], [0.05]),
                                                   (df_qubiq_particles_02, ['mass'], [style_Q], ['QUBIQ D0 G0.333 - масса частицы'], [0, 1.6e-10], [None], [0.8], [0.05], [0.05]),
                                                   (df_qubiq_particles_03, ['mass'], [style_Q], ['QUBIQ D0 G1 - масса частицы'], [0, 1.6e-10], [None], [0.8], [0.05], [0.05]), GOST=GOST, x_limits=x_limits, swap_axes=False)

    plot_result('03_p_density', x_label, r'$\rho,\ \frac{кг}{м^3}$', (df_fluent_01, ['p_density'], [style_F], ['Fluent D0 G0 - плотность частицы'], [540, 690], [None], [0.6], [0.1], [0.02]),
                                                                     (df_fluent_02, ['p_density'], [style_F], ['Fluent D0 G0.333 - плотность частицы'], [540, 690], [None], [0.6], [0.1], [0.04]),
                                                                     (df_fluent_03, ['p_density'], [style_F], ['Fluent D0 G1 - плотность частицы'], [540, 690], [None], [0.4], [0.1], [0.04]),
                                                                     (df_qubiq_particles_01, ['density'], [style_Q], ['QUBIQ D0 G0 - плотность частицы'], [540, 690], [None], [0.8], [0.1], [0.02]),
                                                                     (df_qubiq_particles_02, ['density'], [style_Q], ['QUBIQ D0 G0.333 - плотность частицы'], [540, 690], [None], [0.8], [0.1], [0.02]),
                                                                     (df_qubiq_particles_03, ['density'], [style_Q], ['QUBIQ D0 G1 - плотность частицы'], [540, 690], [None], [0.8], [0.1], [0.02]), GOST=GOST, x_limits=x_limits, swap_axes=False)

    plot_result('04_pT', x_label, r'$T,\ K$', (df_fluent_01, ['p_temperature'], [style_F], [r'Fluent D0 G0 - температура частицы'], [290, 440], [None], [0.4], [0.1], [-0.1]),
                                              (df_fluent_02, ['p_temperature'], [style_F], [r'Fluent D0 G0.333 - температура частицы'], [290, 440], [None], [0.6], [0.1], [-0.1]),
                                              (df_fluent_03, ['p_temperature'], [style_F], [r'Fluent D0 G1 - температура частицы'], [290, 440], [None], [0.8], [0.1], [-0.1]),
                                              (df_qubiq_particles_01, ['temperature'], [style_Q], ['QUBIQ D0 G0 - температура частицы'], [290, 440], [None], [0.8], [0.1], [-0.05]),
                                              (df_qubiq_particles_02, ['temperature'], [style_Q], ['QUBIQ D0 G0.333 - температура частицы'], [290, 440], [None], [0.8], [0.1], [-0.05]),
                                              (df_qubiq_particles_03, ['temperature'], [style_Q], ['QUBIQ D0 G1 - температура частицы'], [290, 440], [None], [0.8], [0.1], [-0.05]), GOST=GOST, x_limits=x_limits, swap_axes=False)

# QUBIQ
if verify_QUBIQ and not verify_FLUENT:
    plot_result('01_p_diameter', x_label, r'$d,\ мкм$', (df_qubiq_particles_01, ['diameter'], [style_Q], ['QUBIQ D0 G0 - диаметр частицы'], [0, 85], [None], [0.9], [-0.1], [-0.1]),
                                                        (df_qubiq_particles_02, ['diameter'], [style_Q], ['QUBIQ D0 G.333 - диаметр частицы'], [0, 85], [None], [0.9], [-0.1], [-0.1]),
                                                        (df_qubiq_particles_03, ['diameter'], [style_Q], ['QUBIQ D0 G1 - диаметр частицы'], [0, 85], [None], [0.9], [-0.1], [-0.1]), GOST=GOST, x_limits=x_limits, swap_axes=False)

    plot_result('02_p_mass', x_label, r'$m,\ кг$', (df_qubiq_particles_01, ['mass'], [style_Q], ['QUBIQ D0 G0 - масса частицы'], [0, 1.6e-10], [None], [0.8], [0.05], [0.05]),
                                                   (df_qubiq_particles_02, ['mass'], [style_Q], ['QUBIQ D0 G0.333 - масса частицы'], [0, 1.6e-10], [None], [0.8], [0.05], [0.05]),
                                                   (df_qubiq_particles_03, ['mass'], [style_Q], ['QUBIQ D0 G1 - масса частицы'], [0, 1.6e-10], [None], [0.8], [0.05], [0.05]), GOST=GOST, x_limits=x_limits, swap_axes=False)

    plot_result('03_p_density', x_label, r'$\rho,\ \frac{кг}{м^3}$', (df_qubiq_particles_01, ['density'], [style_Q], ['QUBIQ D0 G0 - плотность частицы'], [540, 690], [None], [0.8], [0.1], [0.02]),
                                                                     (df_qubiq_particles_02, ['density'], [style_Q], ['QUBIQ D0 G0.333 - плотность частицы'], [540, 690], [None], [0.8], [0.1], [0.02]),
                                                                     (df_qubiq_particles_03, ['density'], [style_Q], ['QUBIQ D0 G1 - плотность частицы'], [540, 690], [None], [0.8], [0.1], [0.02]), GOST=GOST, x_limits=x_limits, swap_axes=False)

    plot_result('04_pT', x_label, r'$T,\ K$', (df_qubiq_particles_01, ['temperature'], [style_Q], ['QUBIQ D0 G0 - температура частицы'], [290, 440], [None], [0.8], [0.1], [-0.05]),
                                              (df_qubiq_particles_02, ['temperature'], [style_Q], ['QUBIQ D0 G0.333 - температура частицы'], [290, 440], [None], [0.8], [0.1], [-0.05]),
                                              (df_qubiq_particles_03, ['temperature'], [style_Q], ['QUBIQ D0 G1 - температура частицы'], [290, 440], [None], [0.8], [0.1], [-0.05]), GOST=GOST, x_limits=x_limits, swap_axes=False)












#
# if verify_QUBIQ:
#     plot_result('02_p_T', x_label, r'$T,\ K$', (df_fluent_particles_01, ['Temperature'], [style_F], ['Fluent ST - температура частицы'], [400, 430], [0.2], [0.1], [-0.1]),
#                                                  (df_qubiq_particles_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура частицы'], [400, 430], [0.4], [0.1], [-0.1]),
#                                                  (df_qubiq_particles_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура частицы'], [400, 430], [0.4], [0.1], [-0.1]), GOST=GOST, x_limits=[0, x_limit])
#
#
# # QUBIQ - FLUENT
# if verify_QUBIQ and verify_FLUENT:
#     plot_result('01_p_D', x_label, r'$d,\ мкм$', (df_fluent_particles_01, ['Diameter'], [style_F], ['Fluent ST - диаметр частицы'], [0, 80], [0.2], [0.1], [0.1]),
#                                                    (df_qubiq_particles_01, ['Diameter'], [style_Q], ['QUBIQ ST - диаметр частицы'], [0, 80], [0.4], [0.1], [0.1]),
#                                                    (df_qubiq_particles_02, ['Diameter'], [style_Q], ['QUBIQ TR - диаметр частицы'], [0, 80], [0.4], [0.1], [0.1]), GOST=GOST, x_limits=[0, x_limit])
#     plot_result('02_p_T',x_label, r'$T,\ K$', (df_fluent_particles_01, ['Temperature'], [style_F], ['Fluent ST - температура частицы'], [400, 430], [0.2], [0.1], [-0.1]),
#                                                 (df_qubiq_particles_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура частицы'], [400, 430], [0.4], [0.1], [-0.1]),
#                                                 (df_qubiq_particles_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура частицы'], [400, 430], [0.4], [0.1], [-0.1]), GOST=GOST, x_limits=[0, x_limit])
#
#
#





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


#
# # ГАЗ и ЧАСТИЦЫ
# if verify_gas:
#     plot_result('03_gT', x_label, r'$T,\ K$', (df_fluent_gas_01, ['Temperature'], [style_F], ['Fluent ST - температура газа'], [1350, 2000], [0.2], [0.1], [0.1]),
#                                                 (df_qubiq_gas_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура газа'], [1350, 2000], [0.4], [0.1], [0.1]),
#                                                 (df_qubiq_gas_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура газа'], [1350, 2000], [0.4], [0.1], [0.1]))
#     plot_result('04_pT_gT', x_label, r'$T\ (K)$', (df_fluent_particles_01, ['Temperature'], [style_F], ['Fluent ST - температура частицы'], [0, 2000], [0.2], [0.1], [0.5]),
#                                                     (df_fluent_gas_01, ['Temperature'], [style_F], ['Fluent ST - температура газа'], [0, 2000], [0.4], [0.1], [-0.2]),
#                                                     (df_qubiq_particles_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура частицы'], [0, 2000], [0.1], [0.1], [0.5]),
#                                                     (df_qubiq_particles_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура частицы'], [0, 2000], [0.1], [0.1], [0.5]),
#                                                     (df_qubiq_gas_01, ['Temperature'], [style_Q], ['QUBIQ ST - температура газа'], [0, 2000], [0.3], [0.1], [-0.2]),
#                                                     (df_qubiq_gas_02, ['Temperature'], [style_Q], ['QUBIQ TR - температура газа'], [0, 2000], [0.3], [0.1], [-0.2]))
#     plot_result('05_gY', x_label, r'$Y$', (df_fluent_gas_01, ['Y_c7h16', 'Y_o2', 'Y_n2'], [style_F, style_F, style_F], ['Fluent ST - массовая доля н-гептана', 'Fluent ST - массовая доля O2', 'Fluent ST - массовая доля N2'], [0, 0.8], [0.1, 0.3, 0.5], [0.1, 0.1, 0.1], [-0.2, 0.2, -0.2]),
#                                             (df_qubiq_gas_01, ['Y_c7h16', 'Y_o2', 'Y_n2'], [style_Q, style_Q, style_Q], ['QUBIQ ST - массовая доля н-гептана', 'QUBIQ ST - массовая доля O2', 'QUBIQ ST - массовая доля N2'], [0, 0.8], [0.15, 0.35, 0.55], [0.1, 0.1, 0.1], [-0.2, 0.2, -0.2]),
#                                             (df_qubiq_gas_02, ['Y_c7h16', 'Y_o2', 'Y_n2'], [style_Q, style_Q, style_Q], ['QUBIQ TR - массовая доля н-гептана', 'QUBIQ TR - массовая доля O2', 'QUBIQ TR - массовая доля N2'], [0, 0.8], [0.15, 0.35, 0.55], [0.1, 0.1, 0.1], [-0.2, 0.2, -0.2]))
#     plot_result('06_gP', x_label, r'$P,\ Па$', (df_fluent_gas_01, ['Pressure'], [style_F], ['Fluent ST - давление газа'], [497000, 502000], [0.2], [0.1], [0.0005]),
#                                                  (df_qubiq_gas_01, ['Pressure'], [style_Q], ['QUBIQ ST - давление газа'], [497000, 502000], [0.3], [0.1], [0.0005]),
#                                                  (df_qubiq_gas_02, ['Pressure'], [style_Q], ['QUBIQ TR - давление газа'], [497000, 502000], [0.3], [0.1], [0.0005]))
#     plot_result('07_gRho', x_label, r'$\rho,\ \frac{кг}{м^3}$', (df_fluent_gas_01, ['Density'], [style_F], ['Fluent ST - плотность газа'], [0.8, 1.5], [0.2], [0.1], [0.0005]),
#                                                                   (df_qubiq_gas_01, ['Density'], [style_Q], ['QUBIQ ST - плотность газа'], [0.8, 1.5], [0.3], [0.1], [0.0005]),
#                                                                   (df_qubiq_gas_02, ['Density'], [style_Q], ['QUBIQ TR - плотность газа'], [0.8, 1.5], [0.3], [0.1], [0.0005]))
#     plot_result('08_gV', x_label, r'$v\ \frac{м}{с}$', (df_fluent_gas_01, ['Velocity'], [style_F], ['Fluent ST - скорость газа'], [40, 60], [0.2], [0.1], [0.0005]),
#                                                          (df_qubiq_gas_01, ['Velocity'], [style_Q], ['QUBIQ ST - скорость газа'], [40, 60], [0.3], [0.1], [0.0005]),
#                                                          (df_qubiq_gas_02, ['Velocity'], [style_Q], ['QUBIQ TR - скорость газа'], [40, 60], [0.3], [0.1], [0.0005]))
#







print('debug')







