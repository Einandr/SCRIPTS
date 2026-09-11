import os
import re
from glob import glob
import pandas as pd


path = r'E:\YASIM\VORON_TEMP\2026_12_Iskra_OPZ\high_OPZ_b08'
file_dpmrpt = 'file.dpmrpt'

discretization_step = 0.01
columns_to_average = ['Diameter', 'Mass', 'Temperature']
columns_to_sum = ['Mass_Flux', 'Diameter_Mass_Flux', 'Mass_Mass_Flux']

os.chdir(path)

def dpmrpt_to_csv(dpmrpt_file, output_dir):
    """
        Конвертирует dpmrpt-файл в CSV-формат.
        Сохраняет результат в указанную папку.

        Args:
            dpmrpt_file (str): Путь к dpmrpt-файлу.
            output_dir (str): Папка для сохранения CSV-файла.
    """

    time_match = re.search(r"_(\d+\.\d+)\.dpmrpt$", dpmrpt_file)
    if time_match:
        time_str = time_match.group(1)
        time = float(time_str)
    else:
        print(f"⚠️ Не удалось извлечь время из файла: {dpmrpt_file}")
        time_str = ''
        time = None

    dpmrpt_path = os.path.join(output_dir, dpmrpt_file)

    with open(dpmrpt_path, 'r') as file:
        lines = file.readlines()

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

    data_start_index = headers_end_index + 2
    data = []
    for line in lines[data_start_index:]:
        data.append([float(value) for value in line.split()])

    df = pd.DataFrame(data, columns=headers)
    df.rename(columns={
        'XPosition': 'CoordinateX',
        'YPosition': 'CoordinateY',
        'ZPosition': 'CoordinateZ'
    }, inplace=True)

    df.sort_values(by='CoordinateX', inplace=True)

    df['Mass_Flux'] = df['Mass'] * df['NumberinParcel'] * abs(df['XVelocity'])
    df['Diameter_Mass_Flux'] = df['Diameter'] * df['Mass'] * df['NumberinParcel'] * abs(df['XVelocity'])
    df['Mass_Mass_Flux'] = df['Mass'] * df['Mass'] * df['NumberinParcel'] * abs(df['XVelocity'])

    df.to_csv(f'particles_time_{time_str}_FLUENT.csv', index=False)

    # --- Осреднение по интервалам X ---
    df['X_interval'] = (df['CoordinateX'] / discretization_step).astype(int)
    agg_dict_mean = {col: 'mean' for col in columns_to_average}
    agg_dict_sum = {col: 'sum' for col in columns_to_sum}
    agg_dict = {**agg_dict_mean, **agg_dict_sum}
    data_averaged = df.groupby('X_interval').agg(agg_dict).reset_index()

    data_averaged.rename(columns={'X_interval': 'Interval'}, inplace=True)
    data_averaged['X'] = data_averaged['Interval'] * discretization_step
    data_averaged.drop(columns=['Interval'], inplace=True)

    cols = ['X'] + [col for col in data_averaged.columns if col != 'X']
    data_averaged = data_averaged[cols]

    data_averaged['Mass_Flow_Rate'] = data_averaged['Mass_Flux'] / discretization_step
    data_averaged['Diameter_mave'] = data_averaged['Diameter_Mass_Flux'] / data_averaged['Mass_Flux']
    data_averaged['Mass_mave'] = data_averaged['Mass_Mass_Flux'] / data_averaged['Mass_Flux']

    data_averaged.to_csv(f'particles_time_{time_str}_averaged_FLUENT.csv', index=False)


dpmrpt_files = glob(os.path.join(path, '*.dpmrpt'))
for file in dpmrpt_files:
    try:
        dpmrpt_to_csv(file, path)
        print(f"✅ Обработан файл: {file}")
    except Exception as e:
        print(f"❌ Ошибка обработки файла {file}: {e}")


print('debug')