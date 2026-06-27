import time
import datetime
import os
import re
import numpy as np
from math import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import csv
import pandas as pd
from IPython.display import display, HTML
import scipy.integrate as integrate
import scipy.optimize as optimize
import xlsxwriter
from pathlib import Path

from utils_fluent import read_mon, plot_pic
from utils import plot_result


path_run = r'D:\YASIM\2026_02_GPA'
dir_run = 'run'


path_data = r'D:\YASIM\2026_02_GPA\v03_db_sbes\out_8000'
file_name = 'm_ptot-rfile.out'
file_name_mfr = 'm_mfr-rfile.out'

# section_names = ['вход', 'после сужения', 'перед поворотом', 'после поворота', 'перед ШГ', 'после ШГ', 'после конфузора', 'выход трубы', 'выход']
# section_names = ['вход', 'после сужения', 'перед поворотом', 'после ШГ', 'перед ШГ', 'выход трубы', 'выход']
# section_names = ['вход', 'после сужения', 'перед поворотом - 1', 'перед поворотом - 2', 'перед поворотом - 3', 'после ШГ', 'перед ШГ', 'выход трубы', 'выход']
section_names = ['вход', 'после конфузора', 'после горизонтального участка', 'после улитки', 'после ШГ', 'после поворота', 'перед ШГ', 'перед поворотом', 'выход трубы', 'выход']
# section_names = ['вход', 'выход']
# section_names = ['вход', 'вход наружный', 'после сужения', 'после горизонтального участка', 'после улитки', 'после ШГ', 'после поворота', 'перед ШГ', 'перед поворотом', 'выход трубы', 'выход']

mfr = True

if mfr:
    # section_names_mfr = ['перед поворотом - 1', 'перед поворотом - 2', 'перед поворотом - 3']
    section_names_mfr = ['вход', 'вход наружный', 'после конфузора', 'после горизонтального участка', 'после улитки', 'после ШГ', 'после поворота', 'перед ШГ', 'перед поворотом', 'выход трубы', 'выход']
    section_names_for_plot_mfr = section_names_mfr
    section_names_mfr_reverse = ['после улитки', 'после поворота', 'перед ШГ', 'выход']
    section_skip = ['вход наружный', 'выход']



section_names_for_plot = section_names

p_base = 101000

# avg_interval = (80000, 95000)
avg_interval = (5.5, 7.5)
# avg_interval = (3.0, 5.1)
# x_label = r'$№\ итерации$'
x_label = r'$время,\ с$'
y_limits = [-1000, 10000]
y_limits_mfr = (0, 120)

path_current_run = ''.join((path_run, '/', dir_run))
Path(path_current_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_current_run)

data, avg_data = read_mon(path_data, file_name, avg_interval)

if mfr:
    data_mfr, avg_data_mfr = read_mon(path_data, file_name_mfr, avg_interval)

for col in data.columns:
    if col != 'Interval' or 'Time_Step':
        data[col] = data[col] - p_base
for col in avg_data.columns:
    if col != 'Interval':
        avg_data[col] = avg_data[col] - p_base

avg_data_transposed = avg_data.T
if mfr:
    avg_data_mfr_transposed = avg_data_mfr.T

if len(section_names) == len(data.columns):
    data.columns = section_names
else:
    print(f"Ошибка: Количество имен ({len(section_names)}) не совпадает с числом столбцов ({len(data.columns)})")

if mfr:
    if len(section_names_mfr) == len(data_mfr.columns):
        data_mfr.columns = section_names_mfr
        for reverse_section in section_names_mfr_reverse:
            if reverse_section in section_names_mfr:
                col_index = section_names_mfr.index(reverse_section)
                col_name = section_names_mfr[col_index]
                if col_name in data_mfr.columns:
                    data_mfr[col_name] = data_mfr[col_name] * -1
        data_mfr = data_mfr.drop(columns=section_skip, errors='ignore')
        section_names_for_plot_mfr = [name for name in section_names_for_plot_mfr if name not in section_skip]
        section_names_mfr = [name for name in section_names_mfr if name not in section_skip]
    else:
        print(f"Ошибка: Количество имен ({len(section_names_mfr)}) не совпадает с числом столбцов ({len(data_mfr.columns)})")




GOST = True
style = '-'
# x_limits = [500, 1700]
x_limits = avg_interval
# x_limits = None

# y_limits = None
styles = [style] * len(section_names)

colors = plt.cm.tab10.colors[:len(section_names)]

plot_result('01_ptot', x_label, r'$p*,\ Па$', (data, section_names, styles, section_names_for_plot, y_limits, colors), GOST=GOST, x_limits=x_limits, swap_axes=False)


output_file = 'average_parameters.xlsx'
avg_data_transposed.to_excel(output_file, index=True)

if mfr:
    # y_limits_mfr = None
    colors_mfr = plt.cm.tab10.colors[:len(section_names_mfr)]
    plot_result('02_mfr', x_label, r'$\dot{m}$, кг/с', (data_mfr, section_names_mfr, [style] * len(section_names_mfr), section_names_for_plot_mfr, y_limits_mfr, colors_mfr), GOST=GOST, x_limits=x_limits, swap_axes=False)
    output_file_mfr = 'average_parameters_mfr.xlsx'
    avg_data_mfr_transposed.to_excel(output_file_mfr, index=True)







print('debug')

