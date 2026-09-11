import os
import re
import pandas as pd
import vtk
from glob import glob



path = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\validation_from_oleg_1st\part'
file_vtk = 'my_xyz_export_time_0.139403.vtk'
discretization_step = 0.01
columns_to_average = ['diameter']


def vtk_to_csv(vtk_file, output_dir="."):
    """
        Конвертирует VTK-файл в CSV-формат с удалением префикса DP/ из имён переменных.
        Сохраняет результат в указанную папку.

        Args:
            vtk_file (str): Путь к VTK-файлу.
            output_dir (str): Папка для сохранения CSV-файла.
    """
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(vtk_file)
    reader.Update()
    if reader.GetOutput() is None:
        print(f"❌ Ошибка: не удалось прочитать файл {vtk_file}")
        return

    polydata = reader.GetOutput()
    points = polydata.GetPoints()
    point_data = polydata.GetPointData()

    headers = ["X", "Y", "Z"]
    data_arrays = []

    for i in range(point_data.GetNumberOfArrays()):
        array = point_data.GetArray(i)
        if not array:
            continue

        var_name = array.GetName().replace("DP/", "")

        if array.GetNumberOfComponents() == 1:  # Скаляр
            headers.append(var_name)
            data_arrays.append((var_name, array, 1))
        elif array.GetNumberOfComponents() == 3:  # Вектор
            headers.extend([f"{var_name}_x", f"{var_name}_y", f"{var_name}_z"])
            data_arrays.append((var_name, array, 3))

    csv_file = os.path.basename(vtk_file).replace('.vtk', '.csv')
    csv_path = os.path.join(output_dir, csv_file)

    with open(csv_path, 'w') as f:
        f.write(" ".join(headers) + "\n")
        for i in range(points.GetNumberOfPoints()):
            x, y, z = points.GetPoint(i)
            row = [str(x), str(y), str(z)]
            for var_name, array, num_components in data_arrays:
                if num_components == 1:  # Скаляр
                    row.append(str(array.GetValue(i)))
                elif num_components == 3:  # Вектор
                    vec = array.GetTuple3(i)
                    row.extend([str(vec[0]), str(vec[1]), str(vec[2])])
            f.write(" ".join(row) + "\n")

    print(f"Файл {vtk_file} успешно сконвертирован в {csv_file} со всеми данными.")
    return csv_path


def process_subdirectory(subdir, parent_dir):
    vtk_files = glob(os.path.join(subdir, '*.vtk'))
    if not vtk_files:
        print(f"⚠️ В папке {subdir} нет VTK-файлов.")
        return

    csv_files = []
    for vtk_file in vtk_files:
        csv_path = vtk_to_csv(vtk_file, subdir)
        if csv_path:
            csv_files.append(csv_path)

    if not csv_files:
        print(f"❌ Не удалось сконвертировать VTK-файлы в папке {subdir}.")
        return

    # Объединяем все CSV-файлы в подпапке в один
    all_dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, sep='\s+', engine='python')
            all_dfs.append(df)
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {csv_file}: {e}")

    if not all_dfs:
        print(f"❌ Не удалось прочитать ни один CSV-файл в папке {subdir}.")
        return

    combined_df = pd.concat(all_dfs, ignore_index=True)
    output_file = os.path.join(parent_dir, f"{os.path.basename(subdir)}.csv")
    combined_df.to_csv(output_file, sep=' ', index=False)
    print(f"✅ Все данные в папке {subdir} объединены в файл: {output_file}")

    # Удаляем временные CSV-файлы
    for csv_file in csv_files:
        try:
            os.remove(csv_file)
            print(f"✅ Удалён временный файл: {csv_file}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить временный файл {csv_file}: {e}")

    # --- Осреднение по интервалам X ---
    combined_df['X_interval'] = (combined_df['X'] / discretization_step).astype(int)
    agg_dict = {col: 'mean' for col in columns_to_average}
    grouped_data = combined_df.groupby('X_interval').agg(agg_dict).reset_index()
    data_averaged = grouped_data.rename(columns={'X_interval': 'Interval'})
    data_averaged['X'] = data_averaged['Interval'] * discretization_step
    data_averaged = data_averaged.drop(columns=['Interval'])
    output_file_averaged = os.path.join(parent_dir, f"{os.path.basename(subdir)}_averaged.csv")
    data_averaged.to_csv(output_file_averaged, sep=' ', index=False)
    print(f"✅ Осреднённые данные из папки {subdir} сохранены в: {output_file_averaged}")


def process_directory(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for subdir in dirs:
            subdir_path = os.path.join(root, subdir)
            process_subdirectory(subdir_path, root)



os.chdir(path)
# vtk_to_csv(file_vtk)
process_directory(path)

# vtk_files = [f for f in os.listdir() if f.endswith('.vtk')]
# for vtk_file in vtk_files:
#     vtk_to_csv(vtk_file)



print('debug')