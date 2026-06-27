import os
import re
import pandas as pd
import vtk



path = r'D:\YASIM\VORON\2026_15_Spalding_Combustion\QUBIQ\T1000K_freq10000_comb_v0.0ms_pmfr0.00000179\part'
file_vtk = 'my_xyz_export_time_0.139403.vtk'
discretization_step = 0.1


def vtk_to_csv(vtk_file, output_dir="."):
    """
        Конвертирует VTK-файл в CSV-формат с удалением префикса DP/ из имён переменных.
        Сохраняет результат в указанную папку.

        Args:
            vtk_file (str): Путь к VTK-файлу.
            output_dir (str): Папка для сохранения XYZ-файла.
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


os.chdir(path)
# vtk_to_csv(file_vtk)

vtk_files = [f for f in os.listdir() if f.endswith('.vtk')]
for vtk_file in vtk_files:
    vtk_to_csv(vtk_file)


#
#
#
#
#
#
#
#
#
#
#
#
#
# # СВЕРЯТЬ ПОРЯДОК С ХУЗ ФАЙЛОМ
# names = ['unknown', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'Diameter', 'Temperature']
# # names = ['unknown', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'Temperature', 'Diameter']
#
# os.chdir(path)
# data = pd.read_csv(file_xyz, delimiter='\t', names=names, index_col=False, skiprows=2)
# data.drop(columns=['unknown'], inplace=True)
# data.sort_values(by='CoordinateX', inplace=True)
# data.to_csv('points_for_tecplot_QUBIQ.csv', index=False)
#
#
#
# # Дискретизация по ОХ с шагом discretization_step
#
# data['X_interval'] = (data['CoordinateX'] / discretization_step).astype(int)
#
# # Группировка данных по интервалам и вычисление средних значений
# grouped_data = data.groupby('X_interval').agg({'Diameter': 'mean', 'Temperature': 'mean'}).reset_index()
#
# # Создание нового DataFrame с осредненными значениями
# data_averaged = grouped_data.rename(columns={'X_interval': 'Interval'})
# data_averaged['CoordinateX'] = data_averaged['Interval'] * discretization_step
#
# # Удаление вспомогательного столбца
# data_averaged = data_averaged.drop(columns=['Interval'])
# data_averaged.to_csv('points_averaged_QUBIQ.csv', index=False)
#





print('debug')