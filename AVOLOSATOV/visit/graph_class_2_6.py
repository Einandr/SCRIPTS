import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from typing import Optional, Tuple, List
import math
import matplotlib


class GraphConfigurator:
    """Класс для настройки и построения графиков"""

    mark_type_list = ['o', 's', '^', '<', '>', 'v', 'D','d', '.', 'p', '*', 'h', 'H', '+', 'x', '|', '_', '1', '2', '3', '4'] # Список возможных маркеров

    line_type_list = ['-', '--', '-.', ':', (0, (10, 5)), (0, (20, 10)), (0, (30, 10)), (0, (20, 5, 2, 5)), (0, (30, 8, 3, 8)), (0, (25, 6, 2, 6, 2, 6))] # Список возможных типов линий

    colors_list = ["black", "#167d16",
                 "#1f77b4", "#FE0000", "#9467bd", "#ff7f0e", "#17becf",
                 "#edc949", "#ff9da7", "#140a72", "#58bc4b", "#e377c2",
                 "#bb5303", "#770707", "#b7a1c3", "#bcbd22", "#f28e2b",
                 "#7f7f7f", "#76b7b2", "#b2df8a", "#ff7f00", "#af7aa1",
                 "#a6cee3", "#8c564b", "#fdbf6f", "#9c755f", "#fb9a99",
                 "#bab0ab", "#33a02c", "#1f78b4", "#e15759", "#f28e2b",
                 "#6a3d9a",
                   "tab:pink", "tab:olive", "tab:cyan", "tab:purple","tab:brown",
                   "tab:orange", "tab:green", "tab:blue", "tab:red", "tab:gray",
                   "white"] # Список возможных цветов при построении графиков

    
    zero_flag = 1e-10 # Параметр для выставления 0 в начале координат (величины менее 1e-10 заменяются 0)

    def __init__(self, 
                 auto_range:bool=True,
                 x_ticks_num:int=5,
                 y_ticks_num:int=5,
                 XxYyZz_i_t_f:bool=False,
                 Ox_lim:Optional[Tuple[float, float]]=(1, 10),
                 Ox_step:Optional[float] = 1,
                 Oy_lim:Optional[Tuple[float, float]]=(2, 10), 
                 Oy_step:Optional[float] = 1,
                 precision_1:int=0, precision_2:int=0,
                 x_label:str='X', y_label:str='Y',
                 x_scale:str='linear', y_scale:str='linear',
                 window_size_x:float=12, window_size_y:float=6,
                 l_space:float=0.1, r_space:float=0.9, t_space:float=0.93, b_space:float=0.07,
                 font_size:int=22, font_family:str="Times New Roman",
                 grid_t_f:bool=True, rt_t_f:bool=True,
                 annot_t_f:bool=False,
                 fraction_of_points:Optional[float]=None,
                 single_value:bool=True,
                 ax=None):

    
        """Инициализация графика и базовых настроек
        
            Args:
                auto_range (bool, optional): Флаг активации автоматического определения границ графика. Defaults to True.
                x_ticks_num (int, optional): Количество меток на оси x для авто режима. Defaults to 5.
                y_ticks_num (int, optional): Количество меток на оси y для авто режима. Defaults to 5.
                XxYyZz_i_t_f (bool, optional): Флаг активации курсива для XxYyZz. Defaults to False.
                Ox_lim (Optional[Tuple], optional): Список из двух значений - левая и правая границы горизонтальной оси. Defaults to (1, 10).
                Ox_step (Optional[float], optional): Шаг по горизонтальной оси. Defaults to 1.
                Oy_lim (Optional[Tuple], optional): Список из двух значений - нижняя и верхняя границы вертикальной оси. Defaults to (1, 10).
                Oy_step (Optional[float], optional): Шаг по вертикальной оси. Defaults to to 1.
                precision_1 (int, optional): Количество знаков после запятой для меток на горизонтальной оси. Defaults to 0.
                precision_2 (int, optional): Количество знаков после запятой для меток на вертикальной оси. Defaults to 0.
                x_label (str, optional): Наименование горизонтальной оси. Defaults to 'X'.
                y_label (str, optional): Наименование вертикальной оси. Defaults to 'Y'.
                x_scale (str, optional): Тип шкалы горизонтальной оси - 'linear'/'log'. Defaults to 'linear'.
                y_scale (str, optional): Тип шкалы вертикальной оси - 'linear'/'log'. Defaults to 'linear'.
                window_size_x (int, optional): Размер окна рисунка по горизонтали. Defaults to 9.
                window_size_y (int, optional):  Размер окна рисунка по вертикали. Defaults to 6.
                l_space (float, optional): Размер поля слева. Defaults to 0.1.
                r_space (float, optional): Размер поля справа. Defaults to 0.9.
                t_space (float, optional): Размер поля сверху. Defaults to 0.93.
                b_space (float, optional): Размер поля снизу. Defaults to 0.07.
                font_size (int, optional): Размер шрифта. Defaults to init: 22.
                font_family (str, optional): Тип шрифта. Defaults to 'Times New Roman'.
                grid_t_f (bool, optional): Включение сетки на поле графика. Defaults True.
                rt_t_f (bool, optional): Включение верхней и правой границ графика. Defaults to True.  
                annot_t_f (bool, optional): Флаг активации аннотаций вместе с построением линий. Defaults to True.
                fraction_of_points (Optional[float], optional): Доля точек, по которым строится перпендикуляр для аннотации. Defaults to None.
                single_value (bool, optional): Замена одинаковых чисел в начале координат. Defaults to True.
                ax (): назначение осей в одно окно рисунка. Defaults to None.          
        """

        self.l_space, self.r_space, self.t_space, self.b_space = l_space, r_space, t_space, b_space
        # Создание окна с указанными размерами (опционально возможно несколько координатных систем в одном окне)
        if ax is None:
            self.fig, self.ax = plt.subplots(figsize=(window_size_x, window_size_y))
            self.fig.subplots_adjust(left=self.l_space, right=self.r_space,
                                     top=self.t_space, bottom=self.b_space) # Изменение размеров полей рисунка
        else:
            self.ax = ax
            self.fig = ax.figure  # сохраняем ссылку на фигуру, если она есть

        # Установка атрибутов экземпляров  
        self.auto_range=auto_range

        self.Ox_lim = Ox_lim
        self.Ox_step = Ox_step
        self.Oy_lim = Oy_lim
        self.Oy_step = Oy_step
        self.x_scale = x_scale
        self.y_scale = y_scale

        self.precision_1 = precision_1
        self.precision_2 = precision_2

        self.x_label = x_label
        self.y_label = y_label

        self.font_size = font_size
        self.font_family = font_family
        self.XxYyZz_i_t_f = XxYyZz_i_t_f

        self.grid_t_f = grid_t_f
        self.rt_t_f = rt_t_f
        self.annot_t_f = annot_t_f
        self.fraction_of_points = fraction_of_points

        self.single_value = single_value

        self.shifting_switch = True
        self.arrow_x = None
        self.arrow_y = None

        self._all_data_x = []
        self._all_data_y = []

        self.x_ticks_num = x_ticks_num
        self.y_ticks_num = y_ticks_num

        self.line_count = 0
        self.mark_count = 0
        self.count = 0
        self.an_ratio = 0.265 #0.4

        # Основные метки и цвета
        self.mc_mark_list = [GraphConfigurator.mark_type_list[i] for i in [0, 1, 2, 6, 7, 9, 10, 12, 13, 14]]
        self.mc_color_list = GraphConfigurator.colors_list
        
        # Проверка на адекватность задания границ графика при использовании логарифмической шкалы
        if self.x_scale == 'log' and (self.Ox_lim[0] <= 0 or self.Ox_lim[1] <= 0): # Правка
            self.Ox_lim = (1e-5, 1e+5)
            if not auto_range:
                print('The boundaries are set incorrectly for logarithmic scale. Automatic correction...')

        if self.y_scale == 'log' and (self.Oy_lim[0] <= 0 or self.Oy_lim[1] <= 0): # Правка
            self.Oy_lim = (1e-5, 1e+5)
            if not auto_range:
                print('The boundaries are set incorrectly for logarithmic scale. Automatic correction...')

        # Массивы для объектов легенды, возможно уже не нужен
        self.annotations = []
        
        self.lines = []

        # Словарь со всеми параметрами аннотаций и индексацией
        self.annot_for_sliders = []

        # Включение настроек по умолчанию для стартового окна
        self.update_graph()


    def update_graph(self):
        """Включение настроек других функций по умолчанию при создании окна
        """

        self.conf_ticks() # Обновление меток
        self.conf_axes() # Обновление оформления осей


    def save(self, path, dpi:int=300):
        """Сохранение графика
        
            Args:
                path (): Путь до места сохранения графика с наименованием.
                dpi (int, optional): Разрешение графика - пикселей на дюйм. Defaults to 300.        
        """
        self.fig.savefig(path, dpi=dpi)
        # plt.close(self.fig)


    @staticmethod
    def format_tick_labels(values, precision:int=2):
        """Форматирование меток на осях в строки с заданной точностью и разделителем ",".
           Если значение равно 0 (1e-10), возвращает "0" без разделителей.

            Args:
                values (): Массив чисел для форматирования.
                precision (int, optional): Количество знаков после запятой. Defaults to 2.
        """
        formatted = []
        for value in values:
            if abs(value) < GraphConfigurator.zero_flag: # Проверка на "практически ноль"
                formatted.append("0")
            else:
                s = f"{value:.{precision}f}".replace('.', ',')
                formatted.append(s)
        return formatted


    def conf_ticks(self, 
                   Ox_lim:Optional[Tuple[float, float]]=None,
                   Ox_step:Optional[float] = None,
                   Oy_lim:Optional[Tuple[float, float]]=None, 
                   Oy_step:Optional[float] = None,
                   x_scale:Optional[str]=None, y_scale:Optional[str]=None, 
                   grid_t_f:Optional[bool]=None,
                   font_size:Optional[int]=None, font_family:Optional[str]=None, 
                   precision_1:Optional[int]=None, precision_2:Optional[int]=None,
                   single_value:bool=None, zero_x:float=-0.03, zero_y:float=-0.055,
                   first_x_label:bool=False, first_y_label:bool=False):

        """Настройка шкалы и меток осей

            Args:
                Ox_lim (Optional[Tuple], optional): Список из двух значений - левая и правая границы горизонтальной оси. Defaults to None -> init: (0, 1).
                Ox_step (Optional[float], optional): Шаг по горизонтальной оси. Defaults to None -> init: 0.1.
                Oy_lim (Optional[Tuple], optional): Список из двух значений - нижняя и верхняя границы вертикальной оси. Defaults to None -> init: (0, 1).
                Oy_step (Optional[float], optional): Шаг по вертикальной оси. Defaults to None -> init: 0.1.
                x_scale (Optional[str], optional): Тип шкалы горизонтальной оси - 'linear'/'log'. Defaults to None -> init: 'linear'.
                y_scale (Optional[str], optional): Тип шкалы вертикальной оси - 'linear'/'log'. Defaults to None -> init:  'linear'.
                grid_t_f (Optional[bool], optional): Включение сетки на поле графика. Defaults to None -> init: True.
                font_size (int, optional): Размер шрифта. Defaults to None -> init: 16.
                font_family (str, optional): Тип шрифта. Defaults to None -> init: 'Times New Roman'.
                single_value (bool, optional): Замена одинаковых чисел в начале координат. Defaults to to None -> init: True.
                zero_x (float, optional): Положение нуля по горизонтали в долях от размера оси. Defaults to -0.03.
                zero_y (float, optional): Положение нуля по вертикали в долях от размера оси. Defaults to -0.055.
        """

        coef1 = 1.000 # коэффициент для установления границ отрисовки осей относительно заданных границ (нужен для корректной отрисовки, а может уже нет)
        coef2 = 5 # коэффициент для установления количества минорный делений 5 -> 5

        # Значения вводятся из init при отсутствии явного указания их через функцию
        if Ox_lim is None: Ox_lim = self.Ox_lim
        if Ox_step is None: Ox_step = self.Ox_step
        if Oy_lim is None: Oy_lim = self.Oy_lim
        if Oy_step is None: Oy_step = self.Oy_step
        if x_scale is None: x_scale = self.x_scale
        if y_scale is None: y_scale = self.y_scale
        if grid_t_f is None: grid_t_f = self.grid_t_f
        if font_size is None: font_size = self.font_size
        if font_family is None: font_family = self.font_family
        if precision_1 is None: precision_1 = self.precision_1

        if single_value is None: single_value = self.single_value
                
        if precision_2 is None: precision_2 = self.precision_2

        # Фиксация границ осей!!! здесь задаются размеры графика
        self.ax.set_xlim(Ox_lim[0], Ox_lim[1] * coef1)
        self.ax.set_ylim(Oy_lim[0], Oy_lim[1] * coef1)

        # Задание типа шкалы, возможные значения: linear/log
        self.ax.set_xscale(x_scale)
        self.ax.set_yscale(y_scale)
        
        # Задание параметров отрисовки делений (длина, ширина)
        self.ax.tick_params(axis='both', which='major', length=6, width=1.0)
        self.ax.tick_params(axis='both', which='minor', length=3, width=0.8)

        #############Правка:
        Ox_steps = math.ceil(round(((Ox_lim[1] - Ox_lim[0]) / Ox_step), -int((math.log10(Ox_step) - 2)))) # правка: обернул в round
        Ox_lim_ticks = (Ox_lim[0], Ox_lim[0] + Ox_step * Ox_steps)
        mimor_num_x = round((Ox_lim_ticks[1] - Ox_lim[1]) / (Ox_step / coef2)) + 1
        

        Oy_steps = math.ceil(round(((Oy_lim[1] - Oy_lim[0]) / Oy_step), -int((math.log10(Oy_step) - 2)))) # правка: обернул в round
        Oy_lim_ticks = (Oy_lim[0], Oy_lim[0] + Oy_step * Oy_steps)
        mimor_num_y = round((Oy_lim_ticks[1] - Oy_lim[1]) / (Oy_step / coef2)) + 1

        # Отрисовка меток на графике в соответствии с типом шкалы и границами
        if x_scale == 'linear' and y_scale == 'linear':
            # Массивы делений для осей, не включающие последние деления (для указания наименования шкалы)
            #############Правка:

            x_ticks = np.linspace(Ox_lim_ticks[0], Ox_lim_ticks[1], 
                                  round((Ox_lim_ticks[1] - Ox_lim_ticks[0]) / Ox_step + 1))[:-1]
            y_ticks = np.linspace(Oy_lim_ticks[0], Oy_lim_ticks[1], 
                                  round((Oy_lim_ticks[1] - Oy_lim_ticks[0]) / Oy_step + 1))[:-1]

            lables_x = self.format_tick_labels(x_ticks, precision_1)
            lables_y = self.format_tick_labels(y_ticks, precision_2)


            if first_x_label:
                lables_x[0] = ''

            if first_y_label:
                lables_y[0] = ''

            # Если включен режим single_value, убираем 0 с осей
            # if single_value and Ox_lim[0] == 0 and Oy_lim[0] == 0:
            #############Правка:
            if single_value:
                if Ox_lim[0] == Oy_lim[0] or (abs(Ox_lim[0]) < GraphConfigurator.zero_flag and abs(Oy_lim[0]) < GraphConfigurator.zero_flag):
                # x_ticks = [tick for tick in x_ticks if abs(tick) > GraphConfigurator.zero_flag] # Удаляются значения меньше zero_flag = 1e-10
                # y_ticks = [tick for tick in y_ticks if abs(tick) > GraphConfigurator.zero_flag]
                
                    x_ticks = x_ticks[1:]
                    y_ticks = y_ticks[1:]

                    #############Правка:
                    lables_x = lables_x[1:]
                    lables_y = lables_y[1:]

            self.ax.set_xticks(x_ticks, labels=lables_x, fontsize=font_size, fontname=font_family)
            self.ax.set_yticks(y_ticks, labels=lables_y, fontsize=font_size, fontname=font_family)
            self.ax.set_xticks(np.linspace(Ox_lim_ticks[0], Ox_lim_ticks[1], 
                                           round((Ox_lim_ticks[1] - Ox_lim_ticks[0]) / Ox_step) * coef2 + 1)[:-mimor_num_x], 
                                           minor=True, labels=None)
            self.ax.set_yticks(np.linspace(Oy_lim_ticks[0], Oy_lim_ticks[1], 
                                           round((Oy_lim_ticks[1] - Oy_lim_ticks[0]) / Oy_step) * coef2 + 1)[:-mimor_num_y], 
                                           minor=True, labels=None)
        
        elif x_scale == 'log' and y_scale == 'linear':
            # Задается корректный массив значений делений для логарифмическо шкалы
            x_ticks = np.logspace(np.log10(Ox_lim[0]), np.log10(Ox_lim[1]), num=int((np.log10(Ox_lim[1]) - np.log10(Ox_lim[0])) + 1)) 
            # Удалени последнего деления (для указания наименования шкалы)
            x_ticks = x_ticks[x_ticks < Ox_lim[1]]
            self.ax.set_xticks(x_ticks)
            # Назначение размера шрифта и семейства для делений логарифмической шкалы
            plt.setp(self.ax.get_xticklabels(), fontname=font_family, fontsize=font_size)
            #############Правка:
            y_ticks = np.linspace(Oy_lim_ticks[0], Oy_lim_ticks[1], 
                                  round((Oy_lim_ticks[1] - Oy_lim_ticks[0]) / Oy_step + 1))[:-1]
            lables_y = self.format_tick_labels(y_ticks, precision_2)

            self.ax.set_yticks(y_ticks, labels=lables_y, fontsize=font_size, fontname=font_family)
            self.ax.set_yticks(np.linspace(Oy_lim_ticks[0], Oy_lim_ticks[1], 
                                           round((Oy_lim_ticks[1] - Oy_lim_ticks[0]) / Oy_step) * coef2 + 1)[:-mimor_num_y], 
                                           minor=True, labels=None)
        
        elif x_scale == 'linear' and y_scale == 'log':
            y_ticks = np.logspace(np.log10(Oy_lim[0]), np.log10(Oy_lim[1]), num=int((np.log10(Oy_lim[1]) - np.log10(Oy_lim[0])) + 1))
            y_ticks = y_ticks[y_ticks < Oy_lim[1]]
            self.ax.set_yticks(y_ticks)
            plt.setp(self.ax.get_yticklabels(), fontname=font_family, fontsize=font_size)
            #############Правка:
            x_ticks = np.linspace(Ox_lim_ticks[0], Ox_lim_ticks[1], 
                                  round((Ox_lim_ticks[1] - Ox_lim_ticks[0]) / Ox_step + 1))[:-1]

            lables_x = self.format_tick_labels(x_ticks, precision_1)

            self.ax.set_xticks(x_ticks, labels=lables_x, fontsize=font_size, fontname=font_family)
            self.ax.set_xticks(np.linspace(Ox_lim_ticks[0], Ox_lim_ticks[1], 
                                           round((Ox_lim_ticks[1] - Ox_lim_ticks[0]) / Ox_step) * coef2 + 1)[:-mimor_num_x], 
                                           minor=True, labels=None)
            
        #############Правка:
        elif x_scale == 'log' and y_scale == 'log':
            x_ticks = np.logspace(np.log10(Ox_lim[0]), np.log10(Ox_lim[1]), num=int((np.log10(Ox_lim[1]) - np.log10(Ox_lim[0])) + 1)) 
            x_ticks = x_ticks[x_ticks < Ox_lim[1]]
            self.ax.set_xticks(x_ticks)
            plt.setp(self.ax.get_xticklabels(), fontname=font_family, fontsize=font_size) 
            y_ticks = np.logspace(np.log10(Oy_lim[0]), np.log10(Oy_lim[1]), num=int((np.log10(Oy_lim[1]) - np.log10(Oy_lim[0])) + 1))
            y_ticks = y_ticks[y_ticks < Oy_lim[1]]
            self.ax.set_yticks(y_ticks)
            plt.setp(self.ax.get_yticklabels(), fontname=font_family, fontsize=font_size)



        # Обработка двух нулей в начале координат - вместо 0 и 0 - один 0
        #############Правка:

        if single_value and x_scale == 'linear' and y_scale == 'linear': #Ox_lim[0] == 0 and Oy_lim[0] == 0:
            if Ox_lim[0] == Oy_lim[0] or (abs(Ox_lim[0]) < GraphConfigurator.zero_flag and abs(Oy_lim[0]) < GraphConfigurator.zero_flag):

                ax_bbox = self.ax.get_position()  # Получение координат точек бокса координатных осей и его длины, ширины      

                # Получаем вертикальное смещение горизонтальных меток от линии оси в пикселях
                tick = self.ax.get_xticklabels()[0] # Берем бокс первой метки
                bbox = tick.get_window_extent(renderer=self.fig.canvas.get_renderer())
                # Переводим пиксели в координаты Axes
                y_rel = (bbox.y0 - self.ax.bbox.y0) / self.ax.bbox.height

                # Получаем горизонтальное смещение вертикальных меток от линии оси в пикселях
                tick = self.ax.get_yticklabels()[0] # Берем бокс первой метки
                bbox = tick.get_window_extent(renderer=self.fig.canvas.get_renderer())
                # Переводим пиксели в координаты Axes
                x_rel = (bbox.x1 - self.ax.bbox.x0) / self.ax.bbox.width

                # В координатной системе всего окна получаем корректные координаты для отображения нуля
                y_fig = ax_bbox.y0 + y_rel * ax_bbox.height
                x_fig = ax_bbox.x0 + x_rel * ax_bbox.width

                # Проверяем, был ли уже установлен объект - текст с нулем

                precision_min = min(precision_1, precision_2)

                s_value = self.format_tick_labels([Ox_lim[0]], precision_min)

                if not hasattr(self, "_single_text"):
                    self._single_text = self.ax.text(
                        x_fig, y_fig, s_value[0], transform=self.fig.transFigure, # '0'
                        va='bottom', ha='right', fontsize=font_size, fontname=font_family
                    )

                else:
                    # Сдвигаем ноль, если он уже был установлен
                    self._single_text.set_position((x_fig, y_fig))
                    self._single_text.set_transform(self.fig.transFigure)
        
        # Еще одна проверка, связанная с автоматическим проставлением границ осей
        else:
            if hasattr(self, "_single_text"):
                self._single_text.remove()   # удаляем текстовый объект с графика
                del self._single_text   
       

        # Сетка на поле графике
        if grid_t_f:
            self.ax.grid(color='grey', linestyle='--', linewidth = 0.5)
                
        return()



    # @staticmethod
    def draw_axis_arrows(self, ax, arrow_t_f: bool = True, headlength: float = 10, headwidth: float = 5):
        """Отрисовка стрелочек на осях
        
            Args:
                ax(): объект - кооридантная рамка.
                arrow_t_f (bool, optional): Флаг активации отрисовки стрелочек на осях. Defaults to True.
                headlength (float, optional): Длина стрелочки. Defaults to 10.
                headwidth (float, optional): Ширина стрелочки. Defaults to 5.
        """

        if not arrow_t_f:
            return()
        
        fig = ax.figure
    
        # Получение координат точек бокса координатных осей и его длины, ширины
        ax_bbox = ax.get_position()  # Получение координат точек бокса координатных осей и его длины, ширины      
        fig_w, fig_h = fig.get_size_inches() # Получение размеров окна
    
        # Смещение стрелки по x (горизонтальная ось)
        self.dx_fig = headlength / fig.dpi / fig_w / ax_bbox.width
        # Смещение стрелки по y (вертикальная ось)
        self.dy_fig = headlength / fig.dpi / fig_h / ax_bbox.height
    
        # Горизонтальная стрелка
        self.arrow_x = self.ax.annotate('', xy=(1 + self.dx_fig, 0), xytext=(0, 0), 
                                  arrowprops=dict(facecolor='black', 
                                                  shrink=0.0, width=0.01, headlength=headlength, headwidth=headwidth), 
                                  xycoords='axes fraction', textcoords='axes fraction')

        # Вертикальная стрелка
        self.arrow_y = self.ax.annotate('', xy=(0, 1 + self.dy_fig), xytext=(0, 0), 
                    arrowprops=dict(facecolor='black', 
                                    shrink=0.0, width=0.01, headlength=headlength, headwidth=headwidth), 
                    xycoords='axes fraction', textcoords='axes fraction')



    def shifting_axes(self,
                      Ox_shifting:bool=False, Oy_shifting:bool=False, 
                      Ox_value:float=0.0, Oy_value:float=0.0):
        """Функция для смещения осей по данным

            Args:
                Ox_shifting (bool, optional): Включение смещения горизонтальной оси. Defaults to False.
                Oy_shifting (bool, optional): Включение смещения вертикальной оси. Defaults to False.
                Ox_value (float, optional): Положение для горизонтальной оси по вертикали. Defaults to 0.0.
                Oy_value (float, optional): Положение для вертикальной оси по горизонтали. Defaults to 0.0.
        """
        
        self.shifting_switch = False # Выключиние повторной отрисовки осей в conf_axes()
        self.rt_t_f = False # Выключиние повторной отрисовки рамки в conf_axes()

        if Ox_shifting:
            self.ax.spines['bottom'].set_position(('data', Ox_value))

            arrow_head_x, arrow_head_y = self.data_to_axes(self.ax.get_xlim()[1], Ox_value) # Перевод координат в систему данных
            arrow_line_x, arrow_line_y = self.data_to_axes(self.ax.get_xlim()[0], Ox_value)

            self.arrow_x.xy = (arrow_head_x + self.dx_fig, arrow_head_y) # Наконечник стрелочки
            self.arrow_x.set_position((arrow_line_x, arrow_line_y)) # Начало стерлочки
        
        if Oy_shifting:
            self.ax.spines['left'].set_position(('data', Oy_value))

            arrow_head_x, arrow_head_y = self.data_to_axes(Oy_value, self.ax.get_ylim()[1]) # Перевод координат в систему данных
            arrow_line_x, arrow_line_y = self.data_to_axes(Oy_value, self.ax.get_ylim()[0])

            self.arrow_y.xy = (arrow_head_x, arrow_head_y + self.dy_fig) # Наконечник стрелочки
            self.arrow_y.set_position((arrow_line_x, arrow_line_y)) # Начало стерлочки


        self.conf_ticks() # Обновление делений на графике
        self.conf_axes() # Обновление наименований и прочего
        self.fig.canvas.draw() # Обновление отрисовки всего графика





    def _draw_partial_italic_text(self, x_y:int, x_fig:float, y_fig:float, text:str, va:str, ha:str, font_family, font_size):
        """
        Курсив для символов XxYyZz в начале подписи оси.

            Args:
                x_y (int): Обозначение оси 0 - x, 1 - y.
                x_fig (float): Базовое (вычисленное) положение вертикальной подписи по горизонтали.
                y_fig (float): Базовое (вычисленное) положение горизонтальной подписи по вертикали.
                text (str): Наименование оси.
                va (str): Якорь для подписи.
                ha (str): Якорь для подписи.
                font_family (str, optional): Тип шрифта. Defaults to 'Times New Roman'.
                font_size (int, optional): Размер шрифта. Defaults to init: 22.
        """

        # Проверяем условие для курсивной первой буквы
        temp_chars = "XxYyZz"
        first_char = ""

        # Обработка случая "X, м" 
        if self.XxYyZz_i_t_f and len(text) > 1 and text[0] in temp_chars and text[1] == ',':
                first_char = text[0]
                rest_text = text[1:]
        # Обработка случая "X" 
        elif self.XxYyZz_i_t_f and len(text) == 1 and text[0] in temp_chars:
            first_char = text[0]
            rest_text = ""
        # Для всех остальных символов (не XxYyZz) курсив не применяется
        else:
            first_char = ""
            rest_text = text

        # Трансформация в координаты фигуры для более удобного позиционирования текста
        trans = self.fig.transFigure

        # Рисуем первую букву курсивом (при выполнении соответствуюших условий)
        if first_char:

            # Изерение размеров одного символа в поле графика для определения смещения текста (определяем бокс символа, и после удаляем его)
            temp = self.ax.text(0, 0, first_char, fontname=font_family, fontsize=font_size, fontstyle="italic")
            renderer = self.fig.canvas.get_renderer()
            bbox = temp.get_window_extent(renderer=renderer)
            width_fig_char = bbox.width / self.fig.get_size_inches()[0] / self.fig.dpi
            # Удаляем временный объект
            temp.remove()

            # Аналогично измеряем размеры оставшегося текста, для определения смещения
            temp = self.ax.text(0, 0, rest_text, fontname=font_family, fontsize=font_size) #, fontstyle="italic"
            renderer = self.fig.canvas.get_renderer()
            bbox = temp.get_window_extent(renderer=renderer)
            width_fig_rest_text = bbox.width / self.fig.get_size_inches()[0] / self.fig.dpi
            # Удаляем временный объект
            temp.remove()

            comma_coef = 0.1

            # Отрисовка наименований осей (для каждой оси свой алгоритм x_y=0 - ось x, x_y=1 - ось y)
            if not x_y:
                # Отрисовка наименования оси для оси x
                # Вычисление положения курсивного символа: по х смещаем на половину длины всего текста и одного символа (с учетом отступа для запятой)
                t1 = self.ax.text(x_fig - (comma_coef * width_fig_char + width_fig_rest_text) / 2,
                                  y_fig, 
                                  first_char, 
                                  transform=trans,
                                  fontname=font_family, fontsize=font_size,
                                  fontstyle="italic", va=va, ha=ha)

                # Рисуем остальной текст рядом
                t2 = self.ax.text(x_fig + ((1 + comma_coef) * width_fig_char) / 2,
                                  y_fig, 
                                  rest_text, 
                                  transform=trans,
                                  fontname=font_family, fontsize=font_size,
                                  fontstyle="normal", va=va, ha=ha)
                return t1, t2
            else:
                # Отрисовка наименования оси для оси y
                # Отрисовываем вначале вторую часть текста
                t2 = self.ax.text(x_fig, 
                                  y_fig, 
                                  rest_text, 
                                  transform=trans,
                                  fontname=font_family, fontsize=font_size,
                                  fontstyle="normal", va=va, ha=ha
                                  )

                # Смещаем курсивный текс на ширину второй части и на ширину символа (с учетом отступа для запятой)
                t1 = self.ax.text(x_fig - width_fig_rest_text - width_fig_char * comma_coef, 
                                  y_fig, 
                                  first_char, 
                                  transform=trans,
                                  fontname=font_family, fontsize=font_size,
                                  fontstyle="italic", va=va, ha=ha)
                return t1, t2
        else:
            # Весь текст обычным шрифтом
            t = self.ax.text(x_fig, 
                             y_fig, 
                             rest_text, 
                             transform=trans,
                             fontname=font_family, fontsize=font_size,
                             fontstyle="normal", va=va, ha=ha)
            # Запятая стоит, чтоб возвращался кортеж (унификация)
            return t,


    def conf_axes(self, x_label:Optional[str]=None, y_label:Optional[str]=None,
                  type_axes_name:bool=False, 
                  manual_axes_t_f:bool=False,
                  x_label_x:float=1.0, x_label_y:float=-0.018, 
                  y_label_x:float=-0.015, y_label_y:float=1.0,
                  arrow_t_f:bool=True,
                  rt_t_f:Optional[bool]=None,
                  font_size:Optional[int]=None, font_family:Optional[str]=None):

        """Функция подписи наименований осей, стрелочек и отрисовки границ

            Args:
                x_label (Optional[str], optional): Наименование горизонтальной оси. Defaults to None -> init: 'X'.
                y_label (Optional[str], optional): Наименование вертикальной оси. Defaults to None -> init: 'Y'.
                type_axes_name (bool, optional): Флаг активации стандартной python подписи осей. Defaults to False.
                manual_axes_t_f (bool, optional): Флаг активации ручной установки положения наименования осей. Defaults to False.
                x_label_x (Optional[float], optional): Положение подписи горизонтальной оси по горизонтали. Defaults to None -> init: 1.03.
                x_label_y (Optional[float], optional): Положение подписи горизонтальной оси по вертикали. Defaults to None -> init: -0.018.
                y_label_x (Optional[float], optional): Положение подписи вертикальной оси по горизонтали. Defaults to None -> init: -0.015.
                y_label_y (Optional[float], optional): Положение подписи вертикальной оси по вертикали. Defaults to None -> init: 0.98.
                arrow_t_f (bool, optional): Включение стрелочек на осях. Defaults to True.
                rt_t_f (Optional[bool], optional): Включение верхней и правой границ графика. Defaults to None -> init: True.
                font_size (int, optional): Размер шрифта. Defaults to None -> init: 16.
                font_family (str, optional): Тип шрифта. Defaults to None -> init: 'Times New Roman'.
        """

        # Установка значений из init
        if x_label is None: x_label = self.x_label
        if y_label is None: y_label = self.y_label
        if rt_t_f is None: rt_t_f = self.rt_t_f
        if font_size is None: font_size = self.font_size
        if font_family is None: font_family = self.font_family

        # Стандартная питоновская отрисовка осей
        if type_axes_name:
            self.ax.set_xlabel(x_label, fontsize=font_size, fontname=font_family) 
            self.ax.set_ylabel(y_label, fontsize=font_size, fontname=font_family)


        # Отрисовка наименований осей вместо последних делений
        else:
            if manual_axes_t_f:
                # Ручной метод выставления положения наименований осей координат (координаты осей (transAxes) 0-1)
                self.ax.text(x_label_x, x_label_y, x_label, transform=self.ax.transAxes, 
                             va='bottom', ha='center', fontsize=font_size, fontname=font_family)
                self.ax.text(y_label_x, y_label_y, y_label, transform=self.ax.transAxes, 
                             va='center', ha='right', fontsize=font_size, fontname=font_family)
                
            else:
                # Автоматический метод выставления наименований осей координат
                # Вычисляем параметры бокса системы координат в окне (положение двух углвых точек, ширину, высоту)
                ax_bbox = self.ax.get_position()  

                # Получаем вертикальное смещение горизонтальных меток от линии оси в пикселях
                tick = self.ax.get_xticklabels()[0] # Берем бокс первой метки
                bbox = tick.get_window_extent(renderer=self.fig.canvas.get_renderer())
                # Переводим пиксели в координаты Axes
                x_lab_y_rel = (bbox.y0 - self.ax.bbox.y0) / self.ax.bbox.height

                # Получаем горизонтальное смещение вертикальных меток от линии оси в пикселях
                tick = self.ax.get_yticklabels()[0] # Берем бокс первой метки
                bbox = tick.get_window_extent(renderer=self.fig.canvas.get_renderer())
                # Переводим пиксели в координаты Axes
                y_lab_x_rel = (bbox.x1 - self.ax.bbox.x0) / self.ax.bbox.width

                # Переводим координаты из координат осей в координаты всего окна
                x_lab_x_fig = ax_bbox.x0 + 1.0 * ax_bbox.width
                x_lab_y_fig = ax_bbox.y0 + x_lab_y_rel * ax_bbox.height
                y_lab_x_fig = ax_bbox.x0 + y_lab_x_rel * ax_bbox.width
                y_lab_y_fig = ax_bbox.y0 + 1.0 * ax_bbox.height

                # Для каждого наименования (x, y) выполняется проверка, были ли они уже созданы, т.к. некоторые добавления на графике
                # могут изменять размеры бокса осей, наименования могут сместиться - необходима корректрировка
                
                if not hasattr(self, "_x_label_text"):
                    self._x_label_text = self._draw_partial_italic_text(0,
                                                                        x_lab_x_fig, x_lab_y_fig, x_label,
                                                                        va='bottom', ha='center',
                                                                        font_family=font_family, font_size=font_size)              
                else:
                    # удаление некорректно отрисованных наименований с проверкой, на кортеж объектов
                    if isinstance(self._x_label_text, tuple):
                        for t in self._x_label_text:
                            t.remove()
                    else:
                        self._x_label_text.remove()

                    self._x_label_text = self._draw_partial_italic_text(0,
                                                                        x_lab_x_fig, x_lab_y_fig, x_label,
                                                                        va='bottom', ha='center',
                                                                        font_family=font_family, font_size=font_size)




                if not hasattr(self, "_y_label_text"):
                    self._y_label_text = self._draw_partial_italic_text(1,
                                                                        y_lab_x_fig, y_lab_y_fig, y_label,
                                                                        va='center', ha='right',
                                                                        font_family=font_family, font_size=font_size)
                else:
                    if isinstance(self._y_label_text, tuple):
                        for t in self._y_label_text:
                            t.remove()
                    else:
                        self._y_label_text.remove()

                    self._y_label_text = self._draw_partial_italic_text(1,
                                                                        y_lab_x_fig, y_lab_y_fig, y_label,
                                                                        va='center', ha='right',
                                                                        font_family=font_family, font_size=font_size)


        # Отрисовка стрелочек
        if self.shifting_switch:
            self.draw_axis_arrows(self.ax, arrow_t_f) #GraphConfigurator

        # Отрисовка правой и верхней границ графика
        self.ax.spines[['top','right']].set_visible(rt_t_f)
        self.ax.spines[['top','right']].set_color('gray')
        self.ax.spines[['top','right']].set_linestyle('--')



    def conf_title(self, title_lab:str='Title', title_t_f:bool=False,
                   font_size:Optional[int]=None, font_family:Optional[str]=None):
        
        """Функция наименования графика

            Args:
                title_lab (str, optional): Наименование графика. Defaults to 'Title'.
                title_t_f (bool, optional): Включение наименования графика. Defaults to False.
                font_size (int, optional): Размер шрифта. Defaults to None -> init: 16.
                font_family (str, optional): Тип шрифта. Defaults to None -> init: 'Times New Roman'.
        """

        if font_size is None: font_size = self.font_size
        if font_family is None: font_family = self.font_family

    # Наименование графика
        if title_t_f:
            self.ax.set_title(title_lab, fontsize = font_size, fontname = font_family)
        return()



    def conf_graph(self, data_x:list, data_y:list, *, mark_only_t_f:bool=False, lab:Optional[str]=None,
                 col:Optional[int]=None, line_type:Optional[int]=None, line_width:float=1.5,
                 mark_t_f:bool=False, mark_every:int=1, mark_col:Optional[str]=None, edge_col:Optional[str]=None, 
                 alpha:float=1.0, mark_type:Optional[int]=None, mark_size:int=20):

        """Функция построения графика

            Args:
                data_x (list): Массив данных по горизонтальной оси.
                data_y (list): Массив данных по вертикальной оси.
                mark_only_t_f (bool, optional): Флаг построения графика только с маркерами. Defaults to False.
                lab (Optional[str], optional): Наименования графика для легенды. Defaults to '1'.
                col (Optional[int], optional): Цвет линии графика. Defaults to 'black'.
                line_type (Optional[int], optional): Тип линии графика. Defaults to 0.
                line_width (float, optional): Толщина линии графика. Defaults to 1.0.
                mark_t_f (bool, optional): Включение маркеров на линии графика. Defaults to False.
                mark_every (int, optional): Частота постановки маркеров. Defaults to 1.
                mark_col (Optional[str], optional): Цвет маркеров. Defaults to None -> col.
                edge_col (Optional[str], optional): Цвет границы графика. Defaults to 'white'.
                alpha (float, optional): Прозрачность графика. Defaults to 1.0.
                mark_type (Optional[int], optional): Тип маркера. Defaults to 0.
                mark_size (int, optional): Размер маркера. Defaults to 20.
        """

        # self.data_x = data_x
        # self.data_y = data_y

        # Попробуем фильтровать None
        self.data_x = [x for x in data_x if x is not None]
        self.data_y = [y for y in data_y if y is not None]

        # Добавление поступающих данных в общий массив для вычисления границ графика
        self._all_data_x.append(np.array(data_x))
        self._all_data_y.append(np.array(data_y))

        # Для автоматического выставления аннотаций для каждого графика: 1, 2, 3...
        if lab is None: lab = str(self.count + 1)

        # Автоматический выбор цвета из списка
        if col is None: 
            if self.count == len(self.mc_color_list):
                self.count = 0
            col = self.mc_color_list[self.count]
        else:
            if type(col) is str:
                col = col
            else:
                col = self.mc_color_list[col]
        
        if edge_col is None: 
            edge_col = col
        else:
            if type(edge_col) is str:
                edge_col = edge_col
            else:
                edge_col = self.mc_color_list[edge_col]
                

        if mark_col is None: 
            mark_col = col
        else:
            if type(mark_col) is str:
                mark_col = mark_col
            else:
                mark_col = self.mc_color_list[mark_col]


        # Автоматический выбор типа метки из списка (список ограничен, поэтому выбор обнуляется)
        if mark_type is None:
            if self.mark_count == len(self.mc_mark_list):
                self.mark_count = 0
            mark_type_str = self.mc_mark_list[self.mark_count]
        else:
            mark_type_str = self.mc_mark_list[mark_type]

        if self.mark_count in [8, 9]:
            edge_col = None
        
        # Автоматический выбор типа линии из списка (список ограничен, поэтому выбор обнуляется)
        if line_type is None:
            if self.line_count == len(GraphConfigurator.line_type_list) - 1:
                self.line_count = 0
            line_type_str = GraphConfigurator.line_type_list[self.line_count]
        else:
            line_type_str = GraphConfigurator.line_type_list[line_type]
       

        # Выбор типа отрисовки - только метки или линии
        if not mark_only_t_f:
            # Выбор типа отрисовки линии с метками или без
            if mark_t_f:
                line = self.ax.plot(data_x, data_y, 
                                    ls=line_type_str, lw=line_width, 
                                    color=col, alpha=alpha)
                self.ax.scatter(data_x[::mark_every], data_y[::mark_every], 
                                marker=mark_type_str, s=mark_size, c=mark_col, 
                                edgecolors=edge_col, alpha=alpha)
                # Фейковый график для правильного отображения легенды - с типом линии и с типом метки
                self.ax.plot([], [], 
                             ls=line_type_str, lw=line_width, color=col, 
                             marker=mark_type_str, markersize=30, markerfacecolor=mark_col, 
                             markeredgecolor=edge_col, label=lab, alpha=alpha)
                self.mark_count += 1 # счетчик меток
            else:
                line = self.ax.plot(data_x, data_y, ls=line_type_str, 
                                    linewidth=line_width, color=col, 
                                    label=lab, alpha=alpha)               
            self.line_count += 1 # счетчик линий
        else:
            line = self.ax.scatter(data_x[::mark_every], data_y[::mark_every], 
                                   marker=mark_type_str, 
                                   s=mark_size, c=mark_col, 
                                   edgecolors=edge_col, alpha=alpha)
            # Фейковый график для правильного отображения легенды
            self.ax.plot([], [], linestyle='', 
                         color = mark_col, 
                         marker=mark_type_str, 
                         markersize=30, markerfacecolor=mark_col, 
                         markeredgecolor=edge_col, 
                         label=lab, alpha=alpha)
            self.mark_count += 1 # счетчик меток


        # Инкремент счётчика графиков
        self.count += 1

        self.lines.append(line) # добавление объекта линии в общий массив для автоматического раставления аннотаций
        # Пока не нужно
        # line_obj = line[0] if isinstance(line, list) else line # взять первый элемент, если он является объектом линии (plot) или сам line, если это уже объект (scatter)
        # self.lines_obj.append(line_obj)
        self.update_limits(auto_range_t_f=self.auto_range) # Вызов функции автоматического выставления границ графика
        self.conf_ticks() # Обновление делений на графике
        if self.annot_t_f: # Автоматически включаем аннотации при выводе conf_graph, если включен флаг
            self.conf_annot()
        self.fig.canvas.draw() # Обновление отрисовки всего графика
        
        
        return(line)

    

    
    @staticmethod
    def nice_limits(data_min:float, data_max:float, n_ticks:int=5):
        """Функция автоматического выбора делений графика по вычисленным границам

            Args:
                data_min (float): Минимальное значение на графике.
                data_max (float): Максимальное значение на графике.
                n_ticks (int, optional): Приблизительное число меток. Defaults to 5.
        """

        # Вычисление ширины диапазона значений (с учетом возможного равенства 0)
        data_range = data_max - data_min
        if data_range == 0:
            #############Правка:
            if data_min != 0:
                data_min = data_min - abs(data_min) * 0.05
                data_max = data_max + abs(data_max) * 0.05
            else:
                data_min = data_min - 0.05
                data_max = data_max + 0.05
            data_range = data_max - data_min


        raw_step = data_range / n_ticks # Вычисление приблизительного шага для делений
        order = 10 ** math.floor(math.log10(raw_step)) # Вычисление порядка шага с округлением в меньшую сторону
        step_candidates = [1, 2, 2.5, 5, 10] # Список наиболее удачных шагов для делений
        step = min(step_candidates, key=lambda s: abs(raw_step - s * order)) # Подбор наиболее подходящего шага из списка
        step *= order # Приведение порядка выбранного шага к порядку приблизительного

        decimals = max (0, -int(math.floor(math.log10(step))) + 2) # Вычисление уровня округления на базе значения шага (для удаления машинных нулей титпа 0.15000000002)
        step = round(step, decimals) # Округление шага

        new_min = round(math.floor(data_min / step) * step, decimals) # Округление в меньшую сторону миниума диапазона
        new_max = round(math.ceil(data_max / step) * step, decimals) # Округление в большую сторону максимума диапазона

        return new_min, new_max, step





    def update_limits(self, auto_range_t_f:bool=True, use_all_data:bool=True,
                      x_ticks_num:Optional[float]=None, 
                      y_ticks_num:Optional[float]=None):
        """Автоматически обновляем пределы графика по всем переданным массивам
            
            Args:
                auto_range_t_f (bool, optional): Флаг активации автоматического вычисления границ графика. Defaults to True.
                use_all_data (bool, optional): Флаг активации использования всех данных для вычисления границ графика. Defaults to True.
                x_ticks_num (float): Приблизительное число меток по оси x. Defaults to 5.
                y_ticks_num (float): Приблизительное число меток. Defaults to 5.
        """
        if not auto_range_t_f:
            return() # Выход из функции, если автоматическое вычисление границ отключено

        if not self._all_data_x or not self._all_data_y:
            return()  # Выход из функции, если данных нет
        

        if use_all_data:
                    # Объединяем все данные, если включен соответствующий флаг
            all_x = np.concatenate(self._all_data_x)
            all_y = np.concatenate(self._all_data_y)
        else:
            all_x = self._all_data_x[-1]
            all_y = self._all_data_y[-1]
        
        # Получение ориентировочного количесвта меток по осям из init
        if x_ticks_num is None: x_ticks_num = self.x_ticks_num
        if y_ticks_num is None: y_ticks_num = self.y_ticks_num


        #Вычисление минимальных и максимальных значений из массивов
        x_min, x_max = all_x.min(), all_x.max()
        y_min, y_max = all_y.min(), all_y.max()


        # Обработка логарифмических шкал для осей x и y c проверкой на отрицательные и нулевые значения
        if self.x_scale == 'log':
            x_min = 10 ** (math.ceil(math.log10(min([x for x in all_x if x > 0]))) - 1)
            x_max = 10 ** (math.floor(math.log10(x_max)) + 1)
            x_step = 10 # не используется, просто значение отличное от None
        else:
            x_min, x_max, x_step = GraphConfigurator.nice_limits(x_min, x_max, x_ticks_num)

        if self.y_scale == 'log':
            y_min = 10 ** (math.ceil(math.log10(min([y for y in all_y if y > 0]))) - 1)
            y_max = 10 ** (math.floor(math.log10(y_max)) + 1)
            y_step = 10 # не используется, просто значение отличное от None
        else:
            y_min, y_max, y_step = GraphConfigurator.nice_limits(y_min, y_max, y_ticks_num)

        self.Ox_lim = (x_min, x_max)
        self.Ox_step = x_step
        self.Oy_lim = (y_min, y_max)
        self.Oy_step = y_step
        
        self.conf_ticks() # Обновление делений на графике
        self.fig.canvas.draw() # Обновление отрисовки всего графика
        return()


    def axes_to_data(self, u:float=0, v:float=0):
        """Функция перевода координат из координат осей (0-1) в координаты данных (Ox_lim)

            Args:
                u (float, optional): Горизонтальная координата в пределах 0...1. Defaults to 0.
                v (float, optional): Вертикальная координата в пределах 0...1. Defaults to 0.
        """
        
        # Из координат осей -> в display (пиксели)
        disp_coords = self.ax.transAxes.transform((u, v))
        # Из display (пиксели) ->  в data
        x, y = self.ax.transData.inverted().transform(disp_coords)
        return(x, y)


    def data_to_axes(self, x:float=0, y:float=0):
        """Функция перевода координат из координат данных (Ox_lim) в координаты осей (0-1)

            Args:
                x (float, optional): Горизонтальная координата в пределах Ox_lim. Defaults to 0.
                y (float, optional): Вертикальная координата в пределах Oy_lim. Defaults to 0.
        """

        # Из data → в display (пиксели)
        disp_coords = self.ax.transData.transform((x, y))
        # Из display → в координаты осей (0–1)
        u, v = self.ax.transAxes.inverted().transform(disp_coords)
        return(u, v)




    def legend_set(self, legend_sep_fig_t_f=True, legend_save:Optional[str]=None, leg_loc='lower center', 
                   box_anchor_a=0.5, box_anchor_b=-0.3,
                   handle_length:float = 2.5, marker_scale:float = 0.4, 
                   ncol:int=4,
                   font_size:Optional[int]=None, font_family:Optional[str]=None):

        """Настройка легенды графика

            Args:
                legend_sep_fig_t_f (bool, optional): Флаг отрисовки легенды в отдельном окне. Defaults to True.
                legend_save (Optional[str], optional): Флаг сохранения легенды отдельным файлом. Defaults to None.
                leg_loc (str, optional): Положение относительно границы графика. Defaults to 'lower center'.
                box_anchor_a (int, optional): Положение по горизонтали. Defaults to 0.5.
                box_anchor_b (int, optional): Положение по вертикали. Defaults to -0.2.
                handle_length (float, optional): Размер легенды?. Defaults to 2.5.
                ncol (int, optional): Количество колонок в легенде (если None - автоматическое). Defaults to 4.                
                marker_scale (float, optional): Масштаб маркеров. Defaults to 0.4.        
                font_size (int, optional): Размер шрифта. Defaults to None -> init: 16.
                font_family (str, optional): Тип шрифта. Defaults to None -> init: 'Times New Roman'.
        """    

        if font_size is None: font_size = self.font_size
        if font_family is None: font_family = self.font_family

        font_prop = font_manager.FontProperties(family = font_family, size = font_size)

        # Отрисовка легенды в отельном окне
        if legend_sep_fig_t_f:

            handles, labels = self.ax.get_legend_handles_labels() # Вытаскиваем параметры легенды для отрисованного графика
            # Создаём отдельную фигуру для легенды
            fig_legend = plt.figure()
            ax = fig_legend.add_subplot(111)
            ax.axis('off')  # Отключаем оси
            # Отрисовываем легенду без рамки и с прозрачным фоном
            legend = ax.legend(handles, labels, loc='center', frameon=False,
                                       prop=font_prop, ncol=ncol,
                                       handlelength=handle_length, markerscale=marker_scale)  # Без рамки
            
            # В подписи графиков для легенды добавляем "-  " в начало текста
            for text in legend.get_texts():
                text.set_text("–  " + text.get_text())

            # Подгоняем размер фигуры под легенду
            fig_legend.canvas.draw()
            renderer = fig_legend.canvas.get_renderer()
            bbox = legend.get_window_extent(renderer=renderer).transformed(fig_legend.dpi_scale_trans.inverted())
            fig_legend.set_size_inches(bbox.width, bbox.height)

            # Сохранение легенды отдельным файлом
            if legend_save is not None:
                fig_legend.savefig(legend_save, dpi=300, bbox_inches='tight', transparent=True)

        # Отрисовка легенды в окне графика
        else:
            self.ax.legend(loc = leg_loc, bbox_to_anchor=(box_anchor_a, box_anchor_b), handleheight=0.0,
                           handlelength = handle_length, markerscale = marker_scale, prop=font_prop, ncol=ncol)
            legend = self.ax.get_legend()

            for text in legend.get_texts():
                text.set_text("–  " + text.get_text())
            
            # Исправляем размер окна с учетом легенды
            self.fig.tight_layout()
            # fig_legend = None  # Забыл уже зачем, удалить, если все будет нормально работать!!!!

        self.conf_ticks() # Обновление делений на графике
        self.conf_axes() # Обновление отрисовки наименований осей
        self.fig.canvas.draw() # Обновление отрисовки всего графика
        
        return()



    def conf_annot(self, lab:Optional[str]=None,
                   manual:bool=False,
                   annot_only_ratio_t_f:bool=False,
                   fraction_of_points:Optional[float]=None,
                   an_ratio:Optional[float]=None, 
                   an_x:Optional[float]=None, 
                   an_y:Optional[float]=None,
                   an_arrow_col:str='black', an_edge_arrow_col:str='black',
                   space:float=0.00001, head_len:float=15, head_wid:float=0.1, line_wid:float=0.1,
                   font_size:Optional[int]=None, font_family:Optional[str]=None):
        
        """Аннотация к линии графика

            Args:
                lab (Optional[str], optional): Наименования графика для легенды. Defaults to None.
                manual (bool, optional): Ручная установка меток. Defaults to False.
                annot_only_ratio_t_f (bool, optional): Изменение только указателя. Defaults to False.
                fraction_of_points (Optional[float], optional): Доля точек, по которым строится перпендикуляр для аннотации. Defaults to 0.05.
                an_ratio (Optional[float], optional): Коэффицент для установки указателя (по длине графика). Defaults to None.
                an_x (Optional[float], optional): Положение текста по горизонтальной оси. Defaults to None.
                an_y (Optional[float], optional): Положение текста по вертикальной оси. Defaults to None.
                an_arrow_col (str, optional): Цвет стрелки. Defaults to 'black'.
                an_edge_arrow_col (str, optional): Цвет границы стрелки. Defaults to 'black'.
                space (float, optional): ?. Defaults to 0.00001.
                head_len (float, optional): Длина стрелки. Defaults to 15.
                head_wid (float, optional): Ширина стрелки. Defaults to 0.1.
                line_wid (float, optional): Ширина линии. Defaults to 0.1.
                font_size (int, optional): Размер шрифта. Defaults to None -> init: 16 + 4.
                font_family (str, optional): Тип шрифта. Defaults to None -> init: 'Times New Roman'.
        """     

        if font_size is None: font_size = self.font_size + 2
        if font_family is None: font_family = self.font_family    
        if fraction_of_points is None: fraction_of_points = self.fraction_of_points

        found = None
        # Проверка по ключу, была ли уже проставлена аннотация (количество аннотаций соответствует количеству линий)
        for item in self.annot_for_sliders:
            if item["key"] == self.count:
                found = item
                break

        # Автоматическое выставление аннотации по номеру линии
        if found is None:
            
            # При отсутствии наименования аннотации, вставляется номер линии
            if lab is None: lab = str(self.count) 

            # Изменение an_ratio, чтоб аннотации не накладывались друг на друга
            if an_ratio is None:
                if self.an_ratio <= 0.9:
                    an_ratio = self.an_ratio
                else:
                    self.an_ratio = 0.1
                    an_ratio = self.an_ratio

                self.an_ratio += 0.1

            # Получение координат точки для указателя из коэффициента длины линии
            # i = math.ceil(an_ratio * len(self.data_x)) - 1
            # pointer_x = self.data_x[i]
            # pointer_y = self.data_y[i]
            pointer_x, pointer_y, an_x_temp, an_y_temp = self.xy_annot(an_ratio=an_ratio, fraction_of_points=fraction_of_points)


            range_coef = 0.08 # Коэффициент для выставления координат анотации (смещение от указателя)

            if manual:
                # Было сделано для перевода координат данных в координаты осей, но сейчас работает напрямую с координатами данных
                # an_x, an_y = self.axes_to_data(an_x, an_y)
                pass
            else:
                # Перевод из координат данных в координаты осей для удобства
                # mid_x, mid_y = self.data_to_axes((abs(self.Ox_lim[1] - self.Ox_lim[0]) / 2),
                #                                  (abs(self.Oy_lim[1] - self.Oy_lim[0]) / 2))
                # pointer_x, pointer_y = self.data_to_axes(pointer_x,
                #                                          pointer_y)

                # Смещение от указателя на заданный коэффициент в зависимости от положения указателя
                if an_x is None:
                    # if pointer_x <= mid_x:
                    #     an_x = pointer_x + range_coef
                    # else:
                    #     an_x = pointer_x - range_coef
                    # an_x = self.axes_to_data(an_x, 0)[0]
                    an_x = an_x_temp

                if an_y is None:
                    # if pointer_y <= mid_y:
                    #     an_y = pointer_y + range_coef
                    # else:
                    #     an_y = pointer_y - range_coef
                    # an_y = self.axes_to_data(0, an_y)[1]
                    an_y = an_y_temp

                # Обратный перевод значений из координатной системы осей в систему данных
                # an_x, an_y = self.axes_to_data(an_x, an_y)
                # pointer_x, pointer_y = self.axes_to_data(pointer_x, pointer_y)


            # Если ключа нет — создаём новую аннотацию
            annot=self.ax.annotate(lab,
                                   xy=(pointer_x, pointer_y),
                                   xytext=(an_x, an_y),
                                   transform=self.fig.transFigure,
                                   arrowprops=dict(facecolor=an_arrow_col, edgecolor=an_edge_arrow_col, 
                                                   shrink=space, headlength=head_len, headwidth=head_wid, width=line_wid),
                                                   color='black', fontsize=font_size, fontname=font_family) 
            
            self.annotations.append(annot) # Пока не нужная штука, сделана для более сложной расстановки аннотаций

            self.annot_for_sliders.append({
                                    "key": self.count,
                                    "annotation_obj": annot,
                                    "lab": lab,
                                    "data_x": self.data_x,
                                    "data_y": self.data_y,
                                    "an_ratio": an_ratio,
                                    "an_x": an_x,
                                    "an_y": an_y
                                    })
        else:

            # Если ключ есть — извлекаем данные и обновляем аннотацию
            annot = found["annotation_obj"]
            # Обновляем координаты аннотации и наименование
            if an_x is None: an_x = found["an_x"]
            if an_y is None: an_y = found["an_y"]
            if an_ratio is None: an_ratio = found["an_ratio"]
            pointer_x, pointer_y, an_x_temp, an_y_temp = self.xy_annot(an_ratio=an_ratio, fraction_of_points=fraction_of_points)

            if annot_only_ratio_t_f:

                found["an_x"] = an_x_temp
                an_x = found["an_x"]
                found["an_y"] = an_y_temp
                an_y = found["an_y"]

            # i = round(an_ratio * len(self.data_x))
            # if an_ratio == 1: i -= 1
            # pointer_x = self.data_x[i]
            # pointer_y = self.data_y[i]

            if lab:
                annot.set_text(lab)
                found["lab"] = lab

            annot.set_position((an_x, an_y))
            annot.xy = (pointer_x, pointer_y)

        return()


    def xy_annot(self, an_ratio, range_coef:float=0.20, fraction_of_points:Optional[float]=0.05):
        """Автоматическое выставление аннотаций перпендикулярно отрезку линии в области выбранной точки

        Args:
            an_ratio (Optional[float], optional): Коэффицент для установки указателя (по длине графика). Defaults to None.
            range_coef (float, optional): Коэффициент для смещения координат анотации. Defaults to 0.2.

        Returns:
            _type_: _description_
        """
        
        # bbox осей в пикселях (display coordinates)
        bbox = self.ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())

        # Ширина и высота области данных в дюймах
        width, height = bbox.width, bbox.height
        ratio_axes = height / width   # Соотношение сторон области осей

        len_data =  len(self.data_x)

        i = round(an_ratio * len_data)
        if an_ratio == 1: i -= 1
        x1, y1 = self.data_to_axes(x=self.data_x[i-1], y=self.data_y[i-1])
        x2, y2 = self.data_to_axes(x=self.data_x[i], y=self.data_y[i])
        

        if fraction_of_points is not None:
            if fraction_of_points > 0.4: fraction_of_points = 0.4
            eps = int(round(len_data * fraction_of_points))
            if eps < 2: eps = 2
            eps = eps + (eps % 2)
        
            if (i - eps / 2) >= 0 and (i + eps / 2) <= len_data - 1:
                low_i = int(i - eps / 2)
                high_i = int(i + eps / 2)
            elif (i - eps / 2) < 0:
                low_i = int(0)
                high_i = int(i + eps / 2 + abs(i - eps / 2))
            else:
                high_i = int(len_data - 1)
                low_i = int(i - eps / 2 - abs(high_i - i))
            
            x1, y1 = self.data_to_axes(x=self.data_x[low_i], y=self.data_y[low_i])
            x2, y2 = self.data_to_axes(x=self.data_x[i], y=self.data_y[i])
            x3, y3 = self.data_to_axes(x=self.data_x[high_i], y=self.data_y[high_i])
        
        else:
            x1, y1 = self.data_to_axes(x=self.data_x[i-1], y=self.data_y[i-1])
            x2, y2 = self.data_to_axes(x=self.data_x[i], y=self.data_y[i])
            x3, y3 = x2, y2

        # Расстояния между точками для вычисления нормали с учетом деформации окна отрисовки
        dx = (x3 - x1) / ratio_axes
        dy = (y3 - y1) * ratio_axes
        length = math.hypot(dx, dy) # гипотенуза

        # Вектор перпендикуляра (повёрнутого на 90°)
        nx = -dy / length
        ny = dx / length

        delta_x = nx * range_coef
        delta_y = ny * range_coef 
        
        if x2 < 0.5 and y2 < 0.5: #or x2 > 0.5 and y2 < 0.5
            an_x = x2 + delta_x
            an_y = y2 + delta_y
        else:
            an_x = x2 - delta_x
            an_y = y2 - delta_y
        
        # Ограничение на выставление аннотации за край области отрисовки
        if an_x >= 1: an_x = 0.95 
        if an_x <= 0: an_x = 0.05
        if an_y >= 1: an_y = 0.95
        if an_y <= 0: an_y = 0.05

        # Перевод координат в координаты данных
        an_x, an_y = self.axes_to_data(an_x, an_y)
        x2, y2 = self.axes_to_data(x2, y2)

        return x2, y2, an_x, an_y



    def add_annotation_with_sliders(self):
        """Отрисвка боксов с бегунками для перемещения аннотаций к графикам

        """

        import ipywidgets as widgets
        from ipywidgets import interact
        from IPython.display import display

        step_coef = 1e-3 # Шаг для основных бегунков
        boxes = [] # Массив боксов с бегунками

        # Цикл для создания боксов с бегунками для всех аннотаций
        for idx, ann_data in enumerate(self.annot_for_sliders):
            
            # Фейковый бегунок для подписи
            title_slider = widgets.FloatSlider(value=0, 
                                               min=0, 
                                               max=0, 
                                               step=0, description=ann_data["lab"],
                                               readout=False) # не показывать значение
            
            # Если шкала логарифмиечская то бегунок работает со степенями 10, а не с максимальными-минимальными значениями на графике
            if self.x_scale == "log":
                min_x = math.log10(self.Ox_lim[0])
                max_x = math.log10(self.Ox_lim[1])
                value_x = math.log10(ann_data["an_x"])
                slider_lab_x = self.x_label + " → 10^"
            else:
                min_x = self.Ox_lim[0]
                max_x = self.Ox_lim[1]
                value_x = ann_data["an_x"]
                slider_lab_x = self.x_label

            # Бегунок для выставления горизонтального положения аннотации
            x_slider = widgets.FloatSlider(value=value_x, 
                                           min=min_x, 
                                           max=max_x, 
                                           step=abs(max_x - min_x) * step_coef, 
                                           description=slider_lab_x)
            
            if self.y_scale == "log":
                min_y = math.log10(self.Oy_lim[0])
                max_y = math.log10(self.Oy_lim[1])
                value_y = math.log10(ann_data["an_y"])
                slider_lab_y = self.y_label + " → 10^"
            else:
                min_y = self.Oy_lim[0]
                max_y = self.Oy_lim[1]
                value_y = ann_data["an_y"]
                slider_lab_y = self.y_label
            
            # Бегунок для выставления вертикального положения аннотации
            y_slider = widgets.FloatSlider(value=value_y, 
                                           min=min_y, 
                                           max=max_y, 
                                           step=abs(max_y - min_y) * step_coef, 
                                           description=slider_lab_y)
            
            # Бегунок для выставления указателя до длине линии
            coeff_slider = widgets.FloatSlider(value=ann_data["an_ratio"], 
                                               min=0, 
                                               max=1, 
                                               step=0.001, 
                                               description='Ratio')

            # Параметры отрисовки бегунков - ширина, длина, расстояния между и т.д.
            width_px='250px'
            height_px='20px'
            margin_px='0 0 4px 0'
            title_slider.layout = widgets.Layout(width='1px', height=height_px, margin=margin_px)
            x_slider.layout = widgets.Layout(width=width_px, height=height_px, margin=margin_px)
            y_slider.layout = widgets.Layout(width=width_px, height=height_px, margin=margin_px)
            coeff_slider.layout = widgets.Layout(width=width_px, height=height_px, margin=margin_px)

            # Создание пары колонок для компактного размещения бегунков
            col1 = widgets.VBox([title_slider, coeff_slider])
            col2 = widgets.VBox([x_slider, y_slider])

            # Объединение двух боксов в 1
            box = widgets.HBox([col1, col2],
                               layout=widgets.Layout(padding='2px', margin='0px', border='2px solid black', width='520px', align_items='flex-start'))

            boxes.append(box) # Добавления бокса одной аннотации в массив



            # Создаёт интерактивный виджет, который вызывает функцию self._update_annotation при изменении значений слайдеров или других виджетов.
            widgets.interactive(self._update_annotation,
                                an_x=x_slider, an_y=y_slider, an_ratio=coeff_slider,
                                annotation_index=widgets.fixed(idx)) # фиксируем индекс, чтобы знать, для какой аннотации бегунки


            # Альтернативный кусок кода без боксов и widgets.
            # interact(self._update_annotation,
            #          an_x=x_slider, an_y=y_slider, an_ratio=coeff_slider,
            #          annotation_index=widgets.fixed(idx)) 

        # Объединение пар боксов в строчку для компактного отображения
        box_col1 = widgets.VBox(boxes[::2])  # все чётные
        box_col2 = widgets.VBox(boxes[1::2]) # все нечётные

        # Отрисовка боксов
        display(widgets.HBox([box_col1, box_col2], layout=widgets.Layout(padding='1px')))




    def _update_annotation(self, an_x:float, an_y:float, an_ratio:float, annotation_index):
        """Смещение созданных ранее аннотаций с помощью бегунков

        Args:
            an_x (float): положение текста аннотации по горизонтали.
            an_y (float): положение текста аннотации по вертикали.
            an_ratio (float): коэффициент для установки указателя.
            annotation_index (_type_): индекс аннотации.
        """
        ann_data = self.annot_for_sliders[annotation_index]
        annotation_obj = ann_data["annotation_obj"]
        data_x = ann_data["data_x"]
        data_y = ann_data["data_y"]

        # Вычисление положения указателя
        i = round(an_ratio * (len(data_x)))
        if an_ratio == 1: i -= 1
        pointer_x = data_x[i]
        pointer_y = data_y[i]

        # Переход от степеней к значениям для логарифмиечской шкалы
        if self.x_scale == "log":
            an_x = 10**an_x
        
        if self.y_scale == "log":
            an_y = 10**an_y

        # an_x, an_y = self.axes_to_data(an_x, an_y) # Скорее всего уже не нужно, т.к. сменил систему координат

        # Смещение текста аннотации и положения указателя
        annotation_obj.set_position((an_x, an_y))
        annotation_obj.xy = (pointer_x, pointer_y)

        self.ax.figure.canvas.draw_idle() # Интерактивное обновление отрисовки




    

    # Временная функция для тестов всяких
    def temp(self):
        return (print(f'{self.annotations}\n{self.lines}'))




    # Пока не работает
    def adjust_annotations(self, step=0.01, max_iter=10):
        """
        Автоматически сдвигаем аннотации, чтобы они не пересекались с линиями и друг с другом.

        step: шаг сдвига в координатах осей
        max_iter: максимальное число итераций на аннотацию
        """
        # import matplotlib.transforms as mtrans

        fig = self.ax.figure
        fig.canvas.draw()  # нужно, чтобы bbox были актуальны
        renderer = fig.canvas.get_renderer()

        # Получаем bbox всех аннотаций в пикселях
        ann_bboxes = [ann.get_window_extent(renderer) for ann in self.annotations]

        # Получаем линии
        lines_data = self.lines

        for i, ann in enumerate(self.annotations):
            iter_count = 0
            while True:
                iter_count += 1
                if iter_count > max_iter:
                    break  # ограничение, чтобы не зациклиться

                # обновляем bbox после возможного сдвига
                bbox = ann.get_window_extent(renderer)

                # проверяем пересечение с другими аннотациями
                collision = False
                for j, other_bbox in enumerate(ann_bboxes):
                    if i != j and bbox.overlaps(other_bbox):
                        collision = True
                        break

                # проверяем пересечение с линиями
                if not collision:
                    for line_data in lines_data:
                        # проверка расстояния до каждого сегмента линии
                        for k in range(len(line_data)-1):
                            x0, y0 = line_data[k]
                            x1, y1 = line_data[k+1]

                            # переводим bbox в data-координаты для простоты
                            x_min, y_min = self.ax.transData.inverted().transform((bbox.x0, bbox.y0))
                            x_max, y_max = self.ax.transData.inverted().transform((bbox.x1, bbox.y1))

                            # простой вариант: если bbox пересекает bounding box сегмента
                            seg_min_x, seg_max_x = min(x0, x1), max(x0, x1)
                            seg_min_y, seg_max_y = min(y0, y1), max(y0, y1)
                            if not (x_max < seg_min_x or x_min > seg_max_x or y_max < seg_min_y or y_min > seg_max_y):
                                collision = True
                                break
                        if collision:
                            break

                if not collision:
                    break  # всё ок, нет пересечений

                # если есть пересечение — сдвигаем аннотацию
                x, y = ann.get_position()           # текущее положение текста
                ann.set_position((x, y + step))     # сдвигаем

                fig.canvas.draw()  # обновляем bbox
                ann_bboxes[i] = ann.get_window_extent(renderer)












# на потом:

# try:
#     import ipympl
#     %matplotlib widget
#     print("Using ipympl")
# except ImportError:
#     print("ipympl not installed, interactive rearrangement of annotations is not available")
#     %matplotlib inline



# pip install ipympl
# pip install ipywidgets

# import matplotlib.pyplot as plt

# %matplotlib widget
# fig, ax = plt.subplots()
# ax.plot([0, 1], [0, 1])

# text = ax.text(0.5, 0.5, "Перетащи меня", fontsize=12, color="red")

# dragging = {"status": False}

# def on_press(event):
#     if text.contains(event)[0]:
#         dragging["status"] = True

# def on_release(event):
#     dragging["status"] = False

# def on_motion(event):
#     if dragging["status"] and event.inaxes == ax:
#         text.set_position((event.xdata, event.ydata))
#         fig.canvas.draw_idle()

# fig.canvas.mpl_connect("button_press_event", on_press)
# fig.canvas.mpl_connect("button_release_event", on_release)
# fig.canvas.mpl_connect("motion_notify_event", on_motion)

# plt.show()






# -------------------Библиотеки для установки-------------------


# Дополнительно установить

# pip install ipympl
# python.exe -m pip install --upgrade pip




# -------------------Примеры использования-------------------





# graph1 = GraphConfigurator()
# Для повторного вызова этого же окна:
# graph1.ax.figure


# %matplotlib widget
# %matplotlib notebook
# %matplotlib inline



# import os

# import math
# import pandas as pd
# import numpy as np

# import sys
# sys.path.append('c:/Users/User/Desktop/temp')

# wp = os.getcwd()

# from __mypackage_py import *
# import numpy as np
# import matplotlib.pyplot as plt


# test_data = pd.read_csv(os.path.join(wp, 'data.csv'), sep=r',', index_col=False, skipinitialspace=True)
# test_data.head(5)



# graph1 = GraphConfigurator(auto_range=True, XxYyZz_i_t_f=True,
#     # Ox_lim=(0, 0.003), Ox_step=0.0005,
#     # Oy_lim=(1e-3, 1000), Oy_step=20, 
#     x_label='X, м', y_label='p',
#     precision_1=1, precision_2=1,
# )


# graph1.conf_graph(*test_data.loc[:, ['x', 'p1']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.2, manual=True, an_x=2, an_y=10)
# graph1.conf_graph(*test_data.loc[:, ['x', 'p2']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.3)
# graph1.conf_graph(*test_data.loc[:, ['x', 'p3']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.4)
# graph1.conf_graph(*test_data.loc[:, ['x', 'p4']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.5)
# graph1.conf_graph(*test_data.loc[:, ['x', 'p5']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.6)
# graph1.conf_graph(*test_data.loc[:, ['x', 'p6']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.7)
# graph1.conf_graph(*test_data.loc[:, ['x', 'p7']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.8)
# graph1.conf_graph(*test_data.loc[:, ['x', 'p8']].values.T, mark_t_f=True, mark_size=40, alpha=1)
# graph1.conf_annot(an_ratio=0.9)


# graph1.add_annotation_with_sliders()
# # graph1.adjust_annotations(step=1, max_iter=20)

# graph1.legend_set(legend_sep_fig_t_f=True)

# # plt.savefig(os.path.join(wp, 'Delta_mass_rate.png'))
# # Пауза на 5 секунд перед закрытием графика
# graph1.ax.figure

# plt.pause(0.001)
# # plt.close()











#============33333333=====DDDDDDDD==================#============33333333=====DDDDDDDD==================#============33333333=====DDDDDDDD==================#
#============33333333=====DDDDDDDDD=================#============33333333=====DDDDDDDDD=================#============33333333=====DDDDDDDDD=================#
#============33====33=====DDD=====DD================#============33====33=====DDD=====DD================#============33====33=====DDD=====DD================#
#============33====33=====DDD======DD===============#============33====33=====DDD======DD===============#============33====33=====DDD======DD===============#
#================33=======DDD=======DD==============#================33=======DDD=======DD==============#================33=======DDD=======DD==============#
#================33=======DDD=======DD==============#================33=======DDD=======DD==============#================33=======DDD=======DD==============#
#============33333333=====DDD========DD=============#============33333333=====DDD========DD=============#============33333333=====DDD========DD=============#
#============33333333=====DDD========DD=============#============33333333=====DDD========DD=============#============33333333=====DDD========DD=============#
#================33=======DDD=======DD==============#================33=======DDD=======DD==============#================33=======DDD=======DD==============#
#================33=======DDD=======DD==============#================33=======DDD=======DD==============#================33=======DDD=======DD==============#
#============33====33=====DDD======DD===============#============33====33=====DDD======DD===============#============33====33=====DDD======DD===============#
#============33====33=====DDD=====DD================#============33====33=====DDD=====DD================#============33====33=====DDD=====DD================#
#============33333333=====DDDDDDDDD=================#============33333333=====DDDDDDDDD=================#============33333333=====DDDDDDDDD=================#
#============33333333=====DDDDDDDD==================#============33333333=====DDDDDDDD==================#============33333333=====DDDDDDDD==================#


from matplotlib import cm
from matplotlib.ticker import LinearLocator
from matplotlib.colors import ListedColormap
import matplotlib.colors

from scipy.spatial import Delaunay
from scipy.interpolate import griddata

from mpl_toolkits.mplot3d import axes3d
from mpl_toolkits.mplot3d import art3d
from mpl_toolkits.mplot3d import proj3d

from matplotlib.patches import FancyArrowPatch
from matplotlib.colors import Normalize
from matplotlib.colorbar import ColorbarBase



class Graph3DConfigurator:
    """Класс для настройки и построения 3D графиков"""

    mark_type_list = ['o', 's', '^', '<', '>', 'v', 'D','d', '.', 'p', '*', 'h', 'H', '+', 'x', '|', '_', '1', '2', '3', '4'] # Список возможных маркеров

    line_type_list = ['-', '--', '-.', ':', '.'] # Список возможных типов линий

    colors_list = ["black", "#167d16",
                 "#1f77b4", "#FE0000", "#9467bd", "#ff7f0e", "#17becf",
                 "#edc949", "#ff9da7", "#140a72", "#58bc4b", "#e377c2",
                 "#bb5303", "#770707", "#b7a1c3", "#bcbd22", "#f28e2b",
                 "#7f7f7f", "#76b7b2", "#b2df8a", "#ff7f00", "#af7aa1",
                 "#a6cee3", "#8c564b", "#fdbf6f", "#9c755f", "#fb9a99",
                 "#bab0ab", "#33a02c", "#1f78b4", "#e15759", "#f28e2b",
                 "#6a3d9a",
                   "tab:pink", "tab:olive", "tab:cyan", "tab:purple","tab:brown",
                   "tab:orange", "tab:green", "tab:blue", "tab:red", "tab:gray"] # Список возможных цветов при построении графиков

    
    zero_flag = 1e-10 # Параметр для выставления 0 в начале координат (величины менее 1e-10 заменяются 0)

    def __init__(self, 
                 auto_range:bool=True,
                 x_ticks_num:int=3, y_ticks_num:int=3, z_ticks_num:int=3,
                 proj_type:str='persp', elev:float=30.0, azim:float=-60.0,
                 x_ratio:float=1.0, y_ratio:float=1.0, z_ratio:float=1.0,
                 colorbar_t_f:bool=False,
                 XxYyZz_i_t_f:bool=False,
                 Ox_lim:Optional[Tuple[float, float]]=(1, 10),
                 Ox_step:Optional[float] = 1,
                 Oy_lim:Optional[Tuple[float, float]]=(1, 10), 
                 Oy_step:Optional[float] = 1,
                 Oz_lim:Optional[Tuple[float, float]]=(1, 10), 
                 Oz_step:Optional[float] = 1,
                 precision_1:int=0, precision_2:int=0, precision_3:int=0,
                 x_label:str='X', y_label:str='Y', z_label:str='Z',
                 x_scale:str='linear', y_scale:str='linear', z_scale:str='linear',
                 window_size_x:int=7, window_size_y:int=7,
                 l_space:float=0.03, r_space:float=0.83, t_space:float=1.0, b_space:float=0.03,
                 font_size:int=16, font_family:str="Times New Roman",
                 grid_t_f:bool=True, rt_t_f:bool=True,
                 annot_t_f:bool=False,
                 fraction_of_points:Optional[float]=None,
                 ax=None):


        """Инициализация графика и базовых настроек
        
            Args:
                auto_range (bool, optional): Флаг активации автоматического определения границ графика. Defaults to True.
                x_ticks_num (int, optional): Количество меток на оси x для авто режима. Defaults to 5.
                y_ticks_num (int, optional): Количество меток на оси y для авто режима. Defaults to 5.
                z_ticks_num (int, optional): Количество меток на оси z для авто режима. Defaults to 5.
                proj_type (str, optional): Тип перспетиквы 'persp'/'ortho'. Defaults to 'persp'.
                elev (float, optional): Угол подъёма, то есть "высота камеры" над плоскостью XY (в градусах). Defaults to 30.0.
                azim (float, optional): Азимут, угол поворота камеры вокруг оси Z (в градусах). Defaults to -60.0.
                x_ratio (float, optional): Коэффициент растяжения оси x. Defaults to 1.
                y_ratio (float, optional): Коэффициент растяжения оси y. Defaults to 1.
                z_ratio (float, optional): Коэффициент растяжения оси z. Defaults to 1.
                colorbar_t_f (bool, optional): Флаг активации отрисовки цветовой легенды. Defaults to False.
                XxYyZz_i_t_f (bool, optional): Флаг активации курсива для XxYyZz. Defaults to False.
                Ox_lim (Optional[Tuple], optional): Список из двух значений - левая и правая границы оси x. Defaults to (1, 10).
                Ox_step (Optional[float], optional): Шаг по оси x. Defaults to 1.
                Oy_lim (Optional[Tuple], optional): Список из двух значений - нижняя и верхняя границы оси y. Defaults to (1, 10).
                Oy_step (Optional[float], optional): Шаг по оси y. Defaults to to 1.
                Oz_lim (Optional[Tuple], optional): Список из двух значений - нижняя и верхняя границы оси z. Defaults to (1, 10).
                Oz_step (Optional[float], optional): Шаг по оси z. Defaults to to 1.
                precision_1 (int, optional): Количество знаков после запятой для меток на оси x. Defaults to 0.
                precision_2 (int, optional): Количество знаков после запятой для меток на оси y. Defaults to 0.
                precision_3 (int, optional): Количество знаков после запятой для меток на оси z. Defaults to 0.
                x_label (str, optional): Наименование оси x. Defaults to 'X'.
                y_label (str, optional): Наименование оси y. Defaults to 'Y'.
                z_label (str, optional): Наименование оси z. Defaults to 'Z'.
                x_scale (str, optional): Тип шкалы оси x - 'linear'/'log'. Defaults to 'linear'.
                y_scale (str, optional): Тип шкалы оси y - 'linear'/'log'. Defaults to 'linear'.
                z_scale (str, optional): Тип шкалы оси z - 'linear'/'log'. Defaults to 'linear'.
                window_size_x (int, optional): Размер окна рисунка по горизонтали. Defaults to 9.
                window_size_y (int, optional):  Размер окна рисунка по вертикали. Defaults to 6.
                l_space (float, optional): Размер поля слева. Defaults to 0.1.
                r_space (float, optional): Размер поля справа. Defaults to 0.9.
                t_space (float, optional): Размер поля сверху. Defaults to 0.93.
                b_space (float, optional): Размер поля снизу. Defaults to 0.07.
                font_size (int, optional): Размер шрифта. Defaults to init: 22.
                font_family (str, optional): Тип шрифта. Defaults to 'Times New Roman'.
                grid_t_f (bool, optional): Включение сетки на поле графика. Defaults True.
                rt_t_f (bool, optional): Включение верхней и правой границ графика. Defaults to True.  
                annot_t_f (bool, optional): Флаг активации аннотаций вместе с построением линий. Defaults to True.
                fraction_of_points (Optional[float], optional): Доля точек, по которым строится перпендикуляр для аннотации. Defaults to None.
                ax (): назначение осей в одно окно рисунка. Defaults to None.          
        """
        
        


        self.l_space, self.r_space, self.t_space, self.b_space = l_space, r_space, t_space, b_space
        self.elev, self.azim = elev, azim
        # Создание окна с указанными размерами (опционально возможно несколько координатных систем в одном окне)
        if ax is None:
            self.fig = plt.figure(figsize=(window_size_x, window_size_y))
            self.ax_fake = self.fig.add_axes([0, 0, 1, 1], projection='3d', proj_type='ortho')
            
            for axis, set in zip([self.ax_fake.xaxis, self.ax_fake.yaxis, self.ax_fake.zaxis], 
                                 [self.ax_fake.set_xticks, self.ax_fake.set_yticks, self.ax_fake.set_zticks]):
                axis.line.set_color((0,0,0,0))  # линии осей прозрачные
                axis.pane.set_facecolor((1,1,1,0))  # фон панели прозрачный
                axis.pane.set_edgecolor((1,1,1,0))  # ребра прозрачные
                set([])

            self.ax_fake.grid(False)
            self.ax_fake.patch.set_alpha(0)  # прозрачный фон
            self.ax_fake.view_init(elev=90, azim=-90)

            self.ax = self.fig.add_axes([self.l_space, self.b_space, 
                                        self.r_space - self.l_space,
                                        self.t_space - self.b_space],
                                         projection='3d', proj_type=proj_type)
            self.ax.set_box_aspect((x_ratio, y_ratio, z_ratio))
            self.ax.view_init(elev=elev, azim=azim)
        else:
            self.ax = ax
            self.fig = ax.figure  # сохраняем ссылку на фигуру, если она есть

        self.elev = elev
        self.azim = azim

        # Установка атрибутов экземпляров  
        self.auto_range=auto_range

        self.Ox_lim = Ox_lim
        self.Ox_step = Ox_step
        self.Oy_lim = Oy_lim
        self.Oy_step = Oy_step
        self.Oz_lim = Oz_lim
        self.Oz_step = Oz_step
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.z_scale = z_scale

        self.precision_1 = precision_1
        self.precision_2 = precision_2
        self.precision_3 = precision_3

        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label

        self.font_size = font_size
        self.font_family = font_family
        self.XxYyZz_i_t_f = XxYyZz_i_t_f

        self.grid_t_f = grid_t_f
        self.rt_t_f = rt_t_f
        # self.annot_t_f = annot_t_f
        # self.fraction_of_points = fraction_of_points

        # self.shifting_switch = True
        self.arrow_x = None
        self.arrow_y = None
        self.arrow_z = None

        self._all_data_x = []
        self._all_data_y = []
        self._all_data_z = []

        self.x_ticks_num = x_ticks_num
        self.y_ticks_num = y_ticks_num
        self.z_ticks_num = z_ticks_num

        self.line_count = 0
        self.mark_count = 0
        self.count = 0

        self.arrow_existence = False
        self.colorbar_t_f = colorbar_t_f
        # self.an_ratio = 0.265

        # Основные метки и цвета
        self.mc_mark_list = [GraphConfigurator.mark_type_list[i] for i in [0, 1, 2, 6, 7, 9, 10, 12, 13, 14]]
        self.mc_color_list = GraphConfigurator.colors_list

        colors = [(0, 0, 1),    # ярко-синий
                  (0, 1, 1),    # голубой
                  (0, 1, 0),    # зелёный
                  (1, 1, 0),    # жёлтый
                  (1, 0, 0)]    # ярко-красный
        
        hex_colors_1 = ["#17FCF8", "#2DFFD0", "#7EFF81", "#CEFD34", "#FEDE00", "#FB9400", "#FC4401", "#FB0405"]
        hex_colors_2 = ["#000000", "#54168C", "#511DF2", "#002EFD", "#00F2F8", "#0DF85E", "#74FF00", "#F3FF07"]
        hex_colors_3 = ["#790C7B", "#5F4163", "#359433", "#10DE10", "#00F32E", "#01DF7E", "#02CCC9", "#01BFF9"]
        hex_colors_4 = ["#303034", "#0A4E82", "#0798FB", "#67E3E6", "#B3F6BA", "#F2E30F", "#F0A851", "#BC3D3D"]
        hex_colors_5 = ["#6A45B2", "#44A1C6", "#8BD9DD", "#8CE7B2", "#EDF24B", "#F2EA7E"]
        hex_const_1 = [self.mc_color_list[0], self.mc_color_list[0]]
        hex_const_2 = [self.mc_color_list[1], self.mc_color_list[1]]
        hex_const_3 = [self.mc_color_list[2], self.mc_color_list[2]]
        hex_const_4 = [self.mc_color_list[3], self.mc_color_list[3]]
        hex_const_5 = [self.mc_color_list[4], self.mc_color_list[4]]
        hex_const_6 = [self.mc_color_list[5], self.mc_color_list[5]]
        custom_cmap_0 = matplotlib.colors.LinearSegmentedColormap.from_list("rainbow_custom", colors)
        custom_cmap_1 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_colors_1)
        custom_cmap_2 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_colors_2)
        custom_cmap_3 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_colors_3)
        custom_cmap_4 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_colors_4)
        custom_cmap_5 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_colors_5)
        custom_cmap_const_1 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_const_1)
        custom_cmap_const_2 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_const_2)
        custom_cmap_const_3 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_const_3)
        custom_cmap_const_4 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_const_4)
        custom_cmap_const_5 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_const_5)
        custom_cmap_const_6 = matplotlib.colors.LinearSegmentedColormap.from_list("", hex_const_6)

        self.color_maps = [custom_cmap_0, custom_cmap_1, custom_cmap_2, custom_cmap_3,  custom_cmap_4, custom_cmap_5,
                           cm.binary,
                           cm.rainbow, cm.gist_rainbow, cm.jet, cm.turbo, 
                           cm.cool, cm.spring, cm.autumn,
                           cm.inferno, cm.viridis, cm.gnuplot,
                           cm.coolwarm, cm.PuOr,
                           custom_cmap_const_1, custom_cmap_const_2, custom_cmap_const_3, custom_cmap_const_4,
                           custom_cmap_const_5, custom_cmap_const_6]
        
        # Проверка на адекватность задания границ графика при использовании логарифмической шкалы
        # if self.x_scale == 'log' and self.Ox_lim[0] <= 0 or self.Ox_lim[1] <= 0:
        #     self.Ox_lim = (1e-5, 1e+5)
        #     if not auto_range:
        #         print('The boundaries are set incorrectly for logarithmic scale. Automatic correction...')

        # if self.y_scale == 'log' and self.Oy_lim[0] <= 0 or self.Oy_lim[1] <= 0:
        #     self.Oy_lim = (1e-5, 1e+5)
        #     if not auto_range:
        #         print('The boundaries are set incorrectly for logarithmic scale. Automatic correction...')

        # Массивы для объектов легенды, возможно уже не нужен
        # self.annotations = []
        
        # self.lines = []

        # Словарь со всеми параметрами аннотаций и индексацией
        # self.annot_for_sliders = []

        # Включение настроек по умолчанию для стартового окна
        self.update_graph()


    def update_graph(self):
        """Включение настроек других функций по умолчанию при создании окна
        """

        self.conf_ticks() # Обновление меток
        self.conf_axes() # Обновление оформления осей


    @staticmethod
    def nice_limits(data_min:float, data_max:float, n_ticks:int=5):
        """Функция автоматического выбора делений графика по вычисленным границам

            Args:
                data_min (float): Минимальное значение на графике.
                data_max (float): Максимальное значение на графике.
                n_ticks (int, optional): Приблизительное число меток. Defaults to 5.
        """

        # Вычисление ширины диапазона значений (с учетом возможного равенства 0)
        data_range = data_max - data_min
        if data_range == 0:
            return data_min - 1, data_max + 1

        raw_step = data_range / n_ticks # Вычисление приблизительного шага для делений
        order = 10 ** math.floor(math.log10(raw_step)) # Вычисление порядка шага с округлением в меньшую сторону
        step_candidates = [1, 2, 2.5, 5, 10] # Список наиболее удачных шагов для делений
        step = min(step_candidates, key=lambda s: abs(raw_step - s * order)) # Подбор наиболее подходящего шага из списка
        step *= order # Приведение порядка выбранного шага к порядку приблизительного

        decimals = max (0, -int(math.floor(math.log10(step))) + 2) # Вычисление уровня округления на базе значения шага (для удаления машинных нулей титпа 0.15000000002)
        step = round(step, decimals) # Округление шага

        new_min = round(math.floor(data_min / step) * step, decimals) # Округление в меньшую сторону миниума диапазона
        new_max = round(math.ceil(data_max / step) * step, decimals) # Округление в большую сторону максимума диапазона

        return new_min, new_max, step





    def update_limits(self, auto_range_t_f:bool=True, use_all_data:bool=True,
                      x_ticks_num:Optional[float]=None, 
                      y_ticks_num:Optional[float]=None,
                      z_ticks_num:Optional[float]=None):
        """Автоматически обновляем пределы графика по всем переданным массивам
            
            Args:
                auto_range_t_f (bool, optional): Флаг активации автоматического вычисления границ графика. Defaults to True.
                use_all_data (bool, optional): Флаг активации использования всех данных для вычисления границ графика. Defaults to True.
                x_ticks_num (float): Приблизительное число меток по оси x. Defaults to 5.
                y_ticks_num (float): Приблизительное число меток по оси y. Defaults to 5.
                z_ticks_num (float): Приблизительное число меток по оси z. Defaults to 5.
        """
        if not auto_range_t_f:
            return() # Выход из функции, если автоматическое вычисление границ отключено

        if not self._all_data_x or not self._all_data_y:
            return()  # Выход из функции, если данных нет
        

        if use_all_data:
                    # Объединяем все данные, если включен соответствующий флаг
            all_x = np.concatenate(self._all_data_x)
            all_y = np.concatenate(self._all_data_y)
            all_z = np.concatenate(self._all_data_z)
        else:
            all_x = self._all_data_x[-1]
            all_y = self._all_data_y[-1]
            all_z = self._all_data_z[-1]
        
        # Получение ориентировочного количесвта меток по осям из init
        if x_ticks_num is None: x_ticks_num = self.x_ticks_num
        if y_ticks_num is None: y_ticks_num = self.y_ticks_num
        if z_ticks_num is None: z_ticks_num = self.z_ticks_num


        #Вычисление минимальных и максимальных значений из массивов
        x_min, x_max = all_x.min(), all_x.max()
        y_min, y_max = all_y.min(), all_y.max()
        z_min, z_max = all_z.min(), all_z.max()


        # Обработка логарифмических шкал для осей x и y c проверкой на отрицательные и нулевые значения
        if self.x_scale == 'log':
            x_min = 10 ** (math.ceil(math.log10(min([x for x in all_x if x > 0]))) - 1)
            x_max = 10 ** (math.floor(math.log10(x_max)) + 1)
            x_step = 10 # не используется, просто значение отличное от None
        else:
            x_min, x_max, x_step = GraphConfigurator.nice_limits(x_min, x_max, x_ticks_num)

        if self.y_scale == 'log':
            y_min = 10 ** (math.ceil(math.log10(min([y for y in all_y if y > 0]))) - 1)
            y_max = 10 ** (math.floor(math.log10(y_max)) + 1)
            y_step = 10 # не используется, просто значение отличное от None
        else:
            y_min, y_max, y_step = GraphConfigurator.nice_limits(y_min, y_max, y_ticks_num)

        if self.z_scale == 'log':
            z_min = 10 ** (math.ceil(math.log10(min([z for z in all_z if z > 0]))) - 1)
            z_max = 10 ** (math.floor(math.log10(z_max)) + 1)
            z_step = 10 # не используется, просто значение отличное от None
        else:
            z_min, z_max, z_step = GraphConfigurator.nice_limits(z_min, z_max, z_ticks_num)

        self.Ox_lim = (x_min, x_max)
        self.Ox_step = x_step
        self.Oy_lim = (y_min, y_max)
        self.Oy_step = y_step
        self.Oz_lim = (z_min, z_max)
        self.Oz_step = z_step
        
        self.conf_ticks() # Обновление делений на графике
        self.fig.canvas.draw() # Обновление отрисовки всего графика
        return()












    
    @staticmethod
    def format_tick_labels(values, precision:int=2):
        """Форматирование меток на осях в строки с заданной точностью и разделителем ",".
           Если значение равно 0 (1e-10), возвращает "0" без разделителей.

            Args:
                values (): Массив чисел для форматирования.
                precision (int, optional): Количество знаков после запятой. Defaults to 2.
        """
        formatted = []
        for value in values:
            if abs(value) < GraphConfigurator.zero_flag: # Проверка на "практически ноль"
                formatted.append("0")
            else:
                s = f"{value:.{precision}f}".replace('.', ',')
                formatted.append(s)
        return formatted


    def conf_ticks(self, 
                   Ox_lim:Optional[Tuple[float, float]]=None,
                   Ox_step:Optional[float] = None,
                   Oy_lim:Optional[Tuple[float, float]]=None, 
                   Oy_step:Optional[float] = None,
                   Oz_lim:Optional[Tuple[float, float]]=None, 
                   Oz_step:Optional[float] = None,
                   x_scale:Optional[str]=None, y_scale:Optional[str]=None, z_scale:Optional[str]=None,
                   grid_t_f:Optional[bool]=None,
                   font_size:Optional[int]=None, font_family:Optional[str]=None, 
                   precision_1:Optional[int]=None, precision_2:Optional[int]=None, precision_3:Optional[int]=None,
                   single_zero:bool=True, zero_x:float=-0.03, zero_y:float=-0.055,
                   pad_x:float=5, pad_y:float=5, pad_z:float=5,):

        """Настройка шкалы и меток осей

            Args:
                Ox_lim (Optional[Tuple], optional): Список из двух значений - левая и правая границы горизонтальной оси. Defaults to None -> init: (0, 1).
                Ox_step (Optional[float], optional): Шаг по горизонтальной оси. Defaults to None -> init: 0.1.
                Oy_lim (Optional[Tuple], optional): Список из двух значений - нижняя и верхняя границы вертикальной оси. Defaults to None -> init: (0, 1).
                Oy_step (Optional[float], optional): Шаг по вертикальной оси. Defaults to None -> init: 0.1.
                Oz_lim (Optional[Tuple], optional): Список из двух значений - нижняя и верхняя границы вертикальной оси. Defaults to None -> init: (0, 1).
                Oz_step (Optional[float], optional): Шаг по вертикальной оси. Defaults to None -> init: 0.1.
                x_scale (Optional[str], optional): Тип шкалы горизонтальной оси - 'linear'/'log'. Defaults to None -> init: 'linear'.
                y_scale (Optional[str], optional): Тип шкалы вертикальной оси - 'linear'/'log'. Defaults to None -> init:  'linear'.
                z_scale (Optional[str], optional): Тип шкалы вертикальной оси - 'linear'/'log'. Defaults to None -> init:  'linear'.
                grid_t_f (Optional[bool], optional): Включение сетки на поле графика. Defaults to None -> init: True.
                font_size (int, optional): Размер шрифта. Defaults to None -> init: 16.
                font_family (str, optional): Тип шрифта. Defaults to None -> init: 'Times New Roman'.
                single_zero (bool, optional): Единственный ноль в начале координат. Defaults to False.
                zero_x (float, optional): Положение нуля по горизонтали в долях от размера оси. Defaults to -0.03.
                zero_y (float, optional): Положение нуля по вертикали в долях от размера оси. Defaults to -0.055.
        """

        coef1 = 1.000 # коэффициент для установления границ отрисовки осей относительно заданных границ (нужен для корректной отрисовки, а может уже нет)
        coef2 = 0.2 # коэффициент для установления количества минорный делений 0.2 -> 5

        # Значения вводятся из init при отсутствии явного указания их через функцию
        if Ox_lim is None: Ox_lim = self.Ox_lim
        if Ox_step is None: Ox_step = self.Ox_step
        if Oy_lim is None: Oy_lim = self.Oy_lim
        if Oy_step is None: Oy_step = self.Oy_step
        if Oz_lim is None: Oz_lim = self.Oz_lim
        if Oz_step is None: Oz_step = self.Oz_step
        if x_scale is None: x_scale = self.x_scale
        if y_scale is None: y_scale = self.y_scale
        if z_scale is None: z_scale = self.z_scale
        if grid_t_f is None: grid_t_f = self.grid_t_f
        if font_size is None: font_size = self.font_size
        if font_family is None: font_family = self.font_family
        if precision_1 is None: precision_1 = self.precision_1
        if precision_2 is None: precision_2 = self.precision_2
        if precision_3 is None: precision_3 = self.precision_3

        # Фиксация границ осей
        self.ax.set_xlim(Ox_lim[0], Ox_lim[1] * coef1)
        self.ax.set_ylim(Oy_lim[0], Oy_lim[1] * coef1)
        self.ax.set_zlim(Oz_lim[0], Oz_lim[1] * coef1)

        # Задание типа шкалы, возможные значения: linear/log
        self.ax.set_xscale(x_scale)
        self.ax.set_yscale(y_scale)
        self.ax.set_zscale(z_scale)
        
        linewidth = 1.0
        inward_factor = 0.4
        outward_factor = 0.1

        if self.elev == 90:
            linewidth = 1.0
            inward_factor = 0.2
            outward_factor = 0.0

        # Задание параметров отрисовки делений (длина, ширина)
        for axis in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
        # _axinfo — приватный словарь mplot3d, он управляет отрисовкой тиков
            axis._axinfo['tick']['linewidth'][True] = linewidth 
            axis._axinfo['tick']['inward_factor'] = inward_factor
            axis._axinfo['tick']['outward_factor'] = outward_factor

        # pad_x, pad_y, pad_z = 10,10,10
        self.ax.xaxis.set_tick_params(pad=pad_x)
        self.ax.yaxis.set_tick_params(pad=pad_y)
        self.ax.zaxis.set_tick_params(pad=pad_z)


        # Отрисовка меток на графике в соответствии с типом шкалы и границами
        if x_scale == 'linear' and y_scale == 'linear' and z_scale == 'linear':
            # Массивы делений для осей, не включающие последние деления (для указания наименования шкалы)
            x_ticks = np.arange(Ox_lim[0], Ox_lim[1], Ox_step)
            y_ticks = np.arange(Oy_lim[0], Oy_lim[1], Oy_step)
            z_ticks = np.arange(Oz_lim[0], Oz_lim[1], Oz_step)

            # Выравнивание массивов
            if True:
                if len(x_ticks) < int(round(abs(Ox_lim[1] - Ox_lim[0]) / Ox_step) + 1):
                    x_ticks = np.append(x_ticks, Ox_lim[1])
                if len(y_ticks) < int(round(abs(Oy_lim[1] - Oy_lim[0]) / Oy_step) + 1):
                    y_ticks = np.append(y_ticks, Oy_lim[1])
                if len(z_ticks) < int(round(abs(Oz_lim[1] - Oz_lim[0]) / Oz_step) + 1):
                    z_ticks = np.append(z_ticks, Oz_lim[1])
            

            

            # Если включен режим single_zero, убираем 0 с осей
            if single_zero and Ox_lim[0] == 0 and Oy_lim[0] == 0:
                x_ticks = [tick for tick in x_ticks if abs(tick) > GraphConfigurator.zero_flag] # Удаляются значения меньше zero_flag = 1e-10
                y_ticks = [tick for tick in y_ticks if abs(tick) > GraphConfigurator.zero_flag]
            
            lables_x = self.format_tick_labels(x_ticks, precision_1)
            lables_x[-1] = self.x_label
            lables_y = self.format_tick_labels(y_ticks, precision_2)
            if self.elev != 90:
                lables_y[0] = ''
            lables_y[-1] = self.y_label
            lables_z = self.format_tick_labels(z_ticks, precision_3)
            lables_z[0] = ''
            lables_z[-1] = self.z_label
            

            if self.elev == 90 and self.azim == -90:
                for label in self.ax.get_yticklabels():
                    label.set_va('center')
                    label.set_ha('right')


            if self.elev != 90:
                for label in self.ax.get_xticklabels():
                    label.set_va('center')
                    label.set_ha('center')
                for label in self.ax.get_yticklabels():
                    label.set_va('center')
                    label.set_ha('center')
                for label in self.ax.get_zticklabels():
                    label.set_va('center')
                    label.set_ha('left')

            self.ax.set_xticks(x_ticks, labels=lables_x, fontsize=font_size, fontname=font_family)
            self.ax.set_yticks(y_ticks, labels=lables_y, fontsize=font_size, fontname=font_family)
            self.ax.set_zticks(z_ticks, labels=lables_z, fontsize=font_size, fontname=font_family)

        # Сетка на поле графике
        if grid_t_f:
            # self.ax.grid(color='grey', linestyle='--', linewidth = 0.5)
                self.ax.grid(which='major', color='grey', linestyle='--', linewidth=0.5)
                self.ax.grid(which='minor', color='lightgrey', linestyle=':', linewidth=0.3)

        if self.elev == 90:
            self.ax.zaxis.line.set_color((0,0,0,0)) 
            self.ax.set_zticks([])    




    def draw_axis_arrows(self, ax, arrow_t_f: bool = True, headlength: float = 10, headwidth: float = 5):
        """Отрисовка стрелочек на осях
        
            Args:
                ax(): объект - кооридантная рамка.
                arrow_t_f (bool, optional): Флаг активации отрисовки стрелочек на осях. Defaults to True.
                headlength (float, optional): Длина стрелочки. Defaults to 10.
                headwidth (float, optional): Ширина стрелочки. Defaults to 5.
        """

        if not arrow_t_f:
            return()
        
        fig = ax.figure
    
        # Получение координат точек бокса координатных осей и его длины, ширины
        ax_bbox = ax.get_position()  # Получение координат точек бокса координатных осей и его длины, ширины      
        fig_w, fig_h = fig.get_size_inches() # Получение размеров окна
    
        # Смещение стрелки по x (горизонтальная ось)
        self.dx_fig = headlength / fig.dpi / fig_w / ax_bbox.width
        # Смещение стрелки по y (вертикальная ось)
        self.dy_fig = headlength / fig.dpi / fig_h / ax_bbox.height
    
        # Горизонтальная стрелка
        self.arrow_x = self.ax.annotate('', xy=(1 + self.dx_fig, 0), xytext=(0, 0), 
                                  arrowprops=dict(facecolor='black', 
                                                  shrink=0.0, width=0.01, headlength=headlength, headwidth=headwidth), 
                                  xycoords='axes fraction', textcoords='axes fraction')

        # Вертикальная стрелка
        self.arrow_y = self.ax.annotate('', xy=(0, 1 + self.dy_fig), xytext=(0, 0), 
                    arrowprops=dict(facecolor='black', 
                                    shrink=0.0, width=0.01, headlength=headlength, headwidth=headwidth), 
                    xycoords='axes fraction', textcoords='axes fraction')


    def conf_axes(self, x_label:Optional[str]=None, y_label:Optional[str]=None, z_label:Optional[str]=None,
                  labelpad_x:Optional[float]=20, labelpad_y:Optional[float]=20, labelpad_z:Optional[float]=20,
                  rotation_x:Optional[float]=0, rotation_y:Optional[float]=0, rotation_z:Optional[float]=0,
                  type_axes_name:bool=False, 
                  manual_axes_t_f:bool=False,
                  x_label_x:float=1.0, x_label_y:float=-0.018, 
                  y_label_x:float=-0.015, y_label_y:float=1.0,
                  arrow_t_f:bool=True,
                  rt_t_f:Optional[bool]=None,
                  font_size:Optional[int]=None, font_family:Optional[str]=None):

        """Функция подписи наименований осей, стрелочек и отрисовки границ

            Args:
                x_label (Optional[str], optional): Наименование оси x. Defaults to None -> init: 'X'.
                y_label (Optional[str], optional): Наименование оси y. Defaults to None -> init: 'Y'.
                z_label (Optional[str], optional): Наименование оси z. Defaults to None -> init: 'Z'.
                labelpad_x (Optional[float], optional): Смещение наименования для стандартного метода оси x. Defaults to 30.
                labelpad_y (Optional[float], optional): Смещение наименования для стандартного метода оси y. Defaults to 30.
                labelpad_z (Optional[float], optional): Смещение наименования для стандартного метода оси z. Defaults to 30.
                type_axes_name (bool, optional): Флаг активации стандартной python подписи осей. Defaults to False.
                manual_axes_t_f (bool, optional): Флаг активации ручной установки положения наименования осей. Defaults to False.
                x_label_x (Optional[float], optional): Положение подписи горизонтальной оси по горизонтали. Defaults to None -> init: 1.03.
                x_label_y (Optional[float], optional): Положение подписи горизонтальной оси по вертикали. Defaults to None -> init: -0.018.
                y_label_x (Optional[float], optional): Положение подписи вертикальной оси по горизонтали. Defaults to None -> init: -0.015.
                y_label_y (Optional[float], optional): Положение подписи вертикальной оси по вертикали. Defaults to None -> init: 0.98.
                arrow_t_f (bool, optional): Включение стрелочек на осях. Defaults to True.
                rt_t_f (Optional[bool], optional): Включение верхней и правой границ графика. Defaults to None -> init: True.
                font_size (int, optional): Размер шрифта. Defaults to None -> init: 16.
                font_family (str, optional): Тип шрифта. Defaults to None -> init: 'Times New Roman'.
        """

        # Установка значений из init
        if x_label is None: x_label = self.x_label
        if y_label is None: y_label = self.y_label
        if z_label is None: z_label = self.z_label
        if rt_t_f is None: rt_t_f = self.rt_t_f
        if font_size is None: font_size = self.font_size
        if font_family is None: font_family = self.font_family




        # Стандартная питоновская отрисовка осей
        if type_axes_name:
            x_label = '      ' + self.x_label + '      '
            y_label = '      ' + self.y_label + '      '
            z_label = '      ' + self.z_label + '      '
            self.ax.set_xlabel(x_label, fontsize=font_size, fontname=font_family, labelpad=labelpad_x, rotation=rotation_x) 
            self.ax.set_ylabel(y_label, fontsize=font_size, fontname=font_family, labelpad=labelpad_y, rotation=rotation_y)
            self.ax.set_zlabel(z_label, fontsize=font_size, fontname=font_family, labelpad=labelpad_z, rotation=rotation_z)


    def conf_graph_surface(self, data_x:list, data_y:list, data_z:list, *, graph_type:str='surface',
                           interpolation:str='linear', mesh_density:float=1,
                           gradient:bool=False, levels:int=20,
                           mark_only_t_f:bool=False, lab:Optional[str]=None,
                           col:Optional[int]=None, color_map:int=0, line_type:Optional[int]=None, line_width:float=1.5,
                           mark_t_f:bool=False, mark_every:int=1, mark_col:Optional[str]=None, edge_col:Optional[str]=None, 
                           alpha:float=1.0, mark_type:Optional[int]=None, mark_size:int=20,
                           test:bool=True):

        """Функция построения графика

            Args:
                data_x (list): Массив данных по оси x.
                data_y (list): Массив данных по оси y.
                data_z (list): Массив данных по оси z.
                graph_type (str, optional): Тип графика 'surface', 'surface_mesh', 'mesh', 'scatter', 'contour', 'tri'. Defaults to 0.
                interpolation (str, optional): Метод интерполяции для графика типа 'surface', 'surface_mesh', доступные значения 'linear', 'cubic'. Defaults to 'linear'.
                mesh_density (float, optional): Плотность сетки. Defaults to 1.0.
                gradient (bool, optional): Флаг включения cmap для точек 'scatter'. Defaults to False.
                levels (int, optional): Количество уровней для 'contour'. Defaults to 20.
                mark_only_t_f (bool, optional): Флаг построения графика только с маркерами. Defaults to False.
                lab (Optional[str], optional): Наименования графика для легенды. Defaults to '1'.
                col (Optional[int], optional): Цвет линии графика. Defaults to 'black'.
                color_map (Optional[int], optional): Тип карты цвета. Defaults to 0.
                line_type (Optional[int], optional): Тип линии графика. Defaults to 0.
                line_width (float, optional): Толщина линии графика. Defaults to 1.0.
                mark_t_f (bool, optional): Включение маркеров на линии графика. Defaults to False.
                mark_every (int, optional): Частота постановки маркеров. Defaults to 1.
                mark_col (Optional[str], optional): Цвет маркеров. Defaults to None -> col.
                edge_col (Optional[str], optional): Цвет границы графика. Defaults to 'white'.
                alpha (float, optional): Прозрачность графика. Defaults to 1.0.
                mark_type (Optional[int], optional): Тип маркера. Defaults to 0.
                mark_size (int, optional): Размер маркера. Defaults to 20.
        """

        # self.data_x = data_x
        # self.data_y = data_y

        # Попробуем фильтровать None
        self.data_x = [x for x in data_x if x is not None]
        self.data_y = [y for y in data_y if y is not None]
        self.data_z = [z for z in data_z if z is not None]

        # Добавление поступающих данных в общий массив для вычисления границ графика
        self._all_data_x.append(np.array(data_x))
        self._all_data_y.append(np.array(data_y))
        self._all_data_z.append(np.array(data_z))

        self.update_limits(auto_range_t_f=self.auto_range) # Вызов функции автоматического выставления границ графика

        # Для использования .min() .max() из numpy
        data_x, data_y, data_z = np.array(data_x), np.array(data_y), np.array(data_z)






        # Для автоматического выставления аннотаций для каждого графика: 1, 2, 3...
        if lab is None: lab = str(self.count + 1)

        # Автоматический выбор цвета из списка
        if col is None: 
            col = self.mc_color_list[self.count]
        else:
            col = self.mc_color_list[col]
        
        if edge_col is None: edge_col = col
        if mark_col is None: mark_col = col
        
        # Автоматический выбор типа метки из списка (список ограничен, поэтому выбор обнуляется)
        if mark_type is None:
            if self.mark_count == len(self.mc_mark_list):
                self.mark_count = 0
            mark_type_str = self.mc_mark_list[self.mark_count]
        else:
            mark_type_str = self.mc_mark_list[mark_type]
        
        # Автоматический выбор типа линии из списка (список ограничен, поэтому выбор обнуляется)
        if line_type is None:
            if self.line_count == len(GraphConfigurator.line_type_list) - 1:
                self.line_count = 0
            line_type_str = GraphConfigurator.line_type_list[self.line_count]
        else:
            line_type_str = GraphConfigurator.line_type_list[line_type]





        if data_x.ndim == 1:
            # Нормализация X, Y, Z
            x_min, x_max = data_x.min(), data_x.max()
            y_min, y_max = data_y.min(), data_y.max()
            # z_min, z_max = data_z.min(), data_z.max()

            x_scaled = (data_x - x_min) / (x_max - x_min)
            y_scaled = (data_y - y_min) / (y_max - y_min)

            points_scaled = np.column_stack((x_scaled, y_scaled))

            if graph_type == 'tri':
                # Триангуляция (по нормализованным координатам)
                tri = Delaunay(points_scaled)

                x_tri = x_scaled * (x_max - x_min) + x_min
                y_tri = y_scaled * (y_max - y_min) + y_min


            if graph_type in ['surface', 'surface_mesh', 'mesh', 'grid_scatter', 'scatter', 'contour']:
                # Создаём сетку в нормализованных координатах ---
                # Для избежания NaN и выбросов на границах вводим смещение delta для нормализованных границ (0,1)
                if graph_type == 'grid_scatter':
                    delta = 0.05
                else:
                    delta = 0.0
                grid_xs, grid_ys = np.meshgrid(
                                               np.linspace(delta, 1-delta, 100),
                                               np.linspace(delta, 1-delta, 100)
                                               )
                
                # Интерполяция 
                grid_z = griddata(points_scaled, data_z, (grid_xs, grid_ys), method=interpolation)

                # Возврат сетки к исходным координатам
                grid_x = grid_xs * (x_max - x_min) + x_min
                grid_y = grid_ys * (y_max - y_min) + y_min

        elif data_x.ndim == 2:
            grid_x, grid_y, grid_z = data_x, data_y, data_z


        norm = Normalize(vmin=self.Oz_lim[0], vmax=self.Oz_lim[1])

        if graph_type == 'surface': #  or graph_type == 'surface_mesh'
            graph3D = self.ax.plot_surface(grid_x, grid_y, grid_z, cmap=self.color_maps[color_map],
                           linewidth=line_width, antialiased=False, alpha=alpha, norm=norm)
            
            

        elif graph_type == 'surface_mesh':
            # frequency = int(round(1 / mesh_density))
            frequency = 1
            self.ax.plot_wireframe(grid_x, grid_y, grid_z, 
                                   rstride=frequency, cstride=frequency,
                                   color=col, linewidth=line_width, alpha=alpha)

        elif graph_type == 'mesh':
            # Вытаскиваем данные по линиям из plot_wireframe, и потом удаляем этот график

            rfrequency, cfrequency = int(1 / mesh_density), int(1 / mesh_density)

            wire = self.ax.plot_wireframe(grid_x, grid_y, grid_z, rstride=rfrequency, cstride=cfrequency)
            nx, ny, _  = np.shape(wire._segments3d)
            wire_x = np.array(wire._segments3d)[:, :, 0].ravel()
            wire_y = np.array(wire._segments3d)[:, :, 1].ravel()
            wire_z = np.array(wire._segments3d)[:, :, 2].ravel()
            wire.remove()


            # Создание данных линий для LineCollection
            wire_x1 = np.vstack([wire_x, np.roll(wire_x, 1)])
            wire_y1 = np.vstack([wire_y, np.roll(wire_y, 1)])
            wire_z1 = np.vstack([wire_z, np.roll(wire_z, 1)])
            # Убираем ложные сегменты, которые «сшивают» строки друг с другом
            to_delete = np.arange(0, nx*ny, ny)
            wire_x1 = np.delete(wire_x1, to_delete, axis=1)
            wire_y1 = np.delete(wire_y1, to_delete, axis=1)
            wire_z1 = np.delete(wire_z1, to_delete, axis=1)
            scalars = np.delete(wire_z, to_delete)

            segs = [list(zip(xl, yl, zl)) for xl, yl, zl in \
                 zip(wire_x1.T, wire_y1.T, wire_z1.T)]

            # Построение сеточной поверхности с помощью line3DCollection
            my_wire = art3d.Line3DCollection(segs, cmap=self.color_maps[color_map], 
                                             alpha=alpha, norm=norm,
                                            #  linestyles=line_type, linewidths=line_width)
                                             linestyles=line_type_str, linewidths=line_width)
            my_wire.set_array(scalars)
            graph3D = self.ax.add_collection(my_wire)

        elif graph_type == 'contour':
            graph3D = self.ax.contour3D(grid_x, grid_y, grid_z, levels=levels, linewidths=line_width,
                                        linestyles=line_type_str, alpha=alpha, cmap=self.color_maps[color_map], 
                                        norm=norm)


        elif graph_type == 'tri':
            graph3D = self.ax.plot_trisurf(x_tri, y_tri, data_z, triangles=tri.simplices, 
                                           cmap=self.color_maps[color_map], alpha=alpha,
                                           edgecolor=col, linewidth=line_width, norm=norm)


        elif graph_type == 'scatter':
            if gradient:
                graph3D = self.ax.scatter(data_x, data_y, data_z, c=data_z,
                                          cmap=self.color_maps[color_map], s=mark_size, 
                                          marker=mark_type_str, norm=norm, edgecolors=edge_col)
            else:
                self.ax.scatter(data_x, data_y, data_z, color=mark_col, s=mark_size, marker=mark_type_str, edgecolors=edge_col)
            
        

        elif graph_type == 'grid_scatter':
            graph3D = self.ax.scatter(grid_x, grid_y, grid_z, c=grid_z, cmap=self.color_maps[color_map], 
                                      s=mark_size, norm=norm)
            
        
        elif graph_type == 'line':
            line = self.ax.plot(data_x, data_y, data_z, 
                                ls=line_type_str, lw=line_width, 
                                color=col, alpha=alpha)
            
        elif graph_type == 'points':
            points = self.ax.scatter(data_x, data_y, data_z, 
                                     color=mark_col, s=mark_size, 
                                     marker=mark_type_str, edgecolors=edge_col)


        # Включение стрелок из класса Arrow3D

        if self.arrow_existence:
            self.i_arrow.remove()
            self.j_arrow.remove()
            if self.elev != 90:
                self.k_arrow.remove()

        arrow_prop_dict = dict(mutation_scale=20, arrowstyle='-|>,head_length=0.4,head_width=0.1', 
                               color='k', shrinkA=0, shrinkB=0)

        self.i_arrow = Arrow3D([self.Ox_lim[0], self.Ox_lim[1]], 
                               [self.Oy_lim[0], self.Oy_lim[0]], 
                               [self.Oz_lim[0], self.Oz_lim[0]], 
                               **arrow_prop_dict)
        if self.elev != 90:
            self.j_arrow = Arrow3D([self.Ox_lim[1], self.Ox_lim[1]], 
                                   [self.Oy_lim[0], self.Oy_lim[1]], 
                                   [self.Oz_lim[0], self.Oz_lim[0]], 
                                   **arrow_prop_dict)
        else:
            self.j_arrow = Arrow3D([self.Ox_lim[0], self.Ox_lim[0]], 
                                   [self.Oy_lim[0], self.Oy_lim[1]], 
                                   [self.Oz_lim[0], self.Oz_lim[0]], 
                                   **arrow_prop_dict)            
        self.k_arrow = Arrow3D([self.Ox_lim[1], self.Ox_lim[1]], 
                               [self.Oy_lim[1], self.Oy_lim[1]], 
                               [self.Oz_lim[0], self.Oz_lim[1]], 
                               **arrow_prop_dict)
        
        self.ax.add_artist(self.i_arrow)
        self.ax.add_artist(self.j_arrow)
        if self.elev != 90:
            self.ax.add_artist(self.k_arrow)

        self.arrow_existence = True



        
        self.conf_ticks() # Обновление делений на графике
        # if self.annot_t_f: # Автоматически включаем аннотации при выводе conf_graph, если включен флаг
        #     self.conf_annot()
        self.fig.canvas.draw() # Обновление отрисовки всего графика


    def colorbase_set(self, colorbase_t_f:bool=True, color_map:int=0, orientation:str='horizontal', 
                      z_max:float=None, z_min:float=None, z_step:float=None, precision:float=None, norm_graph:bool=True,
                      alpha:float=1,
                      font_size:int=20, 
                      save_t_f:bool=False, path=False, dpi:int=300,
                      a:float= 6, b:float = 1):
        if not colorbase_t_f:
            return()
        
        if orientation == 'horizontal':
            self.fig_cb, self.ax_cb = plt.subplots(figsize=(a, b))
            self.fig_cb.subplots_adjust(bottom=0.5)
        if orientation == 'vertical':
            self.fig_cb, self.ax_cb = plt.subplots(figsize=(b, a))
            self.fig_cb.subplots_adjust(right=0.5)
        

        if norm_graph:
            norm = Normalize(vmin=self.Oz_lim[0], vmax=self.Oz_lim[1])
        else:
            norm = Normalize(vmin=z_min, vmax=z_max)

        if precision is None:
            precision_3 = self.precision_3
        else:
            precision_3 = precision

        # Выравнивание массивов
        # z_ticks = np.arange(self.Oz_lim[0], self.Oz_lim[1], self.Oz_step)  
        # if len(z_ticks) < int(round(abs(self.Oz_lim[1] - self.Oz_lim[0]) / self.Oz_step) + 1):
        #     z_ticks = np.append(z_ticks, self.Oz_lim[1])     

        #############Правка:

        if z_max is None or z_min is None or z_step is None:
            z_min = self.Oz_lim[0]
            z_max = self.Oz_lim[1]
            z_step = self.Oz_step

        Oz_steps = math.ceil((z_max - z_min) / z_step)
        Oz_lim_ticks = (z_min, z_min + z_step * Oz_steps)
        z_ticks = np.linspace(Oz_lim_ticks[0], Oz_lim_ticks[1], 
                      round((Oz_lim_ticks[1] - Oz_lim_ticks[0]) / z_step + 1))

        

        # if z_max is not None:
        #     z_ticks = np.arange(z_min, z_max, z_step)      
        #     if len(z_ticks) < int(round(abs(z_max - z_min) / z_step) + 1):
        #         z_ticks = np.append(z_ticks, z_max)

        labels_z = self.format_tick_labels(z_ticks, precision_3)    

        cb = ColorbarBase(self.ax_cb,
                          cmap=self.color_maps[color_map],   # любая colormap
                          norm=norm,
                          orientation=orientation,  # или 'vertical'
                          ticks=z_ticks,
                          alpha=alpha
        )

        if orientation == 'horizontal':
            cb.ax.set_xticklabels(labels_z)
        else:
            cb.ax.set_yticklabels(labels_z)

        cb.ax.tick_params(labelsize=font_size)
        for label in (cb.ax.get_xticklabels() if orientation == 'horizontal' else cb.ax.get_yticklabels()):
            label.set_fontname(self.font_family)


        # === подгоняем размер ===
        self.fig_cb.canvas.draw()
        renderer = self.fig_cb.canvas.get_renderer()
        bbox = cb.ax.get_tightbbox(renderer=renderer)  # учитывает подписи!
        bbox = bbox.transformed(self.fig_cb.dpi_scale_trans.inverted())
    
        # добавляем запас вокруг (например, 20%)
        pad_w, pad_h = 0.2 * bbox.width, 0.4 * bbox.height
        self.fig_cb.set_size_inches(bbox.width + pad_w, bbox.height + pad_h)
    
        if save_t_f:
            self.fig_cb.savefig(path, dpi=dpi, bbox_inches="tight", transparent=True)


    def save(self, path, dpi:int=300):
        """Сохранение графика
        
            Args:
                path (): Путь до места сохранения графика с наименованием.
                dpi (int, optional): Разрешение графика - пикселей на дюйм. Defaults to 300.        
        """
        self.fig.savefig(path, dpi=dpi)


# import numpy as np
# from matplotlib import pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
# from matplotlib.patches import FancyArrowPatch
# from mpl_toolkits.mplot3d import proj3d

class Arrow3D(FancyArrowPatch):
    def __init__(self, xs, ys, zs, *args, **kwargs):
        super().__init__((0,0), (0,0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def do_3d_projection(self, renderer=None):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
        self.set_positions((xs[0],ys[0]),(xs[1],ys[1]))

        return np.min(zs)





            