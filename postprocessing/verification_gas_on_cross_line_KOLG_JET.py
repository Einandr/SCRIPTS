import os
from pathlib import Path
import time

import pandas as pd
import matplotlib.pyplot as plt

from utils import plot_result, make_lines_data


verify_QUBIQ = True
verify_FLUENT = False

GOST = False

styles_Q = ['-', '--', '-.']
names_Q = ['тетра 22 млн.', 'тетра 42 млн.', 'тетра 140 млн.']

styles_F = ['-', '--', '-.']
names_F = ['11 млн.', '30 млн.', '85 млн.']

path_verification = r'D:\YASIM\VORON\2026_11_JET\KOLG_Results\verification'
dir_verification = 'run'

qubiq_paths = [
    r'D:\YASIM\VORON\2026_11_JET\KOLG_Results\sq_tet_22\data_converted_QUBIQ_2D.csv',
    r'D:\YASIM\VORON\2026_11_JET\KOLG_Results\sq_tet_42\data_converted_QUBIQ_2D.csv',
    r'D:\YASIM\VORON\2026_11_JET\KOLG_Results\sq_tet_140\data_converted_QUBIQ_2D.csv'
]

fluent_paths = [
    r'D:\YASIM\VORON\2026_01_OPZ\results_hot\fluent\3mm_pmfr_0.005_SST\data_converted_FLUENT_2D.csv',
]

x_label = r'$X,\ м$'
# x_label = r'$\tau,\ с$'

# parameters = ['Temperature', 'Y_Air', 'Y_CP', 'Y_GPG', 'Pressure', 'Velocity', ]
# parameter_labels = [r'$T,\ K$', r'$Y_{Air}$', r'$Y_{CP}$', r'$Y_{GPG}$', r'$p,\ Па$', r'$\upsilon,\ м/с$']
# parameter_limits = [[2000.0, 2700.0], [0.65, 1], [0, 0.35], [0, 0.01], [499800, 503000], [0, 25]]

# parameters = ['Temperature', 'Y_Air', 'Y_CP', 'Y_GPG', 'Pressure', 'Velocity', 'turbulent_kinetic_energy', 'specific_dissipation_rate']
# parameter_labels = [r'$T,\ K$', r'$Y_{Air}$', r'$Y_{CP}$', r'$Y_{GPG}$', r'$p,\ Па$', r'$\upsilon,\ м/с$', 'K', 'OMEGA']
# # parameter_limits = [[2000.0, 3300.0], [0, 1], [0, 1], [0, 0.01], [500000, 503000], [0, 25], [0, 3], [0, 10000]]
# parameter_limits = [[2000.0, 3300.0], [0, 1], [0, 1], [0, 0.01], [500000, 504000], [0, 25], [0, 3], [0, 10000]]

parameters = ['Velocity', 'Velocity_X', 'Temperature', 'Density']
parameter_labels = [r'$\upsilon,\ м/с$', r'$\upsilon,\ м/с$', r'$T,\ K$', r'$\rho,\ кг/м.куб.$']
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

# sections_x = [0.3]
# sections = [0.1, 0.2, 0.3, 0.4, 0.5]
sections = [0.1, 0.3, 0.5]
# sections_x = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]

standard_colors = plt.cm.tab10.colors
section_colors = standard_colors[:len(sections)]

path_verification_current_run = ''.join((path_verification, '/', dir_verification))
Path(path_verification_current_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_verification_current_run)

start_time = time.time()
section_dfs_qubiq_list = []
section_dfs_fluent_list = []
if verify_QUBIQ:
    for path in qubiq_paths:
        data = pd.read_csv(path)
        section_dfs_qubiq = make_lines_data(data, parameters, sections)
        section_dfs_qubiq_list.append(section_dfs_qubiq)
if verify_FLUENT:
    for path in fluent_paths:
        data = pd.read_csv(path)
        section_dfs_fluent = make_lines_data(data, parameters, sections)
        section_dfs_fluent_list.append(section_dfs_fluent)
print(f"Время выполнения: {time.time() - start_time:.4f} секунд")

pic_base_name = 'lines'

for parameter, label, limits in zip(parameters, parameter_labels, parameter_limits):
    plot_data = []

    section_dfs = []
    if verify_FLUENT and verify_QUBIQ:
        for fluent_sections, qubiq_sections in zip(section_dfs_fluent_list, section_dfs_qubiq_list):
            section_dfs.extend(list(zip(fluent_sections, qubiq_sections)))
    elif verify_FLUENT:
        for fluent_sections in section_dfs_fluent_list:
            section_dfs.extend([(df, None) for df in fluent_sections])
    elif verify_QUBIQ:
        for qubiq_sections in section_dfs_qubiq_list:
            section_dfs.extend([(None, df) for df in qubiq_sections])

    all_values = []
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
        section_index = i % len(sections)
        section = sections[section_index]
        color = section_colors[section_index]
        section_str = f"{section:.2f}".replace('.', ',')

        if qubiq_df is not None:
            qubiq_index = i // len(sections)
            style_Q = styles_Q[qubiq_index % len(styles_Q)]
            name_Q = names_Q[qubiq_index % len(names_Q)]
            section_label_qubiq = f'X = {section_str} м., {name_Q}'
            # section_label_qubiq = f'X = {section_str} м., {name_Q}, СПК «ГиперКуб-ГРАФ»'
            plot_data.append((
                qubiq_df,
                [parameter],
                [style_Q],
                [section_label_qubiq],
                y_limits,
                [color]
            ))

        if fluent_df is not None:
            fluent_index = i // len(sections)
            style_F = styles_F[fluent_index % len(styles_F)]
            name_F = names_F[fluent_index % len(names_F)]
            section_label_fluent = f'X = {section_str} м., {name_F}'
            # section_label_fluent = f'X = {section_str} м., {name_F}, ПК «ANSYS Fluent»'
            plot_data.append((
                fluent_df,
                [parameter],
                [style_F],
                [section_label_fluent],
                y_limits,
                [color]
            ))

    pic_name = f"{pic_base_name}_{parameter}"
    # x_limits = [min(section_df['CoordinateY']), max(section_df['CoordinateY'])]
    x_limits = [0, 0.05]
    plot_result(pic_name, x_label, label, *plot_data, GOST=GOST, x_limits=x_limits, swap_axes=True)


