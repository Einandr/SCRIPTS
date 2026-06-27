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

verify_FLUENT = True
verify_QUBIQ = True

GOST = True

style_Q = '-'
style_F = '--'

verify_sources = [verify_FLUENT, verify_QUBIQ]
number_of_sources = sum(verify_sources)

path_verification = r'D:\YASIM\VORON\2026_01_OPZ\verification_hot'
dir_verification = 'run'


if verify_QUBIQ:
    path_qubiq = r'D:\YASIM\VORON\2026_01_OPZ\results_hot\qubiq\3mm_pmfr_0.005_RANS\data_converted_QUBIQ_2D.csv'

if verify_FLUENT:
    path_fluent = r'D:\YASIM\VORON\2026_01_OPZ\results_hot\fluent\3mm_pmfr_0.005_SST\data_converted_FLUENT_2D.csv'


path_verification_current_run = ''.join((path_verification, '/', dir_verification))
Path(path_verification_current_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_verification_current_run)

if verify_FLUENT:
    df_fluent = pd.read_csv(path_fluent)

if verify_QUBIQ:
    df_qubiq = pd.read_csv(path_qubiq)

x_label = r'$X,\ м$'
# x_label = r'$\tau,\ с$'


# parameters = ['Temperature', 'Y_Air', 'Y_CP', 'Y_GPG', 'Pressure', 'Velocity', ]
# parameter_labels = [r'$T,\ K$', r'$Y_{Air}$', r'$Y_{CP}$', r'$Y_{GPG}$', r'$p,\ Па$', r'$\upsilon,\ м/с$']
# parameter_limits = [[2000.0, 2700.0], [0.65, 1], [0, 0.35], [0, 0.01], [499800, 503000], [0, 25]]

parameters = ['Temperature', 'Y_Air', 'Y_CP', 'Y_GPG', 'Pressure', 'Velocity', 'turbulent_kinetic_energy', 'specific_dissipation_rate']
parameter_labels = [r'$T,\ K$', r'$Y_{Air}$', r'$Y_{CP}$', r'$Y_{GPG}$', r'$p,\ Па$', r'$\upsilon,\ м/с$', 'K', 'OMEGA']
# parameter_limits = [[2000.0, 3300.0], [0, 1], [0, 1], [0, 0.01], [500000, 503000], [0, 25], [0, 3], [0, 10000]]
parameter_limits = [[2000.0, 3300.0], [0, 1], [0, 1], [0, 0.01], [500000, 504000], [0, 25], [0, 3], [0, 10000]]

# y_limits = {
#     'Temperature': [2000, 2800],
#     'Pressure': [500000, 504000],
#     'Velocity': [0, 25],
#     'Y_Air': [0, 1],
#     'Y_CP': [0, 1],
#     'turbulent_kinetic_energy': [0, 0.5],
#     'specific_dissipation_rate': [0, 5000]
# }


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


if verify_FLUENT:
    section_dfs_fluent = make_lines_data(df_fluent, parameters, sections_x)
if verify_QUBIQ:
    section_dfs_qubiq = make_lines_data(df_qubiq, parameters, sections_x)


pic_base_name = 'lines'
style = style_Q

for parameter, label, limits in zip(parameters, parameter_labels, parameter_limits):
    plot_data = []

    # if verify_FLUENT and not verify_QUBIQ:
    #     section_dfs = section_dfs_fluent
    # if verify_QUBIQ and not verify_FLUENT:
    #     section_dfs = section_dfs_qubiq
    # if verify_FLUENT and verify_QUBIQ:
    #     section_df =

    # Определяем, какие данные использовать
    if verify_FLUENT and verify_QUBIQ:
        section_dfs = list(zip(section_dfs_fluent, section_dfs_qubiq))
    elif verify_FLUENT:
        section_dfs = [(df, None) for df in section_dfs_fluent]
    elif verify_QUBIQ:
        section_dfs = [(None, df) for df in section_dfs_qubiq]

    # Определение Y лимитов
    all_values = []
    # for section_df in section_dfs:
    #     all_values.extend(section_df[parameter].dropna().values)
    for fluent_df, qubiq_df in section_dfs:
        if fluent_df is not None:
            all_values.extend(fluent_df[parameter].dropna().values)
        if qubiq_df is not None:
            all_values.extend(qubiq_df[parameter].dropna().values)

    if not GOST:
        y_limits = [min(all_values), max(all_values)]
    else:
        y_limits = limits


    for i, (fluent_df, qubiq_df) in enumerate(section_dfs):
        section_x = sections_x[i]
        color = section_colors[i]
        print('текущий цвет', color)

        if qubiq_df is not None:
            section_label_qubiq = f'X = {section_x:.2f} м, СПК «ГиперКуб-ГРАФ»'.replace('.', ',')
            plot_data.append((
                qubiq_df,
                [parameter],
                [style_Q],
                [section_label_qubiq],
                y_limits,
                [color]
            ))



        if fluent_df is not None:
            section_label_fluent = f'X = {section_x:.2f} м, ПК «ANSYS Fluent»'.replace('.', ',')
            plot_data.append((
                fluent_df,
                [parameter],
                [style_F],
                [section_label_fluent],
                y_limits,
                [color]
            ))

    print('РАЗМЕР плот даты:', len(plot_data))


        # section_label = f'Сечение X = {section_x:.2f} м'.replace('.', ',')
        # plot_data.append((
        #     section_df,
        #     [parameter],
        #     [style],
        #     [section_label],
        #     y_limits
        # ))

    pic_name = f"{pic_base_name}_{parameter}"
    # x_limits = [min(section_df['CoordinateY']), max(section_df['CoordinateY'])]
    x_limits = [-0.05, 0.05]
    plot_result(pic_name, x_label, label, *plot_data, GOST=GOST, x_limits=x_limits, swap_axes=True)









print('debug')







