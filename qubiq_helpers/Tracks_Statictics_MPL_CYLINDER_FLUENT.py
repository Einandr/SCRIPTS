import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import locale
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pathlib import Path

path = r'D:\YASIM\VORON\2025_09_MPL\TASK_DECEMBER\04_TT2_OLD_MODELS\02_fluent_basic_and_extended'

post_visit_gas = False
time_end = 0.025                    # for using qubiq monitors
qubiq_gas_dt = 1.542019e-6          # not used if using qubiq monitors

dir_out = 'out'
dir_tracks = 'tracks'
dir_qubiq_postproc = r'postproc\monitors'
dir_post = 'post'
dir_post_visit = 'post_visit'

# GOST_plots = False
GOST_plots = True

os.chdir(''.join((path, '/', dir_out)))


# regions = ['region0']
# legend = ['d2000']
# legend = ['d200', 'd150', 'd100']
# dfr = []
# for r in regions:
#     data = pd.read_csv(''.join(('tracks_', r, '.csv')))
#     data.sort_values('CoordinateZ', inplace=True)
#     dfr.append(data)




df = pd.read_csv(''.join((path, '/', dir_out, '/', 'points_for_tecplot_FLUENT.csv')), dtype=float)

# df['mass_Y1'] = df['mass'] * df['Y1']
# df['mass_Y2'] = df['mass'] * df['Y2']
# df['mass_Y3'] = df['mass'] * df['Y3']

# Переименование столбцов
df = df.rename(columns={
    'Diameter': 'diameter',
    'Temperature': 'temperature',
    'Density': 'density',
    'Mass': 'mass',
    'ID': 'track_id',
    'ResidenceTime': 'time',
    'TimeStep': 'dt'
})

df['diameter'] = df['diameter'] * 1e6
grouped = df.groupby('track_id')


# Создаём датафрейм с первыми частицами (минимальное время)
min_time_per_track = df.loc[df.groupby('track_id')['time'].idxmin()]
min_time_per_track.to_csv('min_time_per_track.csv', index=False)

# Создаём датафрейм с последними частицами (максимальное время)
max_time_per_track = df.loc[df.groupby('track_id')['time'].idxmax()]

# Рассчитываем среднее и стандартное отклонение по времени и координате X
mean_time = max_time_per_track['time'].mean()
std_time = max_time_per_track['time'].std()
min_time_max = max_time_per_track['time'].min()
max_time_max = max_time_per_track['time'].max()

mean_x = max_time_per_track['CoordinateX'].mean()
std_x = max_time_per_track['CoordinateX'].std()
min_x_max = max_time_per_track['CoordinateX'].min()
max_x_max = max_time_per_track['CoordinateX'].max()

# Рассчитываем нормализованное отклонение (RSD) для времени и координаты X
rsd_time = (std_time / mean_time) * 100
rsd_x = (std_x / mean_x) * 100



# Создаём словарь со статистикой
stats = {
    'Parameter': ['Time', 'Time', 'Time', 'Time', 'Time', 'CoordinateX', 'CoordinateX', 'CoordinateX', 'CoordinateX', 'CoordinateX'],
    'Metric': ['Mean', 'Standard Deviation', 'RSD (%)', 'Minimum', 'Maximum', 'Mean', 'Standard Deviation', 'RSD (%)', 'Minimum', 'Maximum'],
    'Value': [
        mean_time, std_time, rsd_time, min_time_max, max_time_max,
        mean_x, std_x, rsd_x, min_x_max, max_x_max
    ]
}

# Создаём датафрейм для статистики
stats_df = pd.DataFrame(stats)

# Сохраняем в Excel
stats_excel_path = 'statistics.xlsx'
stats_df.to_excel(stats_excel_path, index=False)

# Сохраняем в текстовый файл
stats_text_path = 'statistics.txt'
with open(stats_text_path, 'w') as f:
    f.write("Statistics for max_time_per_track:\n\n")
    f.write(f"Time: Mean = {mean_time:.6f}, Std Dev = {std_time:.6f}, RSD = {rsd_time:.2f}%, Min = {min_time_max:.6f}, Max = {max_time_max:.6f}\n")
    f.write(f"CoordinateX: Mean = {mean_x:.6f}, Std Dev = {std_x:.6f}, RSD = {rsd_x:.2f}%, Min = {min_x_max:.6f}, Max = {max_x_max:.6f}\n")


path_post = ''.join((path, '/', dir_post))
Path(path_post).mkdir(parents=True, exist_ok=True)
os.chdir(path_post)




# df['time'] = df['dt'].cumsum()
# df.set_index('time', drop=False, inplace=True)

# print('total time is:', df['dt'].sum())


plt.rcParams["figure.figsize"] = [15.00, 7]
plt.rcParams["figure.autolayout"] = True

if post_visit_gas:
    os.chdir(''.join((path, '/', dir_post_visit)))
    df_gas = pd.read_csv(''.join((path, '/', dir_post_visit, '/', 'points.txt')), sep=' ')
    # APPROXIMATELY!!! LATER CORRECT
    df_gas['time'] = df_gas['time_step']*qubiq_gas_dt
    # df_gas.set_index('time', drop=False, inplace=True)

    # getting time from monitors:
    # so far monitors doesn't provide first and last time points. So add them artificially
    monitors_headers = ['time', 'temperature', 'pressure']
    df_gas_monitors = pd.read_csv(''.join((path, '/', dir_out, '/', dir_qubiq_postproc, '/', 'monitor0.dat')), sep='\t', skiprows=1, dtype=float, header=None, names=monitors_headers)
    length_to_set = len(df_gas['time'])
    lenth_available = len(df_gas_monitors['time'].values)
    end_offset = length_to_set - lenth_available - 1

    test1 = len(df_gas['time'][1:].values)
    test2 = len(df_gas_monitors['time'].values)
    print(df_gas.loc[1:lenth_available, 'time'])
    print(df_gas_monitors['time'].values)

    df_gas.loc[1:lenth_available, 'time'] = df_gas_monitors['time'].values
    df_gas.loc[lenth_available+1, 'time'] = time_end
    df_gas.drop(df_gas.tail(end_offset-1).index, inplace=True)
    df_gas.set_index('time', drop=False, inplace=True)


# ax = dfr[0].plot(x='CoordinateZ', y='diameter', grid=True)
# for df in dfr[1:]:
#     df.plot(ax=ax, x='CoordinateZ', y='diameter', grid=True)
# ax.legend(legend)
# ax.set_ylim([0, 0.00021])
# plt.savefig('plot_diam.jpeg')


# ax = dfr[0].plot(x='CoordinateZ', y='temperature', grid=True)
# for df in dfr[1:]:
#     df.plot(ax=ax, x='CoordinateZ', y='temperature', grid=True)
# ax.legend(legend)
# ax.set_ylim([0, 0.00021])

# plt.savefig('plot_temp.jpeg')


def plot_picture(x, y, name):
    ax = df.plot(x=x, y=y, grid=True)
    # ax.legend(legend)
    # ax.set_ylim([0, 0.00021])
    plt.savefig(''.join((name, '.jpeg')))
    plt.close()


x_t_label = r'$время\ (с)$'

# def plot_result(df, y, style, label, ylabel, pic_name):
#     df.plot(y=y, use_index=True, style=style, grid=True, label=label, xlabel=x_t_label, ylabel=ylabel, xlim=0)
#     # if t_complete_volatile_evaporation is not None:
#     #     plt.axvline(t_complete_volatile_evaporation, color='black', linestyle='--', label=''.join(('полное испарение летучего,\nt = ', '{0:.{1}}'.format(t_complete_volatile_evaporation, 6), ' с')))
#     # if t_complete_combustible_combustion is not None:
#     #     plt.axvline(t_complete_combustible_combustion, color='black', linestyle='--', label=''.join(('полное сгорание горючего,\nt = ', '{0:.{1}}'.format(t_complete_combustible_combustion, 6), ' с')))
#     # if t_complete_oxidizer_consumption is not None:
#     #     plt.axvline(t_complete_oxidizer_consumption, color='black', linestyle='--', label=''.join(('полное выгорание окислителя,\nt = ', '{0:.{1}}'.format(t_complete_oxidizer_consumption, 6), ' с')))
#     plt.legend(loc='best', fontsize='small')
#     plt.savefig(''.join(('pic_', pic_name, '.jpeg')), dpi=400, bbox_inches='tight')
#     plt.close()

# Функция для построения графиков
def plot_result(df, y, style, label, ylabel, pic_name, track_id):
    ax = df.plot(y=y, use_index=True, style=style, grid=True, label=label, xlabel=r'$время\ (с)$', ylabel=ylabel, xlim=0)
    plt.title(f'Track ID: {track_id}')
    plt.legend(loc='best', fontsize='small')
    plt.savefig(''.join((path_post, '/', f'track_{track_id}_{pic_name}.jpeg')), dpi=400, bbox_inches='tight')
    plt.close()


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
            return f'{value:.2e}'.replace('.', ',').replace('e+0', 'e').replace('e-0', 'e-').replace('e', '·10^')
        else:  # auto
            if 1e-3 <= abs(value) < 1e5:
                if value.is_integer():
                    return f'{int(value)}'
                else:
                    return f'{value:.2f}'.replace('.', ',')
            else:
                return f'{value:.2e}'.replace('.', ',').replace('e+0', ' e').replace('e-0', ' e-').replace('e+', ' e+').replace('e-', ' e-')

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda value, tick_number: format_tick(value, tick_number, x_format)))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda value, tick_number: format_tick(value, tick_number, y_format)))

    # Настройки ГОСТ
    if GOST_plots:
        # Убираем крайние черточки на шкалах
        ax.set_xlim(0, max(x_data))
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


for track_id, group in grouped:
    group['time'] = group['dt'].cumsum()
    group.set_index('time', drop=False, inplace=True)


# ОТРИСОВКА ГРАФИКОВ
plot_all_tracks(grouped, ['diameter'], ['-'], [r'$диаметр\ частицы\ [мкм]$'], r'$d\ (мкм)$', 'diameter_x',
                x_column='CoordinateX',
                x_label=r'$X\ (м)$',
                show_track_legend=False,
                max_legend_entries=5,
                renumber_tracks=True,
                GOST_plots=GOST_plots,
                x_limits=(0, 0.54),
                y_limits=(0, 25),
                selected_tracks_x_value=0.4,
                selected_tracks_number=5)

plot_all_tracks(grouped, ['CoordinateY'], ['-'], [r'$координата\ У\ [м]$'], r'$Y\ (м)$', 'cooridnate_Y_x',
                x_column='CoordinateX',
                x_label=r'$X\ (м)$',
                show_track_legend=True,
                max_legend_entries=5,
                renumber_tracks=True,
                GOST_plots=GOST_plots,
                y_limits=(-0.05, 0.05))

plot_all_tracks(grouped, ['temperature'], ['-'], [r'$температура\ частицы\ [К]$'], r'$T\ (K)$', 'temperature_x',
                x_column='CoordinateX',
                x_label=r'$X\ (м)$',
                show_track_legend=False,
                max_legend_entries=5,
                renumber_tracks=True,
                GOST_plots=GOST_plots,
                x_limits=(0, 0.54),
                y_limits=(1800, 2600),
                selected_tracks_x_value=0.4,
                selected_tracks_number=5)

plot_all_tracks(grouped, ['mass'], ['-'], [r'$масса\ частицы\ [кг]$'], r'$m\ (кг)$', 'mass_x',
                x_column='CoordinateX',
                x_label=r'$X\ (м)$',
                show_track_legend=False,
                max_legend_entries=5,
                renumber_tracks=True,
                GOST_plots=GOST_plots,
                x_limits=(0, 0.54),
                y_limits=(0, 2.1e-11),
                selected_tracks_x_value=0.4,
                selected_tracks_number=5,)

# plot_all_tracks(grouped, ['density'], ['-'], [r'$плотность частицы\ \left[\frac{кг}{м^3}\right]$'], r'$\rho\ \left(\frac{кг}{м^3}\right)$', 'density_x',
#                 x_column='CoordinateX',
#                 x_label=r'$X\ (м)$',
#                 show_track_legend=False,
#                 max_legend_entries=5,
#                 renumber_tracks=True,
#                 GOST_plots=GOST_plots,
#                 y_limits=(2250, 4000),
#                 selected_tracks_x_value=0.45,
#                 selected_tracks_number=5,)

# plot_all_tracks(grouped, ['Y1', 'Y2', 'Y3'], ['-', '-', '-'], ['Y Volatile', 'Y Combustible', 'Y Inert'], 'Y', 'mass_fractions_x',
#                 x_column='CoordinateX',
#                 x_label=r'$X\ (м)$',
#                 show_track_legend=False,
#                 max_legend_entries=5,
#                 renumber_tracks=True,
#                 GOST_plots=GOST_plots,
#                 y_limits=(0, 1),
#                 annotation_ratios=[0.1, 0.45, 0.45],
#                 annotation_offsets_x=[0.05, 0.05, 0.05],
#                 annotation_offsets_y=[0.3, 0.15, -0.15],
#                 selected_tracks_x_value=0.45,
#                 selected_tracks_number=5,)

# plot_all_tracks(grouped, ['mass_Y1', 'mass_Y2', 'mass_Y3'], ['-', '-', '-'], ['Mass Volatile', 'Mass Combustible', 'Mass Inert'], r'$m\ (кг)$', 'mass_components_x',
#                 x_column='CoordinateX',
#                 x_label=r'$X\ (м)$',
#                 show_track_legend=False,
#                 max_legend_entries=5,
#                 renumber_tracks=True,
#                 GOST_plots=GOST_plots,
#                 y_limits=(0, 1.75e-11),
#                 annotation_ratios=[0.1, 0.2, 0.45],
#                 annotation_offsets_x=[0.05, 0.05, 0.05],
#                 annotation_offsets_y=[0.3, 0.05, 0.5],
#                 selected_tracks_x_value=0.45,
#                 selected_tracks_number=5,)


# plot_3d(grouped, 'temperature', r'$Temperature\ (K)$', 'trajectories_temperature')
# plot_3d(grouped, 'temperature', r'$Temperature\ (K)$', 'trajectories_temperature_z', view='z')
# plot_3d(grouped, 'temperature', r'$Temperature\ (K)$', 'trajectories_temperature_xy', view='xy')
# plot_3d(grouped, 'diameter', r'$Diameter\ (m)$', 'trajectories_diameter_xy', view='xy')
# plot_3d(grouped, 'mass', r'$Mass\ (kg)$', 'trajectories_mass_xz', view='xz')
# plot_3d(grouped, 'Y1', r'$Y\ Volatile$', 'trajectories_Y1_yz', view='yz')
# plot_3d(grouped, 'temperature', r'$Temperature\ (K)$', 'trajectories_temperature_custom', elev=20, azim=30)

# plot_3d(grouped, 'temperature', r'$Temperature\ (K)$', 'trajectories_temperature_front', view='front', y_limits=(-0.05, 0.05), z_limits=(-0.05, 0.05))
# plot_3d(grouped, 'temperature', r'$Temperature\ (K)$', 'trajectories_temperature_up', view='up', y_limits=(-0.05, 0.05), z_limits=(-0.05, 0.05))
# plot_3d(grouped, 'temperature', r'$Temperature\ (K)$', 'trajectories_temperature_side', view='side', y_limits=(-0.05, 0.05), z_limits=(-0.05, 0.05))



writer = pd.ExcelWriter(''.join(('qubiq_result_particles', '.xlsx')), engine="xlsxwriter")
with writer:
    for track_id, group in grouped:
        group.to_excel(writer, index=False, sheet_name=f'track_{track_id}')

# df.to_excel(writer, index=False, sheet_name='result')
# mf_products_preliminary.to_excel(writer, index=True, sheet_name='mf_products_preliminary')
# mf_products_final.to_excel(writer, index=True, sheet_name='mf_products_final_full')
# g_CPCF.to_excel(writer, index=True, sheet_name='mf_products_final')
# writer.close()

if post_visit_gas:
    writer = pd.ExcelWriter(''.join(('qubiq_result_gas', '.xlsx')), engine="xlsxwriter")
    df_gas.to_excel(writer, index=False, sheet_name='result')
    writer.close()

# plot_result(df,['diameter'], ['-'], [r'$диаметр\ частицы\ [мкм]$'], r'$d\ (мкм)$', '01_p_diameter')
# plot_result(df,['temperature'], ['-'], [r'$температура\ частицы\ [К]$'], r'$T\ (K)$', '04_p_temperature')
# plot_result(df,['mass'], ['-'], [r'$масса\ частицы\ [кг]$'], r'$m\ (кг)$', '02_p_mass')
# plot_result(df,['density'], ['-'], [r'$плотность частицы\ \left[\frac{кг}{м^3}\right]$'], r'$\rho\ \left(\frac{кг}{м^3}\right)$', '05_p_density')

if post_visit_gas:
    plot_result(df_gas, ['temperature'], ['-'], [r'$температура\ газа\ [К]$'], r'$T\ (K)$', '05_g_temperature')
    plot_result(df_gas,['mass_fractions_O2', 'mass_fractions_GV', 'mass_fractions_N2', 'mass_fractions_CPCP', 'mass_fractions_CPCF'], ['-', '-', '-', '-', '-'], ['массовая доля окислителя', 'массовая доля летучего', 'массовая доля азота', 'массовая доля первичных продуктов окисления', 'массовая доля конечных продуктов окисления'], r'$Y$', '08_g_mass_fractions')
    plot_result(df_gas, ['pressure'], ['-'], [r'давление\ газа\ [Па]$'], r'$P\ (Па)$', '06_g_pressure')



print('end')