import os
import re
import pandas as pd


path = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\06_LES_high_regenerated\2nd_mom_time'
file_dpmrpt = 'file.dpmrpt'

discretization_step = 0.01

os.chdir(path)

def read_custom_format(file_path):
    # Открываем файл и считываем строки
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Находим индекс строки, с которой начинаются данные
    headers_start_index = 0
    headers_end_index = 0
    for i, line in enumerate(lines):
        print(i, line)
        if line.startswith(' ------'):
            headers_start_index = i + 1
        if line.startswith('-------'):
            headers_end_index = i
            break
    print('data_start_index data_end_index', headers_start_index, headers_end_index)

    headers = []
    i = headers_start_index
    while i < headers_end_index:
        line = lines[i]
        column_name = line.split()[2]
        column_name = column_name.replace("Particle", "")
        headers.append(column_name)
        print(column_name)
        i += 1
    print(headers)

    # Считываем данные, начиная с найденной строки

    data_start_index = headers_end_index + 2
    data = []
    for line in lines[data_start_index:]:
        data.append([float(value) for value in line.split()])

    # Создаем DataFrame
    df = pd.DataFrame(data, columns=headers)
    df.rename(columns={
        'XPosition': 'CoordinateX',
        'YPosition': 'CoordinateY',
        'ZPosition': 'CoordinateZ'
    }, inplace=True)
    return df


data = read_custom_format(file_dpmrpt)
data.sort_values(by='CoordinateX', inplace=True)

data['Mass_Flux'] = data['Mass'] * data['NumberinParcel'] * abs(data['XVelocity'])
data['Diameter_Mass_Flux'] = data['Diameter'] * data['Mass'] * data['NumberinParcel'] * abs(data['XVelocity'])
data['Mass_Mass_Flux'] = data['Mass'] * data['Mass'] * data['NumberinParcel'] * abs(data['XVelocity'])


data.to_csv('points_for_tecplot_FLUENT.csv', index=False)



# Дискретизация по ОХ с шагом discretization_step
data['X_interval'] = (data['CoordinateX'] / discretization_step).astype(int)

# Группировка данных по интервалам и вычисление средних значений
grouped_data = data.groupby('X_interval').agg({
    'Diameter': 'mean',
    'Mass': 'mean',
    'Temperature': 'mean',
    'Mass_Flux': 'sum',
    'Diameter_Mass_Flux': 'sum',
    'Mass_Mass_Flux': 'sum',
}).reset_index()


grouped_data.rename(columns={'X_interval': 'Interval'}, inplace=True)
grouped_data['CoordinateX'] = grouped_data['Interval']*discretization_step
grouped_data.drop(columns=['Interval'], inplace=True)

cols = grouped_data.columns.tolist()
cols = ['CoordinateX'] + [col for col in cols if col != 'CoordinateX']
grouped_data = grouped_data[cols]

grouped_data['Mass_Flow_Rate'] = grouped_data['Mass_Flux']/discretization_step
grouped_data['Diameter_mave'] = grouped_data['Diameter_Mass_Flux']/grouped_data['Mass_Flux']
grouped_data['Mass_mave'] = grouped_data['Mass_Mass_Flux']/grouped_data['Mass_Flux']

grouped_data.to_csv('points_averaged_FLUENT.csv', index=False)

print('debug')