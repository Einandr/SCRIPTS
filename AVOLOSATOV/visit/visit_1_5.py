import subprocess
import os

# import visit
import time
import numpy as np
import math

from typing import Optional, Tuple, List, Dict


from matplotlib.colors import Normalize
from matplotlib.colorbar import ColorbarBase
import matplotlib.pyplot as plt
import matplotlib.colors





class visit_py:




    def __init__(self,
                 adding:int=0, 
                 ):
        
        """Инициализация базовых настроек
        
            Args:
                adding (int, optional): Дозаписывание скрипта, пока сделано несколько косячно.. нужно использовать снаружи цикл и в adding ставить i. Defaults to 0.
                
        """
        

        self.adding = adding




    def format_tick_labels(self, values, precision:int=2):
        """Замена точек на запятые, на данный момент только для легенды

            Args:
                values (List[float]): список чисел для замены
                precision (int, optional): количесвто знаков после запятой. Defaults to 2.

            Returns:
                List[str]: список строковых переменных (числа с запятыми вместо точек)
        """


        formatted = []
        for value in values:
            if abs(value) < 1e-10:
                formatted.append("0")
            else:
                s = f"{value:.{precision}f}".replace('.', ',')
                formatted.append(s)
        return formatted



    def colorbase_set(self, colorbase_t_f:bool=True, orientation:str='horizontal', 
                      z_max:float=None, z_min:float=None, z_step:float=None, precision:float=0,
                      font_size:int=20, font_family:str="Times New Roman", 
                      save_t_f:bool=False, path:str='', dpi:int=300,
                      a:float= 6, b:float = 1,
                      labels_z:List[str]=None):
        """Для сохранения картинки легенды отдельно (цветовая легенда как в visit)

            Args:
                colorbase_t_f (bool, optional): Включение отображения цветовой легенды. Defaults to True.
                orientation (str, optional): Положение легенды - вертикальное/горизонтальное ('vertical'/'horizontal'). Defaults to 'horizontal'.
                z_max (float, optional): Максимальное значение для легенды. Defaults to None.
                z_min (float, optional): Минимальное значение для легенды. Defaults to None.
                z_step (float, optional): Шаг меток. Defaults to None.
                precision (float, optional): Количество знаков после запятой. Defaults to 0.
                font_size (int, optional): Размер шрифта. Defaults to 20.
                font_family (str, optional): Семейство шрифта. Defaults to "Times New Roman".
                save_t_f (bool, optional): Включения сохранения в файл. Defaults to False.
                path (str, optional): Путь с наименованием картинки. Defaults to False.
                dpi (int, optional): Количество пикселей на дюйм. Defaults to 300.
                a (float, optional): Длина картинки. Defaults to 6.
                b (float, optional): Ширина картинки. Defaults to 1.
        """



        if not colorbase_t_f:
            return()

        if orientation == 'horizontal':
            fig_cb, ax_cb = plt.subplots(figsize=(a, b))
            fig_cb.subplots_adjust(bottom=0.5)
        if orientation == 'vertical':
            fig_cb, ax_cb = plt.subplots(figsize=(b, a))
            fig_cb.subplots_adjust(right=0.5)

        norm = Normalize(vmin=z_min, vmax=z_max)

        z_ticks = np.arange(z_min, z_max, z_step)
        if len(z_ticks) < int(round(abs(z_max - z_min) / z_step) + 1):
            z_ticks = np.append(z_ticks, z_max)

        print(z_ticks)
        
        if labels_z is None:
            labels_z = self.format_tick_labels(z_ticks, precision)

        colors = [(0, 0, 1),    # ярко-синий
                  (0, 1, 1),    # голубой
                  (0, 1, 0),    # зелёный
                  (1, 1, 0),    # жёлтый
                  (1, 0, 0)]    # ярко-красный

        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("rainbow_custom", colors)
        cb = ColorbarBase(ax_cb, cmap=cmap, norm=norm, orientation=orientation, ticks=z_ticks)

        if orientation == 'horizontal':
            cb.ax.set_xticklabels(labels_z)
        else:
            cb.ax.set_yticklabels(labels_z)

        cb.ax.tick_params(labelsize=font_size)
        for label in (cb.ax.get_xticklabels() if orientation == 'horizontal' else cb.ax.get_yticklabels()):
            label.set_fontname(font_family)

        fig_cb.canvas.draw()
        renderer = fig_cb.canvas.get_renderer()
        bbox = cb.ax.get_tightbbox(renderer=renderer)
        bbox = bbox.transformed(fig_cb.dpi_scale_trans.inverted())

        pad_w, pad_h = 0.2 * bbox.width, 0.4 * bbox.height
        fig_cb.set_size_inches(bbox.width + pad_w, bbox.height + pad_h)

        if save_t_f:
           fig_cb.savefig(path, dpi=dpi, bbox_inches="tight", transparent=True)



    def creating_script_file(self,
                             visit_wp:str="", data_wp:str="", script_wp:str="", script_name:str='visit_script.py', result_wp:str="",
                             variables:List[str]=['3D/FLUID/mesh', '3D/FLUID/pressure', '3D/FLUID/density'], 
                             extra_variables:Dict[str,str]={},
                             database:bool=False):

        """Создание файла скрипта с записью импорта библиотек и функций, открытием файла результатов и вычислением габаритных размеров расчетной области

            Args:
                visit_wp (str, optional): Путь до visit.exe.  Defaults to ""
                data_wp (str, optional): Путь до файлов данных. Defaults to "".
                result_wp (str, optional): Путь до файлов обработанных результатов. Defaults to "".
                script_wp (str, optional): Установка пути для создаваемого скрипта. Defaults to "".
                script_name (str, optional): Наименование скрипта. Defaults to "test_2.py".
                variables (List[str], optional): Массив переменных, первое значение - сетка. Defaults to ['3D/FLUID/mesh', '3D/FLUID/pressure'].
                adding (int, optional): Дозаписывание скрипта, пока сделано несколько косячно.. нужно использовать снаружи цикл и в adding ставить i. Defaults to 0.
                database (bool, optional): Открытие всех silo-файлов в папке. Defaults to False.
                

                data_wp: открытие одного файла - просто name_123.root; открытие всех файлов - name_*.root
        """

        self.visit_wp = visit_wp
        self.data_wp = data_wp
        self.result_wp = result_wp
        self.script_wp = script_wp
        self.script_name = script_name

        self.database = database

        self.variables = variables
        self.extra_variables = extra_variables



        if self.adding == 0:
            with open(os.path.join(self.script_wp, self.script_name), 'w', encoding='utf-8') as self.file:
                self.file.write("""import os\nimport visit\nimport time\nimport numpy as np\nimport math\n""" +
                                """\n""" * 3)
            self.adding += 1
        
        else:
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""\n""" * 3 +
                                r"""print('\n\n\n\n\n----processing a new file----\n\n\n\n\n')""" +
                                """\n""" * 3)
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""import os\nimport visit\nimport time\nimport numpy as np\nimport math\n""" +
                                """\n""" * 3)
                

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write("""def nice_limits(data_min:float, data_max:float, n_ticks:int=5):\n""" + 
                            """   data_range = data_max - data_min\n""" +
                            """   if data_range == 0:\n""" +
                            """      data_min = data_min - data_min * 0.05\n""" +
                            """      data_max = data_max + data_max * 0.05\n""" +
                            """      data_range = data_max - data_min\n\n\n""" +
                            """   raw_step = data_range / n_ticks\n""" +
                            """   order = 10 ** math.floor(math.log10(raw_step))\n""" +
                            """   step_candidates = [1, 2, 2.5, 5, 10]\n""" +
                            """   step = min(step_candidates, key=lambda s: abs(raw_step - s * order))\n""" +
                            """   step *= order\n\n""" +
                            """   decimals = max (0, -int(math.floor(math.log10(step))) + 2)\n""" +
                            """   step = round(step, decimals)\n\n""" +
                            """   new_min = round(math.floor(data_min / step) * step, decimals)\n""" +
                            """   new_max = round(math.ceil(data_max / step) * step, decimals)\n\n""" +
                            """   return new_min, new_max, step\n""" +
                            """\n""" * 4)


        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write("""def format_tick_labels(values, precision:int=2):\n\n""" +
                            """   formatted = []\n""" +
                            """   for value in values:\n""" +
                            """      if abs(value) < 1e-10:\n""" +
                            """         formatted.append("0")\n""" +
                            """      else:\n""" +
                            r"""         s = f"{value:.{precision}f}".replace('.', ',')""" +
                            """\n""" +
                            """         formatted.append(s)\n""" +
                            """   return formatted\n""" +
                            """\n""" * 4)

        if database:
            line_opening_DB = f"""visit.OpenDatabase(r'{self.data_wp}' + ' database')\n"""
            if False:
                line_opening_DB = f"""visit.OpenDatabase(r'{os.path.join(self.script_wp, self.script_name)}' + ' database')\n"""
        else:
            line_opening_DB = f"""visit.OpenDatabase(r'{self.data_wp}')\n"""
            if False:
                line_opening_DB = f"""visit.OpenDatabase(r'{os.path.join(self.script_wp, self.script_name)}')\n"""

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""parameter = '{self.variables[0]}'\n""" +
                            line_opening_DB + # Открываем файл с результатами
                            """visit.AddPlot('Mesh', parameter)\n""" + # Добавляем поле (Pseudocolor для переменной 'density')
                            """visit.DrawPlots()\n""" + # Отрисовываем
                            """\n""" * 3 +

                            """temp = visit.Query('SpatialExtents')\n""" + # Получаем границы расчетной области
                            """start = temp.find('(')\nend = temp.find(')')\n""" + # Находим начало и конец кортежа
                            """tuple_str = temp[start+1:end]\n""" + # Вырезаем содержимое скобок
                            """boundaries = [float(x.split("=")[-1].strip()) for x in tuple_str.split(",")]\n""" + 
                            """x_min, x_max = boundaries[0], boundaries[1]\ny_min, y_max = boundaries[2], boundaries[3]\nz_min, z_max = boundaries[4], boundaries[5]\n""" +
                            r"""print(f'x_min = {x_min}, x_max = {x_max},\ny_min = {y_min}, y_max = {y_max},\nz_min = {z_min}, z_max = {z_max},\n')""" +
                            """\n""" * 2 + 
                            """num_files = visit.TimeSliderGetNStates()\n""" +
                            """visit.TimeSliderSetState(num_files - 1)\n""" + 
                            r"""print(f'num_files = {num_files}')""" +
                            """\n""" * 2 +
                            """visit.DeleteActivePlots()""" + 
                            """\n""" * 4)
    

        if extra_variables:
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                for key, value in extra_variables.items():
                    self.file.write(f"""visit.DefineScalarExpression("{key}", "{value}")\n""")
                
                self.file.write(f"""\n""" * 4)

            for key in extra_variables.keys():
                variables.append(key)

        self.variables = variables

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""variables = {self.variables}"""+ 
                            """\n""" * 4)
        
        self.file.close()



    def time_set(self, i:Optional[int]=None):
        
        if not self.database or i is None:
            return()
        
        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""\n\nvisit.TimeSliderSetState({i})\n\n""")


    def cross_sectional_avereging(self,
                                  norm:Tuple[float, float, float]=(1.0, 0.0, 0.0),
                                  c_min:Optional[float]=None, c_max:Optional[float]=None,
                                  num_slices:int=21, type:str='Point',
                                  result_file:str='cross_sectional_avereging.csv'):
        """Для сохранения распределения средних по сечениям параметров вдоль прямой

            Args:
                norm (Tuple[float, float, float], optional): Вектор нормали к поверхности сечения. Defaults to (1.0, 0.0, 0.0).
                c_min (Optional[float], optional): Начало линии для срезов (по умолчанию вычисляется из габаритов области). Defaults to None.
                c_max (Optional[float], optional): Конец линии для срезов (по умолчанию вычисляется из габаритов области). Defaults to None.
                num_slices (int, optional): Число срезов. Defaults to 21.
                type (str, optional): Тип срезов. Defaults to 'Point'.
                result_file (str, optional): Имя файла результатов. Defaults to 'cross_sectional_avereging.csv'.
        """

        
        if abs(norm[0]) == 1.0:
            if c_min is None and c_max is None:
                with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    """c_min = x_min + abs(x_min * 0.001)\n""" + 
                                    """c_max = x_max * 0.99999\n""")
        elif abs(norm[1]) == 1.0:
            if c_min is None and c_max is None:
                with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    """c_min = y_min + abs(y_min * 0.001)\n""" + 
                                    """c_max = y_max * 0.99999\n""")
        elif abs(norm[2]) == 1.0:
            if c_min is None and c_max is None:
                with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    """c_min = z_min + abs(z_min * 0.001)\n""" + 
                                    """c_max = z_max * 0.99999\n""")
        
        if c_min is not None and c_max is not None:
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    f"""c_min = {c_min}\n""" + 
                                    f"""c_max = {c_max}\n""")       
        

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""num_slices = {num_slices}\n""" +  
                            """positions = np.linspace(c_min, c_max, num_slices)\n""" + 
                            f"""norm = {list(norm)}\n""" + 
                            f"""type = '{type}'""" +
                            """\n""" * 4)
            
        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""num_var = {len(self.variables) - 1 + 1}\n""" +
                            """temp_arr = [[] for _ in range(num_var)]\n""" + 
                            """temp_arr[0].extend(positions.tolist())""" +
                            """\n""" * 4)

        for i in range(1, len(self.variables)):
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write(f"""parameter = variables[{i}]\n""" +
                                f"""visit.AddPlot("Pseudocolor", parameter)\n""" +
                                """visit.DrawPlots()\n""" + 
                                """visit.AddOperator("Slice")\n""" +
                                """\n""" * 2 + 
                                """for i, coor in enumerate(positions):\n""" + 
                                """   slice_op = visit.SliceAttributes()\n""" +
                                """   if type == "Point":\n""" +
                                """      slice_op.originType = slice_op.Point\n""" +
                                """      slice_op.originPoint = [x * coor for x in norm]\n""" +
                                """   elif type == "Percent":\n""" +
                                """      slice_op.originType = slice_op.Percent\n""" +
                                """      slice_op.originPercent = coor\n""" +
                                """   slice_op.normal = norm\n""" +
                                """   visit.SetOperatorOptions(slice_op)\n""" +
                                """   visit.DrawPlots()\n""" +
                                """\n""" * 2 +

                                """   visit.Query("Average Value")\n""" +
                                """   avg_var = visit.GetQueryOutputValue()\n""" +
                                r"""   print(f'coor = {coor}, {parameter.split("/")[-1]} = {avg_var}')""" +
                                """\n"""
                                f"""   temp_arr[{i}].append(avg_var)\n\n""" +
                                """visit.DeleteActivePlots()\n""" +
                                """\n""" * 4
                                )

        

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "w") as file:\n""" + 
                            """   file.write('coor')\n""" +
                            """   for i in variables[1:]:\n""" +
                            """      file.write(f' {i.split("/")[-1]}')\n""" + 
                            r"""   file.write('\n')""" +
                            """\n""" * 2)
            
            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "a") as file:\n""" +
                            """   for j in range(len(temp_arr[0])):\n""" +
                            """      for i in temp_arr:\n""" + 
                            r"""         file.write(f'{i[j]} ')""" + 
                            """\n""" +
                            r"""      file.write('\n')""" + 
                            """\nfile.close()\n""" +
                            """\n""" * 4)

        self.file.close()


    def pick(self,
             X_data:List[float]=[0, 1], Y_data:List[float]=[0, 1], Z_data:List[float]=[0, 1],
             result_file:str='pick.csv'):
        """Для выборки данных по списку точек, длины списков должны быть одинаковыми.

            Args:
                X_data (List[float], optional): Список координат по оси X. Defaults to [0, 1].
                Y_data (List[float], optional): Список координат по оси Y. Defaults to [0, 1].
                Z_data (List[float], optional): Список координат по оси Z. Defaults to [0, 1].
                result_file (str, optional): Имя файла результатов. Defaults to 'pick.csv'.
        """
        



        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""X_points = {X_data.tolist()}\n""" +
                            f"""Y_points = {Y_data.tolist()}\n""" +
                            f"""Z_points = {Z_data.tolist()}\n""" +
                            """\n""" * 4)


        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""num_var = {len(self.variables) - 1 + 3}\n""" +
                            """temp_arr = [[] for _ in range(num_var)]\n""" + 
                            """temp_arr[0].extend(X_points)\n""" +
                            """temp_arr[1].extend(Y_points)\n""" +
                            """temp_arr[2].extend(Z_points)\n""" +
                            """\n""" * 4)


        for i in range(1, len(self.variables)):
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write(f"""parameter = variables[{i}]\n""" +
                                    f"""visit.AddPlot("Pseudocolor", parameter)\n""" +
                                    """visit.DrawPlots()\n""" + 
                                    """for i in range(len(X_points)):\n""" + 
                                    """   visit.Pick((X_points[i], Y_points[i], Z_points[i]))\n""" + 
                                    """   pick = float(visit.GetPickOutput().split('=')[-1])\n""" +
                                    r"""   print(f'{parameter.split("/")[-1]} = {pick}')""" +
                                    """\n""" * 2 + 
                                    f"""   temp_arr[{i + 2}].append(pick)\n\n""" +
                                    """visit.DeleteActivePlots()\n""" +
                                    """\n""" * 4)

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "w") as file:\n""" + 
                            """   file.write('x y z')\n""" +
                            """   for i in variables[1:]:\n""" +
                            """      file.write(f' {i.split("/")[-1]}')\n""" + 
                            r"""   file.write('\n')""" +
                            """\n""" * 2)
            
            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "a") as file:\n""" +
                            """   for j in range(len(temp_arr[0])):\n""" +
                            """      for i in temp_arr:\n""" + 
                            r"""         file.write(f'{i[j]} ')""" + 
                            """\n""" +
                            r"""      file.write('\n')""" + 
                            """\nfile.close()\n""" +
                            """\n""" * 4)

        self.file.close()


    def lineout(self,
                X_data:List[float]=[0, 1], Y_data:List[float]=[0, 1], Z_data:List[float]=[0, 1], num_points:int=100,
                result_file:str='lineout.csv',
                centering:int=0):
        """Для выборки данных по линии, длины списков должны быть одинаковыми.

            Args:
                X_data (List[float], optional): Начало и конец линии по оси X. Defaults to [0, 1].
                Y_data (List[float], optional): Начало и конец линии по оси Y. Defaults to [0, 1].
                Z_data (List[float], optional): Начало и конец линии по оси Z. Defaults to [0, 1].
                num_points (int, optional): Количество точек на линии. Defaults to 100.
                result_file (str, optional): Имя файла результатов. Defaults to 'lineout.csv'.
                centering (int, optional): Способ построения поля - Natural - 0, Nodal - 1, Zonal - 2. Defaults to Natural.
        """

        L_line = math.sqrt((X_data[1] - X_data[0]) ** 2 + (Y_data[1] - Y_data[0]) ** 2 + (Z_data[1] - Z_data[0]) ** 2)

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""Idx_points = range(0, {num_points + 1})\n""" +
                            f"""X_points = np.linspace({X_data[0]}, {X_data[1]}, {num_points + 1})\n""" +
                            f"""Y_points = np.linspace({Y_data[0]}, {Y_data[1]}, {num_points + 1})\n""" +
                            f"""Z_points = np.linspace({Z_data[0]}, {Z_data[1]}, {num_points + 1})\n""" +
                            f"""L_points = np.linspace({0}, {L_line}, {num_points + 1})\n""" +
                            """\n""" * 4)



            self.file.write(f"""num_var = {len(self.variables) - 1 + 5}\n""" +
                            """temp_arr = [[] for _ in range(num_var)]\n""" + 
                            """temp_arr[0].extend(Idx_points)\n""" +
                            """temp_arr[1].extend(X_points)\n""" +
                            """temp_arr[2].extend(Y_points)\n""" +
                            """temp_arr[3].extend(Z_points)\n""" +
                            """temp_arr[4].extend(L_points)\n""" +
                            """\n""" * 4)
            
            self.file.write("""temp_lineout_arr = [[] for _ in range(2)]\n""" + 
                            """\n""" * 2)

        for i in range(1, len(self.variables)):
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write(f"""parameter = variables[{i}]\n""" +
                                    f"""visit.AddPlot("Pseudocolor", parameter)\n""" +
                                    """visit.DrawPlots()\n""" + 
                                    """p = visit.PseudocolorAttributes()\n""" +
                                    f"""p.centering = {centering}\n""" +
                                    """LineAtts = visit.LineoutAttributes()\n""" +
                                    f"""visit.Lineout(({X_data[0]}, {Y_data[0]}, {Z_data[0]}), ({X_data[1]}, {Y_data[1]}, {Z_data[1]}), {num_points})\n""" + 
                                    """visit.SetActiveWindow(2)\n""" +
                                    """info = visit.GetPlotInformation()\n""" +
                                    """lineout = info["Curve"]\n""" +
                                    """print(lineout[1::2])\n\n\n""" + 


                                    ###temp
                                    """temp_visit_arr = [[], []]\n"""+
                                    f"""idx_visit = [int(round(x / {L_line} * {num_points})) for x in lineout[0::2]] \n""" +
                                    # """temp_visit_arr[0].extend(idx_visit)\n""" +
                                    # """temp_visit_arr[1].extend(lineout[1::2])\n""" +
                                    f"""for i in range({num_points} + 1):\n""" +
                                    """   if i in idx_visit:\n""" +
                                    """      pos = idx_visit.index(i)\n""" +
                                    """      temp_visit_arr[0].append(i)\n""" +
                                    """      temp_visit_arr[1].append(lineout[1::2][pos])\n""" +
                                    """   else:\n""" +
                                    """      temp_visit_arr[0].append(i)\n""" +
                                    """      temp_visit_arr[1].append(None)\n""" +

                                    """print(temp_visit_arr)\n\n\n""" + 


                                    ###temp
                                    f"""temp_arr[{i + 4}].extend(temp_visit_arr[1])\n""" +
                                    """visit.DeleteWindow()\n""" +
                                    """visit.SetActiveWindow(1)\n""" +
                                    """visit.DeleteActivePlots()\n""" +
                                    """\n""" * 4)

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "w") as file:\n""" + 
                            """   file.write('idx x y z l')\n""" +
                            """   for i in variables[1:]:\n""" +
                            """      file.write(f' {i.split("/")[-1]}')\n""" + 
                            r"""   file.write('\n')""" +
                            """\n""" * 2)
            
            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "a") as file:\n""" +
                            """   for j in range(len(temp_arr[0])):\n""" +
                            """      for i in temp_arr:\n""" + 
                            r"""         file.write(f'{i[j]} ')""" + 
                            """\n""" +
                            r"""      file.write('\n')""" + 
                            """\nfile.close()\n""" +
                            """\n""" * 4)

        self.file.close()



    def pseudocolor_slice(self, 
                          point:Tuple[float, float, float]=(0.0, 0.0, 0.0),
                          norm:Tuple[float, float, float]=(0.0, -1.0, 0.0),
                          upaxis:Tuple[float, float, float]=None,
                          angle:Tuple[float, float]=None,
                          geom_size:Tuple[float, float]=(0.1, 0.1),
                          pixels:float=1000,
                          result_file:str='pseudocolor_slice',
                          axis_t_f:bool=False, legend_t_f:bool=False, auto_minmax_t_f:bool=True,
                          l_min:List[float]=None, l_max:List[float]=None, l_num_ticks:List[float]=None,
                          space:Tuple[float, float, float, float]=(0.1, 0.9, 0.1, 0.9),
                          font_scale:float=2,
                          ticks_spacing_x:Tuple[float, float, float]=None, ticks_spacing_y:Tuple[float, float, float]=None,
                          autoSetScaling:int=0, x_scale:float=-3, y_scale:float=-3,
                          line_width:int=2,
                          centering:int=0):#str='Natural'):
        """Для построения pseudocolor

            Args:
                point (Tuple[float, float, float], optional): Опорная точка для построения сечения. Defaults to (0.0, 0.0, 0.0).
                norm (Tuple[float, float, float], optional): Вектор нормали к плоскости сечения. Defaults to (0.0, -1.0, 0.0).
                upaxis (Tuple[float, float, float], optional): Вектор нормали к плоскости вида (по умолчанию равен вектору нормали к плоскости сечения). Defaults to None.
                angle (Tuple[float, float], optional): Два угла для альтернативного выставления вектора нормали в градусах. Defaults to None.
                geom_size (Tuple[float, float], optional): Ориентировочные габаритные размеры расчетной области в сечении в метрах для выбора соотношения сторон картинки. Defaults to (0.1, 0.1).
                pixels (float, optional): Количество пикселей на дюйм картинки. Defaults to 1000.
                result_file (str, optional): Имя файла результатов. Defaults to 'pseudocolor_slice'.
                axis_t_f (bool, optional): Включение отрисовки осей. Defaults to False.
                legend_t_f (bool, optional): Включение отрисовки легенды. Defaults to False.
                auto_minmax_t_f (bool, optional): Включение автоопределения минимального и максимального значений (окургление до адекватных чисел) на легенде. Defaults to False.
                l_min (List[float], optional): Список минимальных значений для pseudocolor, количество значений должно соответствовать количеству переменных. Defaults to None.
                l_max (List[float], optional): Список максимальных значений для pseudocolor, количество значений должно соответствовать количеству переменных. Defaults to None.
                space (Tuple[float, float, float, float], optional): Список отступов (белых полей) - слева, справа, снизу, сверху. Defaults to (0.1, 0.9, 0.1, 0.9).
                font_scale (float, optional): Масштаб меток на осях. Defaults to 2.       
                ticks_spacing_x (Tuple[float, float, float], optional): Параметры меток на оси X - минимальное значение, максимальное, шаг. При значении None - автоопределение. Defaults to None.        
                ticks_spacing_y (Tuple[float, float, float], optional): Параметры меток на оси Y - минимальное значение, максимальное, шаг. При значении None - автоопределение. Defaults to None. 
                autoSetScaling (int, optional): авто масштабирование значений осей. Defaults to 0.
                x_scale (float, optional): масштабирование по x. Defaults to 0.
                y_scale (float, optional): масштабирование по y. Defaults to 0.
                line_width (int, optional): Ширина линии осей и меток. Defaults to 2.
                centering (int, optional): Способ построения поля - Natural - 0, Nodal - 1, Zonal - 2. Defaults to Natural.
        """

        if angle:
            angle = [math.radians(angle[0]), math.radians(angle[1])]

            norm = (round(-math.sin(angle[0]) * math.cos(angle[1]), 8),
                    round(math.cos(angle[0]) * math.cos(angle[1]), 8),
                    round(math.sin(angle[1]), 8))


        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write(f"""\n\nprint('norm = ' + '{norm}')\n\n\n""")


        if upaxis is None:
            upaxis = norm

        if auto_minmax_t_f:
            line_minflag = """p.minFlag = 1\n"""
            line_maxflag = """p.maxFlag = 1\n"""
        else:
            line_minflag = """p.minFlag = 0\n"""
            line_maxflag = """p.maxFlag = 0\n"""
        
        # if l_min is not None and l_max is not None:
        #     line_min = f"""p.min = {l_min}\n"""
        #     line_max = f"""p.max = {l_max}\n"""
        # else:
        #     line_min = """p.min = new_min\n"""
        #     line_max = """p.max = new_max\n"""


        if legend_t_f:
            line_1 = """annot.legendInfoFlag = 1        # легенды\n"""
        else:
            line_1 = """annot.legendInfoFlag = 0        # легенды\n"""

        if axis_t_f:
            line_2 = """annot.axes2D.visible = 1\n"""
        else:
            line_2 = """annot.axes2D.visible = 0\n"""

    
        if ticks_spacing_x is None or ticks_spacing_y is None:
            line_3 = """annot.axes2D.autoSetTicks = 1\n"""
            ticks_spacing_x = (-1, 1, 0.5)
            ticks_spacing_y = (-1, 1, 0.5)
        else:
            line_3 = """annot.axes2D.autoSetTicks = 0\n"""

        

        for i in range(1, len(self.variables)):
            

            if l_min is not None and l_max is not None:
                line_minmax = f"""new_min, new_max = {l_min[i-1]}, {l_max[i-1]}\n"""
            else:
                line_minmax = ""

            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write(f"""parameter = variables[{i}]\n""" +
                                f"""visit.AddPlot("Pseudocolor", parameter)\n""" +
                                """visit.DrawPlots()\n""" + 
                                """\n""" * 2 +
                                """temp = visit.Query("Min",limitsMode=1).split(' ')\n""" +
                                """pseudo_min = float(temp[temp.index('=') + 1])\n""" +
                                r"""print(f'min = {pseudo_min}')""" +
                                """\n""" +
                                """temp = visit.Query("Max", limitsMode=1).split(' ')\n""" +
                                """pseudo_max = float(temp[temp.index('=') + 1])\n""" +
                                r"""print(f'max = {pseudo_max}')""" +
                                """\n""" * 2)
                
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""a = nice_limits(pseudo_min, pseudo_max)\n""" +
                                """print(a)\n"""+
                                """new_min, new_max, new_step = a[0], a[1], a[2]\n""" +
                                line_minmax +
                                """\n""" * 2 +
                                """p = visit.PseudocolorAttributes()\n""" +
                                f"""p.centering = {centering}\n""" +
                                line_minflag +
                                line_maxflag +
                                """p.min = new_min\n""" +
                                """p.max = new_max\n""" +
                                r"""print(f'new_min = {new_min}')""" +
                                """\n""" +
                                r"""print(f'new_max = {new_max}')""" +
                                """\n\nvisit.SetPlotOptions(p)\n""" +
                                """visit.DrawPlots()\n""" +
                                """\n""" * 3)



            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""visit.AddOperator("Slice")\n""" +
                                """s = visit.SliceAttributes()\n""" +
                                """s.project2d = 1\n""" +
                                f"""s.originPoint = {point}\n""" + 
                                """s.originType=s.Point\n""" + 
                                f"""s.normal = {norm}\n""" +
                                f"""s.upAxis = {upaxis}\n""" +
                                """visit.SetOperatorOptions(s)\n""" +
                                """visit.DrawPlots()\n""" +
                                """visit.ResetView()\n""" +
                                """\n""" * 2)
            
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""annot = visit.AnnotationAttributes()\n"""+
                                """annot.userInfoFlag = 0          # имя пользователя / хост\n""" +
                                """annot.databaseInfoFlag = 0      # путь к базе\n""" +
                                """annot.timeInfoFlag = 0          # время/шаг\n""" +
                                line_1 +    
                                f"""annot.axes2D.lineWidth = {line_width}\n""" +
                                """\n""" * 2 +                          
                                """annot.axes2D.xAxis.label.scaling = 0\n""" +
                                """annot.axes2D.xAxis.label.font.font = annot.axes2D.xAxis.label.font.Times\n""" +
                                """annot.axes2D.xAxis.label.font.bold = 0\n""" +
                                """annot.axes2D.xAxis.label.font.italic = 0\n""" +
                                f"""annot.axes2D.xAxis.label.font.scale = {font_scale}\n""" +
                                f"""annot.axes2D.xAxis.tickMarks.minorSpacing = {ticks_spacing_x[2] / 5}\n""" +
                                f"""annot.axes2D.xAxis.tickMarks.majorSpacing = {ticks_spacing_x[2]}\n""" +
                                f"""annot.axes2D.xAxis.tickMarks.majorMinimum = {ticks_spacing_x[0]}\n""" +
                                f"""annot.axes2D.xAxis.tickMarks.majorMaximum = {ticks_spacing_x[1]}\n""" +
                                """annot.axes2D.xAxis.title.visible = 0\n""" +   
                                f"""annot.axes2D.xAxis.label.scaling = {x_scale}\n""" +
                                """\n""" * 2 +                               
                                """annot.axes2D.yAxis.label.font.font = annot.axes2D.yAxis.label.font.Times\n""" +
                                """annot.axes2D.yAxis.label.font.bold = 0\n""" +
                                """annot.axes2D.yAxis.label.font.italic = 0\n""" +
                                f"""annot.axes2D.yAxis.label.font.scale = {font_scale}\n""" +
                                f"""annot.axes2D.yAxis.tickMarks.minorSpacing = {ticks_spacing_y[2] / 5}\n""" +
                                f"""annot.axes2D.yAxis.tickMarks.majorSpacing = {ticks_spacing_y[2]}\n""" +
                                f"""annot.axes2D.yAxis.tickMarks.majorMinimum = {ticks_spacing_y[0]}\n""" +
                                f"""annot.axes2D.yAxis.tickMarks.majorMaximum = {ticks_spacing_y[1]}\n""" +
                                """annot.axes2D.yAxis.title.visible = 0\n""" +
                                f"""annot.axes2D.yAxis.label.scaling = {y_scale}\n""" +
                                """\n""" * 2 +    
                                line_2 +
                                line_3 +
                                f"""annot.axes2D.autoSetScaling = {autoSetScaling}\n""" +
                                """annot.axes3D.visible = 0\n""" +
                                """annot.axesArray.visible = 0\n""" +
                                """annot.axes3D.triadFlag = 0             # убираем оси в углу\n""" +
                                """annot.axes3D.bboxFlag = 0             # убираем рамку вокруг области\n""" +
                                """annot.backgroundMode = annot.Solid\n""" +
                                """annot.foregroundColor = (0, 0, 0, 255)\n""" +
                                """annot.backgroundColor = (255, 255, 255, 255)  # фон белый (или прозрачный)\n""" +
                                """visit.SetAnnotationAttributes(annot)\n""" +
                                """visit.SetViewExtentsType("actual")\n""" +
                                """visit.ResetView()\n""" +
                                """\n""" * 2)

            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""v2d = visit.GetView2D()\n""" +
                                f"""v2d.viewportCoords = {space}\n""" +
                                """visit.SetView2D(v2d)\n""" +
                                """visit.DrawPlots()\n\n""")

            temp_file_name = result_file + self.variables[i].split("/")[-1] + "_"

            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""sw = visit.SaveWindowAttributes()\n""" +
                                f"""#sw.outputDirectory = r'{self.result_wp}'\n""" +
                                f"""sw.fileName = r'{os.path.join(self.result_wp, temp_file_name)}'\n""" + 
                                # """sw.family = 0\n""" +
                                """sw.format = sw.PNG\n""" +
                                f"""pixels = {pixels}\n""" +
                                f"""sw.width = int(pixels * {geom_size[0]} * ({space[3] - space[2]}))\n""" +
                                f"""sw.height = int(pixels * {geom_size[1]} * ({space[1] - space[0]}))\n""" +
                                """sw.resConstraint = sw.NoConstraint\n""" +
                                """visit.SetSaveWindowAttributes(sw)\n""" +
                                """visit.SaveWindow()\n""" +
                                """\n""" * 4)
                
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                self.file.write("""visit.DeleteActivePlots()\n\n\n""")

            
            # Настройка камеры
            # with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            #     self.file.write(f"""v3d = visit.GetView3D()\n""" +
            #                     f"""v3d.viewNormal = {norm}\n""" +
            #                     """v3d.focus = ((x_max + x_min) / 2, (y_max + y_min) / 2, (z_max + z_min) / 2)\n""")



        self.file.close()


    def mass_flow_rate_convergence(self,
                                  norm:Tuple[float, float, float]=(1.0, 0.0, 0.0),
                                  c_min:Optional[float] = None, c_max:Optional[float] = None,
                                  type:str='Point', mr_variables:List=['/ALL/density', '/ALL/velocity_x'],
                                  result_file:str='mass_flow_rate_convergence.csv'):

        num_slices=2

        """Для сохранения сходимости по массовому расходу

            Args:
                norm (Tuple[float, float, float], optional): Вектор нормали к поверхности сечения. Defaults to (1.0, 0.0, 0.0).
                c_min (Optional[float], optional): Начало расчетной области (по умолчанию вычисляется из габаритов области). Defaults to None.
                c_max (Optional[float], optional): Конец расчетной области (по умолчанию вычисляется из габаритов области). Defaults to None.
                type (str, optional): Тип срезов. Defaults to 'Point'.
                result_file (str, optional): Имя файла результатов. Defaults to 'mass_flow_rate_convergence.csv'.
        """



        self.file.close()


        if abs(norm[0]) == 1.0:
            if c_min is None and c_max is None:
                with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    """c_min = x_min + abs(x_min * 0.001)\n""" + 
                                    """c_max = x_max * 0.999\n""")
        elif abs(norm[1]) == 1.0:
            if c_min is None and c_max is None:
                with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    """c_min = y_min + abs(y_min * 0.001)\n""" + 
                                    """c_max = y_max * 0.999\n""")
        elif abs(norm[2]) == 1.0:
            if c_min is None and c_max is None:
                with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    """c_min = z_min + abs(z_min * 0.001)\n""" + 
                                    """c_max = z_max * 0.999\n""")
        
        if c_min is not None and c_max is not None:
            with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
                    self.file.write("""\n""" * 4 + 
                                    f"""c_min = {c_min}\n""" + 
                                    f"""c_max = {c_max}\n""")       

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""num_slices = {num_slices}\n""" +  
                            """positions = np.linspace(c_min, c_max, num_slices)\n""" + 
                            """file_steps = np.linspace(0, num_files - 1, num_files)\n""" + 
                            f"""norm = {list(norm)}\n""" + 
                            f"""type = '{type}'""" +
                            """\n""" * 4)

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""num_var = {len(self.variables) - 1 + 1}\n""" +
                            """temp_arr = [[] for _ in range(3)]\n""" + 
                            """temp_arr[0].extend(file_steps.tolist())""" +
                            """\n""" * 4)



        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""visit.DefineScalarExpression("mass_rate", "<{mr_variables[0]}> * <{mr_variables[1]}>")\n""" +
                            """visit.AddPlot("Pseudocolor", "mass_rate")\n""" + 
                            """visit.DrawPlots()\n""" +
                            """visit.AddOperator("Slice")\n\n\n""")
            
        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""for i in range(num_files):\n""" +
                            """   visit.TimeSliderSetState(i)\n""" + 
                            """\n""" * 2 + 
                            """   delta = []\n""" +
                            """   for coor in [c_min, c_max]:\n"""
                            """      slice_op = visit.SliceAttributes()\n""" +
                            """      slice_op.originType = slice_op.Point\n""" +
                            """      slice_op.originPoint = [x * coor for x in norm]\n""" +
                            """      slice_op.normal = norm\n""" +
                            """      visit.SetOperatorOptions(slice_op)\n""" +
                            """      visit.DrawPlots()\n""" +
                            """\n""" * 2 +
                            """      visit.Query("Weighted Variable Sum")\n""" +
                            """      WVS_var = visit.GetQueryOutputValue()\n""" +
                            r"""      print(f'coor = {coor}, mass_rate = {WVS_var}')""" +
                            """\n""" +
                            """      delta.append(WVS_var)\n""" +
                            """\n""" +
                            """   if delta[0] == delta[1] or delta[0] == 0:\n""" +
                            """      delta_WVS = 0\n""" +
                            """   else:\n""" +
                            """      delta_WVS = abs(delta[1] - delta[0]) / delta[0] * 100\n""" +
                            r"""      print(f'time = {i}, delta_WVS = {delta_WVS}')""" +
                            """\n""" * 2 +
                            """   visit.Query("Time")\n""" +
                            """   time_i = visit.GetQueryOutputValue()\n\n""" +
                            """   temp_arr[1].append(time_i)\n""" +
                            """   temp_arr[2].append(delta_WVS)\n""" +
                            """visit.DeleteActivePlots()\n""" +
                            """\n""" * 4)
            
        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "w") as file:\n""" + 
                            """   file.write('file_num time mfr')\n""" +
                            r"""   file.write('\n')""" +
                            """\n""" * 2)


            self.file.write(f"""with open(r'{os.path.join(self.result_wp, result_file)}', "a") as file:\n""" +
                            """   for j in range(len(temp_arr[0])):\n""" +
                            """      for i in temp_arr:\n""" + 
                            r"""         file.write(f'{i[j]} ')""" + 
                            """\n""" +
                            r"""      file.write('\n')""" + 
                            """\nfile.close()\n""" +
                            """\n""" * 4)



        self.file.close()



    def closing_visit_countdown(self, time:int=0):
        """Обратный отсчет до закрытия visit

            Args:
                time (int, optional): Время до закрытия терминала visit. Defaults to 5.
        """

        if time == 0:
            return()

        with open(os.path.join(self.script_wp, self.script_name), 'a', encoding='utf-8') as self.file:
            self.file.write("""\n""" * 4 +
                            f"""countdown = {time}\n""" +
                            """for i in range(countdown, 0, -1):\n""" + 
                            r"""   print(f"VisIt закроется через {i} секунд...", end="\r")""" + 
                            """\n   time.sleep(1)\n"""
                            """print("Закрытие VisIt!")\n"""
                            """exit()\n""")

        self.file.close()









    # def temp(self):
    #     self.file.write()

            


    def launch(self, win_t_f:bool=True):
        """Запуск visit

            Args:
                win_t_f (bool, optional): Запуск visit с графическим окном. Defaults to True.
        """

        if win_t_f:
            line_1 = ""
        else:
            line_1 = "-nowin"

        proc = subprocess.run([self.visit_wp,
                               "-cli",    # текстовый режим
                               line_1,  # без окон
                               "-s", os.path.join(self.script_wp, self.script_name)  # путь к скрипту
                               ])


# %.0f - целые числа
# %# -9.4g - e с 4 знаками после запятой