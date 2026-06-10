import os
import re
import pandas as pd
import matplotlib.pyplot as plt



path = r'D:\YASIM\VORON\2025_07_AXYSIM_CIAM\QUBIQ\3D_2nd_primitive\EXPORTS'
file = 'ensight_nozzle_minus_odin_mach.csv'

os.chdir(path)
variable = 'Mach'
sort_axis = 'X'
axis = False


def read_csv_format(file_path):
    # Считываем CSV-файл в DataFrame
    df = pd.read_csv(file_path, skiprows=4)
    df.columns = df.columns.str.strip()
    # Переименовываем столбцы, если это необходимо
    df.rename(columns={
        'X-Coord': 'X',
        'Y-Coord': 'Y',
        'Z-Coord': 'Z',
    }, inplace=True, errors='ignore')

    print(df.columns)
    # df.drop(columns=['Z', 'Distance'])
    df.drop(columns=['Z', 'Distance'], inplace=True, errors='ignore')

    return df


def plot_and_save(df, variable, output_image_name):
    plt.figure(figsize=(10, 6))
    if not axis:
        # Построение графика variable от Y с перевернутыми осями
        plt.plot(df[variable], df['Y'], marker='o', linestyle='-')
        plt.xlabel(variable)
        plt.ylabel('Y')
        plt.title(f'{variable} vs Y')
    if axis:
        # Построение графика variable от X с нормальными осями
        plt.plot(df['X'], df[variable], marker='o', linestyle='-')
        plt.xlabel('X')
        plt.ylabel(variable)
        plt.title(f'{variable} vs X')

    # plt.ylim(bottom=5, top=6)
    plt.xlim(left=5, right=6)
    plt.grid(True)
    # Сохранение графика в файл
    plt.savefig(output_image_name)
    plt.close()

data = read_csv_format(file)

if axis:
    data.sort_values(by=sort_axis, inplace=True)

export_name = os.path.splitext(file)[0].replace('ensight_', '')

data.to_excel(f'data_{export_name}.xlsx', index=False)

plot_and_save(data, variable, f'pic_{export_name}.png')


print('debug')