import sys
import os
import re
import pandas as pd
import vtk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.pylab as pylab
from glob import glob
from scipy.interpolate import interp1d, griddata
from enum import Enum, auto


class Solver(Enum):
    FLUENT = auto()
    QUBIQ = auto()


# from tecplot.utils import Solver
from postprocessing.utils import create_animation_tracks, AnimateBy


params = {'legend.fontsize'      : 'xx-large',
          'legend.title_fontsize': 'xx-large',
          'axes.labelsize'       : 'xx-large',
          'axes.titlesize'       : 'xx-large',
          'xtick.labelsize'      : 'xx-large',
          'ytick.labelsize'      : 'xx-large'}
pylab.rcParams.update(params)

plt.rcParams['animation.ffmpeg_path'] = r'C:\Users\YA\Downloads\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'

save_tracks_by_Track_ID = False
animate_tracks = True
# animate_by_string = 'TRACK_ID'
animate_by_string = 'TIME'
# solver_string = 'FLUENT'
solver_string = 'QUBIQ'

# time_range = (0.400345, 0.402265)
time_range = None

track_id_range = (1000, 38000)
# track_id_range = (3, 12)
# track_id_range = None

mfr_particles = 0.1155


solver = Solver[solver_string.upper()]
animate_by = AnimateBy[animate_by_string.upper()]

match solver:
    case Solver.FLUENT:
        parameters_to_plot = ['Diameter', 'Mass', 'Temperature', 'Mass_Flux','Diameter_Mass_Flux','Mass_Mass_Flux','Mass_Flow_Rate','Diameter_mave','Mass_mave']
    case Solver.QUBIQ:
        parameters_to_plot = ['diameter']
        # parameters_to_plot = ['diameter', 'mass', 'temperature', 'density']
        # parameters_to_plot = ['diameter', 'mass', 'temperature', 'density', 'velocity_x', 'velocity_y', 'velocity_z', 'velocity']
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")


match solver:
    case Solver.FLUENT:
        # input_dir = r'D:\YASIM\VORON\2026_15_Spalding_Combustion\FLUENT\T1000K_freq10000_comb_v0.0ms_pmfr0.00000179_ts1e-5_Direct'
        # input_dir = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\03_LES_analytic\part'
        # input_dir = r'E:\YASIM\VORON_TEMP\2026_12_Iskra_OPZ\high_changed_opz_coeff'
        input_dir = r'E:\YASIM\VORON_TEMP\2026_12_Iskra_OPZ\high_OPZ_b08'
    case Solver.QUBIQ:
        input_dir = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\validation_from_oleg_1st\part'
        # input_dir = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\LES_HOT_HIGH\part'
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")


output_dir = os.path.join(input_dir, "tracks")
os.makedirs(output_dir, exist_ok=True)
path_animation = os.path.join(input_dir, "animations")
os.makedirs(path_animation, exist_ok=True)


def extract_time_from_filename(filename):
    """Извлекает время из имени файла (например, 'my_xyz_export_time_0.139403.csv' -> 0.139403)."""
    match = re.search(r'time_([0-9.]+)', filename)
    time_str = match.group(1).rstrip('.')
    return float(time_str) if match else None




# match solver:
#     case Solver.FLUENT:
#
#     case Solver.QUBIQ:
#
#     case _:
#         raise ValueError(f"Неподдерживаемый решатель: {solver}")


match solver:
    case Solver.FLUENT:
        if animate_by == AnimateBy.TIME:
            files = glob(os.path.join(input_dir, '*_averaged_FLUENT.csv'))
        else:
            files = [f for f in glob(os.path.join(input_dir, '*.txt')) if not f.endswith('_averaged.txt')]
    case Solver.QUBIQ:
        if animate_by == AnimateBy.TIME:
            files = glob(os.path.join(input_dir, '*_averaged.csv'))
        else:
            files = [f for f in glob(os.path.join(input_dir, '*.csv')) if not f.endswith('_averaged.csv')]
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")

all_data = []

for file in files:
    try:
        match solver:
            case Solver.FLUENT:
                df = pd.read_csv(file, sep=',', engine='python')
            case Solver.QUBIQ:
                df = pd.read_csv(file, sep='\s+', engine='python')
            case _:
                raise ValueError(f"Неподдерживаемый решатель: {solver}")

        time = extract_time_from_filename(os.path.basename(file))
        if time is None:
            print(f"⚠️ Не удалось извлечь время из файла: {file}")
            continue
        df['time'] = time
        if not df.empty and len(df.columns) > 0:
            match solver:
                case Solver.FLUENT:

                    df = df.rename(columns={
                        'p_ID': 'track_id',
                        'p_current_time': 'time',
                        'p_diameter': 'diameter',
                        'p_mass': 'mass',
                        'p_temperature': 'temperature',
                        'p_density': 'density',
                    })
                case Solver.QUBIQ:
                    pass
                case _:
                    raise ValueError(f"Неподдерживаемый решатель: {solver}")
            all_data.append(df)
    except Exception as e:
        print(f"❌ Ошибка при чтении файла {file}: {e}")
        continue

if not all_data:
    print("❌ Не найдены файлы для обработки.")


combined_df = pd.concat(all_data, ignore_index=True)
match animate_by:
    case AnimateBy.TRACK_ID:
        combined_df = combined_df.sort_values(by=['track_id', 'time'])
        combined_df['time_local'] = combined_df.groupby('track_id')['time'].transform(
            lambda x: x - x.min()
        )
        combined_df = combined_df.set_index('time_local', drop=False, append=False)
    case AnimateBy.TIME:
        combined_df = combined_df.sort_values(by=['time', 'X'])
    case _:
        raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")




if save_tracks_by_Track_ID and animate_by==AnimateBy.TRACK_ID:
    for track_id, track_data in combined_df.groupby('track_id'):
        track_file = os.path.join(output_dir, f'track_{track_id}.csv')
        track_data.sort_values(by='time', inplace=True)  # Сортируем по времени
        # time_min = track_data['time'].min()
        # track_data['time_local'] = track_data['time'] - time_min
        track_data.to_csv(track_file, index=False)
        print(f"✅ Сохранён трек {track_id} в {track_file}")




# Фильтрация треков
match animate_by:
    case AnimateBy.TRACK_ID:
        if track_id_range:
            # Фильтруем по диапазону track_id (учитываем пропущенные значения)
            filtered_tracks = combined_df[
                (combined_df['track_id'] >= track_id_range[0]) &
                (combined_df['track_id'] <= track_id_range[1])
            ]
        else:
            filtered_tracks = combined_df
    case AnimateBy.TIME:
        if time_range:
            print('что же он выдаст', combined_df['time'], time_range)
            filtered_tracks = combined_df[
                (combined_df['time'] >= time_range[0]) &
                (combined_df['time'] <= time_range[1])
            ]
        else:
            filtered_tracks = combined_df
    case _:
        raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")


match solver:
    case Solver.FLUENT:
        filtered_tracks.loc[:, 'Diameter'] = filtered_tracks['Diameter'] * 1e6
        filtered_tracks.loc[:, 'Diameter_mave'] = filtered_tracks['Diameter_mave'] * 1e6
        filtered_tracks.loc[:, 'Combustion_Efficiency'] = 1 - filtered_tracks['Mass_Flow_Rate']/mfr_particles
    case Solver.QUBIQ:
        filtered_tracks['diameter'] = filtered_tracks['diameter'] * 1e6
    case _:
        raise ValueError(f"Неподдерживаемый решатель: {solver}")


# Определяем количество кадров (frames)
match animate_by:
    case AnimateBy.TRACK_ID:
        unique_tracks = filtered_tracks['track_id'].unique()
        frames = len(unique_tracks)
        print(f"📊 Найдено {frames} треков для анимации.")
    case AnimateBy.TIME:
        unique_time = filtered_tracks['time'].unique()
        frames = len(unique_time)
        print(f"📊 Найдено {frames} моментов времени для анимации.")
    case _:
        raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")

# match animate_by:
#     case AnimateBy.TRACK_ID:
#
#     case AnimateBy.TIME:
#
#     case _:
#         raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")

match animate_by:
    case AnimateBy.TRACK_ID:
        track_counts = filtered_tracks.groupby('track_id').size()
        max_points_track_id = track_counts.idxmax()
        max_points = track_counts.max()
        print(f"Track ID с максимальным числом точек: {max_points_track_id}")
        print(f"Максимальное количество точек: {max_points}")
        # Интерполяция данных каждого трека на регулярную сетку
        interpolation_steps = max_points
        max_track_lifetime = filtered_tracks['time_local'].max()
        max_time_local_per_track = filtered_tracks.groupby('track_id')['time_local'].max()
        min_track_lifetime = max_time_local_per_track.min()
        avg_track_lifetime = max_time_local_per_track.mean()
        print(f"📊 Минимальное время жизни трека: {min_track_lifetime:.6f} с")
        print(f"📊 Максимальное время жизни трека: {max_track_lifetime:.6f} с")
        print(f"📊 Среднее время жизни треков: {avg_track_lifetime:.6f} с")

        normalized_time_grid = np.linspace(0, avg_track_lifetime, interpolation_steps)
        interpolated_data = {}
        for param in parameters_to_plot:
            interpolated_data[param] = []

        for track_id, track_data in filtered_tracks.groupby('track_id'):
            track_max_time = track_data['time_local'].max()
            normalized_time = track_data['time_local'] * (avg_track_lifetime / track_max_time)
            for param in parameters_to_plot:
                if param in track_data.columns:
                    interp_func = interp1d(
                        normalized_time,
                        # track_data['time_local'],
                        track_data[param],
                        kind='linear',
                        bounds_error=False,
                        fill_value=np.nan
                    )
                    interpolated_values = interp_func(normalized_time_grid)
                    interpolated_data[param].append(interpolated_values)

            # print(interpolated_data['diameter'])

        averaged_data = pd.DataFrame({'time_local': normalized_time_grid})
        for param in parameters_to_plot:
            if interpolated_data[param]:
                # averaged_data[param] = np.mean(interpolated_data[param], axis=0)
                averaged_data[param] = np.nanmean(interpolated_data[param], axis=0)

        avg_file = os.path.join(output_dir, 'averaged_data.csv')
        averaged_data.to_csv(avg_file, index=False)
        print(f"✅ Осреднённые данные сохранены в {avg_file}")
    case AnimateBy.TIME:
        if 'X' in filtered_tracks.columns:
            # Группируем по времени и осредняем параметры
            averaged_data = filtered_tracks.groupby('X').agg({
                param: 'mean' for param in parameters_to_plot
            }).reset_index()

            avg_file = os.path.join(output_dir, 'averaged_data_by_time.csv')
            averaged_data.to_csv(avg_file, index=False)
            print(f"✅ Осреднённые данные по времени сохранены в {avg_file}")
        else:
            print("⚠️ В данных отсутствует столбец 'X' для осреднения по времени.")
    case _:
        raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")




style_average = '-'
style_instant = '--'

GOST = True
line_width = 2

y_limits = {
    'particle_Diameter': [0, 5],
    'particle_Temperature': [0, 600],
    'particle_Mass': [0, 1.8e-13],
    'particle_Mass_Flow_Rate': [0,0.15],
    'particle_Density': [0, 850],
    'particle_Velocity': [0, 100],
    'particle_Velocity_x': [0, 100],
    'particle_Velocity_y': [0, 100],
    'particle_Velocity_z': [0, 100],
    'particle_Combustion_Efficiency': [0,1.1]
}

colors = plt.cm.tab10.colors[:10]
y_limits_default = None




match animate_by:
    case AnimateBy.TRACK_ID:
        min_track_id = filtered_tracks['track_id'].min()
        min_track_group = filtered_tracks[filtered_tracks['track_id'] == min_track_id]
        max_points_track_group = filtered_tracks[filtered_tracks['track_id'] == max_points_track_id]
    case AnimateBy.TIME:
        min_time = filtered_tracks['time'].min()
        min_time_group = filtered_tracks[filtered_tracks['time'] == min_time]
    case _:
        raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")

# match animate_by:
#     case AnimateBy.TRACK_ID:
#
#     case AnimateBy.TIME:
#
#     case _:
#         raise ValueError(f"Неподдерживаемый тип анимации: {animate_by}")

if animate_tracks:
    os.chdir(path_animation)
    # ox_label = r'$t,\ с$'
    ox_label = r'$x,\ м$'
    # oy_label = r'$d,\ мкм$'
    # x_limits = None
    t_limit_low = 0
    t_limit_high = 0.01
    vertical_lines = None
    horizontal_lines = None
    show_track_numbers_or_time = True

    x_limit_low = -0.5
    # x_limit_high = 1.7
    x_limit_high = 3.7

    match solver:
        case Solver.FLUENT:
            config_diameter = [
                (min_time_group, ['Diameter'], [style_instant], ['для момента времени'], y_limits['particle_Diameter'], colors),
            ]
            config_diameter_mave = [
                (min_time_group, ['Diameter_mave'], [style_instant], ['для момента времени'], y_limits['particle_Diameter'], colors),
            ]
            config_mass = [
                (min_time_group, ['Mass'], [style_instant], ['для момента времени'], y_limits['particle_Mass'], colors),
            ]
            config_mass_mave = [
                (min_time_group, ['Mass_mave'], [style_instant], ['для момента времени'], y_limits['particle_Mass'], colors),
            ]
            config_mass_flow_rate = [
                (min_time_group, ['Mass_Flow_Rate'], [style_instant], ['для момента времени'], y_limits['particle_Mass_Flow_Rate'], colors),
            ]
            config_combustion_efficiency = [
                (min_time_group, ['Combustion_Efficiency'], [style_instant], ['для момента времени'], y_limits['particle_Combustion_Efficiency'], colors),
            ]

        case Solver.QUBIQ:
            config_diameter = [
                (min_time_group, ['diameter'], [style_instant], ['для момента времени'], y_limits['particle_Diameter'], colors),
            ]
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")


    # config_temperature = [
    #     (max_points_track_group, ['temperature'], [style_instant], ['для конкретного трека'], y_limits['particle_Temperature'], colors),
    # ]
    #
    # config_mass = [
    #     (max_points_track_group, ['mass'], [style_instant], ['для конкретного трека'], y_limits['particle_Mass'], colors),
    # ]
    #
    # config_density = [
    #     (max_points_track_group, ['density'], [style_instant], ['для конкретного трека'], y_limits['particle_Density'], colors),
    # ]


    match solver:
        case Solver.FLUENT:
            # ДИАМЕТР
            create_animation_tracks(
                animate_by=animate_by.TIME,
                anim_base_name='',
                ox_label=ox_label,
                oy_label=r'$d,\ мкм$',
                filtered_tracks=filtered_tracks,
                params_config=config_diameter,
                GOST=GOST,
                ox_limits=[x_limit_low, x_limit_high],
                line_width=line_width,
                output_name='Diameter',
                show_track_numbers_or_time=show_track_numbers_or_time
            )

            # ДИАМЕТР осредненный по расходу
            create_animation_tracks(
                animate_by=animate_by.TIME,
                anim_base_name='',
                ox_label=ox_label,
                oy_label=r'$d,\ мкм$',
                filtered_tracks=filtered_tracks,
                params_config=config_diameter_mave,
                GOST=GOST,
                ox_limits=[x_limit_low, x_limit_high],
                line_width=line_width,
                output_name='Diameter_mave',
                show_track_numbers_or_time=show_track_numbers_or_time
            )

            # МАССА
            create_animation_tracks(
                animate_by=animate_by.TIME,
                anim_base_name='',
                ox_label=ox_label,
                oy_label=r'$m,\ кг$',
                filtered_tracks=filtered_tracks,
                params_config=config_mass,
                GOST=GOST,
                ox_limits=[x_limit_low, x_limit_high],
                line_width=line_width,
                output_name='Mass',
                show_track_numbers_or_time=show_track_numbers_or_time
            )

            # МАССА осредненная по расходу
            create_animation_tracks(
                animate_by=animate_by.TIME,
                anim_base_name='',
                ox_label=ox_label,
                oy_label=r'$m,\ кг$',
                filtered_tracks=filtered_tracks,
                params_config=config_mass_mave,
                GOST=GOST,
                ox_limits=[x_limit_low, x_limit_high],
                line_width=line_width,
                output_name='Mass_mave',
                show_track_numbers_or_time=show_track_numbers_or_time
            )

            # Расход
            create_animation_tracks(
                animate_by=animate_by.TIME,
                anim_base_name='',
                ox_label=ox_label,
                oy_label=r'$m,\ кг$',
                filtered_tracks=filtered_tracks,
                params_config=config_mass_flow_rate,
                GOST=GOST,
                ox_limits=[x_limit_low, x_limit_high],
                line_width=line_width,
                output_name='MFR',
                show_track_numbers_or_time=show_track_numbers_or_time
            )

            # Полнота сгорания частиц
            create_animation_tracks(
                animate_by=animate_by.TIME,
                anim_base_name='',
                ox_label=ox_label,
                oy_label=r'$m,\ кг$',
                filtered_tracks=filtered_tracks,
                params_config=config_combustion_efficiency,
                GOST=GOST,
                ox_limits=[x_limit_low, x_limit_high],
                line_width=line_width,
                output_name='Etta',
                show_track_numbers_or_time=show_track_numbers_or_time
            )

        case Solver.QUBIQ:
            create_animation_tracks(
                animate_by=animate_by.TIME,
                anim_base_name='',
                ox_label=ox_label,
                oy_label=r'$d,\ мкм$',
                filtered_tracks=filtered_tracks,
                params_config=config_diameter,
                GOST=GOST,
                ox_limits=[x_limit_low, x_limit_high],
                line_width=line_width,
                output_name='Diameter',
                show_track_numbers_or_time=show_track_numbers_or_time
            )
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")





    # create_animation_tracks(
    #     animate_by=animate_by.TIME,
    #     anim_base_name='',
    #     ox_label=ox_label,
    #     oy_label=r'$d,\ мкм$',
    #     filtered_tracks=filtered_tracks,
    #     params_config=config_diameter,
    #     GOST=GOST,
    #     ox_limits=[t_limit_low, t_limit_high],
    #     line_width=line_width,
    #     output_name='Diameter',
    #     show_track_numbers_or_time=show_track_numbers_or_time
    # )

    # create_animation_tracks(
    #     anim_base_name='',
    #     ox_label=ox_label,
    #     oy_label=r'$T,\ K$',
    #     filtered_tracks=filtered_tracks,
    #     params_config=config_temperature,
    #     GOST=GOST,
    #     ox_limits=[t_limit_low, t_limit_high],
    #     line_width=line_width,
    #     output_name='Temperature',
    #     show_track_numbers=show_track_numbers
    # )
    #
    # create_animation_tracks(
    #     anim_base_name='',
    #     ox_label=ox_label,
    #     oy_label=r'$m,\ кг$',
    #     filtered_tracks=filtered_tracks,
    #     params_config=config_mass,
    #     GOST=GOST,
    #     ox_limits=[t_limit_low, t_limit_high],
    #     line_width=line_width,
    #     output_name='Mass',
    #     show_track_numbers=show_track_numbers
    # )
    #
    # create_animation_tracks(
    #     anim_base_name='',
    #     ox_label=ox_label,
    #     oy_label=r'$\rho\ \left(\frac{кг}{м^3}\right)$',
    #     filtered_tracks=filtered_tracks,
    #     params_config=config_density,
    #     GOST=GOST,
    #     ox_limits=[t_limit_low, t_limit_high],
    #     line_width=line_width,
    #     output_name='Density',
    #     show_track_numbers=show_track_numbers
    # )

r'$\rho\ \left(\frac{кг}{м^3}\right)$'

print('debug')