import os
import re
import pandas as pd




path = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_10x1000mm_QUBIQ\D0_G1_Y1\out'
file_tracks_all = 'tracks_all.txt'

discretization_step = 0.001

os.chdir(path)
data = pd.read_csv(file_tracks_all)

data.rename(columns={'diameter': 'Diameter', 'temperature': 'Temperature'}, inplace=True)

# data.drop(columns=['unknown', 'unknown2'], inplace=True)
data.sort_values(by='CoordinateX', inplace=True)
# Не нужен - можно использовать tracks_all
data.to_csv('points_for_tecplot_QUBIQ.csv', index=False)

# Дискретизация по ОХ с шагом discretization_step
data['X_interval'] = (data['CoordinateX'] / discretization_step).astype(int)

# Группировка данных по интервалам и вычисление средних значений
grouped_data = data.groupby('X_interval').agg({'Diameter': 'mean', 'Temperature': 'mean'}).reset_index()

# Создание нового DataFrame с осредненными значениями
data_averaged = grouped_data.rename(columns={'X_interval': 'Interval'})
data_averaged['CoordinateX'] = data_averaged['Interval'] * discretization_step

# Удаление вспомогательного столбца
data_averaged = data_averaged.drop(columns=['Interval'])
data_averaged.to_csv('points_averaged_QUBIQ.csv', index=False)


print('debug')