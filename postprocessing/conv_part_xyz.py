import os
import re
import pandas as pd




path = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\LES_HOT_HIGH'
file_xyz = 'visit_ex_db.xyz'
discretization_step = 0.1

# СВЕРЯТЬ ПОРЯДОК С ХУЗ ФАЙЛОМ
names = ['unknown', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'Diameter', 'Temperature']
# names = ['unknown', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'Temperature', 'Diameter']

os.chdir(path)
data = pd.read_csv(file_xyz, delimiter='\t', names=names, index_col=False, skiprows=2)
data.drop(columns=['unknown'], inplace=True)
data.sort_values(by='CoordinateX', inplace=True)
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