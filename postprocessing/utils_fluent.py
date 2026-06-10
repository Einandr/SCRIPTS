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


def read_mon(file_path, file_name, avg_interval=None):
    full_path = f"{file_path}/{file_name}"
    with open(full_path, 'r') as f:
        first_line = f.readline()  # Первая строка (не нужна)
        second_line = f.readline()  # Вторая строка (не нужна)
        third_line = f.readline()
    if '"Time Step"' in third_line:
        third_line = third_line.replace('"Time Step"', '"Time_Step"')
    column_names = re.findall(r'"([^"]+)"', third_line)
    new_column_names = []
    for col_name in column_names:
        col_name = re.sub(r'.*\(|\).*', '', col_name)
        new_column_names.append(col_name)

    data = pd.read_csv(full_path, delimiter=' ', skiprows=3, header=None, names=new_column_names)

    # Удаление колонки Time_Step, если она есть
    data.drop(columns=['Time_Step'], inplace=True, errors='ignore')

    for col in data.columns:
        if col == 'Iteration':
            data[col] = data[col].astype(int)
        elif col == 'flow-time':
            data[col] = data[col].astype(float)
        else:
            data[col] = pd.to_numeric(data[col], errors='coerce')

    # Определение индексной колонки
    if 'flow-time' in data.columns:
        idx_col = 'flow-time'
    # elif 'Time_Step' in data.columns:
    #     idx_col = 'Time_Step'
    elif 'Iteration' in data.columns:
        idx_col = 'Iteration'
    else:
        raise ValueError("No valid index column found (flow-time, Time_Step, Time, or Iteration).")

    data = data.set_index(idx_col)

    if avg_interval is not None:
        min_val, max_val = avg_interval
    else:
        min_val, max_val = data.index.min(), data.index.max()

    avg_data = data.loc[min_val:max_val].mean(numeric_only=True).to_frame().T
    avg_data.insert(0, 'Interval', f'{min_val}-{max_val}')
    return data, avg_data



# def read_mon(file_path, file_name):
#     data = pd.read_csv(''.join((file_path, file_name)), delimiter=' ', skiprows=2)
#     new_column_names = []
#     for c in data.columns:
#         c = re.sub('\"', '', c)
#         c = re.sub('^\(', '', c)
#         c = re.sub('\)\)', ')', c)
#         new_column_names.append(c)
#     data.columns = new_column_names
#     return data
#
# def var_mean(df, var_name, min, max):
#     return df[var_name].loc[(df['Iteration'] >= min) & (df['Iteration'] <= max)].mean(axis=0)


def read_forces_file(filename, force_axis, walls):
    file = ''.join((path, workdir, '\\', filename))
    with open(filename, 'r') as fin:
        data_read = fin.read().splitlines(True)
    names = data_read[2]
    names = re.sub('["#]', '', names)
    names = re.sub(r'[\s]+', ' ', names)
    names = re.sub(r'Time Step', 'Time-Step', names)
    names = re.sub('^[(\s]+', '', names)
    names = re.sub('[)\s]+$', '', names)
    df = pd.read_csv(file, sep=' ', skiprows=3, header=None, skipinitialspace=True, names=names.split())
    for key in walls.keys():
        df[''.join(('m_f', force_axis, '(sum_', key, ')'))] = 0
        for item in walls[key]:
            df[''.join(('m_f', force_axis, '(sum_', key, ')'))] += df[''.join(('m_f', force_axis, '(', item, ')'))]
    return df


def read_moments_file(filename, force_axis, walls):
    file = ''.join((path, workdir, '\\', filename))
    with open(filename, 'r') as fin:
        data_read = fin.read().splitlines(True)
    names = data_read[2]
    names = re.sub('["#]', '', names)
    names = re.sub(r'[\s]+', ' ', names)
    names = re.sub(r'Time Step', 'Time-Step', names)
    names = re.sub('^[(\s]+', '', names)
    names = re.sub('[)\s]+$', '', names)
    df = pd.read_csv(file, sep=' ', skiprows=3, header=None, skipinitialspace=True, names=names.split())
    for key in walls.keys():
        df[''.join(('m_m', force_axis, '(sum_', key, ')'))] = 0
        for item in walls[key]:
            df[''.join(('m_m', force_axis, '(sum_', key, ')'))] += df[''.join(('m_m', force_axis, '(', item, ')'))]
    return df



def plot_pic(data_name, x, y, xlabel, ylabel, legend, xmin, xmax, ymin, ymax, use_xlimits, use_ylimits, pic_name):
    plt.rcParams["figure.figsize"] = (12, 6)
    ax = data_name.plot(x=x, y=y, grid=True, linewidth=1)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(legend)
    plt.legend(fontsize='x-small')
    # plt.plot(x[x_out], y[x_out], 'ro')
    # plt.axvline(x=x[x_out], linestyle='dashed', color='black')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.axvline(x=xmin, color='black')
    plt.axvline(x=xmax, color='black')
    if use_xlimits:
        ax.set_xlim(xmin=xmin, xmax=xmax)
    if use_ylimits:
        ax.set_ylim(ymin=ymin, ymax=ymax)
    plt.savefig(pic_name, dpi=400, bbox_inches='tight')
    plt.close()
    return None


def plot_pic_simple(data_name, x, y, xlabel, ylabel, legend, pic_name):
    plt.rcParams["figure.figsize"] = (12, 6)
    ax = data_name.plot(x=x, y=y, grid=True, linewidth=1)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(legend)
    plt.legend(fontsize='x-small')
    # plt.plot(x[x_out], y[x_out], 'ro')
    # plt.axvline(x=x[x_out], linestyle='dashed', color='black')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(pic_name, dpi=400, bbox_inches='tight')
    plt.close()
    return None






def plot_pic_force(data_name, axis, key, x, xlabel, ylabel, xmin, xmax, ymin, ymax, use_xlimits, use_ylimits, show_wall_all, pic_name):
    y = []
    if show_wall_all:
        if ''.join(('sum_', key)) not in walls[key]:
            walls[key].append(''.join(('sum_', key)))
    for item in walls[key]:
        y.append(''.join(('m_f', axis, '(', item, ')')))
    plot_pic(data_name, x, y, xlabel, ylabel, wallnames[key], xmin, xmax, ymin, ymax, use_xlimits, use_ylimits, pic_name)
    return None


def plot_pic_moment(data_name, axis, key, x, xlabel, ylabel, xmin, xmax, ymin, ymax, use_xlimits, use_ylimits, show_wall_all, pic_name):
    y = []
    if show_wall_all:
        if ''.join(('sum_', key)) not in walls[key]:
            walls[key].append(''.join(('sum_', key)))
    for item in walls[key]:
        y.append(''.join(('m_m', axis, '(', item, ')')))
    plot_pic(data_name, x, y, xlabel, ylabel, wallnames[key], xmin, xmax, ymin, ymax, use_xlimits, use_ylimits, pic_name)
    return None

# (data_name, x, y, xlabel, ylabel, legend, xmin, xmax, ymin, ymax, use_xlimits, use_ylimits, pic_name):



def var_mean(df, var_name, min, max, ave_parameter):
    return df[var_name].loc[(df[ave_parameter] >= min) & (df[ave_parameter] <= max)].mean(axis=0)


def write_averaged_result(boundaries, m_name, data_name, ave_parameter, outname):
    wb = xlsxwriter.Workbook(outname.join((m_name, '.xlsx')))
    wsh = wb.add_worksheet()

    for ind, item in enumerate(boundaries):
        wsh.set_column('A:B', 20)
        wsh.write(''.join(('A', str(ind+1))), item)
        wsh.write(''.join(('B', str(ind+1))), '{:.0f}'.format(var_mean(data_name, ''.join((m_name, '(', item, ')')), imin, imax, ave_parameter)))
    wb.close()

def write_averaged_result_simple(boundaries, m_name, data_name, ave_parameter, outname):
    wb = xlsxwriter.Workbook(outname.join((m_name, '.xlsx')))
    wsh = wb.add_worksheet()

    for ind, item in enumerate(boundaries):
        wsh.set_column('A:B', 20)
        wsh.write(''.join(('A', str(ind+1))), item)
        wsh.write(''.join(('B', str(ind+1))), '{:.2f}'.format(var_mean(data_name, item, imin, imax, ave_parameter)))
    wb.close()



print('stop debug')