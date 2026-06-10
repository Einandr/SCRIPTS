import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *
from species_class import *
import time
import datetime
import os
import re
import numpy as np
import csv
import sqlite3
import configparser
from ast import literal_eval
import Kinetics_Initiate as kin



# import species_class as sp

from mendeleev import element
import logging

import subprocess


import shutil
import tpmath
import tputils
# from moviepy.editor import VideoFileClip, ImageClip, clips_array
# logging.basicConfig(level=logging.DEBUG)

tp.session.connect()



#TODO: написать распыл форсунок через функции для универсальности
#TODO: добавить склейку фильмов для анализа

config_path = r'D:\YASIM\2022_04_VORON\KS_GTD\Config_GTD_methane_6sp.ini'

# ВЫПОЛНЕНИЕ ПРОГРАММЫ - ДАЛЬШЕ НЕ ЛЕЗЕМ! ВСЕ НАСТРОЙКИ ЧЕРЕЗ ФАЙЛ КОНФИГУРАЦИИ
# НО ВОЗМОЖНА НЕОБХОДИМОСТЬ СМЕНЫ МНОЖИТЕЛЕЙ НОМЕРОВ ПЕРЕМЕННЫХ ДЛЯ ИНТЕГРИРОВАНИЯ

time_script_start = datetime.datetime.now()
print('time start:', time_script_start)

conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
conf.read(config_path, encoding='utf-8')

'''
Функция для конвертирования данных из файла конфигурации в кортеж. 
В файле конфигурации возможна запись в любом формате - пустая строка, одиночное значение, множество значений через запятую
'''
def convert_to_tuple(input):
    if input == '':
        print('1')
        return ()
    elif type(literal_eval(input)) == int or type(literal_eval(input)) == float or type(literal_eval(input)) == str:
        print('2')
        return literal_eval(input),
    else:
        print('3')
        return literal_eval(input)


# Директории
# work_path = conf.get('path', 'work_dir')  # рабочая директория проекта
work_path_case_data = conf.get('path', 'work_dir_case_data')  # рабочая директория результатов расчета
work_path = ''.join((work_path_case_data, '\\output\\'))
path_chemkin = conf.get('path', 'chemkin')
path_thermo_db = conf.get('path', 'thermo')

# Файлы результатов расчёта
case_name = conf.get('file', 'case')                # имя кейса
data_name_start = conf.get('file', 'data_start')    # имя первого дата-файла
data_name_end = conf.get('file', 'data_end')        # имя последнего дата-файла

# Особенности геометрии
n_cross_sections = conf.getint('geom', 'n_cross_sections')  # число промежуточных поперечных сечений для записи графиков по длине
n_cross_show = conf.getint('geom', 'n_cross_show')          # число промежуточных поперечных сечений для отображения
x_cross_start = conf.getfloat('geom', 'x_cross_start')      # координата начального поперечного сечения
x_cross_end = conf.getfloat('geom', 'x_cross_end')          # координата конечного поперечного сечения
x_cross_out = conf.getfloat('geom', 'x_cross_out')          # координата поперечного сечения для замера тяги
Slice_Position = conf.getfloat('geom', 'slice_position')    # координата продольного сечения
n_injectors = conf.getint('geom', 'n_injectors')            # число инжекторов (если рисуем картинку распыла)
Rotation = literal_eval(conf.get('geom', 'rotation'))       # углы поворота модели
width = conf.getfloat('geom', 'frame_width')                # ширина кадра
height = conf.getfloat('geom', 'frame_height')              # высота кадра


# Зоны. Нумерация +1 учтена в коде, тут задавать как в Текплоте.
Zones_transparent = convert_to_tuple(conf.get('zones', 'zones_transparent'))    # Зоны для высокой прозрачности 80% - может быть и стенка и вход, выход, симметрия
Zones_wall = convert_to_tuple(conf.get('zones', 'zones_wall'))                  # Стенки - для задания прозрачности по умолчанию
Zones_show = convert_to_tuple(conf.get('zones', 'zones_show'))                  # Включить по умолчанию выключенные зоны - вход, выход, симметрия
Zones_hide = convert_to_tuple(conf.get('zones', 'zones_hide'))                  # Выключить по умолчанию показанные зоны - интерфейсы
Zones_oblique = convert_to_tuple(conf.get('zones', 'zones_oblique'))            # Зоны для низкой прозрачности - может быть и стенка и вход, выход, симметрия
Zones_average = convert_to_tuple(conf.get('zones', 'zones_average'))            # Зоны для вычисления осредненных величин
Translucency_transp = conf.getfloat('zones', 'Translucency_transp')
Translucency_obl = conf.getfloat('zones', 'Translucency_obl')
Translucency_wall = conf.getfloat('zones', 'translucency_wall')
Translucency_slice = conf.getfloat('zones', 'translucency_slice')

# Переменные для вывода на экран
Variables_Plot = convert_to_tuple(conf.get('variables', 'variables_plot'))
Variables_Legend = convert_to_tuple(conf.get('variables', 'variables_legend'))
Variables_Min = convert_to_tuple(conf.get('variables', 'variables_min'))
Variables_Max = convert_to_tuple(conf.get('variables', 'variables_max'))
Variables_Inc = convert_to_tuple(conf.get('variables', 'variables_inc'))
Species_Plot = convert_to_tuple(conf.get('variables', 'species_plot'))
# frames_dim = convert_to_tuple(conf.get('variables', 'frames_dim'))                # первый размер - число фреймов по горизонтали, второй - по вертикали
frames_dim = (1, len(Variables_Plot)+len(Species_Plot))
Y_max = convert_to_tuple(conf.get('variables', 'y_max'))

# Режим
cff = conf.getboolean('mode', 'cff')
calculate_thrust = conf.getboolean('mode', 'calculate_thrust')
export_movie = conf.getboolean('mode', 'export_movie')
movie_all_frames_at_once = conf.getboolean('mode', 'movie_all_frames_at_once')
export_images = conf.getboolean('mode', 'export_images')
export_spray = conf.getboolean('mode', 'export_spray')
minimal_mode = conf.getboolean('mode', 'minimal_mode')
calculate_average = conf.getboolean('mode', 'calculate_average')
average_for_integration = conf.getboolean('mode', 'average_for_integration')
extract_time_varying_plots = conf.getboolean('mode', 'extract_time_varying_plots')


# Инициализация кинетики
get_species_names = kin.read_chemkin_file(path_chemkin)
get_kinetics = kin.initiate_kinetics(path_thermo_db, get_species_names)

list_species = get_kinetics[0]
list_mu = get_kinetics[1]
list_H0_298 = get_kinetics[2]
list_H0 = get_kinetics[3]

# количество компонент
n_species = len(list_species)

# количество осредняемых зон
n_zones_average = len(Zones_average)

# Создание списка имен кейс и дата файлов для загрузки
case_file_names = ''.join((work_path_case_data, case_name))
print('case files loading list:\n', case_file_names, '\n')

data_file_names = []
names = os.listdir(work_path_case_data)
data_name = data_name_start
for name in names:
    if data_name_start <= name <= data_name_end:
        new_element = ''.join((work_path_case_data, name))
        data_file_names.append(new_element)
print('data files loading list:\n')
for x in range(len(data_file_names)):
    print(data_file_names[x])

case_and_data_file_names = [case_file_names]
for item in data_file_names:
    case_and_data_file_names.append(item)

n_ts = len(data_file_names)  # число шагов по времени
print('loading ', str(n_ts), 'data files...\n')

work_path_integrate = work_path.replace('\\', '/')

# Проверка есть ли папка для сохранения результатов интегрирования
directory_integrate = ''.join((work_path, 'av_time'))
if not os.path.exists(directory_integrate):
    os.makedirs(directory_integrate)
time.sleep(1)

list_time = []
list_int_p = []
list_int_ro_vx_vx = []
os.chdir(directory_integrate)

# ВЫЧИСЛЕНИЕ ТЯГИ НА ВЫХОДНОМ СЕЧЕНИИ


if calculate_thrust:
    for ind, item in enumerate(data_file_names):
        input_list = [str(item), case_file_names, str(x_cross_out), str(variable_number_Ro_Vx_Vx_Group), str(variable_number_p_stat), work_path_integrate]
        with open('D:\\Simulation\\!Python_CIAM\\2_Comb_DES\\f_input.txt', 'w') as f:
            for line in input_list:
                f.write('%s\n' % line)
        #res = extract_thrust.extract_thrust(item, case_file_names, x_cross_out, variable_number_Ro_Vx_Vx_Group, variable_number_p_stat, work_path_integrate)
        cmd = ['python', 'D:\\Simulation\\!Python_CIAM\\2_Comb_DES\\extract_thrust.py']
        subprocess.Popen(cmd).wait()
        print('computing thrust, file № ', ind)
    shutil.move('D:\\Simulation\\!Python_CIAM\\2_Comb_DES\\f_output.txt', ''.join((work_path_integrate, '\\\\av_time\\thrust.txt')))
    os.remove('D:\\Simulation\\!Python_CIAM\\2_Comb_DES\\f_input.txt')
    print('thrust computed')
os.chdir(work_path)


# ВОЗМОЖНО нужно только для ЛЕГАСИ
variables = ['Pressure', 'X Velocity', 'Y Velocity', 'Z Velocity', 'Temperature', 'Density']
specie = 0
while specie <= n_species-1:
    variables.append(''.join(('Species ', str(specie))))
    specie += 1


# Загрузка кейс и дата файлов - без данных по частицам
print('Loading files...')
tp.macro.execute_command("$!Page Name = 'Untitled'")
tp.macro.execute_command('$!PageControl Create')
tp.new_layout()

if cff:
    tp.data.load_fluent_cff(case_and_data_file_names,
                            read_data_option=ReadDataOption.Replace,
                            include_particle_zones=False)
else:
    tp.data.load_fluent(case_filenames=[case_file_names],
                        data_filenames=data_file_names,
                        include_additional_quantities=False,
                        append=False,
                        all_poly_zones=True,
                        average_to_nodes=None,
                        variables=variables)
tp.macro.execute_command('$!RedrawAll')


dataset = tp.active_frame().dataset
n_zones = int(dataset.num_zones/dataset.num_solution_times)
time_start = min(dataset.solution_times)  # время начала записи фильма
time_end = max(dataset.solution_times)  # время окончания записи фильма
if dataset.num_solution_times > 1:
    delta_ts = (time_end-time_start) / (len(dataset.solution_times)-1)
else:
    delta_ts = 1


# переключение на последний временной шаг
tp.macro.execute_command(''.join(('$!GlobalTime SolutionTime = ', str(time_end))))

# Настройка положения и первичных параметров


tp.macro.execute_command('$!FrameLayout XYPos{X = 0}')
tp.macro.execute_command('$!FrameLayout XYPos{Y = 0}')
tp.macro.execute_command(''.join(('$!FrameLayout Width = ', str(width))))
tp.macro.execute_command(''.join(('$!FrameLayout Height = ', str(height))))
tp.macro.execute_command('$!WorkspaceView FitAllFrames')

tp.active_frame().plot().view.psi = Rotation[0]
tp.active_frame().plot().view.theta = Rotation[1]
tp.active_frame().plot().view.alpha = Rotation[2]
tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
tp.macro.execute_command('$!Interface ZoneBoundingBoxMode = Off')

#Вывод физического времени - теперь внутри функции для каждого фрейма
# tp.macro.execute_command("""$!AttachText
#   AnchorPos {X=5 Y=90}
#   TextShape {IsBold=Yes IsItalic=Yes Height=12}
#   Text = '&(solutiontime%.5f)'""")


print('Changing variables names...')


if cff:
    dataset.variable('Static Temperature').name = 'T'
    dataset.variable('Static Pressure').name = 'Pressure'
    for ind, sp in enumerate(list_species):
        dataset.variable(''.join(('Mass fraction of ', sp.name.lower()))).name = ''.join(('Y_', sp.name))


if not cff:
    dataset.variable('Temperature').name = 'T'
    for ind, sp in enumerate(list_species):
        dataset.variable(''.join(('Species ', str(ind)))).name = ''.join(('Y_', sp.name))


def Plot_Variable(Frame, Variable, Var_Min, Var_Max, Var_Increment, Contour, Slices, Slice_Orientation, Slice_Position, Trans_Wall, Trans_Slice, Trans_Transp, Trans_Obl, Legend_Text):
    print('Plotting variable', Variable, 'on frame', str(Frame), '...')
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(Frame))))
    tp.macro.execute_command(''.join(('$!Setcontourvar Var = "', Variable, '" Contourgroup = 1')))
    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
    tp.macro.execute_command("""$!AttachText 
      AnchorPos {X=1 Y=95}
      TextShape {IsBold=Yes IsItalic=Yes Height=12}
      Text = '&(solutiontime%.5f)'""")

    # Отображение скрытых по умолчанию зон
    for item in Zones_show:
        tp.active_frame().plot().fieldmap(item-1).show = True
    # Скрытие показанных по умолчанию зон
    for item in Zones_hide:
        tp.active_frame().plot().fieldmap(item-1).show = False
    # Прозрачность "прозрачных" зон
    for item in Zones_transparent:
        tp.active_frame().plot().fieldmap(item-1).effects.surface_translucency = Trans_Transp
    # Прозрачность "непрозрачных" зон
    for item in Zones_oblique:
        tp.active_frame().plot().fieldmap(item-1).effects.surface_translucency = Trans_Obl
    # Прозрачность стенок
    for item in Zones_wall:
        tp.active_frame().plot().fieldmap(item-1).effects.surface_translucency = Trans_Wall
    if Contour:
        tp.active_frame().plot().show_contour = True
    else:
        tp.active_frame().plot().show_contour = False
    if Slices:
        if Slice_Orientation == 'X':
            tp.active_frame().plot().slice(0).orientation = SliceSurface.XPlanes
            tp.active_frame().plot().slice(0).origin = (Slice_Position, tp.active_frame().plot().slice(0).origin[1], tp.active_frame().plot().slice(0).origin[2])
        elif Slice_Orientation == 'Y':
            tp.active_frame().plot().slice(0).orientation = SliceSurface.YPlanes
            tp.active_frame().plot().slice(0).origin = (tp.active_frame().plot().slice(0).origin[0], Slice_Position, tp.active_frame().plot().slice(0).origin[2])
        elif Slice_Orientation == 'Z':
            tp.active_frame().plot().slice(0).orientation = SliceSurface.ZPlanes
            tp.active_frame().plot().slice(0).origin = (tp.active_frame().plot().slice(0).origin[0], tp.active_frame().plot().slice(0).origin[1], Slice_Position)
        tp.active_frame().plot().slice(0).effects.use_translucency = True
        tp.active_frame().plot().slice(0).effects.surface_translucency = Trans_Slice
        tp.active_frame().plot().slice(0).show_primary_slice = True
        tp.active_frame().plot().slice(0).show_start_and_end_slices = False
        tp.active_frame().plot().slice(0).show_intermediate_slices = False
        tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True

    tp.active_frame().plot().contour(0).colormap_name = 'Modified Rainbow - Dark ends'
    tp.active_frame().plot().contour(0).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = Var_Min
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = Var_Max
    tp.active_frame().plot().contour(0).legend.vertical = False
    tp.active_frame().plot().contour(0).legend.label_location = ContLegendLabelLocation.Increment
    tp.active_frame().plot().contour(0).legend.label_increment = Var_Increment
    tp.active_frame().plot().contour(0).legend.position = (tp.active_frame().plot().contour(0).legend.position[0], 15)
    tp.active_frame().plot().contour(0).legend.number_font.size = 4.5
    tp.active_frame().plot().contour(0).legend.number_font.bold = True
    tp.active_frame().plot().contour(0).legend.number_font.italic = True
    tp.active_frame().plot().contour(0).legend.box.box_type = tp.constant.TextBox.None_
    tp.active_frame().plot().contour(0).legend.header.show = False
    if Legend_Text:
        tp.macro.execute_command(''.join(('$!AttachText AnchorPos {X=1 Y=5} TextShape {IsBold=Yes IsItalic=Yes Height=10} Text=\'', Legend_Text, '\'')))


def Plot_Variable_Av(Frame, Variable, Var_Min, Var_Max, Var_Increment, Contour, Slices, Slice_Orientation, Slice_Position, Trans_Wall, Trans_Slice, Trans_Transp, Trans_Obl, Legend_Text):
    print('Plotting variable Av', Variable, 'on frame', str(Frame), '...')
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(Frame))))
    tp.macro.execute_command(''.join(('$!Setcontourvar Var = "', Variable, '" Contourgroup = 1')))
    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True

    y_recmin = 0
    y_recmax = 0.65
    y_recmin += height * (Frame - 1)
    y_recmax += height * (Frame - 1)
    try:
        tp.macro.execute_command(''.join(('$!Pick AddAllInRect\n',
                                          'SelectText = Yes\n',
                                          'SelectGeoms = No\n',
                                          'SelectZones = No\n',
                                          'ConsiderStyle = Yes\n',
                                          'X1 = 0\n',
                                          'X2 = 1.5\n',
                                          'Y1 = ', str(y_recmin), '\n',
                                          'Y2 = ', str(y_recmax), '\n')))
        tp.macro.execute_command('$!Pick Clear')
    except Exception:
        print('no need for clearing time text, continue...')

    # скрытие мгновенных и отображение осредненных
    i = 0
    while i < n_zones:
        tp.active_frame().plot().fieldmaps(i).show = False
        print('hiding instant zone ', i)
        i += 1

    i = n_zones
    while i < n_zones + n_zones_average:
        tp.active_frame().plot().fieldmaps(i).show = True
        print('showing average zone ', i)
        i += 1

    if n_zones_average == n_zones:
        # Отображение скрытых по умолчанию зон
        for item in Zones_show:
            tp.active_frame().plot().fieldmap(item-1+n_zones).show = True
            print('showing zone ', item-1+n_zones)
        # Скрытие показанных по умолчанию зон
        for item in Zones_hide:
            tp.active_frame().plot().fieldmap(item-1+n_zones).show = False
            print('hiding zone ', item-1+n_zones)
        # Прозрачность "прозрачных" зон
        for item in Zones_transparent:
            tp.active_frame().plot().fieldmap(item-1+n_zones).effects.surface_translucency = Trans_Transp
        # Прозрачность "непрозрачных" зон
        for item in Zones_oblique:
            tp.active_frame().plot().fieldmap(item-1+n_zones).effects.surface_translucency = Trans_Obl
        # Прозрачность стенок
        for item in Zones_wall:
            tp.active_frame().plot().fieldmap(item-1+n_zones).effects.surface_translucency = Trans_Wall
    if Contour:
        tp.active_frame().plot().show_contour = True
    else:
        tp.active_frame().plot().show_contour = False
    if Slices:
        if Slice_Orientation == 'X':
            tp.active_frame().plot().slice(0).orientation = SliceSurface.XPlanes
            tp.active_frame().plot().slice(0).origin = (Slice_Position, tp.active_frame().plot().slice(0).origin[1], tp.active_frame().plot().slice(0).origin[2])
        elif Slice_Orientation == 'Y':
            tp.active_frame().plot().slice(0).orientation = SliceSurface.YPlanes
            tp.active_frame().plot().slice(0).origin = (tp.active_frame().plot().slice(0).origin[0], Slice_Position, tp.active_frame().plot().slice(0).origin[2])
        elif Slice_Orientation == 'Z':
            tp.active_frame().plot().slice(0).orientation = SliceSurface.ZPlanes
            tp.active_frame().plot().slice(0).origin = (tp.active_frame().plot().slice(0).origin[0], tp.active_frame().plot().slice(0).origin[1], Slice_Position)
        tp.active_frame().plot().slice(0).effects.use_translucency = True
        tp.active_frame().plot().slice(0).effects.surface_translucency = Trans_Slice
        tp.active_frame().plot().slice(0).show_primary_slice = True
        tp.active_frame().plot().slice(0).show_start_and_end_slices = False
        tp.active_frame().plot().slice(0).show_intermediate_slices = False
        tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True

    tp.active_frame().plot().contour(0).colormap_name = 'Modified Rainbow - Dark ends'
    tp.active_frame().plot().contour(0).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = Var_Min
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = Var_Max
    tp.active_frame().plot().contour(0).legend.vertical = False
    tp.active_frame().plot().contour(0).legend.label_location = ContLegendLabelLocation.Increment
    tp.active_frame().plot().contour(0).legend.label_increment = Var_Increment
    tp.active_frame().plot().contour(0).legend.position = (tp.active_frame().plot().contour(0).legend.position[0], 15)
    tp.active_frame().plot().contour(0).legend.number_font.size = 4.5
    tp.active_frame().plot().contour(0).legend.number_font.bold = True
    tp.active_frame().plot().contour(0).legend.number_font.italic = True
    tp.active_frame().plot().contour(0).legend.box.box_type = tp.constant.TextBox.None_
    tp.active_frame().plot().contour(0).legend.header.show = False
    if Legend_Text:
        tp.macro.execute_command(''.join(('$!AttachText AnchorPos {X=1 Y=5} TextShape {IsBold=Yes IsItalic=Yes Height=10} Text=\'', Legend_Text, '\'')))


def Plot_Isosurfaces(Frame, Min, Mid, Max, Translucensy):
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(Frame))))
    tp.active_frame().plot(PlotType.Cartesian3D).show_isosurfaces = True
    tp.active_frame().plot().isosurface(0).isosurface_selection = IsoSurfaceSelection.ThreeSpecificValues
    tp.active_frame().plot().isosurface(0).isosurface_values[0] = Min
    tp.active_frame().plot().isosurface(0).isosurface_values[1] = Mid
    tp.active_frame().plot().isosurface(0).isosurface_values[2] = Max
    tp.active_frame().plot().isosurface(0).effects.use_translucency = True
    tp.active_frame().plot().isosurface(0).effects.surface_translucency = Translucensy


# Отображение полей
# Фрейм №1 - температура
Plot_Variable(1, Variables_Plot[0], Variables_Min[0], Variables_Max[0], Variables_Inc[0], False, True, 'Z', Slice_Position, Translucency_wall, Translucency_slice, Translucency_transp, Translucency_obl, Variables_Legend[0])
#Plot_Isosurfaces(1, 750, 1500, 2500, 75)
tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
tp.macro.execute_command('$!RedrawAll')




print('\ncomputing total RoVx...')
tp.data.operate.execute_equation(equation='{RoVx}={Density} * {X Velocity}')

# Расходы компонент по RoVx
print('\ncomputing components RoVx...')
for sp in list_species:
    equation_RoVx = ''.join(('{RoVx_', sp.name, '} = {RoVx}*{Y_', sp.name, '}'))
    print(equation_RoVx)
    tp.data.operate.execute_equation(equation=equation_RoVx)


if not minimal_mode:
    # Вычисление числа Маха
    print('\ncomputing velocity...')
    tp.data.operate.execute_equation(equation='{Velocity} = ({X Velocity}**2+{Y Velocity}**2+{Z Velocity}**2)**0.5')

    # Уравнения теплоемкости для всех компонент:
    print('\ncomputing Cp...')
    for x in list_species:
        print(x.cp_tecplot_equation())
        tp.data.operate.execute_equation(equation=x.cp_tecplot_equation())

    # Теплоемкость смеси
    print('\ncomputing Cp and R for mixture...')
    equation_Cp_mix = '{Cp_mix}=('
    for sp in list_species:
        equation_Cp_mix += ''.join(('{Y_', str(sp.name), '}*{Cp_', str(sp.name), '}+'))
    equation_Cp_mix = equation_Cp_mix[0:-1]
    equation_Cp_mix += ')'
    print(equation_Cp_mix)
    tp.data.operate.execute_equation(equation=equation_Cp_mix)

    # Газовая постоянная смеси
    equation_R_mix = ''.join(('{R_mix}=', str(adx.R0*1000), '/('))
    for sp in list_species:
        equation_R_mix += ''.join(('{Y_', sp.name, '}*', str(sp.mu()), '+'))
    equation_R_mix = equation_R_mix[0:-1]
    equation_R_mix += ')'
    print(equation_R_mix)
    tp.data.operate.execute_equation(equation=equation_R_mix, ignore_divide_by_zero=True)

    # Газодинамические функции
    print('\ncomputing gasodynamic functions...')
    tp.data.operate.execute_equation(equation='{k}={Cp_mix}/({Cp_mix}-{R_mix})')
    tp.data.operate.execute_equation(equation='{Mach}={Velocity}/MAX(SQRT({k}*{R_mix}*{T}), 1e-6)', ignore_divide_by_zero=True)
    tp.data.operate.execute_equation(equation='{tau}=(1+({k}-1)/2*{Mach}**2)**(-1)')
    tp.data.operate.execute_equation(equation='{pi}=(1+({k}-1)/2*{Mach}**2)**(-{k}/({k}-1))')

    print('\ncomputing P* T*...')
    tp.data.operate.execute_equation(equation='{T_tot}={T}/{tau}')
    tp.data.operate.execute_equation(equation='{P_tot}={Pressure}/{pi}')

    # Поток энтальпии образования (в дальнейшем будем делить на RoVx - осреднять по расходу)
    print('\ncomputing enthalpy flow...')
    equation_RoVxH0 = '{Ro_Vx_Enthalpy_0}=('
    for sp in list_species:
        equation_RoVxH0 += ''.join(('{Y_', sp.name, '}*(', str(sp.h0_298()), ')/', str(sp.mu()), '+'))
    equation_RoVxH0 = equation_RoVxH0[0:-1]
    equation_RoVxH0 += ')'
    print(equation_RoVxH0)
    tp.data.operate.execute_equation(equation=equation_RoVxH0)


    # Импульс (для расчета тяги)
    print('\ncomputing impuls...')
    tp.data.operate.execute_equation(equation='{RoVxVx}={Density} * {X Velocity} * {X Velocity}')


# Создание новых фреймов
def create_new_frame(x0, y0, width, height):
    command = ''.join(('$!CreateNewFrame XYPos {X=', str(x0), ' Y=', str(y0), '} Width=', str(width), ' Height=', str(height)))
    tp.macro.execute_command(command)
    tp.active_frame().plot_type = PlotType.Cartesian3D


n_frames = 1
if export_images or export_movie:
    n_frames = frames_dim[0]*frames_dim[1]
    i = 0
    while i < frames_dim[0]:
        j = 0
        while j < frames_dim[1]:
            x0 = i*width
            y0 = j*height
            if i!=0 or j!=0:
                create_new_frame(x0, y0, width, height)
                print('Creating new frame', i*frames_dim[1]+j+1)
            j += 1
        i += 1
    tp.macro.execute_command('''$!Framecontrol Activatebynumber Frame = 1'''
                             '$!Linking BetweenFrames{Link3DView = Yes}'
                             '$!Linking BetweenFrames{LinkContourLevels = Yes}'
                             '$!Linking BetweenFrames{LinkSolutionTime = Yes}'
                             '$!Linking BetweenFrames{LinkSlicePositions = Yes}'
                             '''$!PropagateLinking LinkType = BetweenFrames FrameCollection = All''')
    tp.macro.execute_command('$!WorkspaceView FitAllFrames')
    tp.macro.execute_command('$!RedrawAll')


# Настройка контуров для каждого фрейма
def Plot_Concentration(Frame, Species_Name, Y_max_input, Contour, Slices, Slice_Orientation, Slice_Position, Trans_Wall, Trans_Slice, Trans_Transp, Trans_Obl, *Legend_Text):
    Variable = ''.join(('Y_', Species_Name))
    if Legend_Text:
        legend = Variable
    else:
        legend = None
    Plot_Variable(Frame, Variable, 0, Y_max_input, Y_max_input/10, Contour, Slices, Slice_Orientation, Slice_Position, Trans_Wall, Trans_Slice, Trans_Transp, Trans_Obl, legend)


def Plot_Concentration_Av(Frame, Species_Name, Y_max_input, Contour, Slices, Slice_Orientation, Slice_Position, Trans_Wall, Trans_Slice, Trans_Transp, Trans_Obl, *Legend_Text):
    Variable = ''.join(('Y_', Species_Name))
    if Legend_Text:
        legend = ''.join(('Y_', Species_Name))
    else:
        legend = None
    Plot_Variable_Av(Frame, Variable, 0, Y_max_input, Y_max_input/10, Contour, Slices, Slice_Orientation, Slice_Position, Trans_Wall, Trans_Slice, Trans_Transp, Trans_Obl, legend)


# Отображение набора поперечных сечений
def Set_Cross_Slices(Frame, n_intemediate):
    print('Plotting cross-sections on frame', str(Frame), '...')
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(Frame))))
    tp.active_frame().plot().slice(0).orientation = SliceSurface.XPlanes
    tp.active_frame().plot().slice(0).show_start_and_end_slices = True
    # При запуске в бэкграунде не слушает следующую команду ?
    tp.active_frame().plot(PlotType.Cartesian3D).show_isosurfaces = False
    tp.active_frame().plot().slice(0).show_intermediate_slices = True
    tp.active_frame().plot().slice(0).show_primary_slice = False
    tp.active_frame().plot().slice(0).end_position = (x_cross_end,
                                                      tp.active_frame().plot().slice(0).end_position[1],
                                                      tp.active_frame().plot().slice(0).end_position[2])
    tp.active_frame().plot().slice(0).num_intermediate_slices = n_intemediate
    tp.active_frame().plot().slice(0).start_position = (x_cross_start,
                                                        tp.active_frame().plot().slice(0).start_position[1],
                                                        tp.active_frame().plot().slice(0).start_position[2])
    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True


def Export_Movie(name, Frame, AllFrames):
    print('Exporting movie ...')
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(Frame))))
    movie_export_command = ''.join(('$!ExportSetup \n  ExportFName = \'', work_path, name, '.mp4\''))
    tp.macro.execute_command('''$!ExportSetup ExportFormat = MPEG4''')
    tp.macro.execute_command('''$!ExportSetup ImageWidth = 1920''')
    tp.macro.execute_command('''$!ExportSetup AnimationSpeed = 25''')
    if AllFrames:
        tp.macro.execute_command('''$!ExportSetup ExportRegion = AllFrames''')
    else:
        tp.macro.execute_command('''$!ExportSetup ExportRegion = CurrentFrame''')
    tp.macro.execute_command(movie_export_command)
    animate_command = ''.join(('$!AnimateTime\n  StartTime = ', str(time_start), '\n  EndTime = ', str(time_end),
                               '\n  Skip = 1\n  CreateMovieFile = Yes'))
    tp.macro.execute_command(animate_command)
    print('Movie on frame ', Frame, name, 'exported\n')


def Save_Image(name, Frame, AllFrames):
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(Frame))))
    if AllFrames:
        tp.export.save_jpeg(''.join((work_path, name, '.jpeg')),
                            width=4096,
                            region=ExportRegion.AllFrames,
                            supersample=3,
                            quality=100,
                            encoding=JPEGEncoding.Standard)
    else:
        tp.export.save_jpeg(''.join((work_path, name, '.jpeg')),
                            width=1920,
                            region=ExportRegion.CurrentFrame,
                            supersample=3,
                            quality=100,
                            encoding=JPEGEncoding.Standard)
    print('Image on frame ', Frame, ', name', name, 'exported\n')


# Запись изображений и видео мгновенных полей
# Отображение мгновенных полей на остальных окнах
if export_images and not minimal_mode:
    for ind, item in enumerate(Variables_Plot):
        if item != 'Pressure' and ind != 0 and item not in get_species_names:
            Plot_Variable(ind+1, item, Variables_Min[ind], Variables_Max[ind], Variables_Inc[ind], False, True, 'Z', Slice_Position, Translucency_wall, Translucency_slice, Translucency_transp, Translucency_obl, Variables_Legend[ind])
        if item == 'Pressure':
            Plot_Variable(ind+1, item, Variables_Min[ind], Variables_Max[ind], Variables_Inc[ind], True, False, 'Z', Slice_Position, Translucency_slice, Translucency_wall, Translucency_transp, Translucency_obl, Variables_Legend[ind])
    for ind, item in enumerate(Species_Plot):
        Plot_Concentration(len(Variables_Plot)+ind+1, item, Y_max[ind], False, True, 'Z', Slice_Position, Translucency_wall, Translucency_slice, Translucency_transp, Translucency_obl, True)

# Экспорт видео в продольных сечениях
# if export_movie and not minimal_mode:
#     if movie_all_frames_at_once:
#         Export_Movie('Mid_Movie', 1, True)
#     else:
#         for ind, item in enumerate(Variables_Plot):
#             Export_Movie(''.join(('Mid_', item)), ind+1, False)
#         for ind, item in enumerate(Species_Plot):
#             Export_Movie(''.join(('Mid_Y_', item)), ind+1+len(Variables_Plot), False)

# Экспорт изображений в продольных сечениях
if export_images and not minimal_mode:
    for ind, item in enumerate(Variables_Plot):
        Save_Image(''.join(('Mid_', item)), ind+1, False)
    for ind, item in enumerate(Species_Plot):
        Save_Image(''.join(('Mid_Y_', item)), ind+1+len(Variables_Plot), False)

if export_images and not minimal_mode:
    tp.active_frame().plot().view.psi = 0
    tp.active_frame().plot().view.theta = 0
    tp.active_frame().plot().view.alpha = 0
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.macro.execute_command('$!RedrawAll')

    for ind, item in enumerate(Variables_Plot):
        Save_Image(''.join(('Mid_XY_', item)), ind+1, False)
    for ind, item in enumerate(Species_Plot):
        Save_Image(''.join(('Mid_XY_Y_', item)), ind+1+len(Variables_Plot), False)

if export_movie:
    for ind, item in enumerate(Variables_Plot):
        Export_Movie(''.join(('Mid_XY_', item)), ind+1, False)
    for ind, item in enumerate(Species_Plot):
        Export_Movie(''.join(('Mid_XY_Y_', item)), ind+1+len(Variables_Plot), False)


if export_images and not minimal_mode:
    tp.active_frame().plot().view.psi = Rotation[0]
    tp.active_frame().plot().view.theta = Rotation[1]
    tp.active_frame().plot().view.alpha = Rotation[2]
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.macro.execute_command('$!RedrawAll')




# Показ поперечных сечений
Plot_Variable(1, Variables_Plot[0], Variables_Min[0], Variables_Max[0], Variables_Inc[0], False, True, 'Z', Slice_Position, Translucency_wall, Translucency_slice, Translucency_transp, Translucency_obl, Variables_Legend[0])
i = 1
while i <= n_frames:
    Set_Cross_Slices(i, n_cross_show)
    i += 1

# Запись фильмов в поперечных сечениях
if export_movie and not minimal_mode:
    if movie_all_frames_at_once:
        Export_Movie('Cross_Movie', 1, True)
    else:
        for ind, item in enumerate(Variables_Plot):
            Export_Movie(''.join(('Cross_', item)), ind+1, False)
        for ind, item in enumerate(Species_Plot):
            Export_Movie(''.join(('Cross_Y_', item)), ind+1+len(Variables_Plot), False)

# Запись изображений в поперечных сечениях
if export_images and not minimal_mode:
    for ind, item in enumerate(Variables_Plot):
        Save_Image(''.join(('Cross_', item)), ind+1, False)
    for ind, item in enumerate(Species_Plot):
        Save_Image(''.join(('Cross_Y_', item)), ind+1+len(Variables_Plot), False)

# Осреднение полей для картинок и для сравнения методов осреднения
if calculate_average:
    print('Computing average variables in Tecplot...')
    variables_to_average = [dataset.variable("T"), dataset.variable("Pressure"), dataset.variable("Velocity")]
    # variables_to_average = [dataset.variable("T")]
    for ind, sp in enumerate(list_species):
        variables_to_average.append(dataset.variable(''.join(('Y_', sp.name))))
    if not minimal_mode:
        variables_to_average.append(dataset.variable("Mach"))
    if average_for_integration:
        variables_to_average.append(dataset.variable("T_tot"))
        variables_to_average.append(dataset.variable("P_tot"))
        variables_to_average.append(dataset.variable("Ro_Vx_Enthalpy_0"))
        variables_to_average.append(dataset.variable("RoVxVx"))
        variables_to_average.append(dataset.variable("RoVx"))
        for ind, sp in enumerate(list_species):
            variables_to_average.append(dataset.variable(''.join(('RoVx_', sp.name))))
    constant_variables = [dataset.variable("X"), dataset.variable("Y"), dataset.variable("Z")]
    for strand in Zones_average:
        zones_by_strand = tputils.get_zones_by_strand(dataset)
        source_zones = zones_by_strand[strand]
        tpmath.compute_average(source_zones, variables_to_average, constant_variables)




# Создание и экспорт осредненных изображений на продольных сечениях, на поперечных сечениях


if export_images and calculate_average and not minimal_mode:
    for ind, item in enumerate(Variables_Plot):
        Plot_Variable_Av(ind + 1, item, Variables_Min[ind], Variables_Max[ind], Variables_Inc[ind], False, True, 'Z', Slice_Position, Translucency_wall, Translucency_slice, Translucency_transp, Translucency_obl, Variables_Legend[ind])
    for ind, item in enumerate(Species_Plot):
        Plot_Concentration_Av(len(Variables_Plot) + ind + 1, item, Y_max[ind], False, True, 'Z', Slice_Position, Translucency_wall, Translucency_slice, Translucency_transp, Translucency_obl, True)

    for ind, item in enumerate(Variables_Plot):
        Save_Image(''.join(('Mid_', item, '_Av')), ind+1, False)
    for ind, item in enumerate(Species_Plot):
        Save_Image(''.join(('Mid_Y_', item, '_Av')), ind+1+len(Variables_Plot), False)

    tp.active_frame().plot().view.psi = 0
    tp.active_frame().plot().view.theta = 0
    tp.active_frame().plot().view.alpha = 0
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.macro.execute_command('$!RedrawAll')

    for ind, item in enumerate(Variables_Plot):
        Save_Image(''.join(('Mid_XY_', item, '_Av')), ind+1, False)
    for ind, item in enumerate(Species_Plot):
        Save_Image(''.join(('Mid_XY_Y_', item, '_Av')), ind+1+len(Variables_Plot), False)



if export_images and not minimal_mode:
    # Создание поперечных сечений
    i = 1
    while i <= n_frames:
        Set_Cross_Slices(i, n_cross_show)
        i += 1
    tp.active_frame().plot().view.psi = Rotation[0]
    tp.active_frame().plot().view.theta = Rotation[1]
    tp.active_frame().plot().view.alpha = Rotation[2]
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.macro.execute_command('$!RedrawAll')

    for ind, item in enumerate(Variables_Plot):
        Save_Image(''.join(('Cross_', item, '_Av')), ind + 1, False)
    for ind, item in enumerate(Species_Plot):
        Save_Image(''.join(('Cross_Y_', item, '_Av')), ind + 1+len(Variables_Plot), False)

tp.macro.execute_command('$!Framecontrol Activatebynumber Frame = 1')


# Подготовка к интегрированию данных в сечениях

# Создание поперечных сечений для интегрирования
print('setting slices...')
print('time:', datetime.datetime.now())


i = n_frames
while i > 1:
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(i))))
    tp.macro.execute_command('$!FrameControl DeleteTop')
    i -= 1
tp.macro.execute_command('$!WorkspaceView FitAllFrames')

tp.active_frame().plot(PlotType.Cartesian3D).show_slices = False
Set_Cross_Slices(1, n_cross_sections)

tp.macro.execute_command('$!RedrawAll')



# Извлечение данных на сечениях
print('extracting data on slices...')
print('time:', datetime.datetime.now())

# скрытие мгновенных и отображение осредненных
i = 0
while i < n_zones:
    tp.active_frame().plot().fieldmaps(i).show = False
    i += 1
i = n_zones
while i < n_zones + n_zones_average:
    tp.active_frame().plot().fieldmaps(int(i)).show = True
    i += 1

if calculate_average:
    tp.active_frame().plot().slices(0).extract(transient_mode=TransientOperationMode.AllSolutionTimes)

# извлечение данных по времени - для записи колеблющихся графиков
if extract_time_varying_plots:
    i = n_zones
    while i < n_zones + n_zones_average:
        tp.active_frame().plot().fieldmaps(int(i)).show = False
        i += 1
    i = 0
    while i < n_zones:
        tp.active_frame().plot().fieldmaps(i).show = True
        i += 1
    tp.macro.execute_extended_command(command_processor_id='Extract Over Time',
                                      command='ExtractSliceOverTime')


# Удаление исходных зон
print('deleting initial zones...')
print('time:', datetime.datetime.now())
tp.active_frame().plot().show_shade=False
if not calculate_average:
    tp.macro.execute_command(''.join(("$!DeleteZones  [1-", str(n_zones*n_ts), "]")))
else:
    tp.macro.execute_command(''.join(("$!DeleteZones  [1-", str(n_zones*n_ts + len(Zones_average)), "]")))

# список зон для присвоения времени (без функции сортировки зон в текплоте)
print('apply times to zones...')
print('time:', datetime.datetime.now())

list_zones = '1-'

if extract_time_varying_plots:
    if calculate_average:
        max_zone = (n_cross_sections + 2)*(n_ts+1)
    else:
        max_zone = (n_cross_sections + 2)*n_ts
else:
    if calculate_average:
        max_zone = (n_cross_sections + 2)
    else:
        max_zone = 1
        print('!!!NOTHING TO SLICES EXTRACT - either turn on calculate_average or extract_time_varying_plots mode. Skipping...!!!')

if extract_time_varying_plots or average_for_integration:
    list_zones += str(max_zone)
    command_to_apply_time = ''.join(('ZoneSet=', list_zones,
                                     ';MultiZonesPerTime=TRUE;ZoneGrouping=Time;GroupSize=', str(n_cross_sections + 2),
                                     ';AssignStrands=TRUE;StrandValue=1;AssignSolutionTime=TRUE;TimeValue=0;DeltaValue=',
                                     str(delta_ts), ';TimeOption=ConstantDelta;'))
    tp.macro.execute_extended_command(command_processor_id='Strand Editor',
                                      command=command_to_apply_time)

    # Интегрирование данных по сечениям
    print('Integrating cross-sections results for time-averaging and plots:\n')
    print('time:', datetime.datetime.now())

    def Integrate(var_number, var_export_name, var_option):
        print('Integrating variable', var_export_name, ', integration option is', var_option, ', variable number is', var_number, '...')
        tp.macro.execute_extended_command(command_processor_id='CFDAnalyzer4',
                                          command=''.join(('Integrate [1-', str(n_cross_sections + 2), '] VariableOption=\'', var_option, '\' XOrigin=0 YOrigin=0 ZOrigin=0 ScalarVar=', str(var_number),
                                        ' Absolute=\'F\' ExcludeBlanked=\'F\' XVariable=1 YVariable=2 ZVariable=3 IntegrateOver=\'Cells\' IntegrateBy=\'TimeStrands\' IRange={MIN =1 MAX = 0 SKIP = 1} JRange={MIN =1 MAX = 0 SKIP = 1} KRange={MIN =1 MAX = 0 SKIP = 1} PlotResults=\'F\' PlotAs=\'Result\' TimeMin=0 TimeMax=1')))
        tp.macro.execute_extended_command(command_processor_id='CFDAnalyzer4',
                                          command=''.join(('SaveIntegrationResults FileName=\'', work_path_integrate, 'av_time/', var_option, '_', var_export_name, '.txt\'')))

    # Интегрирование необходимых величин:
    Integrate(dataset.variable('X').index+1, 'x', 'Average')
    Integrate(dataset.variable('RoVx').index+1, 'mfr', 'Scalar')

    # Расходы компонент
    for ind, sp in enumerate(list_species):
        Integrate(dataset.variable(''.join(('RoVx_', sp.name))).index+1, ''.join(('mfr_', sp.name)), 'Scalar')

    if not minimal_mode:
        Integrate(dataset.variable('T_tot').index+1, 't_tot', 'Average')
        Integrate(dataset.variable('T').index+1, 't_stat', 'Average')
        Integrate(dataset.variable('P_tot').index+1, 'p_tot', 'Average')
        Integrate(dataset.variable('Pressure').index+1, 'p_stat', 'Average')
        Integrate(dataset.variable('Velocity').index+1, 'v', 'Average')
        Integrate(dataset.variable('Mach').index+1, 'mach', 'Average')

        # Энтальпия образования состава при стандартных условиях 298 К
        Integrate(dataset.variable('Ro_Vx_Enthalpy_0').index+1, 'Ro_Vx_Enthalpy_0', 'Average')

        # Интеграл импульса по оси ОХ
        Integrate(dataset.variable('RoVxVx').index+1, 'Ro_Vx_Vx', 'Scalar')

        # Интеграл статического давления по сечению
        Integrate(dataset.variable('Pressure').index+1, 'p_stat', 'Scalar')

    # Средние концентрации
    for ind, sp in enumerate(list_species):
        name = ''.join(('Y_', sp.name))
        Integrate(dataset.variable(name).index + 1, name, 'Average')





# Создание изображений распыла из форсунок
if export_spray:

    # Список зон инжекторов
    injectors_zones_list = []
    i = n_zones
    while i < n_injectors + n_zones:
        injectors_zones_list.append(i)
        i += 1

    print('Zones number for injectors:\n', injectors_zones_list, '\n')

    # Создание списка имен кейс и дата файлов для загрузки
    case_file_names = ''.join((work_path_case_data, case_name))
    print('case files loading list:\n', case_file_names, '\n')

    data_file_name_last = ''.join((work_path_case_data, data_name_end))
    print('last data file loaded for spray picture:\n', data_file_name_last)

    # Загружка кейс и дата файлов
    tp.macro.execute_command("$!Page Name = 'Untitled'")
    tp.macro.execute_command('$!PageControl Create')
    tp.new_layout()

    tp.data.load_fluent(case_filenames=[case_file_names],
                        data_filenames=[data_file_name_last],
                        include_particle_data=True,
                        include_additional_quantities=False,
                        append=False,
                        all_poly_zones=True,
                        average_to_nodes=None)

    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)

    # Настройка положения и первичных параметров

    tp.macro.execute_command('$!FrameLayout XYPos{X = 0}')
    tp.macro.execute_command('$!FrameLayout XYPos{Y = 0}')
    tp.macro.execute_command('$!FrameLayout Width = 8')
    tp.macro.execute_command('$!FrameLayout Height = 3')
    tp.macro.execute_command('$!FrameLayout Showborder = yes')
    tp.macro.execute_command('$!WorkspaceView FitAllFrames')

    # Создание новых фреймов
    tp.macro.execute_command('''$!CreateNewFrame 
      XYPos
        {
        X = 0
        Y = 3
        }
      Width = 8
      Height = 1.25''')
    tp.active_frame().plot_type = PlotType.Cartesian3D

    tp.macro.execute_command('''$!CreateNewFrame 
      XYPos
        {
        X = 0
        Y = 4.25
        }
      Width = 8
      Height = 1.25''')
    tp.active_frame().plot_type = PlotType.Cartesian3D

    # Создание новых фреймов
    tp.macro.execute_command('''$!CreateNewFrame 
      XYPos
        {
        X = 0
        Y = 5.5
        }
      Width = 8
      Height = 3''')
    tp.active_frame().plot_type = PlotType.Cartesian3D

    # Создание новых фреймов
    tp.macro.execute_command('''$!CreateNewFrame 
      XYPos
        {
        X = 0
        Y = 8.5
        }
      Width = 8
      Height = 3''')
    tp.active_frame().plot_type = PlotType.Cartesian3D

    tp.macro.execute_command('$!WorkspaceView FitAllFrames')
    tp.macro.execute_command('$!RedrawAll')

    tp.macro.execute_command('''$!Framecontrol Activatebynumber
    Frame = 1''')
    tp.active_frame().plot().view.psi = 45
    tp.active_frame().plot().view.theta = -105
    tp.active_frame().plot().view.alpha = 100
    tp.active_frame().plot().view.width = 1.5

    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
    for item_index in (3, 4):
        tp.active_frame().plot().fieldmap(item_index).effects.surface_translucency = 80

    tp.data.operate.execute_equation(equation='{P_D_micron} = {Particle Diameter}*1e6')
    tp.macro.execute_command('''$!Setcontourvar 
      Var = "P_D_micron"
      Contourgroup = 1''')

    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20

    tp.active_frame().plot().show_contour = True
    tp.active_frame().plot().contour(0).colormap_name = 'Sequential - Pink/Purple'
    tp.active_frame().plot().contour(0).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().contour(0).legend.vertical = False
    tp.active_frame().plot().contour(0).legend.label_location = ContLegendLabelLocation.Increment
    tp.active_frame().plot().contour(0).legend.label_increment = 2
    tp.active_frame().plot().contour(0).legend.position = (95, 15)
    tp.active_frame().plot().contour(0).legend.number_font.size = 4.5
    tp.active_frame().plot().contour(0).legend.number_font.bold = True
    tp.active_frame().plot().contour(0).legend.number_font.italic = True
    tp.active_frame().plot().contour(0).legend.box.box_type = tp.constant.TextBox.None_
    tp.active_frame().plot().contour(0).legend.show_header = False

    tp.macro.execute_command("""$!AttachText 
      AnchorPos
        {
        X = 3
        Y = 5
        }
      TextShape
        {
        IsBold = Yes
        IsItalic = Yes
        Height = 10
        }
      Text = 'D (микрон)'""")

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "Temperature"
      Contourgroup = 2''')

    tp.active_frame().plot().contour(1).colormap_name = 'Modified Rainbow - Dark ends'
    tp.active_frame().plot().contour(1).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(1).colormap_filter.continuous_min = 250
    tp.active_frame().plot().contour(1).colormap_filter.continuous_max = 3000
    tp.active_frame().plot().contour(1).legend.vertical = False
    tp.active_frame().plot().contour(1).legend.label_location = ContLegendLabelLocation.Increment
    tp.active_frame().plot().contour(1).legend.label_increment = 250
    tp.active_frame().plot().contour(1).legend.position = (95, 30)
    tp.active_frame().plot().contour(1).legend.number_font.size = 4.5
    tp.active_frame().plot().contour(1).legend.number_font.bold = True
    tp.active_frame().plot().contour(1).legend.number_font.italic = True
    tp.active_frame().plot().contour(1).legend.box.box_type = tp.constant.TextBox.None_
    tp.active_frame().plot().contour(1).legend.show_header = False

    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True
    tp.active_frame().plot().slice(0).orientation = SliceSurface.ZPlanes
    tp.active_frame().plot().slice(0).effects.use_translucency = True
    tp.active_frame().plot().slice(0).effects.surface_translucency = 75
    tp.active_frame().plot().slice(0).contour.flood_contour_group_index = 1
    tp.macro.execute_command('$!RedrawAll')

    tp.active_frame().plot().view.width = 0.92
    tp.active_frame().plot().view.position = (5.65, 1.33, 5.25)

    tp.macro.execute_command("""$!AttachText 
      AnchorPos
        {
        X = 3
        Y = 20
        }
      TextShape
        {
        IsBold = Yes
        IsItalic = Yes
        Height = 10
        }
      Text = 'T (K)'""")

    tp.active_frame().plot().show_scatter = True
    tp.active_frame().plot().fieldmap(3).scatter.show = False
    tp.active_frame().plot().fieldmap(4).scatter.show = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.color = tp.active_frame().plot().contour(0)
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.symbol().shape = GeomShape.Sphere
    tp.macro.execute_command('$!GlobalScatter Var = "P_D_micron"')
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size_by_variable = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size = 0.5
    tp.macro.execute_command('$!RedrawAll')

    # фрейм 2 - вид сбоку целиком
    tp.macro.execute_command('''$!Framecontrol Activatebynumber
    Frame = 2''')
    tp.active_frame().plot().view.psi = 0
    tp.active_frame().plot().view.theta = 0
    tp.active_frame().plot().view.alpha = 0
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
    for item_index in (3, 4):
        tp.active_frame().plot().fieldmap(item_index).effects.surface_translucency = 80
    tp.active_frame().plot().view.width = 1.1
    tp.active_frame().plot().view.position = (0.6, 0, 1)

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "P_D_micron"
      Contourgroup = 1''')
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().show_contour = True
    tp.active_frame().plot().contour(0).colormap_name = 'Sequential - Pink/Purple'
    tp.active_frame().plot().contour(0).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().contour(0).legend.show = False

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "Temperature"
      Contourgroup = 2''')
    tp.active_frame().plot().contour(1).colormap_name = 'Modified Rainbow - Dark ends'
    tp.active_frame().plot().contour(1).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(1).colormap_filter.continuous_min = 250
    tp.active_frame().plot().contour(1).colormap_filter.continuous_max = 3000
    tp.active_frame().plot().contour(1).legend.show = False

    tp.macro.execute_command("""$!AttachText 
      AnchorPos
        {
        X = 3
        Y = 5
        }
      TextShape
        {
        IsBold = Yes
        IsItalic = Yes
        Height = 10
        }
      Text = 'Вид сбоку'""")

    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True
    tp.active_frame().plot().slice(0).orientation = SliceSurface.ZPlanes
    tp.active_frame().plot().slice(0).effects.use_translucency = True
    tp.active_frame().plot().slice(0).effects.surface_translucency = 75
    tp.active_frame().plot().slice(0).contour.flood_contour_group_index = 1
    tp.macro.execute_command('$!RedrawAll')

    tp.active_frame().plot().show_scatter = True
    tp.active_frame().plot().fieldmap(3).scatter.show = False
    tp.active_frame().plot().fieldmap(4).scatter.show = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.color = tp.active_frame().plot().contour(0)
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.symbol().shape = GeomShape.Sphere
    tp.macro.execute_command('$!GlobalScatter Var = "P_D_micron"')
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size_by_variable = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size = 0.5
    tp.macro.execute_command('$!RedrawAll')

    # фрейм 3 - вид сверху целиком
    tp.macro.execute_command('''$!Framecontrol Activatebynumber
    Frame = 3''')
    tp.active_frame().plot().view.psi = 90
    tp.active_frame().plot().view.theta = -180
    tp.active_frame().plot().view.alpha = -180
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
    for item_index in (3, 4):
        tp.active_frame().plot().fieldmap(item_index).effects.surface_translucency = 80
    tp.active_frame().plot().view.width = 1.1
    tp.active_frame().plot().view.position = (0.6, 1, 0)

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "P_D_micron"
      Contourgroup = 1''')
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().show_contour = True
    tp.active_frame().plot().contour(0).colormap_name = 'Sequential - Pink/Purple'
    tp.active_frame().plot().contour(0).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().contour(0).legend.show = False

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "Temperature"
      Contourgroup = 2''')
    tp.active_frame().plot().contour(1).colormap_name = 'Modified Rainbow - Dark ends'
    tp.active_frame().plot().contour(1).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(1).colormap_filter.continuous_min = 250
    tp.active_frame().plot().contour(1).colormap_filter.continuous_max = 3000
    tp.active_frame().plot().contour(1).legend.show = False

    tp.macro.execute_command("""$!AttachText 
      AnchorPos
        {
        X = 3
        Y = 5
        }
      TextShape
        {
        IsBold = Yes
        IsItalic = Yes
        Height = 10
        }
      Text = 'Вид сверху'""")

    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True
    tp.active_frame().plot().slice(0).orientation = SliceSurface.YPlanes
    tp.active_frame().plot().slice(0).effects.use_translucency = True
    tp.active_frame().plot().slice(0).effects.surface_translucency = 75
    tp.active_frame().plot().slice(0).contour.flood_contour_group_index = 1
    tp.macro.execute_command('$!RedrawAll')

    tp.active_frame().plot().show_scatter = True
    tp.active_frame().plot().fieldmap(3).scatter.show = False
    tp.active_frame().plot().fieldmap(4).scatter.show = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.color = tp.active_frame().plot().contour(0)
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.symbol().shape = GeomShape.Sphere
    tp.macro.execute_command('$!GlobalScatter Var = "P_D_micron"')
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size_by_variable = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size = 0.5
    tp.macro.execute_command('$!RedrawAll')

    # фрейм 4 - вид сбоку близко
    tp.macro.execute_command('''$!Framecontrol Activatebynumber
    Frame = 4''')
    tp.active_frame().plot().view.psi = 0
    tp.active_frame().plot().view.theta = 0
    tp.active_frame().plot().view.alpha = 0
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
    for item_index in (3, 4):
        tp.active_frame().plot().fieldmap(item_index).effects.surface_translucency = 80
    tp.active_frame().plot().view.width = 0.3
    tp.active_frame().plot().view.position = (0.4, 0, 1)

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "P_D_micron"
      Contourgroup = 1''')
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().show_contour = True
    tp.active_frame().plot().contour(0).colormap_name = 'Sequential - Pink/Purple'
    tp.active_frame().plot().contour(0).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().contour(0).legend.show = False

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "Temperature"
      Contourgroup = 2''')
    tp.active_frame().plot().contour(1).colormap_name = 'Modified Rainbow - Dark ends'
    tp.active_frame().plot().contour(1).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(1).colormap_filter.continuous_min = 250
    tp.active_frame().plot().contour(1).colormap_filter.continuous_max = 3000
    tp.active_frame().plot().contour(1).legend.show = False

    tp.macro.execute_command("""$!AttachText 
      AnchorPos
        {
        X = 3
        Y = 5
        }
      TextShape
        {
        IsBold = Yes
        IsItalic = Yes
        Height = 10
        }
      Text = 'Вид сбоку'""")

    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True
    tp.active_frame().plot().slice(0).orientation = SliceSurface.ZPlanes
    tp.active_frame().plot().slice(0).effects.use_translucency = True
    tp.active_frame().plot().slice(0).effects.surface_translucency = 75
    tp.active_frame().plot().slice(0).contour.flood_contour_group_index = 1
    tp.macro.execute_command('$!RedrawAll')

    tp.active_frame().plot().show_scatter = True
    tp.active_frame().plot().fieldmap(3).scatter.show = False
    tp.active_frame().plot().fieldmap(4).scatter.show = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.color = tp.active_frame().plot().contour(0)
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.symbol().shape = GeomShape.Sphere
    tp.macro.execute_command('$!GlobalScatter Var = "P_D_micron"')
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size_by_variable = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size = 0.5
    tp.macro.execute_command('$!RedrawAll')

    # фрейм 5 - вид сверху близко
    tp.macro.execute_command('''$!Framecontrol Activatebynumber
    Frame = 5''')
    tp.active_frame().plot().view.psi = 90
    tp.active_frame().plot().view.theta = -180
    tp.active_frame().plot().view.alpha = -180
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
    for item_index in (3, 4):
        tp.active_frame().plot().fieldmap(item_index).effects.surface_translucency = 80
    tp.active_frame().plot().view.width = 0.3
    tp.active_frame().plot().view.position = (0.4, 1, 0)

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "P_D_micron"
      Contourgroup = 1''')
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().show_contour = True
    tp.active_frame().plot().contour(0).colormap_name = 'Sequential - Pink/Purple'
    tp.active_frame().plot().contour(0).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = 0
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 20
    tp.active_frame().plot().contour(0).legend.show = False

    tp.macro.execute_command('''$!Setcontourvar 
      Var = "Temperature"
      Contourgroup = 2''')
    tp.active_frame().plot().contour(1).colormap_name = 'Modified Rainbow - Dark ends'
    tp.active_frame().plot().contour(1).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(1).colormap_filter.continuous_min = 250
    tp.active_frame().plot().contour(1).colormap_filter.continuous_max = 3000
    tp.active_frame().plot().contour(1).legend.show = False

    tp.macro.execute_command("""$!AttachText 
      AnchorPos
        {
        X = 3
        Y = 5
        }
      TextShape
        {
        IsBold = Yes
        IsItalic = Yes
        Height = 10
        }
      Text = 'Вид сверху'""")

    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True
    tp.active_frame().plot().slice(0).orientation = SliceSurface.YPlanes
    tp.active_frame().plot().slice(0).effects.use_translucency = True
    tp.active_frame().plot().slice(0).effects.surface_translucency = 75
    tp.active_frame().plot().slice(0).contour.flood_contour_group_index = 1
    tp.macro.execute_command('$!RedrawAll')

    tp.active_frame().plot().show_scatter = True
    tp.active_frame().plot().fieldmap(3).scatter.show = False
    tp.active_frame().plot().fieldmap(4).scatter.show = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.color = tp.active_frame().plot().contour(0)
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.symbol().shape = GeomShape.Sphere
    tp.macro.execute_command('$!GlobalScatter Var = "P_D_micron"')
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size_by_variable = False
    for item_index in injectors_zones_list:
        tp.active_frame().plot().fieldmap(item_index).scatter.size = 0.5
    tp.macro.execute_command('$!RedrawAll')

    # запись изображений распыла из форсунок
    tp.export.save_jpeg(''.join((work_path, 'Picture_5_spray.jpeg')),
                        width=4096,
                        region=ExportRegion.AllFrames,
                        supersample=2,
                        quality=100,
                        encoding=JPEGEncoding.Standard)

# Вывод времени выполнения скрипта
time_script_end = datetime.datetime.now()
print('time end:', time_script_end)
delta = time_script_end - time_script_start
print('script execution time:', delta.seconds, 'seconds')
print('script execution time:', "{:4.2}".format(delta.seconds / 60), 'minutes')
print('script execution time:', "{:4.2}".format(delta.seconds / 3600), 'hours')
print('THE END')
# End Macro.
