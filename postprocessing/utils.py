import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import locale
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pathlib import Path
from enum import Enum, auto
from scipy.interpolate import interp1d, griddata
from scipy.interpolate import LinearNDInterpolator
import matplotlib.animation as animation

class AnimateBy(Enum):
    TRACK_ID = auto()
    TIME = auto()


# match animate_by:
#     case AnimateBy.TRACK_ID:
#
#     case AnimateBy.TIME:
#
#     case _:
#         raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")


def create_animation_tracks(
    animate_by: AnimateBy,
    anim_base_name: str,
    ox_label: str,
    oy_label: str,
    filtered_tracks: list,
    # aggregator,
    # data_on_interval: dict,
    # x_coord: np.ndarray,
    params_config: list,
    GOST: bool = True,
    ox_limits: list = None,
    line_width: int = 1,
    vertical_lines: list = None,
    horizontal_lines: list = None,
    fps: int = 24,
    output_name: str = None,
    show_track_numbers_or_time: bool = False
):
    """
    Создает анимацию для заданных параметров.

    Args:
        anim_base_name: Базовое имя для файла.
        ox_label: Метка оси X.
        oy_label: Метка оси Y.
        filtered_tracks: список Dataframe данных для каждого трека
        aggregator: Объект DataAggregator.
        data_on_interval: Словарь с данными для анимации.
        x_coord: Координаты по оси X.
        params_config: Конфигурация параметров для анимации.
            Пример:
            [
                {
                    'averaged': (df_averaged, ['Temperature'], [style_average], ['осредненная'], y_limits['Temperature'], colors),
                    'instant': (data_on_interval, ['Temperature'], [style_instant], ['мгновенная'], y_limits_default, colors)
                },
                {
                    'averaged': (df_averaged, ['Y_air', 'Y_cp', 'Y_gpg'], [style_average]*3, ['осредненная - воздух', 'осредненная - ПС', 'осредненная - ГПГ'], y_limits['Y_air'], colors),
                    'instant': (data_on_interval, ['Y_air', 'Y_cp', 'Y_gpg'], [style_instant]*3, ['мгновенная - воздух', 'мгновенная - ПС', 'мгновенная - ГПГ'], y_limits_default, colors)
                }
            ]
        GOST: Применять ли ГОСТ-стиль.
        ox_limits: Лимиты по оси OX.
        line_width: Ширина линий.
        fps: Частота кадров в секунду.
        output_name: Имя выходного файла (если не указано, используется pic_base_name).
        show_track_numbers_or_time: Показывать ли номера треков или время.
    """
    print(f"Анимация для файла с именем {output_name} ...")

    if output_name is None:
        output_name = anim_base_name

    match animate_by:
        case AnimateBy.TRACK_ID:
            unique_tracks = filtered_tracks['track_id'].unique()
            frames = len(unique_tracks)
            print(f"📊 Найдено {frames} треков для анимации.")
            min_track_id = filtered_tracks['track_id'].min()
            track_counts = filtered_tracks.groupby('track_id').size()
            max_points_track_id = track_counts.idxmax()
            max_points = track_counts.max()
            print(f"Track ID с максимальным числом точек: {max_points_track_id}")
            print(f"Максимальное количество точек: {max_points}")
            max_points_track_group = filtered_tracks[filtered_tracks['track_id'] == max_points_track_id]
        case AnimateBy.TIME:
            unique_time = filtered_tracks['time'].unique()
            frames = len(unique_time)
            print(f"📊 Найдено {frames} моментов времени для анимации.")
            min_time = filtered_tracks['time'].min()
            time_counts = filtered_tracks.groupby('time').size()
            max_points = time_counts.max()
            print(f"время с максимальным числом точек (должно быть у всех одинаково): {max_points}")
            print(f"Максимальное количество точек: {max_points}")
        case _:
            raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")
    fig, ax, lines = plot_result(
        f"{anim_base_name}",
        ox_label,
        oy_label,
        *params_config,
        # x_values=x_coord,
        GOST=GOST,
        x_limits=ox_limits,
        swap_axes=False,
        line_width=line_width,
        vertical_lines=vertical_lines,
        horizontal_lines=horizontal_lines,
        animation=True
    )

    for line in lines:
        line.set_data(np.linspace(0, 0.1, max_points), np.zeros(max_points))

    parameters = params_config[0][1]

    if show_track_numbers_or_time:
        match animate_by:
            case AnimateBy.TRACK_ID:
                text = ax.set_title(f'Номер трека: {min_track_id}', fontsize=12)
            case AnimateBy.TIME:
                text = ax.set_title(f'Время: {min_time}', fontsize=12)
            case _:
                raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")


    def animate(i):
        # print('animation i is', i)
        # current_track_id = min_track_id + i

        match animate_by:
            case AnimateBy.TRACK_ID:
                current_track_id = unique_tracks[i]
                current_track_df = filtered_tracks[filtered_tracks['track_id'] == current_track_id]
                if current_track_df.empty:
                    print(f"⚠️ Нет данных для трека {current_track_id}")
                    return lines + [text]
                for line, param in zip(lines, parameters):
                    x_data = current_track_df['time_local'].values
                    y_data = current_track_df[param].values
                    # Дополняем данные до max_points (если нужно)
                    if len(x_data) < max_points:
                        x_padded = np.pad(x_data, (0, max_points - len(x_data)), mode='edge')
                        y_padded = np.pad(y_data, (0, max_points - len(y_data)), mode='edge')
                        # print(x_padded)
                        # print(y_padded)
                    else:
                        x_padded = x_data[:max_points]
                        y_padded = y_data[:max_points]
                        # print(x_padded)
                        # print(y_padded)
                    line.set_data(x_padded, y_padded)
                if show_track_numbers_or_time:
                    text.set_text(f'Номер трека: {current_track_id}')

            case AnimateBy.TIME:
                current_time = unique_time[i]
                current_time_df = filtered_tracks[filtered_tracks['time'] == current_time]
                if current_time_df.empty:
                    print(f"⚠️ Нет данных для времени {current_time}")
                    return lines + [text]
                for line, param in zip(lines, parameters):
                    x_data = current_time_df['X'].values
                    y_data = current_time_df[param].values
                    # Дополняем данные до max_points (если нужно)
                    if len(x_data) < max_points:
                        x_padded = np.pad(x_data, (0, max_points - len(x_data)), mode='edge')
                        y_padded = np.pad(y_data, (0, max_points - len(y_data)), mode='edge')
                        # print(x_padded)
                        # print(y_padded)
                    else:
                        x_padded = x_data[:max_points]
                        y_padded = y_data[:max_points]
                        # print(x_padded)
                        # print(y_padded)
                    line.set_data(x_padded, y_padded)
                if show_track_numbers_or_time:
                    time_text = f"Время: {current_time:.4f}"
                    # text.set_fontfamily('monospace')
                    text.set_text(time_text)
            case _:
                raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")
        return lines + [text]

    ani = animation.FuncAnimation(
        fig,
        animate,
        frames=frames,
        interval=1000/fps,
        blit=True,
        repeat=True
    )

    ani.save(f"{anim_base_name}{output_name}.mp4", writer='ffmpeg', fps=fps, dpi=200, bitrate=5000)
    plt.close(fig)
    return ani









def create_animation(
    anim_base_name: str,
    x_label: str,
    y_label: str,
    aggregator,
    data_on_interval: dict,
    x_coord: np.ndarray,
    params_config: list,
    GOST: bool = True,
    x_limits: list = None,
    line_width: int = 1,
    vertical_lines: list = None,
    horizontal_lines: list = None,
    fps: int = 24,
    output_name: str = None,
    show_time: bool = False
):
    """
    Создает анимацию для заданных параметров.

    Args:
        anim_base_name: Базовое имя для файла.
        x_label: Метка оси X.
        y_label: Метка оси Y.
        aggregator: Объект DataAggregator.
        data_on_interval: Словарь с данными для анимации.
        x_coord: Координаты по оси X.
        params_config: Конфигурация параметров для анимации.
            Пример:
            [
                {
                    'averaged': (df_averaged, ['Temperature'], [style_average], ['осредненная'], y_limits['Temperature'], colors),
                    'instant': (data_on_interval, ['Temperature'], [style_instant], ['мгновенная'], y_limits_default, colors)
                },
                {
                    'averaged': (df_averaged, ['Y_air', 'Y_cp', 'Y_gpg'], [style_average]*3, ['осредненная - воздух', 'осредненная - ПС', 'осредненная - ГПГ'], y_limits['Y_air'], colors),
                    'instant': (data_on_interval, ['Y_air', 'Y_cp', 'Y_gpg'], [style_instant]*3, ['мгновенная - воздух', 'мгновенная - ПС', 'мгновенная - ГПГ'], y_limits_default, colors)
                }
            ]
        GOST: Применять ли ГОСТ-стиль.
        x_limits: Лимиты по оси X.
        line_width: Ширина линий.
        fps: Частота кадров в секунду.
        output_name: Имя выходного файла (если не указано, используется pic_base_name).
    """
    print(f"Анимация для файла с именем {output_name} ...")

    if output_name is None:
        output_name = anim_base_name

    if show_time:
        time_values = aggregator.time

    # Инициализируем фигуру и оси
    fig, ax, lines = plot_result(
        f"{anim_base_name}",
        x_label,
        y_label,
        *params_config,
        x_values=x_coord,
        GOST=GOST,
        x_limits=x_limits,
        swap_axes=False,
        line_width=line_width,
        vertical_lines=vertical_lines,
        horizontal_lines=horizontal_lines,
        animation=True
    )

    parameters = params_config[0][1]        # Берем имена параметров из первого набора данных

    time_text = ax.set_title(f'Время: {time_values[0]:.4f} с', fontsize=12)

    def animate(i):
        for line, param in zip(lines, parameters):
            line.set_ydata(data_on_interval[param][:, i])
        time_text.set_text(f'Время: {time_values[i]:.4f} с')
        return lines + [time_text]

    ani = animation.FuncAnimation(
        fig,
        animate,
        frames=len(time_values),
        interval=1000/fps,
        blit=True,
        repeat=True
    )

    ani.save(f"{anim_base_name}{output_name}.gif", writer='pillow', fps=fps, dpi=400)
    plt.close(fig)
    return ani


def plot_result(
        pic_name: str,
        x_label: str,
        y_label: str,
        *plot_data,
        x_values: np.ndarray = None,
        GOST: bool = False,
        x_limits: tuple = None,
        swap_axes: bool = False,
        line_width: int = 1,
        delete_x_nticks: int = 1,
        vertical_lines: list = None,
        horizontal_lines: list = None,
        animation: bool = False,
        current_frame: int = 0,
        fig: plt.Figure = None,
        ax: plt.Axes = None,
        lines: list = None
 ):
    """
        Строит график зависимости параметров от времени или другой координаты
        :param pic_name: Имя файла для сохранения картинки графика.
        :param x_label: Метка x оси.
        :param y_label: Метка Y оси.
        :param plot_data: Кортеж данных для построения графиков.
        :param x_values: Значения по оси ОХ.
        :param GOST: Применять ли ГОСТ-стиль.
        :param x_limits: Устанавливать ли предел ОХ.
        :param swap_axes: Поменять X Y оси местами.
        :param line_width: Ширина линий.
        :param delete_x_nticks: Сколько меток линии ОХ удалить (обычно 1 или 2).
        :param vertical_lines: Добавить вертикальные линии.
        :param horizontal_lines: Добавить горизонтальные линии.
        """
    # fig, ax = plt.subplots(figsize=(10, 6))
    fig, ax = plt.subplots(figsize=(7, 3))
    # fig, ax = plt.subplots(figsize=(7, 4))

    if animation:
        lines = []
        lines_static = []
        lines_animation = []
        parameters_animation = []

    annotation_ratios = []  # привязка линий выносок
    annotation_offsets_x = []  # отступы линий выносок X
    annotation_offsets_y = []  # отступы линий выносок Y
    number_of_plots_from_one_source = []  # число графиков из одного источника для верификации

    standard_colors = plt.cm.tab10.colors

    # Обрабатываем данные: если это массив NumPy, используем его напрямую

    color_index = 0
    for ind, data in enumerate(plot_data):
        processed_plot_data = []
        data_source, param_names, styles, labels, *optional = data
        is_static = isinstance(data_source, pd.DataFrame)
        # Получаем значения параметров
        if is_static:
            # Для DataFrame: получаем значения из столбцов
            y_values_list = [data_source[col].values for col in param_names]
            # Используем индекс DataFrame как x_values для каждого параметра
            current_x_values = data_source.index
            # if x_values is None:
            #     x_values = data_source.index
        else:
            # Для словаря с массивами: получаем значения из словаря
            y_values_list = [data_source[col][:, 0] for col in param_names]
            if x_values is None:
                raise ValueError('Без использования DataFrame должен быть передан x_values')
            current_x_values = x_values


        y_limits = optional[0] if len(optional) > 0 else None
        colors = optional[1] if len(optional) > 1 else None
        # print('текущие цвета из функции:', colors)
        if GOST and len(optional) > 2:
            annotation_ratios.append(optional[2])
            annotation_offsets_x.append(optional[3])
            annotation_offsets_y.append(optional[4])
        if GOST:
            number_of_plots_from_one_source.append(len(param_names))
        if not (len(param_names) == len(styles) == len(labels)):
            raise ValueError(
                f"Количество параметров ({len(param_names)}), стилей ({len(styles)}) и меток ({len(labels)}) должно совпадать"
            )
        for i, y_values in enumerate(y_values_list):
            processed_plot_data.append((y_values, styles[i], labels[i], y_limits, colors[i], is_static))
            print(f'добавлены данные, стиль {styles[i]}')

        xlim = x_limits if x_limits else (None, None)
        ylim = y_limits if y_limits else (None, None)

        if swap_axes:
            ax.set_xlim(ylim)
            ax.set_ylim(xlim)
            print(f'X лимиты (бывшие Y): {ylim}')
            print(f'Y лимиты (бывшие X): {xlim}')
        else:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            print(f'X лимиты: {xlim}')
            print(f'Y лимиты: {ylim}')

        for line in ax.lines:
            if max(line.get_ydata()) == 0:
                line.remove()

        standard_colors = plt.cm.tab10.colors
        print('Standard colors:', standard_colors)

        print('перед запуском цикла:')

        for idx, (y_values, style, label, y_limit, color, is_static) in enumerate(processed_plot_data):
            if not color:
                print('ЦВЕТ не передан, использую стандартную палитру')
                color = standard_colors[ind % len(colors)]
                print(ind, color)
            if colors and idx < len(colors) and colors[idx] is not None:
                print('зашел сюда')
                color = colors[idx]

            if swap_axes:
                line, = ax.plot(y_values, current_x_values, color=color, linestyle=style, label=label, markersize=2.5, markevery=200, linewidth=line_width)
            else:
                line, = ax.plot(current_x_values, y_values, color=color, linestyle=style, label=label, markersize=2.5, markevery=200, linewidth=line_width)
                print(f'добавил линию для параметра')
            # if animation and not is_static:
            #     lines.append(line)
            if animation:
                lines.append(line)

            if swap_axes:
                ax.set_xlabel(y_label, fontsize=12)
                ax.set_ylabel(x_label, fontsize=12)
            else:
                ax.set_xlabel(x_label, fontsize=12)
                ax.set_ylabel(y_label, fontsize=12)

        color_index += 1

        ax.grid(True)

    print(f'размер processed_plot_data {len(processed_plot_data)}')

    def format_tick(value, tick_number, axis_format):
        if value == 0:
            return '0'

        if axis_format == 'int':
            return f'{int(value)}'
        elif axis_format == 'float':
            return f'{value:.2f}'.replace('.', ',')
        elif axis_format == 'scientific':
            return f'{value:.2e}'.replace('.', ',').replace('e+0', 'e').replace('e-0', 'e-').replace('e', '·10^')
        else:  # auto
            if 1e-3 <= abs(value) < 1e5:
                if value.is_integer():
                    return f'{int(value)}'
                else:
                    return f'{value:.2f}'.replace('.', ',')
            else:
                return f'{value:.1e}'.replace('.', ',').replace('e+0', ' e').replace('e-0', ' e-').replace('e+', ' e+').replace('e-', ' e-')

    x_format = 'auto'
    y_format = 'auto'
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda value, tick_number: format_tick(value, tick_number, x_format)))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda value, tick_number: format_tick(value, tick_number, y_format)))

    # НАСТРОЙКИ ГОСТ
    if GOST:
        cumulative_lines = sum(number_of_plots_from_one_source)

        # Убираем крайние черточки на шкалах
        xticks = ax.get_xticks()
        xticks = xticks[:-delete_x_nticks]
        ax.set_xticks(xticks)
        ax.xaxis.set_label_coords(0.97, -0.02)

        yticks = ax.get_yticks()
        yticks = yticks[1:-1]
        ax.set_yticks(yticks)

        ax.tick_params(axis='both', labelsize=12)

        # Поворачиваем подпись OY горизонтально
        ax.yaxis.label.set_rotation(0)
        ax.yaxis.set_label_coords(-0.07, 0.97)

        # Стрелочки на осях
        plt.annotate('', xy=(1.02, 0), xytext=(0.0, 0),
             arrowprops=dict(facecolor='black', shrink=0.0, width=0.01, headlength=8, headwidth=5),
             xycoords='axes fraction', textcoords='axes fraction')
        plt.annotate('', xy=(0, 1.02), xytext=(0, 0),
             arrowprops=dict(facecolor='black', shrink=0.0, width=0.01, headlength=8, headwidth=5),
             xycoords='axes fraction', textcoords='axes fraction')

        # Правая и верхняя границы графика
        plt.gca().spines[['top', 'right']].set_color('gray')

        label_counter = 0
        ind_source = 0
        cumulative_number_of_plots = number_of_plots_from_one_source[ind_source]

        if annotation_ratios and annotation_offsets_x and annotation_offsets_y:
            for i, line in enumerate(ax.lines):
                if i >= cumulative_number_of_plots:
                    ind_source += 1
                    cumulative_number_of_plots += number_of_plots_from_one_source[ind_source]
                x_data = line.get_xdata()
                y_data = line.get_ydata()

                ind_line_inside_source = i + number_of_plots_from_one_source[ind_source] - cumulative_number_of_plots

                annotation_ratio = annotation_ratios[ind_source][ind_line_inside_source]
                annotation_offset_x = annotation_offsets_x[ind_source][ind_line_inside_source]
                annotation_offset_y = annotation_offsets_y[ind_source][ind_line_inside_source]
                ind = round(annotation_ratio * len(x_data))

                # КОСТЫЛЬ
                style_S = '-'
                number_of_sources = 2

                # if (line._linestyle == style_S) and (cumulative_lines > number_of_sources):
                #     label_counter += 1
                #     label = str(label_counter)
                #     ax.annotate(label, xy=(x_data[ind], y_data[ind]), xytext=(x_data[ind] + annotation_offset_x*max(x_data), y_data[ind] + annotation_offset_y*max(y_data)),
                #                 arrowprops=dict(facecolor='black', shrink=0.00001, headlength=5, headwidth=0.1, width=0.1),
                #                 color='black', fontname='Times New Roman')
        else:
            print('Указан ГОСТ стиль но не переданы данные для выносных линий')

        # легенда снаружи графика
        # ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        # легенда внутри графика
        # ax.legend(loc='upper left', fontsize='small')
        ax.legend(loc='best', fontsize='small')

    if not GOST:
        ax.legend(loc='best', fontsize='xx-small')
        # ax.legend(loc='lower left', fontsize='xx-small')

    if vertical_lines:
        for line in horizontal_lines:
            ax.axvline(
                x=line,
                color='black',
                linestyle='--',
                linewidth=line_width,
                # label='Линия x=3'
            )

    if horizontal_lines:
        for line in horizontal_lines:
            ax.axhline(
                y=line,
                color='black',
                linestyle='--',
                linewidth=line_width,
                # label='Линия y=5'
            )

    plt.rcParams['font.family'] = 'Times New Roman'

    if not animation:
        plt.savefig(''.join((pic_name, '.jpeg')), dpi=400, bbox_inches='tight')
        plt.close()
        return None
    else:
        return fig, ax, lines


def plot_all_tracks(grouped,
                    y_columns,
                    styles,
                    ylabels,
                    ylabel_common,
                    pic_name,
                    x_column='time',
                    x_label=None,
                    show_track_legend=True,
                    max_legend_entries=5,
                    renumber_tracks=False,
                    GOST_plots=False,
                    x_limits=None,
                    y_limits=None,
                    x_format='auto',
                    y_format='auto',
                    annotation_ratios=None,
                    annotation_offsets_x=None,
                    annotation_offsets_y=None,
                    selected_tracks_x_value=None,
                    selected_tracks_number=None):
    """
    Строит графики для всех треков.
    :param grouped: Группированные данные по трекам.
    :param y_columns: Список столбцов для построения.
    :param styles: Список стилей линий.
    :param ylabels: Список меток для легенды.
    :param ylabel_common: Общая метка оси Y.
    :param pic_name: Имя для сохранения графика.
    :param x_column: Столбец для оси X.
    :param x_label: Метка оси X.
    :param show_track_legend: Показывать легенду для треков.
    :param max_legend_entries: Максимальное количество элементов в легенде.
    :param renumber_tracks: Перенумеровывать треки.
    :param GOST_plots: Использовать стиль ГОСТ.
    """

    plt.figure(figsize=(8, 3.2))

    # Задаем размер шрифта для всех элементов графика
    # Настройка формата меток на осях с использованием запятых
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')  # Устанавливаем русскую локаль
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    # plt.rcParams['font.size'] = 10
    # plt.rcParams['axes.titlesize'] = 12
    # plt.rcParams['axes.labelsize'] = 10
    # plt.rcParams['xtick.labelsize'] = 10
    # plt.rcParams['ytick.labelsize'] = 10
    # plt.rcParams['legend.fontsize'] = 10

    ax = plt.gca()

    colors = plt.cm.tab10.colors
    track_ids = list(grouped.groups.keys())

    if x_column not in df.columns and x_column != 'time':
        raise ValueError(f"Column '{x_column}' not found in DataFrame")

    # Построение только для части выбранных треков
    if selected_tracks_x_value is not None and selected_tracks_number is not None:
        track_values = []
        for orig_track_id, group in grouped:
            x_data = group[x_column].values
            y_data = group[y_columns[0]].values
            if selected_tracks_x_value < x_data[0] or selected_tracks_x_value > x_data[-1]:
                print('!!!WARNING!!! - tracks selection X value is out of range - skipped selection')
                continue
            y_at_x = np.interp(selected_tracks_x_value, x_data, y_data)
            track_values.append((orig_track_id, y_at_x))
        if not track_values:
            return

        # Сортируем по значению y_at_x
        track_values.sort(key=lambda x: x[1])
        selected_tracks = [track_values[0][0], track_values[-1][0]]
        if selected_tracks_number > 2:
            step = (len(track_values) - 1) // (selected_tracks_number - 1)
            for i in range(1, selected_tracks_number - 1):
                selected_tracks.append(track_values[i * step][0])
        track_ids = selected_tracks

    # Если включена перенумерация треков
    if renumber_tracks:
        track_ids_for_legend = list(range(1, len(track_ids) + 1))
    else:
        track_ids_for_legend = track_ids

    # Если только один параметр, то показываем легенду для треков
    if len(y_columns) == 1:
        for idx, orig_track_id in enumerate(track_ids):
            group = grouped.get_group(orig_track_id)
            group = group.copy()
            group['time'] = group['dt'].cumsum()
            group.set_index('time', drop=False, inplace=True)

            x_data = group[x_column] if x_column != 'time' else group['time']

            track_id_for_legend = track_ids_for_legend[idx]
            ax.plot(x_data, group[y_columns[0]], linestyle=styles[0], color=colors[idx % len(colors)],
                   label=f'Трек № {int(track_id_for_legend)}' if idx < max_legend_entries else "")

        plt.grid(True)
        if x_column == 'time':
            plt.xlabel(r'$время\ (с)$')
        else:
            plt.xlabel(x_label if x_label else x_column)
        plt.ylabel(ylabel_common)
        if not GOST_plots:
            plt.title(f'{ylabel_common}')

        if show_track_legend:
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='best', fontsize='medium')
            # plt.legend(loc='best', fontsize='medium')
            if len(track_ids) > max_legend_entries:
                ax.text(0.98, 0.02, f'... и еще {len(track_ids) - max_legend_entries} треков',
                        transform=ax.transAxes, ha='right', va='bottom', fontsize='small')

    # Если несколько параметров, то показываем легенду для стилей линий
    else:
        print('come many parameters')
        # Создаем пустые линии для легенды стилей
        legend_lines = []
        for style_idx, ylabel in enumerate(ylabels):
            line, = ax.plot([], [], linestyle=styles[style_idx], color=colors[style_idx], label=ylabel)
            legend_lines.append(line)

        for idx, orig_track_id in enumerate(track_ids):
            group = grouped.get_group(orig_track_id)
            group = group.copy()
            group['time'] = group['dt'].cumsum()
            group.set_index('time', drop=False, inplace=True)

            x_data = group[x_column] if x_column != 'time' else group['time']

            for style_idx, y in enumerate(y_columns):
                ax.plot(x_data, group[y], linestyle=styles[style_idx], color=colors[style_idx], label=None)

        plt.grid(True)
        if x_column == 'time':
            plt.xlabel(r'$время\ (с)$')
        else:
            plt.xlabel(x_label if x_label else x_column)
        plt.ylabel(ylabel_common)
        if not GOST_plots:
            plt.title(f'{ylabel_common}')

        print('legend lines:', legend_lines)
        # Легенда для стилей линий
        if not GOST_plots:
            ax.legend(handles=legend_lines, loc='upper right', fontsize='small')

    # Настройка форматов меток оси
    def format_tick(value, tick_number, axis_format):
        if value == 0:
            return '0'

        if axis_format == 'int':
            return f'{int(value)}'
        elif axis_format == 'float':
            return f'{value:.2f}'.replace('.', ',')
        elif axis_format == 'scientific':
            return f'{value:.3e}'.replace('.', ',').replace('e+0', 'e').replace('e-0', 'e-').replace('e', '·10^')
        else:  # auto
            if 1e-3 <= abs(value) < 1e5:
                if value.is_integer():
                    return f'{int(value)}'
                else:
                    return f'{value:.2f}'.replace('.', ',')
            else:
                return f'{value:.3e}'.replace('.', ',').replace('e+0', ' e').replace('e-0', ' e-').replace('e+', ' e+').replace('e-', ' e-')

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda value, tick_number: format_tick(value, tick_number, x_format)))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda value, tick_number: format_tick(value, tick_number, y_format)))

    # Настройки ГОСТ
    if GOST_plots:
        # Убираем крайние черточки на шкалах
        # if x_limits:
        #     ax.set_xlim(x_limits[0], x_limits[1])

        # ax.set_xlim(0, max(x_data))
        xticks = ax.get_xticks()
        xticks = xticks[:-1]
        ax.set_xticks(xticks)
        ax.xaxis.set_label_coords(0.97, -0.02)

        if y_limits:
            ax.set_ylim(y_limits[0], y_limits[1])
        if x_limits:
            ax.set_xlim(x_limits[0], x_limits[1])
        yticks = ax.get_yticks()
        yticks = yticks[:-1]
        ax.set_yticks(yticks)

        # Поворачиваем подпись OY горизонтально
        ax.yaxis.label.set_rotation(0)
        ax.yaxis.set_label_coords(-0.05, 0.97)

        # Стрелочки на осях
        plt.annotate('', xy=(1.02, 0), xytext=(0.0, 0),
                     arrowprops=dict(facecolor='black', shrink=0.0, width=0.01, headlength=8, headwidth=5),
                     xycoords='axes fraction', textcoords='axes fraction')
        plt.annotate('', xy=(0, 1.02), xytext=(0, 0),
                     arrowprops=dict(facecolor='black', shrink=0.0, width=0.01, headlength=8, headwidth=5),
                     xycoords='axes fraction', textcoords='axes fraction')

        # Правая и верхняя границы графика
        plt.gca().spines[['top', 'right']].set_color('gray')

        # Выносные линии
        if annotation_ratios and annotation_offsets_x and annotation_offsets_y:
            indices = list(range(len(y_columns), len(y_columns) * 2))
            for param_idx, index in enumerate(indices):
                line = ax.lines[index]
                x_data = line.get_xdata()
                y_data = line.get_ydata()

                # Проверка на наличие данных
                if len(x_data) == 0 or len(y_data) == 0:
                    continue

                ind = round(annotation_ratios[param_idx] * len(x_data))
                ax.annotate(f'{param_idx + 1}', xy=(x_data[ind], y_data[ind]),
                            xytext=(x_data[ind] + annotation_offsets_x[param_idx] * max(x_data),
                                    y_data[ind] + annotation_offsets_y[param_idx] * max(y_data)),
                            arrowprops=dict(facecolor='black', shrink=0.00001, headlength=5, headwidth=0.1, width=0.1),
                            color='black', fontname='Times New Roman')

        # Легенда
        # ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')


    plt.tight_layout()
    # plt.savefig(os.path.join(path_post, f'all_{pic_name}.jpeg'), dpi=400, bbox_inches='tight')

    plt.rcParams['font.family'] = 'Times New Roman'
    plt.savefig(os.path.join(path_post, f'all_{pic_name}.jpeg'), dpi=400, bbox_inches='tight')
    plt.close()


def plot_3d(grouped, color_param, color_label, pic_name, elev=30, azim=45, view='default', vmin=None, vmax=None,
            fit_to_data=True, equal_aspect=False, x_limits=None, y_limits=None, z_limits=None):
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Определяем минимальное и максимальное значение для цветовой шкалы
    if vmin is None or vmax is None:
        all_values = np.concatenate([group[color_param].values for _, group in grouped])
        vmin = all_values.min() if vmin is None else vmin
        vmax = all_values.max() if vmax is None else vmax

    # Определяем пределы осей на основе данных, если они не заданы
    if x_limits is None or y_limits is None or z_limits is None:
        all_x = np.concatenate([group['CoordinateX'].values for _, group in grouped])
        all_y = np.concatenate([group['CoordinateY'].values for _, group in grouped])
        all_z = np.concatenate([group['CoordinateZ'].values for _, group in grouped])

        x_limits = (all_x.min(), all_x.max()) if x_limits is None else x_limits
        y_limits = (all_y.min(), all_y.max()) if y_limits is None else y_limits
        z_limits = (all_z.min(), all_z.max()) if z_limits is None else z_limits

    for track_id, group in grouped:
        group = group.copy()
        group['time'] = group['dt'].cumsum()

        # Получаем данные для построения
        x = group['CoordinateX']
        y = group['CoordinateY']
        z = group['CoordinateZ']
        c = group[color_param]

        # Строим 3D-график с использованием цветовой шкалы rainbow
        sc = ax.scatter(x, y, z, c=c, cmap='rainbow', vmin=vmin, vmax=vmax)

    ax.set_xlabel('CoordinateX')
    ax.set_ylabel('CoordinateY')
    ax.set_zlabel('CoordinateZ')

    ax.set_xlim3d((x_limits))
    ax.set_ylim3d((y_limits))
    ax.set_zlim3d((z_limits))

    # ax.set_xlim(x_limits)
    # ax.set_ylim(y_limits)
    # ax.set_zlim(z_limits)

    # Устанавливаем равномерное масштабирование осей, если equal_aspect=True
    if equal_aspect:
        x_range = x_limits[1] - x_limits[0]
        y_range = y_limits[1] - y_limits[0]
        z_range = z_limits[1] - z_limits[0]

        max_range = max(x_range, y_range, z_range) * 0.5

        x_middle = np.mean(x_limits)
        y_middle = np.mean(y_limits)
        z_middle = np.mean(z_limits)

        ax.set_xlim(x_middle - max_range, x_middle + max_range)
        ax.set_ylim(y_middle - max_range, y_middle + max_range)
        ax.set_zlim(z_middle - max_range, z_middle + max_range)

    # Если fit_to_data=True, то устанавливаем пределы осей в соответствии с данными
    # if fit_to_data:
    #     ax.autoscale_view()

    # Устанавливаем углы обзора
    ax.view_init(elev=elev, azim=azim)

    # Устанавливаем вид в зависимости от параметра view
    if view == 'xy':
        ax.view_init(elev=90, azim=-90)
    elif view == 'xz':
        ax.view_init(elev=0, azim=-90)
    elif view == 'yz':
        ax.view_init(elev=0, azim=0)
    elif view == 'front':
        ax.view_init(elev=90, azim=-90)
    elif view == 'up':
        ax.view_init(elev=180, azim=-90)
    elif view == 'side':
        ax.view_init(elev=0, azim=45)

    # Добавление цветовой шкалы
    cbar = fig.colorbar(sc, ax=ax, shrink=0.5, aspect=5)
    cbar.set_label(color_label)

    plt.title(f'3D Trajectories Colored by {color_label}')
    plt.savefig(os.path.join(path_post, f'3d_{pic_name}.jpeg'), dpi=400, bbox_inches='tight')
    plt.close()


def make_lines_data(data, parameters, sections):
    section_dfs = []
    x = data['CoordinateX'].values
    y = data['CoordinateY'].values
    interpolators = {}
    for parameter in parameters:
        z = data[parameter].values
        interpolators[parameter] = LinearNDInterpolator(list(zip(x, y)), z)
    for section_x in sections:
        section_data = {'CoordinateY': np.linspace(min(data['CoordinateY']), max(data['CoordinateY']), 100)}
        for parameter in parameters:
            points_line = [(section_x, yi) for yi in section_data['CoordinateY']]
            z_line = interpolators[parameter](points_line)
            section_data[parameter] = z_line
        section_df = pd.DataFrame(section_data)
        for parameter in parameters:
            section_df[parameter] = pd.Series(section_df[parameter]).interpolate(method='linear', limit_direction='both')
        section_df.dropna(inplace=True)
        section_df.set_index('CoordinateY', inplace=True, drop=False)
        section_dfs.append(section_df)
    return section_dfs
