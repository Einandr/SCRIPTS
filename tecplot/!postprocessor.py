import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *
# from species_class import *
import time
import datetime
import os
import re
import numpy as np
import csv
import sqlite3
import configparser
from ast import literal_eval
# import Kinetics_Initiate as kin
from pathlib import Path
import re
import pandas as pd
from enum import Enum, auto
from collections import Counter
# import species_class as sp

from mendeleev import element
import logging

import subprocess


import shutil
import tpmath
import tputils
from utils import *
# from moviepy.editor import VideoFileClip, ImageClip, clips_array
# logging.basicConfig(level=logging.DEBUG)


config_path = r'D:\SCRIPTS\tecplot\config_iskra_high.ini'


time_start = datetime.datetime.now()
print('Время старта:', time_start)

conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
conf.read(config_path, encoding='utf-8')

# Режим
solver = Solver[conf.get('mode', 'solver', fallback='FLUENT').upper()]
reload_data_config = conf.getboolean('mode', 'reload_data', fallback=False)
reload_data = False
if reload_data_config:
    answer = input("В конфигурации установлено reload_data = yes. Загрузить данные заново? (y/n): ").strip().lower()
    reload_data = answer == 'y'


if reload_data:
    print(f"Данные будут перезагружены.")
else:
    print(f"Данные не будут перезагружены. Экспортируем сечения на текущих загруженных данных.")

mass_flow_rate = conf.getboolean('mode', 'mass_flow_rate')
combustion_efficiency_species = conf.getboolean('mode', 'combustion_efficiency_species')
combustion_efficiency_energetic = conf.getboolean('mode', 'combustion_efficiency_energetic')
pictures = conf.getboolean('mode', 'pictures')
movies = conf.getboolean('mode', 'movies')
slices = conf.getboolean('mode', 'slices')
slices_3D_averaged = conf.getboolean('mode', 'slices_3D_averaged')
particles = conf.getboolean('mode', 'particles')
show_time = conf.getboolean('mode', 'show_time')
average_3d_fields = conf.getboolean('mode', 'average_3d_fields')

# Зоны
zone_indices_not_particles = convert_to_tuple(conf.get('zones', 'zone_indices_not_particles'))
zone_indices_particles = convert_to_tuple(conf.get('zones', 'zone_indices_particles'))

# calculate_thrust = conf.getboolean('mode', 'calculate_thrust')
# export_movie = conf.getboolean('mode', 'export_movie')
# movie_all_frames_at_once = conf.getboolean('mode', 'movie_all_frames_at_once')
# export_images = conf.getboolean('mode', 'export_images')
# export_spray = conf.getboolean('mode', 'export_spray')
# minimal_mode = conf.getboolean('mode', 'minimal_mode')
# calculate_average = conf.getboolean('mode', 'calculate_average')
# average_for_integration = conf.getboolean('mode', 'average_for_integration')
# extract_time_varying_plots = conf.getboolean('mode', 'extract_time_varying_plots')



# Файлы результатов расчёта
case_name = conf.get('file', 'case')
data_name_start = conf.get('file', 'data_start')
data_name_end = conf.get('file', 'data_end')
cff = case_name.endswith('.h5') and data_name_start.endswith('.h5') and data_name_end.endswith('.h5')
data_qubiq = conf.get('file', 'data_qubiq')

# Директории
path_case_data = conf.get('path', 'path_case_data')
path_data_qubiq = conf.get('path', 'path_data_qubiq')

dir_slices = conf.get('path', 'dir_slices')
dir_pictures = conf.get('path', 'dir_pictures')
dir_movies = conf.get('path', 'dir_movies')
dir_current_run = 'run'

match solver:
    case Solver.FLUENT:
        path_save_slices = ''.join((path_case_data, '/', dir_current_run, '/', dir_slices))
        path_save_pictures = ''.join((path_case_data, '/', dir_current_run, '/', dir_pictures))
        path_save_movies = ''.join((path_case_data, '/', dir_current_run, '/', dir_movies))
    case Solver.QUBIQ:
        path_save_slices = ''.join((path_data_qubiq, '/', dir_current_run, '/', dir_slices))
        path_save_pictures = ''.join((path_data_qubiq, '/', dir_current_run, '/', dir_pictures))
        path_save_movies = ''.join((path_data_qubiq, '/', dir_current_run, '/', dir_movies))
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")


Path(path_save_slices).mkdir(parents=True, exist_ok=True)
os.chdir(path_save_slices)


# Геометрия

# n_zones = conf.getint('geom', 'n_zones')
x_cross_start = conf.getfloat('geom', 'x_cross_start')
x_cross_end = conf.getfloat('geom', 'x_cross_end')
discretization_step_show = conf.getfloat('geom', 'discretization_step_show')
discretization_step_export_unsteady = conf.getfloat('geom', 'discretization_step_export_unsteady')
discretization_step_export_averaged = conf.getfloat('geom', 'discretization_step_export_averaged')
rotation_angles = literal_eval(conf.get('geom', 'rotation_angles'))

# x_cross_out = conf.getfloat('geom', 'x_cross_out')                      # координата поперечного сечения для замера тяги
# Slice_Position = conf.getfloat('geom', 'slice_position')                # координата продольного сечения
# n_injectors = conf.getint('geom', 'n_injectors')                        # число инжекторов (если рисуем картинку распыла)
frame_width = conf.getfloat('geom', 'frame_width')
frame_height = conf.getfloat('geom', 'frame_height')
view_width = conf.getfloat('geom', 'view_width')

# Переменные для вывода на экран
variables_plot = convert_to_tuple(conf.get('variables', 'variables_plot'))
variables_legend = convert_to_tuple(conf.get('variables', 'variables_legend'))
variables_min = convert_to_tuple(conf.get('variables', 'variables_min'))
variables_max = convert_to_tuple(conf.get('variables', 'variables_max'))
variables_increment = convert_to_tuple(conf.get('variables', 'variables_increment'))
species_plot = convert_to_tuple(conf.get('variables', 'species_plot'))
species_ymax = convert_to_tuple(conf.get('variables', 'species_ymax'))
species_increment = convert_to_tuple(conf.get('variables', 'species_increment'))

particles_variables_plot = convert_to_tuple(conf.get('variables', 'particles_variables_plot'))
particles_variables_legend = convert_to_tuple(conf.get('variables', 'particles_variables_legend'))
particles_variables_min = convert_to_tuple(conf.get('variables', 'particles_variables_min'))
particles_variables_max = convert_to_tuple(conf.get('variables', 'particles_variables_max'))
particles_variables_increment = convert_to_tuple(conf.get('variables', 'particles_variables_increment'))


tp.session.connect()

# Загрузка кейс и дата файлов
if reload_data:
    match solver:
        case Solver.FLUENT:
            print('Загрузка файлов FLUENT:')
            tp.macro.execute_command("$!Page Name = 'Untitled'")
            tp.macro.execute_command('$!PageControl Create')
            tp.new_layout()

            # Создание списка имен файлов для загрузки (с расширением на множество кейсов если будет подвижная сетка)
            # Список case файлов
            case_file_names = [''.join((path_case_data, '/', case_name))]
            print('Список case файлов:')
            for x in range(len(case_file_names)):
                print(case_file_names[x])

            # Список data файлов
            data_file_names = []
            names = os.listdir(path_case_data)
            data_name = data_name_start
            for name in names:
                if data_name_start <= name <= data_name_end:
                    new_element = ''.join((path_case_data, '/', name))
                    data_file_names.append(new_element)
            print('Список data файлов:')
            for x in range(len(data_file_names)):
                print(data_file_names[x])
            print(f'Всего загружено {len(data_file_names)} data файлов.')

            case_and_data_file_names = case_file_names + data_file_names

            if cff:
                tp.data.load_fluent_cff(case_and_data_file_names,
                                        read_data_option=ReadDataOption.Replace,
                                        include_particle_zones=True)
            else:
                tp.data.load_fluent(case_filenames=case_file_names,
                                    data_filenames=data_file_names,
                                    include_additional_quantities=False,
                                    append=False,
                                    all_poly_zones=True,
                                    average_to_nodes=None,
                                    include_particle_data=True)

        case Solver.QUBIQ:
            print('Загрузка файлов QUBIQ:')
            # tp.macro.execute_command("$!Page Name = 'Untitled'")
            # tp.macro.execute_command('$!PageControl Create')
            # tp.new_layout()
            data_file_names = [''.join((path_data_qubiq, '/', data_qubiq))]
            tp.data.load_tecplot(data_file_names,
                                 read_data_option=ReadDataOption.Replace)
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")
    tp.macro.execute_command('$!RedrawAll')


dataset = tp.active_frame().dataset
tp.macro.execute_command('$!WorkspaceView FitAllFrames')
tp.macro.execute_command('$!Interface ZoneBoundingBoxMode = Off')
plot_solution_time()


if dataset.solution_times:
    solution_time_start = min(dataset.solution_times)
    solution_time_end = max(dataset.solution_times)
else:
    solution_time_start = 0
    solution_time_end = 0
    print("Внимание: нет временных меток в наборе данных, используем 0")
if dataset.num_solution_times > 1:
    solution_delta_time = (solution_time_end-solution_time_start) / (len(dataset.solution_times)-1)
else:
    solution_delta_time = 1

# переключение на последний временной шаг
tp.macro.execute_command(''.join(('$!GlobalTime SolutionTime = ', str(solution_time_end))))

# Формирование списка компонент
species = parse_species(dataset, solver)
# Переименование переменных
rename_variables(dataset, solver)

# Удаление неиспользуемых переменных
all_variables = dataset.variables()
variable_names_all = [var.name for var in all_variables]
variable_names_to_keep = list(variables_plot) + list(particles_variables_plot) + ['CoordinateX', 'CoordinateY', 'CoordinateZ', 'Velocity_X', 'Velocity_Y', 'Velocity_Z',  'mean_Velocity_X', 'mean_Velocity_Y', 'mean_Velocity_Z', 'Density', 'mean_Density']

match solver:
    case Solver.FLUENT:
        variable_names_average_3d_fields = list(variables_plot)
    case Solver.QUBIQ:
        variable_names_average_3d_fields = [f"mean_{var}" for var in variables_plot]
        variable_names_to_keep.extend([f"mean_{var}" for var in variables_plot])
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")

variable_names_constant = ['CoordinateX', 'CoordinateY', 'CoordinateZ']

if mass_flow_rate:
    match solver:
        case Solver.FLUENT:
            variable_names_to_keep.append('RhoVx')
            variable_names_average_3d_fields.append('RhoVx')
            for sp in species:
                variable_names_to_keep.append(f'RhoVx_{sp}')
                variable_names_average_3d_fields.append(f'RhoVx_{sp}')
        case Solver.QUBIQ:
            variable_names_to_keep.append('RhoVx')
            variable_names_to_keep.append('mean_RhoVx')
            variable_names_average_3d_fields.append('mean_RhoVx')
            for sp in species:
                variable_names_to_keep.append(f'RhoVx_{sp}')
                variable_names_to_keep.append(f'mean_RhoVx_{sp}')
                variable_names_average_3d_fields.append(f'mean_RhoVx_{sp}')
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")

if combustion_efficiency_species:
    match solver:
        case Solver.FLUENT:
            for sp in species:
                variable_names_to_keep.append(f'RhoVx_{sp}')
                variable_names_average_3d_fields.append(f'RhoVx_{sp}')
        case Solver.QUBIQ:
            for sp in species:
                variable_names_to_keep.append(f'RhoVx_{sp}')
                variable_names_to_keep.append(f'mean_RhoVx_{sp}')
                variable_names_average_3d_fields.append(f'mean_RhoVx_{sp}')
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")

match solver:
    case Solver.FLUENT:
        variable_names_to_keep += [f'Y_{sp}' for sp in species]
        variable_names_average_3d_fields += [f'Y_{sp}' for sp in species]
    case Solver.QUBIQ:
        variable_names_to_keep += [f'Y_{sp}' for sp in species]
        variable_names_to_keep += [f'mean_Y_{sp}' for sp in species]
        variable_names_average_3d_fields += [f'mean_Y_{sp}' for sp in species]
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")

print(f"Переменные для сохранения: {variable_names_to_keep}")
variable_names_to_delete = [var_name for var_name in variable_names_all if var_name not in variable_names_to_keep]
print(f"Переменные для удаления: {variable_names_to_delete}")

variable_indices_to_delete = [dataset.variable(var_name).index for var_name in variable_names_to_delete]
if variable_indices_to_delete:
    dataset.delete_variables(variable_indices_to_delete)

remaining_variables = [var.name for var in dataset.variables()]
print(f"Оставшиеся переменные: {remaining_variables}")

tp.active_frame().plot().frame.width = frame_width
tp.active_frame().plot().frame.height = frame_height
tp.active_frame().plot().frame.show_border = False
set_rotation_angles((0, 0, 0))
tp.active_frame().plot().view.width = view_width
tp.macro.execute_command('$!WorkspaceView FitAllFrames')

# При повторном запуске - удаляем ранее созданные зоны на поперечных сечениях
zones_to_delete = [
    zone for zone in dataset.zones()
    if zone.name.startswith("Slice")
]
if zones_to_delete:
    dataset.delete_zones(zones_to_delete)
    print(f"Удалено {len(zones_to_delete)} зон с именами, начинающимися на 'Slice'.")
else:
    print("Зоны с именами, начинающимися на 'Slice', не найдены.")

solution_times = [zone.solution_time for zone in dataset.zones()]
time_counts = Counter(solution_times)
unique_times = sorted(time_counts.keys())
number_of_time_steps = len(unique_times)
start_time = unique_times[0]
end_time = unique_times[-1]
zones_per_time_step = time_counts[unique_times[0]]
print("Уникальные времена и количество зон для каждого:")
for time, count in time_counts.items():
    print(f"Время: {time}, количество зон: {count}")
print("\nСписок уникальных времён:", unique_times)
# Проверяем, что количество зон одинаково для всех времён
all_counts_equal = all(count == zones_per_time_step for count in time_counts.values())
if all_counts_equal:
    print("Количество зон одинаково для всех временных шагов.")
else:
    print("Внимание: количество зон различается для разных временных шагов!")

for zone in dataset.zones():
    if zone.index < zones_per_time_step:
        print(f'прозрачность зоны {zone.name} c индексом {zone.index} установлена на 80')
        tp.active_frame().plot().fieldmap(zone.index).effects.surface_translucency = 80


# Досчитываем недостающие переменные
var_names = [var.name for var in dataset.variables()]

match solver:
    case Solver.FLUENT:
        execute_equation('Velocity', '({Velocity_X}**2+{Velocity_Y}**2+{Velocity_Z}**2)**0.5', var_names)
        # execute_equation('Total Pressure', '{Static Pressure} +  {Density}*{Velocity}*{Velocity}/2', var_names)
        # execute_equation('Total Pressure Relative', '{Total Pressure} - 101000', var_names)
    case Solver.QUBIQ:
        execute_equation('mean_Velocity', '({mean_Velocity_X}**2+{mean_Velocity_Y}**2+{mean_Velocity_Z}**2)**0.5', var_names)
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")

if mass_flow_rate:
    match solver:
        case Solver.FLUENT:
            execute_equation('RhoVx', '{Density}*{Velocity_X}', var_names)
        case Solver.QUBIQ:
            execute_equation('RhoVx', '{Density}*{Velocity_X}', var_names)
            execute_equation('mean_RhoVx', '{mean_Density}*{mean_Velocity_X}', var_names)
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")

if combustion_efficiency_species:
    print('Вычисление RhoVx компонент...')
    match solver:
        case Solver.FLUENT:
            for sp in species:
                name = f'RhoVx_{sp}'
                equation = f'{{RhoVx}}*{{Y_{sp}}}'
                execute_equation(name, equation, var_names)
        case Solver.QUBIQ:
            for sp in species:
                name = f'RhoVx_{sp}'
                equation = f'{{RhoVx}}*{{Y_{sp}}}'
                execute_equation(name, equation, var_names)
                name2 = f'mean_RhoVx_{sp}'
                equation2 = f'{{mean_RhoVx}}*{{mean_Y_{sp}}}'
                execute_equation(name2, equation2, var_names)
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")


# Экспорт рисунков на продольном сечении
if pictures or movies:
    # Отрисовка и сохранение полей основных переменных
    for var_name, legend_text, var_min, var_max, var_increment in zip(variables_plot, variables_legend, variables_min, variables_max, variables_increment):
        if plot_variable(dataset, var_name, var_min, var_max, var_increment, slice='Z'):
            pic_name = ''.join(('slice_', var_name))
            if pictures:
                save_image(path_save_pictures, pic_name)
            if movies:
                export_movie(path_save_movies, pic_name, start_time, end_time)

    # Отрисовка и сохранение полей концентрации компонент
    for sp, sp_ymax, sp_increment in zip(species_plot, species_ymax, species_increment):
        var_name = f'Y_{sp}'
        if plot_variable(dataset, var_name, 0, sp_ymax, sp_increment, slice='Z'):
            pic_name = ''.join(('slice_', var_name))
            if pictures:
                save_image(path_save_pictures, pic_name)
            if movies:
                export_movie(path_save_movies, pic_name, start_time, end_time)


# Экспорт рисунков - полей на внешней стенке
views = [{'angles': (0, 0, 0), 'suffix': 'xy'},
         {'angles': (90, 180, 180), 'suffix': 'xz_up'},
         {'angles': (90, 0, 0), 'suffix': 'xz_down'}]
if pictures or movies:
    # Отрисовка и сохранение полей основных переменных
    for var_name, legend_text, var_min, var_max, var_increment in zip(variables_plot, variables_legend, variables_min, variables_max, variables_increment):
        if plot_variable(dataset, var_name, var_min, var_max, var_increment):
            if pictures:
                for view in views:
                    set_rotation_angles(view['angles'])
                    tp.active_frame().plot().view.width = view_width
                    pic_name = f"contour_{view['suffix']}_{var_name}"
                    save_image(path_save_pictures, pic_name)
            if movies:
                for view in views:
                    set_rotation_angles(view['angles'])
                    tp.active_frame().plot().view.width = view_width
                    pic_name = f"contour_{view['suffix']}_{var_name}"
                    export_movie(path_save_movies, pic_name, start_time, end_time)

    # Отрисовка и сохранение полей концентрации компонент
    for sp, sp_ymax, sp_increment in zip(species_plot, species_ymax, species_increment):
        var_name = f'Y_{sp}'
        if plot_variable(dataset, var_name, 0, sp_ymax, sp_increment):
            pic_name = ''.join(('contour_', var_name))
            if pictures:
                for view in views:
                    set_rotation_angles(view['angles'])
                    tp.active_frame().plot().view.width = view_width
                    pic_name = f"contour_{view['suffix']}_{var_name}"
                    save_image(path_save_pictures, pic_name)
            if movies:
                for view in views:
                    set_rotation_angles(view['angles'])
                    tp.active_frame().plot().view.width = view_width
                    pic_name = f"contour_{view['suffix']}_{var_name}"
                    export_movie(path_save_movies, pic_name, start_time, end_time)



print('Установка поперечных сечений...')
n_cross_sections_show = int((x_cross_end - x_cross_start) / discretization_step_show) + 1
print(f'Всего сечений для рисунков - {n_cross_sections_show} при шаге дискретизации {discretization_step_show}, x_start={x_cross_start}, x_end={x_cross_end}')

n_cross_sections_export_unsteady = int((x_cross_end - x_cross_start) / discretization_step_export_unsteady) + 1
print(f'Всего сечений для экспорта НЕСТАЦИОНАРНЫХ данных - {n_cross_sections_export_unsteady} при шаге дискретизации {discretization_step_export_unsteady}, x_start={x_cross_start}, x_end={x_cross_end}')

n_cross_sections_export_averaged = int((x_cross_end - x_cross_start) / discretization_step_export_averaged) + 1
print(f'Всего сечений для экспорта НЕСТАЦИОНАРНЫХ данных - {n_cross_sections_export_averaged} при шаге дискретизации {discretization_step_export_averaged}, x_start={x_cross_start}, x_end={x_cross_end}')



set_rotation_angles(rotation_angles)
tp.active_frame().plot().view.width = view_width

# Экспорт рисунков на поперечных сечениях
if pictures:
    # Отрисовка и сохранение полей основных переменных
    for var_name, legend_text, var_min, var_max, var_increment in zip(variables_plot, variables_legend, variables_min, variables_max, variables_increment):
        if set_cross_sections(x_cross_start, x_cross_end, n_cross_sections_show, dataset, var_name, var_min, var_max, var_increment):
            pic_name = ''.join(('cross_', var_name))
            save_image(path_save_pictures, pic_name)

    # Отрисовка и сохранение полей концентрации компонент
    for sp, sp_ymax, sp_increment in zip(species_plot, species_ymax, species_increment):
        var_name = f'Y_{sp}'
        if set_cross_sections(x_cross_start, x_cross_end, n_cross_sections_show, dataset, var_name, 0, sp_ymax, sp_increment):
            pic_name = ''.join(('cross_', var_name))
            save_image(path_save_pictures, pic_name)



# Экспорт рисунков для частиц
if particles:
    # if pictures or movies:
    set_rotation_angles((0, 0, 0))
    tp.active_frame().plot().view.width = view_width
    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = False
    tp.active_frame().plot().show_scatter = True

    for zone in zone_indices_not_particles:
        tp.active_frame().plot().fieldmaps(zone - 1).scatter.show = False
    for zone in zone_indices_particles:
        tp.active_frame().plot().fieldmaps(zone - 1).scatter.show = True
        tp.active_frame().plot().fieldmaps(zone - 1).scatter.color = tp.active_frame().plot().contour(0)
        tp.active_frame().plot().fieldmaps(zone - 1).scatter.symbol().shape = GeomShape.Sphere
        tp.active_frame().plot().fieldmaps(zone - 1).scatter.size = 0.1

    for var_name, legend_text, var_min, var_max, var_increment in zip(particles_variables_plot, particles_variables_legend, particles_variables_min, particles_variables_max, particles_variables_increment):
        if plot_variable(dataset, var_name, var_min, var_max, var_increment, slice='Z', shade=True):
            tp.active_frame().plot(PlotType.Cartesian3D).show_slices = False
            set_rotation_angles((0, 0, 0))
            tp.active_frame().plot().view.width = view_width
            pic_name = ''.join(('particles_xy_', var_name))
            save_image(path_save_pictures, pic_name)
            export_movie(path_save_movies, pic_name, start_time, end_time)
            set_rotation_angles((90, 180, 180))
            tp.active_frame().plot().view.width = view_width
            pic_name = ''.join(('particles_xz_', var_name))
            save_image(path_save_pictures, pic_name)
            export_movie(path_save_movies, pic_name, start_time, end_time)

tp.active_frame().plot().show_scatter = False


def Integrate(var_name, var_integration_option, integrate_by, start_time, end_time, min_zone, max_zone, path_save_slices_slashes):
    """Интегрирование по сечениям.
    Args:
        var_name: Имя переменной.
        var_integration_option: Опции интегрирования.
        integrate_by: Zones или TimeStrands.
    """
    try:
        var_number = dataset.variable(var_name).index + 1
    except AttributeError:
        print(f"Переменная '{var_name}' отсутствует. Пропускаем интегрирование.")
        return
    print(f'Интегрирование переменной {var_name}, параметр интегрирования - {var_integration_option}...')
    tp.macro.execute_extended_command(command_processor_id='CFDAnalyzer4',
    command=f'Integrate [{str(min_zone)}-{str(max_zone)}] VariableOption=\'{var_integration_option}\' XOrigin=0 YOrigin=0 ZOrigin=0 ScalarVar={str(var_number)} Absolute=\'F\' ExcludeBlanked=\'F\' XVariable=1 YVariable=2 ZVariable=3 IntegrateOver=\'Cells\' IntegrateBy=\'{integrate_by}\' IRange={{MIN =1 MAX = 0 SKIP = 1}} JRange={{MIN =1 MAX = 0 SKIP = 1}} KRange={{MIN =1 MAX = 0 SKIP = 1}} PlotResults=\'F\' PlotAs=\'Result\' TimeMin={start_time} TimeMax={end_time}')
    tp.macro.execute_extended_command(command_processor_id='CFDAnalyzer4',
        command=f'SaveIntegrationResults FileName=\'{path_save_slices_slashes}/{var_integration_option}_{var_name}.txt\'')


def get_integration_config(solver):
    if solver == Solver.FLUENT:
        config = {
            'CoordinateX': 'Average',
            'Temperature': 'Average',
            'Pressure': 'Average',
            'Velocity': 'Average',
            **{f'Y_{sp}': 'Average' for sp in species}
        }
        if mass_flow_rate:
            config.update({
                'RhoVx': 'Scalar'
            })
        if combustion_efficiency_species:
            config.update({
                **{f'RhoVx_{sp}': 'Scalar' for sp in species}
            })
    elif solver == Solver.QUBIQ:
        config = {
            'CoordinateX': 'Average',
            'mean_Temperature': 'Average',
            'mean_Pressure': 'Average',
            'mean_Velocity': 'Average',
            **{f'mean_Y_{sp}': 'Average' for sp in species}
        }
        if mass_flow_rate:
            config.update({
                'mean_RhoVx': 'Scalar'
            })
        if combustion_efficiency_species:
            config.update({
                **{f'mean_RhoVx_{sp}': 'Scalar' for sp in species}
            })
    else:
        raise ValueError(f"Неизвестный тип симуляции: {solver}")
    return config


def extract_values(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    values = []
    for line in lines:
        if "Zone" in line and ":" in line:
            value = float(line.split(":")[1].strip())
            values.append(value)
    return values


# Число зон в исходных данных для всех временных шагов!
n_zones = dataset.num_zones

if slices:
    # Проверка не запущен ли скрипт заново после осреднения
    # В таком случае нужно пропустить нестационарный экспорт на сечениях
    zones_after_3d_averaging = [
        zone for zone in dataset.zones()
        if zone.name.startswith("Time Average")
    ]
    if zones_after_3d_averaging:
        print(f"Присутствует {len(zones_after_3d_averaging)} зон с именем 'Time Average' после осреднения 3D полей. Скрипт был запущен заново после осреднения. Экспорт нестационартных данных на сечениях пропущен.")
    else:
        print('Подготовка к экспорту данных на сечениях - НЕСТАЦИОНАРНЫЕ поля...')
        set_cross_sections(x_cross_start, x_cross_end, n_cross_sections_export_unsteady, dataset, variables_plot[0], variables_min[0], variables_max[0], variables_increment[0])

        print('Извлечение данных на сечениях...')
        tp.active_frame().plot().slices(0).extract(transient_mode=TransientOperationMode.AllSolutionTimes)

        print('Вычисление интегралов на сечениях:')

        path_save_slices_slashes = path_save_slices.replace('\\', '/')

        # Получаем все уникальные значения time_strand
        time_strands = [zone.strand for zone in dataset.zones() if hasattr(zone, 'strand')]
        max_time_strand = max(time_strands) if time_strands else 0
        print(f"Максимальный time_strand: {max_time_strand}")
        min_time_strand = max_time_strand - n_cross_sections_export_unsteady + 1

        integration_config = get_integration_config(solver)

        # integrate_by = 'Zones'
        integrate_by = 'TimeStrands'

        for var, option in integration_config.items():
            Integrate(var, option, integrate_by, start_time, end_time, min_time_strand, max_time_strand, path_save_slices_slashes)

        # result_df = pd.DataFrame()
        # for var, option in integration_config.items():
        #     file_path = os.path.join(path_save_slices_slashes, f"{option}_{var}.txt")
        #     if not os.path.exists(file_path):
        #         print(f"Файл не найден: {file_path}")
        #         continue
        #     values = extract_values(file_path)
        #     result_df[var.replace('mean_', '')] = values




if average_3d_fields:
    # Удаляем если ранее были созданы зоны на поперечных сечениях
    zones_to_delete = [
        zone for zone in dataset.zones()
        if zone.name.startswith("Slice")
    ]
    if zones_to_delete:
        dataset.delete_zones(zones_to_delete)
        print(f"Перед осреднением 3D полей - удалено {len(zones_to_delete)} зон с именами, начинающимися на 'Slice'.")
    else:
        print("Перед осреднением 3D полей - зоны с именами, начинающимися на 'Slice', не найдены (не были созданы ранее).")

    # Удаляем зоны с инжекторами
    zones_to_delete_particles = [
        zone for zone in dataset.zones()
        if zone.name.startswith("injection")
    ]
    if zones_to_delete_particles:
        dataset.delete_zones(zones_to_delete_particles)
        print(f"Перед осреднением 3D полей - удалено {len(zones_to_delete_particles)} зон с именами, начинающимися на 'injection'.")
    else:
        print("Перед осреднением 3D полей - зоны с именами, начинающимися на 'injection', не найдены (кейс без частиц).")

    # Для решателя FLUENT проводим отдельно вычисление осредненных полей
    if solver == Solver.FLUENT:
        print('Вычисление средних значений на 3D полях...')
        variables_to_average = [dataset.variable(name) for name in variable_names_average_3d_fields]
        variables_constant = [dataset.variable(name) for name in variable_names_constant]
        zones_by_strand = tputils.get_zones_by_strand(dataset)

        # Переключение на первый временной шаг
        tp.macro.execute_command(''.join(('$!GlobalTime SolutionTime = ', str(solution_time_start))))

        # Проверка не запущен ли скрипт заново
        zones_after_3d_averaging = [
            zone for zone in dataset.zones()
            if zone.name.startswith("Time Average")
        ]
        if zones_after_3d_averaging:
            print(f"Присутствует {len(zones_after_3d_averaging)} зон с именем 'Time Average' после осреднения 3D полей. Скрипт был запущен заново после осреднения. Вычисление осреднённых 3D полей пропущено, переходим к рисункам и экспорту осреднённых данных на сечениях.")
        else:
            for zone in zone_indices_not_particles:
                source_zones = zones_by_strand[zone]
                tpmath.compute_average(source_zones, variables_to_average, variables_constant)

            # Удаление нестационарных зон
            zones_to_delete_unsteady = [
                zone for zone in dataset.zones()
                if not zone.name.startswith("Time Average")
            ]
            if zones_to_delete_unsteady:
                dataset.delete_zones(zones_to_delete_unsteady)
                print(f"Удалено {len(zones_to_delete_unsteady)} нестационарных зон с именами, НЕ начинающимися на 'Time Average'.")
            else:
                print("Нестационарных зоне нет -  это невозможно!")

            # Отображение осреднённых зон
            for zone in zone_indices_not_particles:
                tp.active_frame().plot().fieldmaps(zone - 1).show = True

            for zone in dataset.zones():
                if zone.index < zones_per_time_step:
                    print(f'прозрачность зоны {zone.name} c индексом {zone.index} установлена на 80')
                    tp.active_frame().plot().fieldmap(zone.index).effects.surface_translucency = 80

    prefix = "mean_" if solver == Solver.QUBIQ else ""

    # Экспорт рисунков на продольном сечении
    if pictures:
        set_rotation_angles((0, 0, 0))
        tp.active_frame().plot().view.width = view_width
        # Отрисовка полей основных переменных
        for var_name, legend_text, var_min, var_max, var_increment in zip(variables_plot, variables_legend, variables_min, variables_max, variables_increment):
            current_var_name = f"{prefix}{var_name}"
            if plot_variable(dataset, current_var_name, var_min, var_max, var_increment, slice='Z'):
                pic_name = ''.join(('slice_av_', var_name))
                save_image(path_save_pictures, pic_name)

        # Отрисовка полей концентрации компонент
        for sp, sp_ymax, sp_increment in zip(species_plot, species_ymax, species_increment):
            var_name = f'Y_{sp}'
            current_var_name = f"{prefix}{var_name}"
            if plot_variable(dataset, current_var_name, 0, sp_ymax, sp_increment, slice='Z'):
                pic_name = ''.join(('slice_av_', var_name))
                save_image(path_save_pictures, pic_name)

        # Отрисовка полей на внешней стенке - основных переменных
        for var_name, legend_text, var_min, var_max, var_increment in zip(variables_plot, variables_legend, variables_min, variables_max, variables_increment):
            current_var_name = f"{prefix}{var_name}"
            if plot_variable(dataset, current_var_name, var_min, var_max, var_increment):
                for view in views:
                    set_rotation_angles(view['angles'])
                    tp.active_frame().plot().view.width = view_width
                    pic_name = f"contour_av_{view['suffix']}_{var_name}"
                    save_image(path_save_pictures, pic_name)

        # Отрисовка полей на внешней стенке - концентрации компонент
        for sp, sp_ymax, sp_increment in zip(species_plot, species_ymax, species_increment):
            var_name = f'Y_{sp}'
            current_var_name = f"{prefix}{var_name}"
            if plot_variable(dataset, current_var_name, 0, sp_ymax, sp_increment):
                pic_name = ''.join(('contour_', var_name))
                for view in views:
                    set_rotation_angles(view['angles'])
                    tp.active_frame().plot().view.width = view_width
                    pic_name = f"contour_{view['suffix']}_{var_name}"
                    save_image(path_save_pictures, pic_name)

    print('Установка поперечных сечений...')
    set_rotation_angles(rotation_angles)
    tp.active_frame().plot().view.width = view_width

    # Экспорт рисунков на поперечных сечениях
    if pictures:
        # Отрисовка и сохранение полей основных переменных
        for var_name, legend_text, var_min, var_max, var_increment in zip(variables_plot, variables_legend, variables_min, variables_max, variables_increment):
            current_var_name = f"{prefix}{var_name}"
            if set_cross_sections(x_cross_start, x_cross_end, n_cross_sections_show, dataset, current_var_name, var_min, var_max, var_increment):
                pic_name = ''.join(('cross_av_', var_name))
                save_image(path_save_pictures, pic_name)

        # Отрисовка и сохранение полей концентрации компонент
        for sp, sp_ymax, sp_increment in zip(species_plot, species_ymax, species_increment):
            var_name = f'Y_{sp}'
            current_var_name = f"{prefix}{var_name}"
            if set_cross_sections(x_cross_start, x_cross_end, n_cross_sections_show, dataset, current_var_name, 0, sp_ymax, sp_increment):
                pic_name = ''.join(('cross_av_', var_name))
                save_image(path_save_pictures, pic_name)

    if slices_3D_averaged:
        print('Подготовка к экспорту данных на сечениях - ОСРЕДНЁННЫЕ поля...')
        set_cross_sections(x_cross_start, x_cross_end, n_cross_sections_export_averaged, dataset, variables_plot[0], variables_min[0], variables_max[0], variables_increment[0])

        print('Извлечение данных на сечениях...')
        tp.active_frame().plot().slices(0).extract(transient_mode=TransientOperationMode.AllSolutionTimes)
        # tp.active_frame().plot().slices(0).extract(transient_mode=TransientOperationMode.CurrentSolutionTime)

        print('Вычисление интегралов на сечениях:')
        path_save_slices_slashes = path_save_slices.replace('\\', '/')

        integration_config = get_integration_config(solver)

        integrate_by = 'Zones'
        # integrate_by = 'TimeStrands'

        for var, option in integration_config.items():
            Integrate(var, option, integrate_by, start_time, end_time, len(zone_indices_not_particles)+1, len(zone_indices_not_particles)+n_cross_sections_export_averaged, path_save_slices_slashes)

        result_df = pd.DataFrame()
        for var, option in integration_config.items():
            file_path = os.path.join(path_save_slices_slashes, f"{option}_{var}.txt")
            if not os.path.exists(file_path):
                print(f"Файл не найден: {file_path}")
                continue
            values = extract_values(file_path)
            result_df[var.replace('mean_', '')] = values

        result_df.to_csv(os.path.join(path_save_slices_slashes, "combined_results.csv"), index=False)



# tp.session.disconnect()

time_end = datetime.datetime.now()
print('Время завершения:', time_end)
delta_time = time_end - time_start
print(f'Время выполнения скрипта {delta_time.seconds} секунд / {delta_time.seconds / 60:.2f} минут / {delta_time.seconds / 3600:.2f} часов')

