import os
import re
import pandas as pd




path = r'D:\YASIM\VORON\2025_07_AXYSIM_CIAM\QUBIQ\3D_2nd_primitive\EXPORTS'
file = 'nozzle_minus_odin_mach.dat'

os.chdir(path)

sort_axis = 'Y'

def read_custom_format(file_path):
    # Открываем файл и считываем строки
    with open(file_path, 'r') as file:
        lines = file.readlines()



    # Находим индекс строки, с которой начинаются данные
    headers_start_index = None
    headers_end_index = None
    data_start_index = None
    headers = []

    for i, line in enumerate(lines):
        print(i, line)
        if line.startswith('VARIABLES = '):
            headers_start_index = i
        if line.startswith('GEOMETRY') and headers_end_index is None:
            headers_end_index = i
        if line.startswith(' DT='):
            data_start_index = i+1
            break
    print('headers_start_index headers_end_index data_start_index', headers_start_index, headers_end_index, data_start_index)

    # Извлечение заголовков
    # if headers_start_index is not None and headers_end_index is not None:
    #     variables_line = lines[headers_start_index].strip()
    #     variables_line = variables_line.replace('VARIABLES=', '').replace('"', '').replace(',', ' ')
    #     headers = variables_line.split()


    i = headers_start_index
    while i < headers_end_index:
        column_name = lines[i]
        column_name = column_name.replace("VARIABLES = ", "")
        column_name = column_name.replace("\"", "")
        column_name = column_name.replace("\n", "")
        column_name = column_name.replace("3D/FLUID_MAIN/", "")
        headers.append(column_name)
        print(column_name)
        i += 1
    print(headers)

    # Считываем данные, начиная с найденной строки

    data_start_index = data_start_index
    data = []
    for line in lines[data_start_index:]:
        elements = line.split()
        print('len_elements, len_headers', len(elements), len(headers))
        if len(elements) == len(headers):
            data.append([float(value) for value in line.split()])
        else:
            # если будет не 1 зона, то можно продолжить
            break

    # Создаем DataFrame
    df = pd.DataFrame(data, columns=headers)
    # df.rename(columns={
    #     'X': 'CoordinateX',
    #     'Y': 'CoordinateY',
    #     'Z': 'CoordinateZ',
    #     'pressure': 'Pressure',
    #     'temperature': 'Temperature',
    #     'density': 'Density',
    #     'velocity_magnitude': 'Velocity',
    #     'Mach': 'Mach',
    #     'mass_fractions_C7H16_nheptane': 'Y_c7h16',
    #     'mass_fractions_O2': 'Y_o2',
    #     'mass_fractions_N2': 'Y_n2'
    # }, inplace=True)
    return df


data = read_custom_format(file)
# data.sort_values(by=sort_axis, inplace=True)

data.to_excel(f'data_{os.path.splitext(file)[0]}.xlsx', index=False)


data.to_csv('data_converted_QUBIQ.csv', index=False)


# Дискретизация по ОХ с шагом 0.001
discretization_step = 0.001
data['X_interval'] = (data['CoordinateX'] / discretization_step).astype(int)

# Определяем столбцы, которые нужно исключить из агрегации
exclude_columns = ['CoordinateY', 'CoordinateZ', 'X_interval']

# Столбцы, по которым нужно вычислить среднее
columns_to_aggregate = [col for col in data.columns if col not in exclude_columns]

# Группировка данных по интервалам и вычисление средних значений
grouped_data = data.groupby('X_interval').agg({col: 'mean' for col in columns_to_aggregate}).reset_index()

# Создание нового DataFrame с осредненными значениями
data_averaged = grouped_data.rename(columns={'X_interval': 'Interval'})
data_averaged['CoordinateX'] = data_averaged['Interval'] * discretization_step

# Удаление вспомогательного столбца
data_averaged = data_averaged.drop(columns=['Interval'])
data_averaged.to_csv('data_averaged_QUBIQ.csv', index=False)

print('debug')