import os
import re
import pandas as pd




path = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\02_LES'
file = 'out_3D'

discretization_step = 0.1

os.chdir(path)
data = pd.read_csv(file, sep=',')
data.columns = data.columns.str.strip()

data.drop(columns=['cellnumber'], inplace=True)
# data.drop(columns=['nodenumber'], inplace=True)

print(data.columns)

data.rename(columns={
    'x-coordinate': 'CoordinateX',
    'y-coordinate': 'CoordinateY',
    'z-coordinate': 'CoordinateZ',
    'pressure': 'Pressure',
    'temperature': 'Temperature',
    'density': 'Density',
    'velocity-magnitude': 'Velocity',
    'mach-number': 'Mach',
    'turb-kinetic-energy': 'turbulent_kinetic_energy',
    'specific-diss-rate': 'specific_dissipation_rate',
    'c7h16': 'Y_c7h16',
    'o2': 'Y_o2',
    'n2': 'Y_n2',
    'gpg': 'Y_GPG',
    'cp': 'Y_CP',
    'air': 'Y_Air'
}, inplace=True)


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

data.to_csv(f'data_converted_FLUENT{suffix}.csv', index=False)


# data.sort_values(by='CoordinateX', inplace=True)
# data.to_csv('data_converted_FLUENT.csv', index=False)


# Дискретизация по ОХ с шагом discretization_step
data['X_interval'] = (data['CoordinateX'] / discretization_step).astype(int)

cols_to_agg = [col for col in data.columns if col not in ['CoordinateX', 'CoordinateY', 'CoordinateZ', 'X_interval']]
grouped_data = data.groupby('X_interval').agg({col: 'mean' for col in cols_to_agg}).reset_index()

data_averaged = grouped_data.rename(columns={'X_interval': 'Interval'})
data_averaged['CoordinateX'] = data_averaged['Interval'] * discretization_step
data_averaged = data_averaged.drop(columns=['Interval'])

data_averaged.to_csv(f'data_averaged_FLUENT{suffix}.csv', index=False)





print('debug')