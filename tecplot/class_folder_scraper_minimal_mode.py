import time
import datetime
import os
import re
import numpy as np
from math import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import csv
import pandas as pd
import xlsxwriter
import Kinetics_Initiate as kin
from statistics import mean
from mpl_toolkits.mplot3d import Axes3D
#import logging
#logging.basicConfig(level=logging.DEBUG)



'''
def file_parser_variable(input_file, n_times, n_skip):
    work_file = csv.reader(open(input_file, 'r'), delimiter=' ')
    variable = np.zeros(shape=(1, int(n_times)), dtype=int)
    variable_1D = np.array([])
    variable_av = np.array([])
    # print(variable)
    # print(variable.shape)
    r = 0
    t = 0
    s = 0
    var_av = 0
    for row in work_file:
        if (2 + (n_times + n_skip) * s) <= r <= ((n_times + n_skip) * (s + 1)):
            if t < n_times:
                var = row[8]
                variable_1D = np.append(variable_1D, float(var))
                var_av += float(var)
            # print(r, '\t', t, '\t', s, '\t', row, '\t', variable_1D)
            t += 1
        if r == (n_times + n_skip) * (s + 1):
            variable_av = np.append(variable_av, var_av / n_times)
            s += 1
            t = 0
            var_av = 0
            variable = np.concatenate((variable, np.expand_dims(variable_1D, axis=0)), axis=0)
            variable_1D = np.array([])
        r += 1
    variable = np.delete(variable, 0, axis=0)
    variable_av = variable_av[:, np.newaxis]
    variable = np.append(variable_av, variable, axis=1)
    # print('average: ', variable_av)
    # print(variable_av.shape)
    # Возвращает двумерный массив НП где первый стобец - осреднённые значения
    return variable
'''


# функция разбора входного файла интегральных параметров, записанных из tecplot
def file_parser_variable(input_file, n_times, n_skip):
    work_file = csv.reader(open(input_file, 'r'), delimiter=' ')
    variable = np.zeros(shape=(1, int(n_times)), dtype=int)
    variable_1D = np.array([])
    # variable_av = np.array([])
    # print(variable)
    # print(variable.shape)
    r = 0
    t = 0
    s = 0
    # var_av = 0
    for row in work_file:
        if (2 + (n_times + n_skip) * s) <= r <= ((n_times + n_skip) * (s + 1)):
            if t < n_times:
                var = row[8]
                variable_1D = np.append(variable_1D, float(var))
                #var_av += float(var)
            # print(r, '\t', t, '\t', s, '\t', row, '\t', variable_1D)
            t += 1
        if r == (n_times + n_skip) * (s + 1):
            #variable_av = np.append(variable_av, var_av / n_times)
            s += 1
            t = 0
            var_av = 0
            variable = np.concatenate((variable, np.expand_dims(variable_1D, axis=0)), axis=0)
            variable_1D = np.array([])
        r += 1
    variable = np.delete(variable, 0, axis=0)
    #variable_av = variable_av[:, np.newaxis]
    #variable = np.append(variable_av, variable, axis=1)
    # print('average: ', variable_av)
    # print(variable_av.shape)
    # Возвращает двумерный массив НП где первый стобец - осреднённые значения
    return variable


class ScrapLocalFolderMinimal:
    def __init__(self, path, n_slices, set_x_throat, list_species, mfr_fuel_all):
        os.chdir(path)
        self.n_skip = 10  # число строк пропустить при разоборе файла интеграла из Tecplot
        self.n_lines = 0
        self.times = []
        self.x_coord = []
        self.n_slices = n_slices
        self.set_x_throat = set_x_throat
        self.list_species = list_species
        self.g = 9.8
        self.mfr_fuel_all = mfr_fuel_all

        # определение количества временных срезов
        for row in csv.reader(open('Average_x.txt', 'r'), delimiter=' '):
            self.n_lines += 1
        self.n_times = (self.n_lines - 1) / self.n_slices - self.n_skip
        print('Загружено шагов по времени: ' + str(int(self.n_times)))

        # создание массива времени и координаты
        file = csv.reader(open('Average_x.txt', 'r'), delimiter=' ')
        r = 1
        s = 0
        for row in file:
            if 2 < r <= self.n_times + 2:
                current_time = row[0]
                self.times.append(current_time)
            r += 1
            if r == (self.n_times + self.n_skip) * (s + 1) - 7:
                s += 1
                current_x = row[8]
                self.x_coord.append(current_x)
        self.np_time = np.array(self.times, dtype=np.float)
        self.np_x = np.array(self.x_coord, dtype=np.float)
        self.set_mfr = file_parser_variable('Scalar_mfr.txt', self.n_times, self.n_skip)

        # Осредненные по площади концентрации
        self.set_Y_species = []
        for sp in self.list_species:
            self.y_sp = file_parser_variable(''.join(('Average_Y_', sp.name, '.txt')), self.n_times, self.n_skip)
            self.set_Y_species.append(self.y_sp)

        # Расход компонент
        self.set_mfr_species = []
        for sp in self.list_species:
            self.mfr_sp = file_parser_variable(''.join(('Scalar_mfr_', sp.name, '.txt')), self.n_times, self.n_skip)
            self.set_mfr_species.append(self.mfr_sp)

        # ПРОВЕРКА
        self.set_Y_sum = sum(self.set_Y_species)

        # Энтальпия образования смеси
        self.set_H0_mixture = 0
        for ind, sp in enumerate(self.list_species):
            self.set_H0_mixture += self.set_Y_species[ind] * sp.h0_298() / sp.mu()


    def time(self):
        return self.np_time

    def x(self):
        return self.np_x

    # Определение индекса сечения критики (для замера тяги и удельного импульса)
    def x_throat(self):
        i_throat = 0
        while self.np_x[i_throat] >= self.set_x_throat:
            i_throat += 1
        return self.np_x[i_throat]

    # СЧИТЫВАНИЕ ВХОДНЫХ ФАЙЛОВ

    def mfr(self):
            return self.set_mfr

    def mfr_species(self):
        return self.set_mfr_species

    def Y_species(self):
        return self.set_Y_species

    # ПРОВЕРКА
    def Y_sum(self):
        return self.set_Y_sum

    def H0_mixture(self):
        return self.set_H0_mixture



class ScrapLocalFolder:
    def __init__(self, path, n_slices, set_x_throat, list_species, mfr_fuel_all):
        os.chdir(path)
        self.n_skip = 10            # число строк пропустить при разоборе файла интеграла из Tecplot
        self.n_lines = 0
        self.times = []
        self.x_coord = []
        self.n_slices = n_slices
        self.set_x_throat = set_x_throat
        self.list_species = list_species
        self.g = 9.8
        self.mfr_fuel_all = mfr_fuel_all

        # определение количества временных срезов
        for row in csv.reader(open('Average_x.txt', 'r'), delimiter=' '):
            self.n_lines += 1
        self.n_times = (self.n_lines - 1) / self.n_slices - self.n_skip
        print('Загружено шагов по времени: ' + str(int(self.n_times)))

        # создание массива времени и координаты
        file = csv.reader(open('Average_x.txt', 'r'), delimiter=' ')
        r = 1
        s = 0
        for row in file:
            if 2 < r <= self.n_times + 2:
                current_time = row[0]
                self.times.append(current_time)
            r += 1
            if r == (self.n_times + self.n_skip) * (s + 1) - 7:
                s += 1
                current_x = row[8]
                self.x_coord.append(current_x)
        self.np_time = np.array(self.times, dtype=np.float)
        self.np_x = np.array(self.x_coord, dtype=np.float)
        self.set_velocity = file_parser_variable('Average_v.txt', self.n_times, self.n_skip)
        self.set_t_tot = file_parser_variable('Average_t_tot.txt', self.n_times, self.n_skip)
        self.set_t_stat = file_parser_variable('Average_t_stat.txt', self.n_times, self.n_skip)
        self.set_p_tot = file_parser_variable('Average_p_tot.txt', self.n_times, self.n_skip)
        self.set_p_stat = file_parser_variable('Average_p_stat.txt', self.n_times, self.n_skip)
        self.set_mach = file_parser_variable('Average_mach.txt', self.n_times, self.n_skip)
        self.set_mfr = file_parser_variable('Scalar_mfr.txt', self.n_times, self.n_skip)

        # Расход компонент
        self.set_mfr_species = []
        for sp in self.list_species:
            self.mfr_sp = file_parser_variable(''.join(('Scalar_mfr_', sp.name, '.txt')), self.n_times, self.n_skip)
            self.set_mfr_species.append(self.mfr_sp)

        self.set_Ro_Vx_Enthalpy_0 = file_parser_variable('Average_Ro_Vx_Enthalpy_0.txt', self.n_times, self.n_skip)
        self.set_Ro_Vx_Vx = file_parser_variable('Scalar_Ro_Vx_Vx.txt', self.n_times, self.n_skip)
        self.set_p_stat_integral = file_parser_variable('Scalar_p_stat.txt', self.n_times, self.n_skip)


        # Осредненные по площади концентрации
        self.set_Y_species = []
        for sp in self.list_species:
            self.y_sp = file_parser_variable(''.join(('Average_Y_', sp.name, '.txt')), self.n_times, self.n_skip)
            self.set_Y_species.append(self.y_sp)

        # Осредненные по расходу концентрации
        self.set_Y_species_mfr_averaged = []
        for ind, sp in enumerate(self.list_species):
            self.y_sp_mfr = self.set_mfr_species[ind] / self.set_mfr
            self.set_Y_species_mfr_averaged.append(self.y_sp_mfr)

        # ПРОВЕРКА
        self.set_Y_sum = sum(self.set_Y_species)

        self.set_Y_sum_mfr_averaged = sum(self.set_Y_species_mfr_averaged)
        self.set_mfr_sum_norm = sum(self.set_mfr_species) / self.set_mfr

        # Энтальпия образования смеси
        self.set_H0_mixture = 0
        for ind, sp in enumerate(self.list_species):
            self.set_H0_mixture += self.set_Y_species[ind] * sp.h0_298() / sp.mu()

    def time(self):
        return self.np_time

    def x(self):
        return self.np_x

    # Определение индекса сечения критики (для замера тяги и удельного импульса)
    def x_throat(self):
        i_throat = 0
        while self.np_x[i_throat] >= self.set_x_throat:
            i_throat += 1
        return self.np_x[i_throat]

    # СЧИТЫВАНИЕ ВХОДНЫХ ФАЙЛОВ


    def velocity(self):
        return self.set_velocity

    def t_tot(self):
        return self.set_t_tot

    def t_stat(self):
        return self.set_t_stat

    def p_tot(self):
        return self.set_p_tot

    def p_stat(self):
        return self.set_p_stat

    def mach(self):
        return self.set_mach

    def mfr(self):
        return self.set_mfr

    def mfr_species(self):
        return self.set_mfr_species

    def Ro_Vx_Enthalpy_0(self):
        return self.set_Ro_Vx_Enthalpy_0

    def Ro_Vx_Vx(self):
        return self.set_Ro_Vx_Vx

    def p_stat_integral(self):
        return self.set_p_stat_integral

    # Перевод из Н в кг
    def Ro_Vx_Vx_kg(self):
        return self.set_Ro_Vx_Vx/self.g

    def p_stat_integral_kg(self):
        return self.set_p_stat_integral/self.g

    # Тяга (кг)
    def F_all(self):
        return self.set_Ro_Vx_Vx/self.g + self.set_p_stat_integral/self.g

    # Удельный импульс (c)
    def I_spec(self):
        return (self.set_Ro_Vx_Vx/self.g + self.set_p_stat_integral/self.g) / self.mfr_fuel_all

    def Y_species(self):
        return self.set_Y_species

    # ПРОВЕРКА
    def Y_sum(self):
        return self.set_Y_sum

    def Y_sum_mfr_averaged(self):
        return self.set_Y_sum_mfr_averaged

    def mfr_sum_norm(self):
        return self.set_mfr_sum_norm

    def H0_mixture(self):
        return self.set_H0_mixture



