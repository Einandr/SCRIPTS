import glob
import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, griddata
from scipy.interpolate import LinearNDInterpolator
import numpy as np

path = r'D:\YASIM\VORON\2026_11_JET\KOLG_Results\sq_tet_140'
file_okc = 'visit_ex_db_140'
discretization_step = 0.01

os.chdir(path)


def read_okc_format(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Считываем количество столбцов
    num_columns = int(lines[0].split()[0])

    # Считываем названия переменных
    variable_lines = lines[1:1 + num_columns]
    headers = []
    for line in variable_lines:
        var_name = line.strip()
        # Вычленяем последнюю часть сложного имени
        if '/' in var_name:
            var_name = var_name.split('/')[-1]
        headers.append(var_name)

    # Пропускаем строки с минимальными и максимальными значениями
    data_start_index = 1 + num_columns + num_columns

    # Считываем данные
    data = []
    for line in lines[data_start_index:]:
        data.append([float(value) for value in line.split()])

    # Создаем DataFrame
    df = pd.DataFrame(data, columns=headers)

    return df


file_pattern = os.path.join(path, f'{file_okc}*.okc')
file_list = glob.glob(file_pattern)

dfs = []
for file_path in sorted(file_list):
    df = read_okc_format(file_path)
    dfs.append(df)


data = pd.concat(dfs, ignore_index=True)

rename_dict = {
    'x': 'CoordinateX',
    'y': 'CoordinateY',
    'z': 'CoordinateZ',
    'pressure': 'Pressure',
    'mean_pressure': 'Pressure',
    'temperature': 'Temperature',
    'mean_temperature': 'Temperature',
    'density': 'Density',
    'mean_density': 'Density',
    'velocity_magnitude': 'Velocity',
    'mean_velocity': 'Velocity',
    'mean_velocity_x': 'Velocity_X',
    'mean_velocity_y': 'Velocity_Y',
    'mean_velocity_z': 'Velocity_Z',
    'Mach': 'Mach'
}

for col in data.columns:
    if col.startswith('mass_fractions_'):
        new_name = 'Y_' + col[len('mass_fractions_'):]
        rename_dict[col] = new_name
    elif col.startswith('mean_mass_fractions_'):
        new_name = 'Y_' + col[len('mean_mass_fractions_'):]
        rename_dict[col] = new_name

# Применяем все замены
data.rename(columns=rename_dict, inplace=True)

z_tolerance = 1e-6
z_min = data['CoordinateZ'].min()
z_max = data['CoordinateZ'].max()
is_2D = abs(z_max - z_min) < z_tolerance

print(f"Минимальное и максимальное значение CoordinateZ: {z_min}, {z_max}")

if is_2D:
    print("Поле 2D: CoordinateZ не меняется.")
    suffix = "_2D"
else:
    print("Поле 3D: CoordinateZ меняется.")
    suffix = "_3D"

data.to_csv(f'data_converted_QUBIQ{suffix}.csv', index=False)


# Дискретизация по ОХ с шагом discretization_step
data['X_interval'] = (data['CoordinateX'] / discretization_step).astype(int)

cols_to_agg = [col for col in data.columns if col not in ['CoordinateX', 'CoordinateY', 'CoordinateZ', 'X_interval']]
grouped_data = data.groupby('X_interval').agg({col: 'mean' for col in cols_to_agg}).reset_index()

data_averaged = grouped_data.rename(columns={'X_interval': 'Interval'})
data_averaged['CoordinateX'] = data_averaged['Interval'] * discretization_step
data_averaged = data_averaged.drop(columns=['Interval'])

data_averaged.to_csv(f'data_averaged_QUBIQ{suffix}.csv', index=False)


print('debug')