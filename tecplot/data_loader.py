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
# import Kinetics_Initiate as kin
from statistics import mean
from mpl_toolkits.mplot3d import Axes3D
#import logging
#logging.basicConfig(level=logging.DEBUG)
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional


def _is_float(s: str) -> bool:
    """Проверяет, является ли строка числом с плавающей точкой."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _load_variable(input_file: Path) -> np.ndarray:
    """Разбор файла с данными (ваша существующая функция)."""
    variable_blocks = []
    current_block = []
    with open(input_file, "r") as f:
        for line in f:
            stripped_line = line.strip()
            if not stripped_line:
                if current_block:
                    variable_blocks.append(np.array(current_block))
                current_block = []
            parts = stripped_line.split()
            if parts and _is_float(parts[0]):
                current_block.append(float(parts[1]))
    if variable_blocks:
        variable = np.vstack(variable_blocks)
    else:
        variable = np.array([])
    return variable


class DataLoader:
    def __init__(self, path: Path):
        self.path = path
        self.file_to_define_n_slices_n_times = 'Average_CoordinateX.txt'
        self.n_skip = 10
        self.n_slices = None
        self.n_time_steps = None
        self.time = None
        self.x_coord = None
        self.data = {}  # Словарь для хранения данных {parameter_name: np.array}

        # Определяем n_slices и n_times
        self._determine_n_slices()
        self._determine_time()
        self._load_x_coord()

        # Сканируем папку и загружаем данные для всех параметров
        self._load_all_data()

    def _determine_n_slices(self):
        with open(self.path / self.file_to_define_n_slices_n_times, "r") as f:
            lines = f.readlines()
        self.n_slices = sum(1 for line in lines if "Time Strand" in line)
        print(f"Определено количество сечений (n_slices): {self.n_slices}")

    def _determine_time(self):
        time = []
        with open(self.path / self.file_to_define_n_slices_n_times, "r") as f:
            for line in f:
                stripped_line = line.strip()
                # print(stripped_line)
                if not stripped_line:
                    break
                parts = stripped_line.split()
                # print(parts)
                if parts and _is_float(parts[0]):
                    print(f'добавляем время {parts[0]}')
                    time.append(float(parts[0]))
        self.n_time_steps = len(time)
        self.time = np.array(time, dtype=np.float64)
        print(f"Определено количество временных шагов (n_times): {self.n_time_steps}")

    def _load_all_data(self):
        """Загружает данные для всех параметров в папке."""

        # Загружаем данные для всех Average_* параметров
        parameters_average = self._scan_data_files(prefix="Average_", suffix=".txt")
        for param in parameters_average:
            file_path = self.path / f"Average_{param}.txt"
            self.data[param] = _load_variable(file_path)

        # Загружаем данные для всех Scalar_* параметров
        parameters_scalar = self._scan_data_files(prefix="Scalar_", suffix=".txt")
        for param in parameters_scalar:
            file_path = self.path / f"Scalar_{param}.txt"
            self.data[param] = _load_variable(file_path)

    def _scan_data_files(self, prefix: str, suffix: str) -> List[str]:
        """Сканирует папку и возвращает список имён параметров, для которых есть файлы."""
        files = [f for f in self.path.iterdir() if f.is_file()]
        parameters = []
        for file in files:
            if file.name.startswith(prefix) and file.name.endswith(suffix):
                param_name = file.name[len(prefix):-len(suffix)]
                parameters.append(param_name)
        return parameters

    def _load_x_coord(self):
        with open(self.path / self.file_to_define_n_slices_n_times, "r") as f:
            file = csv.reader(f, delimiter=" ")
            x_coord = []
            r = 1
            s = 0
            for row in file:
                r += 1
                if r == (self.n_time_steps + self.n_skip) * (s + 1) - 7:
                    s += 1
                    x_coord.append(float(row[8]))
        self.x_coord = np.array(x_coord, dtype=np.float64)

    def get_parameter(self, param_name: str) -> np.ndarray:
        """Возвращает массив данных для указанного параметра."""
        return self.data.get(param_name, None)

    def get_all_parameters(self) -> dict:
        """Возвращает словарь со всеми загруженными параметрами."""
        return self.data


class DataAggregator:
    def __init__(self, work_path: str):
        self.work_path = Path(work_path)
        self.only_dirs = [d for d in os.listdir(self.work_path) if os.path.isdir(os.path.join(self.work_path, d))]
        self.time = None
        self.x_coord = None
        self.raw_data: Dict[str, np.ndarray] = {}
        self._aggregate_data()

    def _aggregate_data(self):
        """Объединяет данные из всех папок."""
        for dir_name in self.only_dirs:
            dir_path = self.work_path / dir_name
            loader = DataLoader(dir_path)

            # Если это первая папка, инициализируем данные
            if self.time is None:
                self.time = loader.time
                self.x_coord = loader.x_coord
                for param_name, param_data in loader.get_all_parameters().items():
                    self.raw_data[param_name] = param_data
            else:
                # Для последующих папок дополняем данные
                self.time = np.hstack((self.time, loader.time))
                for param_name, param_data in loader.get_all_parameters().items():
                    if param_name in self.raw_data:
                        self.raw_data[param_name] = np.hstack((self.raw_data[param_name], param_data))
                    else:
                        print(f'Параметр {param_name} отсутствует в наборе данных из первой папки')

    def get_parameter(self, param_name: str) -> Optional[np.ndarray]:
        """Возвращает массив данных для указанного параметра."""
        return self.raw_data.get(param_name, None)

    def get_all_parameters(self) -> Dict[str, np.ndarray]:
        """Возвращает словарь со всеми загруженными параметрами."""
        return self.raw_data

    def get_data_on_interval(self, left: int, right: int = 0) -> Dict[str, np.ndarray]:
        """
        Возвращает данные на интервале времени.
        Args:
            left: Левая граница интервала
            right: Правая граница интервала (0 - до конца)
        Returns:
            Словарь с данными на интервале
        """
        data_on_interval = {}
        for param_name, param_data in self.raw_data.items():
            data_on_interval[param_name] = self._reduce_2d_array(param_data, left, right)
        return data_on_interval

    def get_averaged_dataframe(self, left: int, right: int = 0) -> pd.DataFrame:
        """
        Возвращает DataFrame с осреднёнными по времени данными.
        Args:
            left: Левая граница интервала осреднения
            right: Правая граница интервала осреднения (0 - до конца)
        Returns:
            DataFrame с осреднёнными данными, где:
            - Индексы: координаты x
            - Колонки: параметры
            - Значения: осреднённые по времени значения
        """
        data_on_interval = self.get_data_on_interval(left, right)
        df = pd.DataFrame(index=self.x_coord)
        for param_name, param_data in data_on_interval.items():
            df[param_name] = param_data.mean(axis=1)
        return df

    def get_instant_dataframe(self, left: int, right: int, point_fraction: float = 0.5) -> pd.DataFrame:
        """
        Возвращает DataFrame с мгновенными значениями в выбранной точке.
        Args:
            left: Левая граница интервала выборки
            right: Правая граница интервала выборки (0 - до конца)
            point_fraction: Доля от 0 до 1 для выбора точки в интервале
        Returns:
            DataFrame с мгновенными значениями, где:
            - Индексы: координаты x
            - Колонки: параметры
            - Значения: мгновенные значения в выбранной точке
        """
        data_on_interval = self.get_data_on_interval(left, right)
        df = pd.DataFrame(index=self.x_coord)
        n_points = next(iter(data_on_interval.values())).shape[1]  # Количество точек в интервале
        point_index = int((n_points - 1) * point_fraction)

        print(f'исходное время {self.time}')
        time_interval = self._reduce_1d_array(self.time, left, right)
        print(f'время интервала {time_interval}')
        # time_interval = self.time[left:(len(self.time) - right if right != 0 else None)]
        instant_time = time_interval[point_index]
        print(f'количество точек {n_points} индекс мгновенной точки {point_index}, время для мгновенной точки: {instant_time}')
        for param_name, param_data in data_on_interval.items():
            df[param_name] = param_data[:, point_index]
        return df

    @staticmethod
    def _reduce_2d_array(array_2d: np.ndarray, left: int, right: int = 0) -> np.ndarray:
        """
        Возвращает выборку из двумерного массива по указанному интервалу столбцов.
        Args:
            array_2d: Исходный двумерный массив (матрица или 2D массив NumPy).
            left: Количество столбцов, которые нужно пропустить слева.
            right: Количество столбцов, которые нужно пропустить справа.
        Returns:
            Массив с выборкой по интервалу столбцов.
        Raises:
            ValueError: Если left или right отрицательны, или если left >= array_2d.shape[1].
        """
        if left < 0 or right < 0:
            raise ValueError("left и right должны быть неотрицательными.")
        if left >= array_2d.shape[1]:
            raise ValueError("left не может быть больше или равен количеству столбцов в массиве.")
        if left + right >= array_2d.shape[1]:
            raise ValueError("сумма left + right не может быть больше или равно количеству столбцов в массиве.")
        if right == 0:
            return array_2d[:, left:]
        else:
            return array_2d[:, left:-right]

    @staticmethod
    def _reduce_1d_array(array_1d: np.ndarray, left: int, right: int = 0) -> np.ndarray:
        """
        Возвращает срез списка по указанному интервалу с обрезкой слева и справа.
        Args:
            array_1d: Исходный одномерный массив (список или 1D массив NumPy).
            left: Количество элементов, которые нужно пропустить слева.
            right: Количество элементов, которые нужно пропустить справа.
        Returns:
            Срез списка от left до (len(lst) - right).
        Raises:
            ValueError: Если left или right отрицательны, или если left >= len(array_1d), или если left + right >= len(array_1d).
        """
        if left < 0 or right < 0:
            raise ValueError("left и right должны быть неотрицательными.")
        if left >= len(array_1d):
            raise ValueError("left не может быть больше или равен размеру массива.")
        if left + right >= len(array_1d):
            raise ValueError("сумма left + right не может быть больше или равно размеру массива.")
        if right == 0:
            return array_1d[left:]
        else:
            return array_1d[left:-right]





#
#
# class ScrapLocalFolderMinimal:
#     def __init__(self, path, n_slices, set_x_throat, list_species, mfr_fuel_all):
#         os.chdir(path)
#         self.n_skip = 10  # число строк пропустить при разоборе файла интеграла из Tecplot
#         self.n_lines = 0
#         self.times = []
#         self.x_coord = []
#         self.n_slices = n_slices
#         self.set_x_throat = set_x_throat
#         self.list_species = list_species
#         self.g = 9.8
#         self.mfr_fuel_all = mfr_fuel_all
#
#         # определение количества временных срезов
#         for row in csv.reader(open('Average_x.txt', 'r'), delimiter=' '):
#             self.n_lines += 1
#         self.n_times = (self.n_lines - 1) / self.n_slices - self.n_skip
#         print('Загружено шагов по времени: ' + str(int(self.n_times)))
#
#         # создание массива времени и координаты
#         file = csv.reader(open('Average_x.txt', 'r'), delimiter=' ')
#         r = 1
#         s = 0
#         for row in file:
#             if 2 < r <= self.n_times + 2:
#                 current_time = row[0]
#                 self.times.append(current_time)
#             r += 1
#             if r == (self.n_times + self.n_skip) * (s + 1) - 7:
#                 s += 1
#                 current_x = row[8]
#                 self.x_coord.append(current_x)
#         self.np_time = np.array(self.times, dtype=np.float)
#         self.np_x = np.array(self.x_coord, dtype=np.float)
#         self.set_mfr = file_parser_variable('Scalar_mfr.txt', self.n_times, self.n_skip)
#
#         # Осредненные по площади концентрации
#         self.set_Y_species = []
#         for sp in self.list_species:
#             self.y_sp = file_parser_variable(''.join(('Average_Y_', sp.name, '.txt')), self.n_times, self.n_skip)
#             self.set_Y_species.append(self.y_sp)
#
#         # Расход компонент
#         self.set_mfr_species = []
#         for sp in self.list_species:
#             self.mfr_sp = file_parser_variable(''.join(('Scalar_mfr_', sp.name, '.txt')), self.n_times, self.n_skip)
#             self.set_mfr_species.append(self.mfr_sp)
#
#         # ПРОВЕРКА
#         self.set_Y_sum = sum(self.set_Y_species)
#
#         # Энтальпия образования смеси
#         self.set_H0_mixture = 0
#         for ind, sp in enumerate(self.list_species):
#             self.set_H0_mixture += self.set_Y_species[ind] * sp.h0_298() / sp.mu()
#
#
#     def time(self):
#         return self.np_time
#
#     def x(self):
#         return self.np_x
#
#     # Определение индекса сечения критики (для замера тяги и удельного импульса)
#     def x_throat(self):
#         i_throat = 0
#         while self.np_x[i_throat] >= self.set_x_throat:
#             i_throat += 1
#         return self.np_x[i_throat]
#
#     # СЧИТЫВАНИЕ ВХОДНЫХ ФАЙЛОВ
#
#     def mfr(self):
#             return self.set_mfr
#
#     def mfr_species(self):
#         return self.set_mfr_species
#
#     def Y_species(self):
#         return self.set_Y_species
#
#     # ПРОВЕРКА
#     def Y_sum(self):
#         return self.set_Y_sum
#
#     def H0_mixture(self):
#         return self.set_H0_mixture
#
#
#
# class ScrapLocalFolder:
#     def __init__(self, path, n_slices, set_x_throat, list_species, mfr_fuel_all):
#         os.chdir(path)
#         self.n_skip = 10            # число строк пропустить при разоборе файла интеграла из Tecplot
#         self.n_lines = 0
#         self.times = []
#         self.x_coord = []
#         self.n_slices = n_slices
#         self.set_x_throat = set_x_throat
#         self.list_species = list_species
#         self.g = 9.8
#         self.mfr_fuel_all = mfr_fuel_all
#
#         # определение количества временных срезов
#         for row in csv.reader(open('Average_x.txt', 'r'), delimiter=' '):
#             self.n_lines += 1
#         self.n_times = (self.n_lines - 1) / self.n_slices - self.n_skip
#         print('Загружено шагов по времени: ' + str(int(self.n_times)))
#
#         # создание массива времени и координаты
#         file = csv.reader(open('Average_x.txt', 'r'), delimiter=' ')
#         r = 1
#         s = 0
#         for row in file:
#             if 2 < r <= self.n_times + 2:
#                 current_time = row[0]
#                 self.times.append(current_time)
#             r += 1
#             if r == (self.n_times + self.n_skip) * (s + 1) - 7:
#                 s += 1
#                 current_x = row[8]
#                 self.x_coord.append(current_x)
#         self.np_time = np.array(self.times, dtype=np.float)
#         self.np_x = np.array(self.x_coord, dtype=np.float)
#         self.set_velocity = file_parser_variable('Average_v.txt', self.n_times, self.n_skip)
#         self.set_t_tot = file_parser_variable('Average_t_tot.txt', self.n_times, self.n_skip)
#         self.set_t_stat = file_parser_variable('Average_t_stat.txt', self.n_times, self.n_skip)
#         self.set_p_tot = file_parser_variable('Average_p_tot.txt', self.n_times, self.n_skip)
#         self.set_p_stat = file_parser_variable('Average_p_stat.txt', self.n_times, self.n_skip)
#         self.set_mach = file_parser_variable('Average_mach.txt', self.n_times, self.n_skip)
#         self.set_mfr = file_parser_variable('Scalar_mfr.txt', self.n_times, self.n_skip)
#
#         # Расход компонент
#         self.set_mfr_species = []
#         for sp in self.list_species:
#             self.mfr_sp = file_parser_variable(''.join(('Scalar_mfr_', sp.name, '.txt')), self.n_times, self.n_skip)
#             self.set_mfr_species.append(self.mfr_sp)
#
#         self.set_Ro_Vx_Enthalpy_0 = file_parser_variable('Average_Ro_Vx_Enthalpy_0.txt', self.n_times, self.n_skip)
#         self.set_Ro_Vx_Vx = file_parser_variable('Scalar_Ro_Vx_Vx.txt', self.n_times, self.n_skip)
#         self.set_p_stat_integral = file_parser_variable('Scalar_p_stat.txt', self.n_times, self.n_skip)
#
#
#         # Осредненные по площади концентрации
#         self.set_Y_species = []
#         for sp in self.list_species:
#             self.y_sp = file_parser_variable(''.join(('Average_Y_', sp.name, '.txt')), self.n_times, self.n_skip)
#             self.set_Y_species.append(self.y_sp)
#
#         # Осредненные по расходу концентрации
#         self.set_Y_species_mfr_averaged = []
#         for ind, sp in enumerate(self.list_species):
#             self.y_sp_mfr = self.set_mfr_species[ind] / self.set_mfr
#             self.set_Y_species_mfr_averaged.append(self.y_sp_mfr)
#
#         # ПРОВЕРКА
#         self.set_Y_sum = sum(self.set_Y_species)
#
#         self.set_Y_sum_mfr_averaged = sum(self.set_Y_species_mfr_averaged)
#         self.set_mfr_sum_norm = sum(self.set_mfr_species) / self.set_mfr
#
#         # Энтальпия образования смеси
#         self.set_H0_mixture = 0
#         for ind, sp in enumerate(self.list_species):
#             self.set_H0_mixture += self.set_Y_species[ind] * sp.h0_298() / sp.mu()
#
#     def time(self):
#         return self.np_time
#
#     def x(self):
#         return self.np_x
#
#     # Определение индекса сечения критики (для замера тяги и удельного импульса)
#     def x_throat(self):
#         i_throat = 0
#         while self.np_x[i_throat] >= self.set_x_throat:
#             i_throat += 1
#         return self.np_x[i_throat]
#
#     # СЧИТЫВАНИЕ ВХОДНЫХ ФАЙЛОВ
#
#
#     def velocity(self):
#         return self.set_velocity
#
#     def t_tot(self):
#         return self.set_t_tot
#
#     def t_stat(self):
#         return self.set_t_stat
#
#     def p_tot(self):
#         return self.set_p_tot
#
#     def p_stat(self):
#         return self.set_p_stat
#
#     def mach(self):
#         return self.set_mach
#
#     def mfr(self):
#         return self.set_mfr
#
#     def mfr_species(self):
#         return self.set_mfr_species
#
#     def Ro_Vx_Enthalpy_0(self):
#         return self.set_Ro_Vx_Enthalpy_0
#
#     def Ro_Vx_Vx(self):
#         return self.set_Ro_Vx_Vx
#
#     def p_stat_integral(self):
#         return self.set_p_stat_integral
#
#     # Перевод из Н в кг
#     def Ro_Vx_Vx_kg(self):
#         return self.set_Ro_Vx_Vx/self.g
#
#     def p_stat_integral_kg(self):
#         return self.set_p_stat_integral/self.g
#
#     # Тяга (кг)
#     def F_all(self):
#         return self.set_Ro_Vx_Vx/self.g + self.set_p_stat_integral/self.g
#
#     # Удельный импульс (c)
#     def I_spec(self):
#         return (self.set_Ro_Vx_Vx/self.g + self.set_p_stat_integral/self.g) / self.mfr_fuel_all
#
#     def Y_species(self):
#         return self.set_Y_species
#
#     # ПРОВЕРКА
#     def Y_sum(self):
#         return self.set_Y_sum
#
#     def Y_sum_mfr_averaged(self):
#         return self.set_Y_sum_mfr_averaged
#
#     def mfr_sum_norm(self):
#         return self.set_mfr_sum_norm
#
#     def H0_mixture(self):
#         return self.set_H0_mixture



