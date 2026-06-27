import time
import datetime
import os
import re
import numpy as np
from math import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.pylab as pylab

params = {'legend.fontsize'      : 'xx-large',
          'legend.title_fontsize': 'xx-large',
          'axes.labelsize'       : 'xx-large',
          'axes.titlesize'       : 'xx-large',
          'xtick.labelsize'      : 'xx-large',
          'ytick.labelsize'      : 'xx-large'}
pylab.rcParams.update(params)
import csv
import pandas as pd
import xlsxwriter
# import Kinetics_Initiate as kin
from statistics import mean
from mpl_toolkits.mplot3d import Axes3D
import logging

logging.basicConfig(level=logging.WARNING)
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)
import configparser
from ast import literal_eval
# from moviepy.editor import VideoFileClip, ImageClip, clips_array
from PIL import Image
from data_loader import *

from postprocessing.utils import plot_result, create_animation

# im = Image.open('movie_plots_etta_G_fuel.gif')
# im.save('movie_plots_etta_G_fuel3.gif', save_all=True, loop=0)


# os.chdir('D:\\Simulation\\!TECPLOT_MACRO\\PYTECPLOT\\Result_2019\\Stupa\\debugfolder\\')

# TODO: переписать scrap_local_folder с наследованием
# TODO: transfer_thermo реализовать экспорт текстового файла формата полиномов NASA чтоб не перебивать вручную

# TODO: добавить график потерь давления
# TODO: добавить безразмерную координату, безразмерные величины, режим показа графиков размерный/безразмерный
# TODO: определение сечения замера расхода, замера тяги, замера выходных параметров по координате, а не по номеру
# TODO: баг с выходом обрезки лево-право за границы доступного диапазона (попытка записи НАН в таблицу эксель)
# TODO: расход топлива и расход воздуха задается напрямую - добавить возможность


config_path = r'D:\SCRIPTS\tecplot\config_iskra_high.ini'

style_average = '-'
style_instant = '--'

GOST = True
line_width = 2

time_start = datetime.datetime.now()
print('Время старта:', time_start)

conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
conf.read(config_path, encoding='utf-8')

# Директории
path_all_slices = conf.get('path', 'path_all_slices')
path_plots_and_animations = conf.get('path', 'path_plots_and_animations')
dir_current_run_plots_and_animations = conf.get('path', 'dir_current_run_plots_and_animations')
dir_plots = conf.get('path', 'dir_plots')
dir_animations = conf.get('path', 'dir_animations')

path_save_plots = ''.join((path_plots_and_animations, '/', dir_current_run_plots_and_animations, '/', dir_plots))
path_save_animations = ''.join((path_plots_and_animations, '/', dir_current_run_plots_and_animations, '/', dir_animations))
Path(path_save_plots).mkdir(parents=True, exist_ok=True)
Path(path_save_animations).mkdir(parents=True, exist_ok=True)
os.chdir(path_save_plots)

# Режим
mass_flow_rate = conf.getboolean('mode', 'mass_flow_rate')
combustion_efficiency_species = conf.getboolean('mode', 'combustion_efficiency_species')


aggregator = DataAggregator(work_path=path_all_slices)

time = aggregator.time
x_coord = aggregator.x_coord
temperature = aggregator.get_parameter("Temperature")
pressure = aggregator.get_parameter("Pressure")
velocity = aggregator.get_parameter("Velocity")

df_averaged = aggregator.get_averaged_dataframe(left=0, right=0)
df_instant = aggregator.get_instant_dataframe(left=0, right=0, point_fraction=1)

data_on_interval = aggregator.get_data_on_interval(left=0, right=0)

y_limits = {
    'particle_diameter'             : [0, 5],
    'particle_mass_flow_rate'       : [0, 1],
    'particle_mass'                 : [0, 1.8e-13],
    'particle_combustion_efficiency': [0, 1.1],
    'Temperature'                   : [500, 2500],
    'Pressure'                      : [0, 1400000],
    'Velocity'                      : [0, 1000],
    'Y_air'                         : [0, 1],
    'Y_cp'                          : [0, 1],
    'Y_gpg'                         : [0, 0.1],
    'mass_flow_rate'                : [0, 10],
    'gas_combustion_efficiency'     : [0, 1.1],
}

x_limit_low = -0.5
x_limit_high = 1.7
particles_mass_flow_rate = 0.495
gas_mass_flow_rate = 6.58 + 0.405
mass_flow_rate_all = gas_mass_flow_rate + particles_mass_flow_rate
x_t_label = r'$X,\ м$'
# x_t_label = r'$\tau,\ с$'
y_Cp_label = r'$Cp\ (\frac{Дж}{кг \cdot К})$'
y_H_label = r'$H\ (\frac{Дж}{кг})$'

# colors = plt.cm.tab10.colors[:len(section_names)]
colors = plt.cm.tab10.colors[:10]
y_limits_default = None
pic_base_name = ''

os.chdir(path_save_plots)

plot_result(f"{pic_base_name}Temperature", x_t_label, r'$T,\ K$', (df_averaged, ['Temperature'], [style_average], ['осредненная'], y_limits['Temperature'], colors),
            (df_instant, ['Temperature'], [style_instant], ['мгновенная'], y_limits_default, colors), GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width)
plot_result(f"{pic_base_name}Pressure", x_t_label, r'$p,\ Па$', (df_averaged, ['Pressure'], [style_average], ['осредненная'], y_limits['Pressure'], colors),
                                                                    (df_instant, ['Pressure'], [style_instant], ['мгновенная'], y_limits_default, colors), GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width)
plot_result(f"{pic_base_name}Velocity", x_t_label, r'$\upsilon,\ м/с$', (df_averaged, ['Velocity'], [style_average], ['осредненная'], y_limits['Velocity'], colors),
                                                                            (df_instant, ['Velocity'], [style_instant], ['мгновенная'], y_limits_default, colors), GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width)
plot_result(f"{pic_base_name}gas_Y1", x_t_label, r'$Y$', (df_averaged, ['Y_air', 'Y_cp', 'Y_gpg'], [style_average, style_average, style_average], ['осредненная - массовая доля воздуха', 'осредненная - массовая доля ПС', 'осредненная - массовая доля ГПГ'], y_limits['Y_air'], colors),
                                                         (df_instant, ['Y_air', 'Y_cp', 'Y_gpg'], [style_instant, style_instant, style_instant], ['мгновенная - массовая доля воздуха', 'мгновенная - массовая доля ПС', 'мгновенная - массовая доля ГПГ'], y_limits_default, colors), GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width),
plot_result(f"{pic_base_name}gas_Y2", x_t_label, r'$Y$', (df_averaged, ['Y_air', 'Y_cp'], [style_average, style_average], ['осредненная - массовая доля воздуха', 'осредненная - массовая доля ПС'], y_limits['Y_air'], colors),
                                                         (df_instant, ['Y_air', 'Y_cp'], [style_instant, style_instant], ['мгновенная - массовая доля воздуха', 'мгновенная - массовая доля ПС'], y_limits_default, colors), GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width),
plot_result(f"{pic_base_name}gas_Y3", x_t_label, r'$Y$', (df_averaged, ['Y_gpg'], [style_average], ['осредненная - массовая доля ГПГ'], y_limits['Y_gpg'], colors),
                                                         (df_instant, ['Y_gpg'], [style_instant], ['мгновенная - массовая доля ГПГ'], y_limits_default, colors), GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width),

if mass_flow_rate and combustion_efficiency_species:
    plot_result(f"{pic_base_name}gas_mass_flow_rate", x_t_label, r'$\dot{m},\ кг/с$',
                (df_averaged, ['RhoVx', 'RhoVx_gpg', 'RhoVx_cp', 'RhoVx_air'], [style_average]*4, ['осредненная - расход', 'осредненная - расход ГПГ', 'осредненная - расход ПС', 'осредненная - расход воздуха'], y_limits['mass_flow_rate'], colors),
                (df_instant, ['RhoVx', 'RhoVx_gpg', 'RhoVx_cp', 'RhoVx_air'], [style_instant]*4, ['мгновенная - расход', 'мгновенная - расход ГПГ', 'мгновенная - расход ПС', 'мгновенная - расход воздуха'], y_limits_default, colors),
                GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width, horizontal_lines=[mass_flow_rate_all, gas_mass_flow_rate])








os.chdir(path_save_animations)

config_temperature = [
    (df_averaged, ['Temperature'], [style_average], ['осредненная'], y_limits['Temperature'], colors),
    (data_on_interval, ['Temperature'], [style_instant], ['мгновенная'], y_limits_default, colors)
]

config_pressure = [
    (df_averaged, ['Pressure'], [style_average], ['осредненная'], y_limits['Pressure'], colors),
    (data_on_interval, ['Pressure'], [style_instant], ['мгновенная'], y_limits_default, colors)
]

config_velocity = [
    (df_averaged, ['Velocity'], [style_average], ['осредненная'], y_limits['Velocity'], colors),
    (data_on_interval, ['Velocity'], [style_instant], ['мгновенная'], y_limits_default, colors)
]

config_y1 = [
    (df_averaged, ['Y_air', 'Y_cp', 'Y_gpg'], [style_average]*3, ['осредненная - массовая доля воздуха', 'осредненная - массовая доля ПС', 'осредненная - массовая доля ГПГ'], y_limits['Y_air'], colors),
    (data_on_interval, ['Y_air', 'Y_cp', 'Y_gpg'], [style_instant]*3, ['мгновенная - массовая доля воздуха', 'мгновенная - массовая доля ПС', 'мгновенная - массовая доля ГПГ'], y_limits_default, colors)
]

config_y2 = [
    (df_averaged, ['Y_air', 'Y_cp'], [style_average]*2, ['осредненная - массовая доля воздуха', 'осредненная - массовая доля ПС'], y_limits['Y_air'], colors),
    (data_on_interval, ['Y_air', 'Y_cp'], [style_instant]*2, ['мгновенная - массовая доля воздуха', 'мгновенная - массовая доля ПС'], y_limits_default, colors)
]

config_y3 = [
    (df_averaged, ['Y_gpg'], [style_average], ['осредненная - массовая доля ГПГ'], y_limits['Y_gpg'], colors),
    (data_on_interval, ['Y_gpg'], [style_instant], ['мгновенная - массовая доля ГПГ'], y_limits_default, colors)
]

if mass_flow_rate and combustion_efficiency_species:
    config_mass_flow_rate = [
        (df_averaged, ['RhoVx', 'RhoVx_gpg', 'RhoVx_cp', 'RhoVx_air'], [style_average]*4, ['осредненная - расход', 'осредненная - расход ГПГ', 'осредненная - расход ПС', 'осредненная - расход воздуха'], y_limits['mass_flow_rate'], colors),
        (data_on_interval, ['RhoVx', 'RhoVx_gpg', 'RhoVx_cp', 'RhoVx_air'], [style_instant]*4, ['мгновенная - расход', 'мгновенная - расход ГПГ', 'мгновенная - расход ПС', 'мгновенная - расход воздуха'], y_limits_default, colors)
    ]

show_time = True

create_animation(
    anim_base_name='',
    x_label=x_t_label,
    y_label=r'$T,\ K$',
    aggregator=aggregator,
    data_on_interval=data_on_interval,
    x_coord=x_coord,
    params_config=config_temperature,
    GOST=GOST,
    x_limits=[x_limit_low, x_limit_high],
    line_width=line_width,
    fps=24,
    output_name='Temperature',
    show_time=show_time
)

create_animation(
    anim_base_name='',
    x_label=x_t_label,
    y_label=r'$p,\ Па$',
    aggregator=aggregator,
    data_on_interval=data_on_interval,
    x_coord=x_coord,
    params_config=config_pressure,
    GOST=GOST,
    x_limits=[x_limit_low, x_limit_high],
    line_width=line_width,
    fps=24,
    output_name='Pressure',
    show_time=show_time
)

create_animation(
    anim_base_name='',
    x_label=x_t_label,
    y_label=r'$\upsilon,\ м/с$',
    aggregator=aggregator,
    data_on_interval=data_on_interval,
    x_coord=x_coord,
    params_config=config_velocity,
    GOST=GOST,
    x_limits=[x_limit_low, x_limit_high],
    line_width=line_width,
    fps=24,
    output_name='Velocity',
    show_time=show_time
)

create_animation(
    anim_base_name='',
    x_label=x_t_label,
    y_label=r'$Y$',
    aggregator=aggregator,
    data_on_interval=data_on_interval,
    x_coord=x_coord,
    params_config=config_y1,
    GOST=GOST,
    x_limits=[x_limit_low, x_limit_high],
    line_width=line_width,
    fps=24,
    output_name='Y1',
    show_time=show_time
)

create_animation(
    anim_base_name='',
    x_label=x_t_label,
    y_label=r'$Y$',
    aggregator=aggregator,
    data_on_interval=data_on_interval,
    x_coord=x_coord,
    params_config=config_y2,
    GOST=GOST,
    x_limits=[x_limit_low, x_limit_high],
    line_width=line_width,
    fps=24,
    output_name='Y2',
    show_time=show_time
)

create_animation(
    anim_base_name='',
    x_label=x_t_label,
    y_label=r'$Y$',
    aggregator=aggregator,
    data_on_interval=data_on_interval,
    x_coord=x_coord,
    params_config=config_y3,
    GOST=GOST,
    x_limits=[x_limit_low, x_limit_high],
    line_width=line_width,
    fps=24,
    output_name='Y3',
    show_time=show_time
)

if mass_flow_rate and combustion_efficiency_species:
    create_animation(
        anim_base_name='',
        x_label=x_t_label,
        y_label=r'$\dot{m},\ кг/с$',
        aggregator=aggregator,
        data_on_interval=data_on_interval,
        x_coord=x_coord,
        params_config=config_mass_flow_rate,
        GOST=GOST,
        x_limits=[x_limit_low, x_limit_high],
        line_width=line_width,
        horizontal_lines=[mass_flow_rate_all, gas_mass_flow_rate],
        fps=24,
        output_name='gas_mass_flow_rate',
        show_time=show_time
    )




# plot_result(f"{pic_base_name}gas_mass_flow_rate", x_t_label, r'$\dot{m},\ кг/с$', (df_instant, ['RhoVx', 'RhoVx_gpg', 'RhoVx_cp', 'RhoVx_air'], [style_instant, style_instant, style_instant, style_instant], ['мгновенная - расход', 'мгновенная - расход ГПГ', 'мгновенная - расход ПС', 'мгновенная - расход воздуха'], y_limits['gas_mass_flow_rate'], colors), GOST=GOST, x_limits=[x_limit_low, x_limit_high], swap_axes=False, line_width=line_width, horizontal_lines=[mass_flow_rate_all, gas_mass_flow_rate])


config_path = r'D:\YASIM\2022_04_VORON\Config_valid_5sp.ini'

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


work_path = conf.get('average', 'work_path')  # рабочая директория проекта

n_inj = conf.getint('geom', 'n_injectors')  # число инжекторов
mfr_fuel_inj = conf.getfloat('average', 'mfr_fuel_inj')

''' Проводится автоматический расчет стехиометрии брутто-реакции, для этого необходимо указать формулы топлива, 
окислителя, и продуктов реакции. Компоненты должны присутствовать в подключаемой базе химической кинетики '''

# Массовый состав газа на входе. Последний компонент вычисляется как 1-сумма остальных
Species_in = convert_to_tuple(conf.get('average', 'Species_in'))
Y_in = convert_to_tuple(conf.get('average', 'Y_in'))
oxidizer = conf.get('average', 'oxidizer')
fuel = conf.get('average', 'fuel')
products = convert_to_tuple(conf.get('average', 'products'))
minimal_mode = conf.getboolean('mode', 'minimal_mode')
brutto_kinetics = conf.getboolean('mode', 'brutto_kinetics')
equilibrium_info = conf.getboolean('mode', 'equilibrium_info')
show_etta_energetic = conf.getboolean('mode', 'show_etta_energetic')
show_etta_fuel = conf.getboolean('mode', 'show_etta_fuel')
'''
Энергетическая полнота вычисляется для брутто-кинетики тоже. Однако её график всегда можно скрыть
'''
if equilibrium_info:
    folder_equilibrium_state = conf.get('average', 'folder_equilibrium_state')
    file_equilibrium_state = conf.get('average', 'file_equilibrium_state')

# в зависимости от направления оси ОХ и геометрии камеры, выбираем сечение для определения параметров на выходе
n_slices = conf.getint('geom', 'n_cross_sections') + 2  # число сечений разбиения на длине камеры сгорания
n_offset = conf.getint('average', 'n_offset')  # в каком сечении измеряется расход - ВАЖНО при определении альфа
n_output = conf.getint('average', 'n_output')  # в каком сечении измеряются параметры на выходе
n_thrust = conf.getint('average', 'n_thrust')  # в каком сечении измеряется тяга (можно использовать если при рассечении остается только одна зона)

# Выбор интервала осреднения по ВРЕМЕНИ для определения АЛЬФА и других параметров
average_left = conf.getint('average', 'average_left')
average_right = conf.getint('average', 'average_right')

x_inj = conf.getfloat('average', 'x_inj')  # Координата расположения инжекторов - при отображении полноты левее этой точки будет 0

# максимальные значения величин на графиках
if equilibrium_info:
    t_equil = conf.getfloat('average', 't_equil')
    y_equil = conf.getfloat('average', 'y_equil')
y_main = conf.getfloat('average', 'y_main')
mfr_fuel = conf.getfloat('average', 'mfr_fuel')
etta = conf.getfloat('average', 'etta')

# границы расчетной области
x_min = conf.getfloat('average', 'x_min')
x_max = conf.getfloat('average', 'x_max')
x_throat = conf.getfloat('average', 'x_throat')

# Имена переменных в таблице равновесного состояния
if equilibrium_info:
    name_mfr_oxidant = conf.get('average', 'name_mfr_oxidant')
    name_mfr_fuel = conf.get('average', 'name_mfr_fuel')
    name_temperature = conf.get('average', 'name_temperature')
    equilibrium_empty = convert_to_tuple(conf.get('average', 'equilibrium_empty_components'))

# инициализация кинетики
path_chemkin = conf.get('path', 'chemkin')
path_thermo_db = conf.get('path', 'thermo')

# ВЫПОЛНЕНИЕ ПРОГРАММЫ
print('Номер сечения для измерения параметров в конце камеры: ', n_output, ' из ', n_slices, ' сечений')
print('Номер сечения для измерения расхода и определения альфа: ', n_offset, ' из ', n_slices, ' сечений')
if not minimal_mode:
    print('Номер сечения для измерения тяги: ', n_thrust, ' из ', n_slices, ' сечений')
    print('!!!ВНИМАНИЕ - тяга корректна если при рассечении остается только 1 "зона"!!!')

# вычисление мольной доли инертного компонента на входе
y_bulk_moles = 1
for item in Y_in:
    y_bulk_moles -= item
Y_in += (y_bulk_moles,)

# вычисление массовых долей состава на входе если убрать топливо - для предварительно перемешанных смесей
Species_in_no_fuel = []
Y_in_no_fuel_unnormalized = []
Y_in_no_fuel = []
normalizer = 1
for ind, item in enumerate(Species_in):
    if item != fuel:
        Species_in_no_fuel.append(item)
        Y_in_no_fuel_unnormalized.append(Y_in[ind])
    if item == fuel:
        normalizer = 1 - Y_in[ind]
for item in Y_in_no_fuel_unnormalized:
    Y_in_no_fuel.append(item / normalizer)

# суммарный расход топлива
mfr_fuel_all = mfr_fuel_inj * n_inj
print('Расход топлива: ', mfr_fuel_all * 1000, ' г/с, ', mfr_fuel_inj * 1000, ' г/с на один инжектор, ', n_inj, ' всего инжекторов')

# Инициализация химической кинетики
get_species_names = kin.read_chemkin_file(path_chemkin)
get_kinetics = kin.initiate_kinetics(path_thermo_db, get_species_names)
list_species = get_kinetics[0]

test = list_species[0].formula

# вычисление энтальпии образования газа-окислителя на входе - без учета топлива для предарительно перемешанных.
H0_oxidant = 0
for ind, p in enumerate(Species_in_no_fuel):
    for spec in list_species:
        if re.fullmatch(p, spec.name):
            print('Counting species for oxidant inlet H0: ', spec.name, ' h0_298 is ', spec.h0_298(), ' mass fraction is ', Y_in_no_fuel[ind])
            H0_oxidant += Y_in_no_fuel[ind] * spec.h0_298() / spec.mu()
print('H0 смеси на входе ', H0_oxidant)


def formula_from_name(species_name):
    for item in list_species:
        if item.name == species_name:
            return item.formula
    else:
        print('No species with name ' + species_name + ' in the database, cant find formula...')
        raise ValueError()


test2 = formula_from_name('O2')


# Вычисление мольного стехиометрического соотношения при заданных формулах топлива, окислителя и продуктов.
def extract_moles(name):
    sp_list = (re.sub(r'(\d+[.,]?)', r'\1 ', formula_from_name(name)))  # выделяем границу молей предыдущего компонента и имени следующего
    sp_list = (re.sub(r'([a-zA-Z]+)', r'\1 ', sp_list))  # выделяем границу компонента и его количества молей
    sp_list = re.split(r'\s', sp_list)  # разбиваем строку по пробелам
    sp_list = [x for x in sp_list if x]
    sp_list_new = []
    for ind, item in enumerate(sp_list):
        sp_list_new.append(item)
        if ind < len(sp_list) - 1:
            if re.match(r'([A-Z]{1})', item) and re.match(r'([A-Z]{1})', sp_list[ind + 1]):
                sp_list_new.append('1')
        if re.match(r'([A-Z]{1})', item) and ind == len(sp_list) - 1:
            sp_list_new.append('1')
    sp_components = [x for ind, x in enumerate(sp_list_new) if ((ind % 2) != 1)]
    sp_moles = [x for ind, x in enumerate(sp_list_new) if ((ind % 2) != 0)]
    return sp_components, sp_moles


def calculate_K_mole(fuel, oxidizer, products):
    moles_fuel = extract_moles(fuel)
    moles_oxidizer = extract_moles(oxidizer)
    list_of_moles_products = []
    for item in products:
        list_of_moles_products.append(extract_moles(item))
    K_mole = 0
    K_prod_list = []
    M_prod_list = []
    print(list_of_moles_products)
    K_prod = 0
    M_prod = 0
    for moles_products in list_of_moles_products:
        for ind, p in enumerate(moles_products[0]):
            print(p)
            for ind_f, f in enumerate(moles_fuel[0]):  # Количество молей продукта в брутто-формуле
                if re.match(f, p):
                    M_prod = float(moles_fuel[1][ind_f]) / float(moles_products[1][ind])

            for ind_o, o in enumerate(moles_oxidizer[0]):  # Количество молей топлива, идущее на образование этого продукта
                if re.match(o, p):
                    K_prod = M_prod * float(moles_products[1][ind]) / float(moles_oxidizer[1][ind_o])
        K_mole += K_prod
        K_prod_list.append(K_prod)
        M_prod_list.append(M_prod)
    # Если задавать продуктом инертный компонент, будет писать нули
    brutto_formula_products = ''
    for ind, item in enumerate(products):
        new_product = ''.join((str(M_prod_list[ind]), ' ', item, ' + '))
        brutto_formula_products = ''.join((brutto_formula_products, new_product))
    brutto_formula = ''.join((fuel, ' + ', str(K_mole), ' ', oxidizer, ' => ', brutto_formula_products[:-3]))
    return K_mole, moles_fuel, K_prod_list, M_prod_list, brutto_formula


calculate_chemistry = calculate_K_mole(fuel, oxidizer, products)

K_mole = calculate_chemistry[0]
brutto_formula = calculate_chemistry[4]
print('Молярное стехиометрическое соотношение: ', K_mole)
print('Брутто-формула: ', brutto_formula)


# Вычисление массового стехиометрического соотношения при заданных формулах топлива, окислителя и продуктов.
def calculate_K_mass(fuel, oxidizer, products, y_in):
    get_chemistry = calculate_K_mole(fuel, oxidizer, products)
    define_K_mole = get_chemistry[0]
    M_products = get_chemistry[3]
    mu_oxidizer = 0
    mu_fuel = 0
    y_in_oxidizer = 0
    for item in list_species:
        print(item.mu())
        if item.name == oxidizer:
            mu_oxidizer = item.mu()
        if item.name == fuel:
            mu_fuel = item.mu()
    for ind, item in enumerate(Species_in):
        if item == oxidizer:
            y_in_oxidizer = y_in[ind]
    define_K_mass = define_K_mole * mu_oxidizer / y_in_oxidizer / mu_fuel
    return define_K_mass, mu_oxidizer, mu_fuel, y_in_oxidizer, M_products


K_mass = calculate_K_mass(fuel, oxidizer, products, Y_in_no_fuel)[0]
print('Массовое стехиометрическое соотношение: ', K_mass)


# Расчет состава итоговой смеси от альфа при наличии только брутто-продуктов
def mix_brutto_universal(alpha, y_in, species_in, fuel, oxidizer, products):
    get_chemistry = calculate_K_mass(fuel, oxidizer, products, y_in)  # расчет мольной стехиометрии реакции
    k_mass = get_chemistry[0]  # массовое стехиометрическое соотношение
    M_products = get_chemistry[4]  # моли продуктов реакции
    y_in_sum = 1 + 1 / (k_mass * alpha)  # суммарная "массовая доля" компонент с учетом топлива
    y_mix_in_fuel = 1 / (k_mass * alpha + 1)  # массовые доли компонент в реагирующей смеси с учетом добавки топлива
    y_mix_in_oxidizer = []
    for ind, item in enumerate(species_in):
        y_mix_specie = y_in[ind] / y_in_sum
        y_mix_in_oxidizer.append(y_mix_specie)
    y_mix_check = sum(y_mix_in_oxidizer) + y_mix_in_fuel

    # Массовые доли вступающих в реакцию топлива и окислителя (по отношению к ИТОГОВОЙ смеси)
    y_react_fuel = 1 / (k_mass * max(alpha, 1)) / y_in_sum  # в числителе массовая доля до смешивания с топливом
    for ind, item in enumerate(species_in):
        if re.fullmatch(item, oxidizer):
            y_react_oxidizer = y_in[ind] / max(alpha, 1) / y_in_sum  # в числителе массовая доля до смешивания с топливом

    # Массовые доли оставшихся в смеси топлива и окислителя
    y_passive_fuel = y_mix_in_fuel - y_react_fuel
    for ind, item in enumerate(species_in):
        if re.fullmatch(item, oxidizer):
            y_passive_oxidizer = y_mix_in_oxidizer[ind] - y_react_oxidizer

    # Массовые доли выделившихся после реакции продуктов
    mass_prod_total = 0
    mu_products = []  # молярные массы продуктов
    for ind, p in enumerate(products):
        for spec in list_species:
            if re.fullmatch(p, spec.name):
                # print('Counting species ', spec.name)
                mu = spec.mu()
                mu_products.append(mu)
                mass_prod_total += M_products[ind] * mu
    y_react = y_react_oxidizer + y_react_fuel  # массовая доля прореагировавших компонент
    y_products = []
    for ind, item in enumerate(products):
        y_products.append(y_react * M_products[ind] * mu_products[ind] / mass_prod_total)

    # Массовые доли продуктов на выходе, с учетом добавки если продукты уже есть на входе - добавляется к y_products
    for ind, p in enumerate(products):
        for ind2, spec in enumerate(species_in):
            if re.fullmatch(spec, p):
                y_products[ind] += y_mix_in_oxidizer[ind2]
                print('Outlet products mass fraction counting: ', spec, ' mass fraction is ', y_products[ind])

    # Проверка - ПОКА ЧТО НЕТ ВОЗМОЖНОСТИ УЧЕСТЬ ПАССИВНЫЕ КОМПОНЕНТЫ БОЛЕЕ ОДНОГО! НУЖЕН РАЗБОР СОСТАВА
    y_out_all = sum(y_products) + y_passive_oxidizer + y_passive_fuel + y_mix_in_oxidizer[-1]
    # Состав смеси на выходе
    sp_out = [fuel, oxidizer]
    sp_out.extend(products)
    sp_out.extend([species_in[-1]])

    y_out = [y_passive_fuel, y_passive_oxidizer]
    y_out.extend(y_products)
    y_out.extend([y_mix_in_oxidizer[-1]])

    species_out = [sp_out, y_out]

    # out_test = sum(species_out[1])

    # Энтальпия образования продуктов
    h0_mix = 0

    # продукты, в т.ч если они были или не были в составе на входе
    for ind, p in enumerate(products):
        for spec in list_species:
            if re.fullmatch(p, spec.name):
                print('Counting species for H0: ', spec.name, ' h0_298 is ', spec.h0_298(), ' mass fraction is ', y_products[ind], ' mu is ', spec.mu())
                h0_add = y_products[ind] * spec.h0_298() / spec.mu()
                h0_mix += h0_add
                print('h0 molar addition: ', h0_add)

    # несгоревшее топливо
    for spec in list_species:
        if re.fullmatch(fuel, spec.name):
            print('Counting species for H0: ', spec.name, ' h0_298 is ', spec.h0_298(), ' mass fraction is ', y_passive_fuel, ' mu is ', spec.mu())
            h0_add = y_passive_fuel * spec.h0_298() / spec.mu()
            h0_mix += h0_add
            print('h0 molar addition: ', h0_add)

    # несработанный окислитель
    for spec in list_species:
        if re.fullmatch(oxidizer, spec.name):
            print('Counting species for H0: ', spec.name, ' h0_298 is ', spec.h0_298(), ' mass fraction is ', y_passive_oxidizer, ' mu is ', spec.mu())
            h0_add = y_passive_oxidizer * spec.h0_298() / spec.mu()
            h0_mix += h0_add
            print('h0 molar addition: ', h0_add)

    # инертный компонент
    for spec in list_species:
        if re.fullmatch(species_in[-1], spec.name):
            print('Counting species for H0: ', spec.name, ' h0_298 is ', spec.h0_298(), ' mass fraction is ', y_mix_in_oxidizer[-1], ' mu is ', spec.mu())
            h0_add = y_mix_in_oxidizer[-1] * spec.h0_298() / spec.mu()
            h0_mix += h0_add
            print('h0 molar addition: ', h0_add)

    return h0_mix, species_out, y_passive_fuel, y_passive_oxidizer, y_products, y_out_all, k_mass, y_mix_in_fuel, y_mix_in_oxidizer, y_mix_check, y_react_fuel, y_react_oxidizer, M_products, mu_products, mass_prod_total


# value = np.array([alpha, Y_passive_ker, Y_passive_O2, Y_mix_in_N2, Y_out_CO2, Y_out_H2O, H0_mix_brutto, Y_out_all])


# test8 = mix_brutto_universal(1, Y_in, Species_in, 'C12H23', 'O2', ('CO2', 'H2O'))

# test8 = mix_brutto_universal(alpha, Y_in, Species_in, fuel, oxidizer, products)

# СОЗДАНИЕ МАССИВОВ ДАННЫХ - СЧИТЫВАНИЕ ФАЙЛОВ
os.chdir(work_path)
# np.set_printoptions(threshold=nan, linewidth=nan)

x_throat_section = None

np_time = None
np_x = None
mfr = None
mfr_species = None

if not minimal_mode:
    t_tot = None
    t_stat = None
    p_tot = None
    p_stat = None
    velocity = None
    mach = None
    Ro_Vx_Enthalpy_0 = None
    Ro_Vx_Vx = None
    p_stat_integral = None
    Ro_Vx_Vx_kg = None
    p_stat_integral_kg = None
    F_all = None
    I_spec = None
    Y_species = None

H0_mixture = None  # вычисляется так как есть данные при МИНИМАЛ но пока не используется. Если CHEMKIN корректно посчитает равновесный состав, можно использовать

only_dirs = [d for d in os.listdir(work_path) if os.path.isdir(os.path.join(work_path, d))]

for dir in only_dirs:
    if minimal_mode:
        result = ScrapLocalFolderMinimal(os.path.join(work_path, dir, 'av_time'), n_slices, x_throat, list_species, mfr_fuel_all)
    else:
        result = ScrapLocalFolder(os.path.join(work_path, dir, 'av_time'), n_slices, x_throat, list_species, mfr_fuel_all)
    if np_time is None:
        np_time = result.time()
        np_x = result.x()
        x_throat_section = result.x_throat()
        mfr = result.mfr()
        H0_mixture = result.H0_mixture()
        Y_species = result.Y_species()
        mfr_species = result.mfr_species()
        if not minimal_mode:
            t_tot = result.t_tot()
            t_stat = result.t_stat()
            p_tot = result.p_tot()
            p_stat = result.p_stat()
            velocity = result.velocity()
            mach = result.mach()
            Ro_Vx_Enthalpy_0 = result.Ro_Vx_Enthalpy_0()
            Ro_Vx_Vx = result.Ro_Vx_Vx()
            p_stat_integral = result.p_stat_integral()
            Ro_Vx_Vx_kg = result.Ro_Vx_Vx_kg()
            p_stat_integral_kg = result.p_stat_integral_kg()
            F_all = result.F_all()
            I_spec = result.I_spec()
    else:
        delta_time = np_time[-1] - np_time[-2]
        time_last = np_time[-1]
        next_times = result.time() + time_last + delta_time
        np_time = np.hstack((np_time, next_times))
        mfr = np.hstack((mfr, result.mfr()))
        H0_mixture = np.hstack((H0_mixture, result.H0_mixture()))
        for ind, sp in enumerate(list_species):
            Y_species[ind] = np.hstack((Y_species[ind], result.Y_species()[ind]))
            mfr_species[ind] = np.hstack((mfr_species[ind], result.mfr_species()[ind]))
        if not minimal_mode:
            t_tot = np.hstack((t_tot, result.t_tot()))
            t_stat = np.hstack((t_stat, result.t_stat()))
            p_tot = np.hstack((p_tot, result.p_tot()))
            p_stat = np.hstack((p_stat, result.p_stat()))
            velocity = np.hstack((velocity, result.velocity()))
            mach = np.hstack((mach, result.mach()))
            Ro_Vx_Enthalpy_0 = np.hstack((Ro_Vx_Enthalpy_0, result.Ro_Vx_Enthalpy_0()))
            Ro_Vx_Vx = np.hstack((Ro_Vx_Vx, result.Ro_Vx_Vx()))
            p_stat_integral = np.hstack((p_stat_integral, result.p_stat_integral()))
            Ro_Vx_Vx_kg = np.hstack((Ro_Vx_Vx_kg, result.Ro_Vx_Vx_kg()))
            p_stat_integral_kg = np.hstack((p_stat_integral_kg, result.p_stat_integral_kg()))
            F_all = np.hstack((F_all, result.F_all()))
            I_spec = np.hstack((I_spec, result.I_spec()))
        print(next_times)


def matrix_2d_reduced(mat, left, right):
    if right != 0:
        mat = np.hstack((np.expand_dims(mat[:, left:-right].mean(axis=1), axis=1), mat[:, left:-right]))
    else:
        mat = np.hstack((np.expand_dims(mat[:, left:].mean(axis=1), axis=1), mat[:, left:]))
    return mat


# Делаем выборку по времени для определения осредненных величин, если необходимо
def list_reduced(lst, left, right):
    if right != 0:
        red = lst[left:-right]
    else:
        red = lst[left:]
    return red


np_time = list_reduced(np_time, average_left, average_right)
n_times = len(np_time)
mfr = matrix_2d_reduced(mfr, average_left, average_right)
H0_mixture = matrix_2d_reduced(H0_mixture, average_left, average_right)
for ind, sp in enumerate(list_species):
    Y_species[ind] = matrix_2d_reduced(Y_species[ind], average_left, average_right)
    mfr_species[ind] = matrix_2d_reduced(mfr_species[ind], average_left, average_right)
if not minimal_mode:
    t_tot = matrix_2d_reduced(t_tot, average_left, average_right)
    t_stat = matrix_2d_reduced(t_stat, average_left, average_right)
    p_tot = matrix_2d_reduced(p_tot, average_left, average_right)
    p_stat = matrix_2d_reduced(p_stat, average_left, average_right)
    velocity = matrix_2d_reduced(velocity, average_left, average_right)
    mach = matrix_2d_reduced(mach, average_left, average_right)
    Ro_Vx_Enthalpy_0 = matrix_2d_reduced(Ro_Vx_Enthalpy_0, average_left, average_right)
    Ro_Vx_Vx = matrix_2d_reduced(Ro_Vx_Vx, average_left, average_right)
    p_stat_integral = matrix_2d_reduced(p_stat_integral, average_left, average_right)
    Ro_Vx_Vx_kg = matrix_2d_reduced(Ro_Vx_Vx_kg, average_left, average_right)
    p_stat_integral_kg = matrix_2d_reduced(p_stat_integral_kg, average_left, average_right)
    F_all = matrix_2d_reduced(F_all, average_left, average_right)
    I_spec = matrix_2d_reduced(I_spec, average_left, average_right)

mfr_mean = mfr[n_offset][0]  # Средний расход - ОЧЕНЬ ВАЖНО для вычисления АЛЬФА

# вычисление к-та избытка окислителя альфа по измеренному расходу
for ind, item in enumerate(Species_in):
    if re.fullmatch(item, oxidizer):
        # mfr_oxidizer_in = (mfr[n_offset][0] - mfr_fuel_all)*Y_in[ind]
        mfr_oxidizer_in = (mfr[n_offset][0]) * Y_in[ind]
        alpha = mfr_oxidizer_in / (mfr_fuel_all * K_mass * Y_in[ind])
print('Средний расход окислителя, измеренный в сечении Х = ', str("{:4.2}".format(np_x[n_offset], type=float)), ' составляет ', str("{:2.2}".format(mfr_oxidizer_in, type=float)) + ' кг/с')
print('Средний коэффициент избытка окислителя альфа = ', "{:4.2}".format(alpha))

# массовая доля инертного компонента в составе окислителя на входе
print('Массовая доля инертного компонента на входе: ', Species_in[-1])

os.chdir(work_path)
print('Рабочая директория: ' + str(os.getcwd()))
if equilibrium_info:
    equilibrium_path = ''.join((folder_equilibrium_state, file_equilibrium_state))
    print('Путь к Файлу равновесных параметров: ' + str(equilibrium_path))

if equilibrium_info:  # тут осталось вычисление энтальпии для расчёта полноты по равновесной энтальпии. Пока не удаляю.
    # считывание файла входных данных равновесного состояния
    Data_Eq = pd.ExcelFile(equilibrium_path)
    df = Data_Eq.parse('1.PSRC1_soln_vs_parameter')
    # парсинг заголовков
    DF_Header = list(df)
    new_header = re.split(r', ', str(DF_Header))
    for i, item in enumerate(new_header):
        new_header[i] = re.sub('\[\'', '', item)
    for i, item in enumerate(new_header):
        new_header[i] = re.sub('\']', '', item)
    # Заполнение таблицы Pandas из результатов расчета Chemkin из Excel
    values_np = np.zeros(shape=(1, len(new_header)), dtype=int)
    i = 0
    while i < len(df):
        values = re.split(r', ', str(df.loc[i].values[0]))
        for j, item in enumerate(values):
            values[j] = float(item)
        values_np_1d = np.array(values)
        values_np = np.concatenate((values_np, np.expand_dims(values_np_1d, axis=0)), axis=0)
        i += 1
    values_np = np.delete(values_np, 0, axis=0)
    df_clean = pd.DataFrame(values_np, columns=pd.Series(new_header))
    # Вычисление к-та избытка окислителя:
    df_clean['alpha'] = pd.Series(df_clean[name_mfr_oxidant] / df_clean[name_mfr_fuel] / K_mass)

    # Тестирование сумма всех массовых долей = 1
    sum_y_all = [0] * len(df_clean[name_mfr_oxidant])
    for sp in list_species:
        if sp.name not in equilibrium_empty:  # НУЖНА ЗАГЛУШКА ДЛЯ ПРОМЕЖУТОЧНЫХ КОМПОНЕНТ, КОТОРЫХ НЕТ В EXCEL ИТОГОВОЙ СМЕСИ КИНЕТИКИ ПРИ ЛЮБОМ АЛЬФА
            sum_y_all += df_clean[''.join(('Mass_fraction_', sp.name, '_()'))]
    df_clean['Y_all'] = pd.Series(sum_y_all)

    # Равновесная энтальпия по продуктам МАССОВАЯ
    sum_h_all = [0] * len(df_clean[name_mfr_oxidant])
    for sp in list_species:
        if sp.name not in equilibrium_empty:
            sum_h_all += df_clean[''.join(('Mass_fraction_', sp.name, '_()'))] * sp.h0_298() / sp.mu()
    df_clean['H_products'] = pd.Series(sum_h_all)

    # ДОБАВЛЕНИЕ ДАННЫХ ПО БРУТТО-РЕАКЦИИ
    # Вычисление к-та избытка окислителя:

    # test3 = mix_brutto_universal(df_clean['alpha'][20], Y_in, fuel, oxidizer, products)[0]

    # value = np.array([alpha, Y_passive_ker, Y_passive_O2, Y_mix_in_N2, Y_out_CO2, Y_out_H2O, H0_mix_brutto, Y_out_all])

    list_H0_out_brutto = []
    extract_out_species = mix_brutto_universal(1, Y_in, Species_in, fuel, oxidizer, products)
    list_Y_out_species = [] * len(extract_out_species[1][0])

    for ind, item in enumerate(list_Y_out_species):
        print(ind, item)

    for row in df_clean['alpha']:
        calculate_point = mix_brutto_universal(row, Y_in, Species_in, fuel, oxidizer, products)
        list_H0_out_brutto.append(calculate_point[0])
        list_Y_out_species.append(calculate_point[1][1])

    df_clean['H_products_brutto'] = list_H0_out_brutto

    list_Y_out_species_T = np.array(list_Y_out_species).T
    for ind, item in enumerate(extract_out_species[1][0]):
        df_clean[''.join(('Y_out_', item))] = list_Y_out_species_T[ind]

    '''
    Линейная интерполяция - вычисление энтальпии образования продуктов МАССОВОЙ при текущем к-те избытка окислителя
    (значения должны быть в порядке возрастания)
    С равновесной энтальпией сравнивать НЕЛЬЗЯ так как можно получить полноту больше единицы! Это физика и никуда не деться, 
    двигатели работают на недоравновесном сжигании и это хорошо. 
    Нужно сравнивать с энтальпией брутто-реакции хотя это тоже не совсем логично.
    '''

    # Равновесная энтальпия состава
    H0_products = np.interp(alpha, np.flipud(df_clean['alpha'].values), np.flipud(df_clean['H_products'].values))

    # Энтальпия образования брутто-продуктов
    H0_products_brutto = np.interp(alpha, np.flipud(df_clean['alpha'].values), np.flipud(df_clean['H_products_brutto'].values))
    print('Равновесная энтальпия используемой кинетики: ', H0_products, 'Энтальпия образования брутто-продуктов: ', H0_products_brutto)
    # Полнота сгорания по энтальпии образования равновесной
    etta_equil = H0_mixture / H0_products  # НЕ ПРИМЕНЯЕТСЯ ТАК КАК МОЖЕТ ПОЛУЧИТЬСЯ БОЛЬШЕ 1

# чтобы отвязаться от использования равновесного состава - вычисляем напрямую
H0_products_brutto = mix_brutto_universal(alpha, Y_in_no_fuel, Species_in_no_fuel, fuel, oxidizer, products)[0]

# Определение свойств топлива
for spec in list_species:
    if re.fullmatch(fuel, spec.name):
        print('Counting fuel for H0 and mu extraction: ', spec.name)
        H0_fuel = spec.h0_298()
        mu_fuel = spec.mu()
print('H0 топлива: ', H0_fuel, ' молярная масса топлива: ', mu_fuel)


# Полнота сгорания по энтальпии образования брутто-продуктов
def etta_brutto(x, H0_mixture, H0_products_brutto):
    if x > x_inj:
        value = H0_mixture / H0_products_brutto
    else:
        value = 0.0
    return value


vector_etta_brutto = np.vectorize(etta_brutto)


# Полнота сгорания по расходу керосина
def etta_fuel(x, mfr_fuel):
    if x > x_inj:
        value = 1 - mfr_fuel / (mfr_fuel_all * min(alpha, 1))
    else:
        value = 0.0
    return value


vector_etta_fuel = np.vectorize(etta_fuel)
np_x_stacked = np.zeros(shape=(1, n_slices))
i = 0
while i <= n_times:
    np_x_stacked = np.concatenate((np_x_stacked, np.expand_dims(np_x, axis=0)), axis=0)
    i += 1
np_x_stacked = np.delete(np_x_stacked, 0, axis=0)
for ind, sp in enumerate(list_species):
    if re.fullmatch(sp.name, fuel):
        etta_fuel_v = vector_etta_fuel(x=np_x_stacked.T, mfr_fuel=mfr_species[ind])

etta_brutto_v = vector_etta_brutto(np_x_stacked.T, H0_mixture, H0_products_brutto)

# Определение выходных параметров
x_output = np_x[n_output]
print('Сечение измерения параметров в конце камеры X = ' + str("{:4.3}".format(x_output, type=float)))

etta_fuel_out = etta_fuel_v[n_output, 0]
etta_brutto_out = etta_brutto_v[n_output, 0]

print('Полнота по расходу керосина: ' + str("{:4.3}".format(etta_fuel_out, type=float)))
print('Полнота по энтальпии образования брутто-продуктов: ' + str("{:4.3}".format(etta_brutto_out, type=float)))

list_data = [np_x.transpose(), p_stat[:, 0], p_tot[:, 0], t_stat[:, 0], t_tot[:, 0], velocity[:, 0], mach[:, 0], Ro_Vx_Enthalpy_0[:, 0], Ro_Vx_Vx[:, 0], p_stat_integral[:, 0], F_all[:, 0], I_spec[:, 0], H0_mixture[:, 0], etta_fuel_v[:, 0], etta_brutto_v[:, 0], mfr[:, 0]]
list_data_columns = ['x', 'pstat', 'ptot', 'tstat', 'ttot', 'velocity', 'mach', 'Ro_Vx_Enthalpy_0', 'Ro_Vx_Vx', 'p_stat_integral', 'F_all', 'I_spec', 'H0_mixture', 'etta_fuel', 'etta_brutto', 'mfr']

for ind, sp in enumerate(list_species):
    list_data.append(mfr_species[ind][:, 0])
    list_data_columns.append(''.join(('mfr_', sp.name)))

for ind, sp in enumerate(list_species):
    list_data.append(Y_species[ind][:, 0])
    list_data_columns.append(''.join(('Y_', sp.name)))

# Time-Averaged parameters distribution:
data = pd.DataFrame(data=list_data).T
data.columns = list_data_columns
data.to_excel('params_time_averaged.xlsx', index=False)

if not minimal_mode:
    t_tot_out = t_tot[n_output, 0]
    t_stat_out = t_stat[n_output, 0]
    v_out = velocity[n_output, 0]
    p_tot_out = p_tot[n_output, 0]
    p_stat_out = p_stat[n_output, 0]
    m_out = mach[n_output, 0]
    print('Полная температура: ' + str("{:6.5}".format(t_tot_out, type=float)))
    print('Статическая темппература ' + str("{:6.5}".format(t_stat_out, type=float)))
    print('Полное давление: ' + str("{:4.3}".format(p_tot_out, type=float)))
    print('Статическое давление: ' + str("{:4.3}".format(p_stat_out, type=float)))
    print('Число Маха: ' + str("{:4.3}".format(m_out, type=float)))

# Y_species_mfr_out = []
Y_species_out = []

for ind, sp in enumerate(list_species):
    # Y_species_mfr_out.append(Y_species_mfr_averaged[ind][n_output, 0])
    Y_species_out.append(Y_species[ind][n_output, 0])

# test11 = sum(Y_species_mfr_out)

test12 = sum(Y_species_out)

if not minimal_mode:
    # вычисление тяги и удельного импульса вы выходном сечении. Применять только если в сечении одна зона, только внутренний тракт без внешней области
    print('Сечение измерения тяги и удельного импульса X = ' + str("{:4.3}".format(x_throat_section, type=float)))
    F_all_out = F_all[n_thrust, 0]
    p_stat_integral_kg_out = p_stat_integral_kg[n_thrust, 0]
    Ro_Vx_Vx_kg_out = Ro_Vx_Vx_kg[n_thrust, 0]
    I_spec_out = I_spec[n_thrust, 0]
    print('Тяга: ' + str("{:5.4}".format(F_all_out, type=float)) + ' кг')
    print('Удельный импульс: ' + str("{:6.5}".format(I_spec_out, type=float)) + ' с')

# ЗАПИСЬ РЕЗУЛЬТАТА В EXCEL
workbook = xlsxwriter.Workbook('result_new.xlsx')
worksheet = workbook.add_worksheet()
worksheet.set_column('A:A', 55)

cell_format01 = workbook.add_format()
cell_format01.set_num_format('0.000')
cell_format02 = workbook.add_format()
cell_format02.set_num_format('0')
cell_format_bold = workbook.add_format()
cell_format_bold.set_bold()

worksheet.write('A1', 'Параметры на выходе', cell_format_bold)

worksheet.write('A2', 'расход топлива, г/с')
worksheet.write('B2', mfr_fuel_all * 1000)
worksheet.write('A3', 'расход окислителя, кг/с')
worksheet.write('B3', mfr_oxidizer_in, cell_format01)
worksheet.write('A4', 'коэффициент избытка окислителя альфа')
worksheet.write('B4', alpha, cell_format01)
worksheet.write('A5', 'полнота по расходу топлива')
worksheet.write('B5', etta_fuel_out, cell_format01)
worksheet.write('A6', 'полнота по энтальпии образования брутто-продуктов')
worksheet.write('B6', etta_brutto_out, cell_format01)
if not minimal_mode:
    worksheet.write('A7', 'полная температура (К)')
    worksheet.write('B7', t_tot_out, cell_format02)
    worksheet.write('A8', 'cтатическая температура (К)')
    worksheet.write('B8', t_stat_out, cell_format02)
    worksheet.write('A9', 'полное давление (бар)')
    worksheet.write('B9', p_tot_out / 100000, cell_format01)
    worksheet.write('A10', 'cтатическое давление (бар)')
    worksheet.write('B10', p_stat_out / 100000, cell_format01)
    worksheet.write('A11', 'число Маха')
    worksheet.write('B11', m_out, cell_format01)
    worksheet.write('A12', 'интеграл статического давления в выходном сечении, кг')
    worksheet.write('B12', p_stat_integral_kg_out, cell_format02)
    worksheet.write('A13', 'интеграл импульса в выходном сечении, кг')
    worksheet.write('B13', Ro_Vx_Vx_kg_out, cell_format02)
    worksheet.write('A14', 'тяга, кг')
    worksheet.write('B14', F_all_out, cell_format02)
    worksheet.write('A15', 'удельный импульс, с')
    worksheet.write('B15', I_spec_out, cell_format02)

worksheet.write('D1', 'Состав газа на выходе (массовая доля)', cell_format_bold)
for ind, sp in enumerate(list_species):
    worksheet.write(''.join(('D', str(2 + ind))), sp.name)
    worksheet.write(''.join(('E', str(2 + ind))), Y_species_out[ind])

worksheet.write('H1', 'Состав газа на входе (массовая доля)', cell_format_bold)
for ind, item in enumerate(Species_in):
    worksheet.write(''.join(('H', str(2 + ind))), item)
    worksheet.write(''.join(('I', str(2 + ind))), Y_in[ind])

workbook.close()

# АНИМАЦИЯ
figures_dict = {}
plt.rcParams["figure.figsize"] = (9, 5)
# plt.subplots_adjust(top=0.92, bottom=0.06, left=0.04, right=0.94, hspace=0.35, wspace=0.35)
# fig.suptitle(''.join((r'$\alpha\ =\ $', str("{:4.3}".format(alpha)))))
cmap = plt.get_cmap('tab20')
cmp_cycle = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']


# use_color = cmap(float(indc) / n_colors)
# plt.show()


def plot_line(x, y, colorind, linestyle=None, label=None, linewidth=None, twin=False):
    use_color = cmp_cycle[int(colorind % len(cmp_cycle))]
    if twin:
        line = ax1_twin.plot(x, y, linestyle=linestyle, color=use_color, label=label, linewidth=linewidth)
    else:
        line = ax1.plot(x, y, linestyle=linestyle, color=use_color, label=label, linewidth=linewidth)
    return line


bulk_species = convert_to_tuple(conf.get('average', 'bulk_species'))
Plot_Y_main = convert_to_tuple(conf.get('average', 'plot_y_main'))
if equilibrium_info:
    Plot_Y_main_Equil = convert_to_tuple(conf.get('average', 'plot_y_main_equil'))

# график 1 - Температура, скорость
if not minimal_mode:
    fig1 = plt.figure()
    fig1.set_tight_layout({'pad': 0})
    figures_dict['T_V'] = fig1
    ax1 = plt.subplot(1, 1, 1)
    ax1.grid(True)
    ax1_twin = ax1.twinx()
    plt.xlim(left=x_min, right=x_max)
    plt.axvline(x=np_x[n_output], color='black')
    line_t_tot, = plot_line(np_x, t_tot[:, 1], 0, linestyle='dashed')
    line_t_tot_av, = plot_line(np_x, t_tot[:, 0], 0, label=r'$T*\ (K)$')
    line_t_stat, = plot_line(np_x, t_stat[:, 1], 1, linestyle='dashed')
    line_t_stat_av, = plot_line(np_x, t_stat[:, 0], 1, label=r'$T\ (K)$')
    line_v, = plot_line(np_x, velocity[:, 1], 2, linestyle='dashed', twin=True)
    line_v_av, = plot_line(np_x, velocity[:, 0], 2, label=r'$V\ (м/с)$', twin=True)
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.set(title=r'$Температура,\ скорость$')
    ax1.xaxis.label.set_size('x-large')
    plt.draw()
    plt.savefig('plot_temperature_velocity.png', bbox_inches='tight')

# график 2 - Давление, число Маха
if not minimal_mode:
    fig2 = plt.figure()
    fig2.set_tight_layout({'pad': 0})
    figures_dict['P_M'] = fig2
    ax1 = plt.subplot(1, 1, 1)
    ax1.grid(True)
    ax1_twin = ax1.twinx()
    plt.xlim(left=x_min, right=x_max)
    plt.axvline(x=np_x[n_output], color='black')
    line_p_tot, = plot_line(np_x, p_tot[:, 1], 0, linestyle='dashed')
    line_p_tot_av, = plot_line(np_x, p_tot[:, 0], 0, label=r'$P*\ (Па)$')
    line_p_stat, = plot_line(np_x, p_stat[:, 1], 1, linestyle='dashed')
    line_p_stat_av, = plot_line(np_x, p_stat[:, 0], 1, label=r'$P\ (Па)$')
    line_M, = plot_line(np_x, mach[:, 1], 2, linestyle='dashed', twin=True)
    line_M_av, = plot_line(np_x, mach[:, 0], 2, label=r'$M$', twin=True)
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.set(title=r'$Давление,\ число\ Маха$')
    plt.savefig('plot_pressure_mach.png', bbox_inches='tight')

# график 3 - Равновесный состав
if equilibrium_info:
    fig3 = plt.figure()
    fig3.set_tight_layout({'pad': 0})
    Lines_Y_main_Equil = []
    ax1 = plt.subplot(1, 1, 1)
    plt.ylim(bottom=0, top=t_equil)
    ax1.grid(True)
    ax1_twin = ax1.twinx()
    plt.ylim(bottom=0, top=y_equil)
    line_temperature, = plot_line(df_clean['alpha'], df_clean[name_temperature], 0, label=r'$T\ (К)$', linewidth=2)
    for ind, item in enumerate(Plot_Y_main_Equil):
        Lines_Y_main_Equil.append(plot_line(df_clean['alpha'], df_clean[''.join(('Mass_fraction_', item, '_()'))], ind + 1, label=r''.join(('$', item, '$')), twin=True, linestyle='dashed'))
    ax1.legend(loc='lower left')
    ax1_twin.legend(loc='upper right')
    ax1.set(xlabel=r'$\alpha - коэффициент\ избытка\ окислителя$')
    ax1.set(title=r'$Зависимость\ равновесной\ температуры\ (K)\ и\ массового\ состава\ от\ \alpha$')
    plt.savefig('plot_equivalence_composition.png', bbox_inches='tight')

# график 4 - Расходы основных компонент
fig4 = plt.figure()
fig4.set_tight_layout({'pad': 0})
figures_dict['G_main'] = fig4
Lines_G_main = ()
Lines_G_main_av = ()
ax1 = plt.subplot(1, 1, 1)
ax1.grid(True)
# plt.ylim(top=mfr_max)
ax1_twin = ax1.twinx()
# plt.ylim(top=mfr_main_max)
plt.xlim(left=x_min, right=x_max)
line_mfr, = plot_line(np_x, mfr[:, 1], 0, linestyle='dashed')
line_mfr_av, = plot_line(np_x, mfr[:, 0], 0, label=r'$G\ (кг/с)$', linewidth=2)
for ind, sp in enumerate(list_species):
    if sp.name in bulk_species:
        line_mfr_bulk, = plot_line(np_x, mfr_species[ind][:, 1], 1, linestyle='dashed')
        line_mfr_bulk_av, = plot_line(np_x, mfr_species[ind][:, 0], 1, label=r''.join(('$G_{', sp.name, '}\ (кг/с)$')), linewidth=2)
for indc, item in enumerate(Plot_Y_main):
    for ind, sp in enumerate(list_species):
        if sp.name == item:
            Lines_G_main = Lines_G_main + (plot_line(np_x, mfr_species[ind][:, 1], indc + 2, linestyle='dashed', twin=True)[0],)
            Lines_G_main_av = Lines_G_main_av + (plot_line(np_x, mfr_species[ind][:, 0], indc + 2, label=r''.join(('$G_{', item, '}\ (кг/с)$')), twin=True)[0],)
plt.axvline(x=np_x[n_offset], color='black')
ax1.legend(loc='upper left')
ax1_twin.legend(loc='upper right')
if not brutto_kinetics:
    ax1.set(title=r'$Расход\ основных\ компонент$')
else:
    ax1.set(title=r'$Расход\ компонент$')
plt.savefig('plot_mfr_main.png', bbox_inches='tight')

# график 5 - Расход радикалов и диссоциированных атомов
if not brutto_kinetics:
    fig5 = plt.figure()
    fig5.set_tight_layout({'pad': 0})
    figures_dict['G_radicals'] = fig5
    Plot_Y_minor = convert_to_tuple(conf.get('average', 'plot_y_minor'))
    Lines_G_minor = ()
    Lines_G_minor_av = ()
    Plot_Y_minor_twin = convert_to_tuple(conf.get('average', 'plot_y_minor_twin'))
    Lines_G_minor_twin = ()
    Lines_G_minor_twin_av = ()
    ax1 = plt.subplot(1, 1, 1)
    ax1.grid(True)
    ax1_twin = ax1.twinx()
    plt.xlim(left=x_min, right=x_max)
    plt.axvline(x=np_x[n_offset], color='black')
    for indc, item in enumerate(Plot_Y_minor):
        for ind, sp in enumerate(list_species):
            if sp.name == item:
                Lines_G_minor = Lines_G_minor + (plot_line(np_x, mfr_species[ind][:, 1], indc, linestyle='dashed')[0],)
                Lines_G_minor_av = Lines_G_minor_av + (plot_line(np_x, mfr_species[ind][:, 0], indc, label=r''.join(('$G_{', item, '}\ (кг/с)$')))[0],)
    for indc, item in enumerate(Plot_Y_minor_twin):
        for ind, sp in enumerate(list_species):
            if sp.name == item:
                Lines_G_minor_twin = Lines_G_minor_twin + (plot_line(np_x, mfr_species[ind][:, 1], indc + len(Plot_Y_minor), linestyle='dashed', twin=True)[0],)
                Lines_G_minor_twin_av = Lines_G_minor_twin_av + (plot_line(np_x, mfr_species[ind][:, 0], indc + len(Plot_Y_minor), label=r''.join(('$G_{', item, '}\ (кг/с)$')), twin=True)[0],)
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.set(title=r'$Расход\ радикалов\ и\ диссоциированных\ атомов$')
    plt.savefig('plot_mfr_radicals.png', bbox_inches='tight')

# text = ax1_twin.text(1, 0.5, ''.join((r'$\alpha\ =\ $', str("{:4.2}".format(alpha)))), ha='center')
# plt.subplots_adjust(right=0.1)


# график 6 - Полнота сгорания и расход топлива
fig6 = plt.figure()
fig6.set_tight_layout({'pad': 0})
figures_dict['etta_G_fuel'] = fig6
ax1 = plt.subplot(1, 1, 1)
ax1.grid(True)
plt.ylim(bottom=0, top=mfr_fuel)
ax1_twin = ax1.twinx()
plt.ylim(top=etta)
plt.xlim(left=x_min, right=x_max)
plt.axvline(x=np_x[n_output], color='black')
for ind, sp in enumerate(list_species):
    if sp.name == fuel:
        line_mfr_fuel, = plot_line(np_x, mfr_species[ind][:, 1], 0, linestyle='dashed')
        line_mfr_fuel_av, = plot_line(np_x, mfr_species[ind][:, 0], 0, label=r''.join(('$G_{', sp.name, '}\ (кг/с)$')), linewidth=2)
if show_etta_energetic:
    line_etta, = plot_line(np_x, etta_brutto_v[:, 1], 1, linewidth=2, linestyle='dashed', twin=True)
    line_etta_av, = plot_line(np_x, etta_brutto_v[:, 0], 1, linewidth=2, label=r'$\eta\ (по\ энтальпии\ образования)$', twin=True)
if show_etta_fuel:
    line_etta_fuel, = plot_line(np_x, etta_fuel_v[:, 1], 2, linewidth=2, linestyle='dashed', twin=True)
    line_etta_fuel_av, = plot_line(np_x, etta_fuel_v[:, 0], 2, linewidth=2, label=r'$\eta\ (по\ расходу\ топлива)$', twin=True)
ax1.legend(loc='upper left')
ax1_twin.legend(loc='lower right')
ax1.set(title=r'$Полнота\ сгорания\ и\ расход\ керосина$')
plt.savefig('plot_combustion_efficiency.png', bbox_inches='tight')

# график 7 - Массовые доли основных компонент
fig7 = plt.figure()
fig7.set_tight_layout({'pad': 0})
figures_dict['Y_main'] = fig7
Lines_Y_main = ()
Lines_Y_main_av = ()
ax1 = plt.subplot(1, 1, 1)
plt.ylim(top=1, bottom=0)
ax1.grid(True)
ax1_twin = ax1.twinx()
plt.ylim(bottom=0, top=y_main)
plt.xlim(left=x_min, right=x_max)
plt.axvline(x=np_x[n_offset], color='black')
for ind, sp in enumerate(list_species):
    if sp.name in bulk_species:
        line_y_bulk, = plot_line(np_x, Y_species[ind][:, 1], ind + 2, linestyle='dashed')
        line_y_bulk_av, = plot_line(np_x, Y_species[ind][:, 0], ind + 2, label=r''.join(('$Y_{', sp.name, '}$')), linewidth=2)
for indc, item in enumerate(Plot_Y_main):
    for ind, sp in enumerate(list_species):
        if sp.name == item:
            Lines_Y_main = Lines_Y_main + (plot_line(np_x, Y_species[ind][:, 1], indc + 2, linestyle='dashed', twin=True)[0],)
            Lines_Y_main_av = Lines_Y_main_av + (plot_line(np_x, Y_species[ind][:, 0], indc + 2, label=r''.join(('$Y_{', item, '}$')), twin=True)[0],)
ax1.legend(loc='upper left')
ax1_twin.legend(loc='upper right')
if not brutto_kinetics:
    ax1.set(title=r'$Массовые\ доли\ основных\ компонент$')
else:
    ax1.set(title=r'$Массовые\ доли\ компонент$')
plt.savefig('plot_Y_main.png', bbox_inches='tight')

# график 8 - Массовая доля радикалов и диссоциированных атомов
if not brutto_kinetics:
    fig8 = plt.figure()
    fig8.set_tight_layout({'pad': 0})
    figures_dict['Y_radicals'] = fig8
    Lines_Y_minor = ()
    Lines_Y_minor_av = ()
    Lines_Y_minor_twin = ()
    Lines_Y_minor_twin_av = ()
    ax1 = plt.subplot(1, 1, 1)
    ax1.grid(True)
    # plt.ylim(ymin=0, ymax=mfr_radicals_max)
    ax1_twin = ax1.twinx()
    # plt.ylim(ymin=0)
    # plt.ylim(ymax=mfr_main_max)
    plt.xlim(left=x_min, right=x_max)
    plt.axvline(x=np_x[n_offset], color='black')
    for indc, item in enumerate(Plot_Y_minor):
        for ind, sp in enumerate(list_species):
            if sp.name == item:
                Lines_Y_minor = Lines_Y_minor + (plot_line(np_x, Y_species[ind][:, 1], indc, linestyle='dashed')[0],)
                Lines_Y_minor_av = Lines_Y_minor_av + (plot_line(np_x, Y_species[ind][:, 0], indc, label=r''.join(('$Y_{', item, '}$')))[0],)
    for indc, item in enumerate(Plot_Y_minor_twin):
        for ind, sp in enumerate(list_species):
            if sp.name == item:
                Lines_Y_minor_twin = Lines_Y_minor_twin + (plot_line(np_x, Y_species[ind][:, 1], indc + len(Plot_Y_minor), linestyle='dashed', twin=True)[0],)
                Lines_Y_minor_twin_av = Lines_Y_minor_twin_av + (plot_line(np_x, Y_species[ind][:, 0], indc + len(Plot_Y_minor), label=r''.join(('$Y_{', item, '}$')), twin=True)[0],)
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.set(title=r'$Массовая\ доля\ радикалов\ и\ диссоциированных\ атомов$')
    plt.savefig('plot_Y_radicals.png', bbox_inches='tight')

if not minimal_mode:
    # график 9 - Компоненты тяги, удельный импульс
    fig9 = plt.figure()
    fig9.set_tight_layout({'pad': 0})
    figures_dict['thrust'] = fig9
    ax1 = plt.subplot(1, 1, 1)
    ax1.grid(True)
    # plt.ylim(bottom=0, top=F_max)
    ax1_twin = ax1.twinx()
    # plt.ylim(bottom=0, top=I_max)
    plt.xlim(left=x_min, right=x_max)
    plt.axvline(x=np_x[n_thrust], color='black')
    line_RoVxVx, = plot_line(np_x, Ro_Vx_Vx_kg[:, 1], 0, linewidth=2, linestyle='dashed')
    line_RoVxVx_av, = plot_line(np_x, Ro_Vx_Vx_kg[:, 0], 0, linewidth=2, label=r'$\rho\cdot\upsilon_{x}^2\ (кг)$')
    line_p_stat_integral, = plot_line(np_x, p_stat_integral_kg[:, 1], 1, linewidth=2, linestyle='dashed')
    line_p_stat_integral_av, = plot_line(np_x, p_stat_integral_kg[:, 0], 1, linewidth=2, label=r'$\int P\ (кг)$')
    line_F_all, = plot_line(np_x, F_all[:, 1], 2, linewidth=2, linestyle='dashed')
    line_F_all_av, = plot_line(np_x, F_all[:, 0], 2, linewidth=2, label=r'$F\ (кг)\ -\ тяга$')
    line_I_spec, = plot_line(np_x, I_spec[:, 1], 3, linewidth=2, linestyle='dashed', twin=True)
    line_I_spec_av, = plot_line(np_x, I_spec[:, 0], 3, linewidth=2, label=r'$I_{уд}\ (с)$', twin=True)
    ax1.legend(loc='lower left')
    ax1_twin.legend(loc='lower right')
    ax1.set(title=r'$Компоненты\ тяги,\ удельный\ импульс$')
    plt.savefig('plot_thrust.png', bbox_inches='tight')
# plt.show()


print('stop here')


def init():
    line_mfr.set_ydata(mfr[:, 1])
    if show_etta_fuel:
        line_etta_fuel.set_ydata(etta_fuel_v[:, 1])
    if show_etta_energetic:
        line_etta.set_ydata(etta_brutto_v[:, 1])
    if not minimal_mode:
        line_t_tot.set_ydata(t_tot[:, 1])
        line_t_stat.set_ydata(t_stat[:, 1])
        line_v.set_ydata(velocity[:, 1])
        line_p_tot.set_ydata(p_tot[:, 1])
        line_p_stat.set_ydata(p_stat[:, 1])
        line_M.set_ydata(mach[:, 1])
        line_RoVxVx.set_ydata(Ro_Vx_Vx_kg[:, 1])
        line_p_stat_integral.set_ydata(p_stat_integral_kg[:, 1])
        line_F_all.set_ydata(F_all[:, 1])
        line_I_spec.set_ydata(I_spec[:, 1])

    for ind, sp in enumerate(list_species):
        if sp.name in bulk_species:
            line_mfr_bulk.set_ydata(mfr_species[ind][:, 1])
            line_y_bulk.set_ydata(Y_species[ind][:, 1])
        for ind2, item in enumerate(Plot_Y_main):
            if sp.name == item:
                Lines_G_main[ind2].set_ydata(mfr_species[ind][:, 1])
                Lines_Y_main[ind2].set_ydata(Y_species[ind][:, 1])
        if sp.name == fuel:
            line_mfr_fuel.set_ydata(mfr_species[ind][:, 1])

        if not brutto_kinetics:  # концентрации и расход радикалов
            for ind2, item in enumerate(Plot_Y_minor):
                if sp.name == item:
                    Lines_G_minor[ind2].set_ydata(mfr_species[ind][:, 1])
                    Lines_Y_minor[ind2].set_ydata(Y_species[ind][:, 1])
            for ind2, item in enumerate(Plot_Y_minor_twin):
                if sp.name == item:
                    Lines_G_minor_twin[ind2].set_ydata(mfr_species[ind][:, 1])
                    Lines_Y_minor_twin[ind2].set_ydata(Y_species[ind][:, 1])
    return line_mfr,


def animate(i):
    if i >= n_times:
        return line_mfr,
    line_mfr.set_ydata(mfr[:, i + 1])
    if show_etta_fuel:
        line_etta_fuel.set_ydata(etta_fuel_v[:, i + 1])
    if show_etta_energetic:  # энергетическая полнота
        line_etta.set_ydata(etta_brutto_v[:, i + 1])
    if not minimal_mode:
        line_t_tot.set_ydata(t_tot[:, i + 1])
        line_t_stat.set_ydata(t_stat[:, i + 1])
        line_v.set_ydata(velocity[:, i + 1])
        line_p_tot.set_ydata(p_tot[:, i + 1])
        line_p_stat.set_ydata(p_stat[:, i + 1])
        line_M.set_ydata(mach[:, i + 1])
        line_RoVxVx.set_ydata(Ro_Vx_Vx_kg[:, i + 1])
        line_p_stat_integral.set_ydata(p_stat_integral_kg[:, i + 1])
        line_F_all.set_ydata(F_all[:, i + 1])
        line_I_spec.set_ydata(I_spec[:, i + 1])

    for ind, sp in enumerate(list_species):
        if sp.name in bulk_species:
            line_mfr_bulk.set_ydata(mfr_species[ind][:, i + 1])
            line_y_bulk.set_ydata(Y_species[ind][:, i + 1])
        for ind2, item in enumerate(Plot_Y_main):
            if sp.name == item:
                Lines_G_main[ind2].set_ydata(mfr_species[ind][:, i + 1])
                Lines_Y_main[ind2].set_ydata(Y_species[ind][:, i + 1])
        if sp.name == fuel:
            line_mfr_fuel.set_ydata(mfr_species[ind][:, i + 1])

        if not brutto_kinetics:  # концентрации и расход радикалов
            for ind2, item in enumerate(Plot_Y_minor):
                if sp.name == item:
                    Lines_G_minor[ind2].set_ydata(mfr_species[ind][:, i + 1])
                    Lines_Y_minor[ind2].set_ydata(Y_species[ind][:, i + 1])
            for ind2, item in enumerate(Plot_Y_minor_twin):
                if sp.name == item:
                    Lines_G_minor_twin[ind2].set_ydata(mfr_species[ind][:, i + 1])
                    Lines_Y_minor_twin[ind2].set_ydata(Y_species[ind][:, i + 1])
    return line_mfr,


# Анимация
for k, f in figures_dict.items():
    print('animating figure ', k, ' ...')
    ani = animation.FuncAnimation(f, animate, init_func=init, interval=10, frames=int(n_times), blit=True, save_count=n_times, repeat=True)
    os.chdir('..')
    output_name = ''.join((work_path, 'plots_', k, '.gif'))
    output_name_loop = ''.join((work_path, 'plots_loop_', k, '.gif'))
    ani.save(output_name, writer='pillow', fps=24)
    Image.open(output_name).save(output_name_loop, save_all=True, loop=0)  # делаем бесконечный loop - очень удобно для презентаций
os.chdir(work_path)

# компоновка единого фильма
# if minimal_mode and brutto_kinetics:
#     final_clip = clips_array([[VideoFileClip('plots_G_main.gif')],
#                               [VideoFileClip('plots_Y_main.gif')],
#                               [VideoFileClip('plots_etta_G_fuel.gif')]])
#     final_clip.write_videofile('plots_array.mp4')
#
# if minimal_mode and not brutto_kinetics:
#     final_clip = clips_array([[VideoFileClip('plots_G_main.gif'), VideoFileClip('plots_Y_radicals.gif')],
#                               [VideoFileClip('plots_Y_main.gif'), VideoFileClip('plots_etta_G_fuel.gif')]])
#     final_clip.write_videofile('plots_array.mp4')
#
# if not minimal_mode and brutto_kinetics:
#     final_clip = clips_array([[VideoFileClip('plots_T_V.gif'), VideoFileClip('plots_P_M.gif')],
#                               [VideoFileClip('plots_G_main.gif'), VideoFileClip('plots_etta_G_fuel.gif')],
#                               [VideoFileClip('plots_Y_main.gif'), VideoFileClip('plots_thrust.gif')]])
#     final_clip.write_videofile('movie_array.mp4')
#
# if not minimal_mode and not brutto_kinetics:
#     final_clip = clips_array([[VideoFileClip('plots_T_V.gif'), VideoFileClip('plots_P_M.gif')],
#                               [VideoFileClip('plots_G_main.gif'), VideoFileClip('plots_G_radicals.gif')],
#                               [VideoFileClip('plots_Y_main.gif'), VideoFileClip('plots_Y_radicals.gif')],
#                               [VideoFileClip('plots_etta_G_fuel.gif'), VideoFileClip('plots_thrust.gif')]])
#     final_clip.write_videofile('plots_array.mp4')


# Вывод времени выполнения скрипта
time_script_end = datetime.datetime.now()
print('time end:', time_script_end)
delta = time_script_end - time_script_start
print('script execution time:', delta.seconds, 'seconds')
print('script execution time:', "{:4.2}".format(delta.seconds / 60), 'minutes')
print('script execution time:', "{:4.2}".format(delta.seconds / 3600), 'hours')
print('THE END')
