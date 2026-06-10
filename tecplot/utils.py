import tecplot as tp
# from tecplot.exception import *
from tecplot.constant import *
from enum import Enum, auto
from ast import literal_eval
from typing import Union, Tuple, Any
from pathlib import Path


class Solver(Enum):
    FLUENT = auto()
    QUBIQ = auto()


def convert_to_tuple(input: str) -> Tuple[Union[int, float, str, Any], ...]:
    """Конвертирует строку из файла конфигурации в кортеж.

    Функция обрабатывает различные форматы входных данных:
    - Пустая строка → возвращает пустой кортеж.
    - Одиночное значение (число, строка) → возвращает кортеж с одним элементом.
    - Множество значений через запятую → возвращает кортеж из этих значений.

    Args:
        input (str): Входная строка из файла конфигурации. Может содержать:
            - Пустую строку.
            - Одиночное значение (например, "42", "3.14", "'hello'").
            - Множество значений через запятую (например, "1, 2, 3" или "'a', 'b', 'c'").

    Returns:
        Tuple[Union[int, float, str, Any], ...]:
            - Пустой кортеж, если входная строка пустая.
            - Кортеж с одним элементом, если входное значение одиночное.
            - Кортеж из нескольких элементов, если вход содержит несколько значений.

    Examples:
        >>> convert_to_tuple('')
        ()
        >>> convert_to_tuple('42')
        (42,)
        >>> convert_to_tuple('1, 2, 3')
        (1, 2, 3)
        >>> convert_to_tuple("'hello'")
        ('hello',)
    """
    if input == '':
        return ()
    elif isinstance(literal_eval(input), (int, float, str)):
        return literal_eval(input),
    else:
        return literal_eval(input)


def rename_variable(old_name, new_name, dataset):
    try:
        print(f'Переименование {old_name} в {new_name}')
        dataset.variable(old_name).name = new_name
    except AttributeError as e:
        print(f'Переменная с именем {old_name} уже переименована в {new_name}')


def execute_equation(name, formula, var_names):
    print(f'Вычисление {{{name}}} = {formula}')
    if name not in var_names:
        tp.data.operate.execute_equation(equation=f'{{{name}}}={formula}')
    else:
        print(f'Переменная {name} уже существует. Вычисление пропущено.')


def set_rotation_angles(rotation_angles):
    tp.active_frame().plot().view.psi = rotation_angles[0]
    tp.active_frame().plot().view.theta = rotation_angles[1]
    tp.active_frame().plot().view.alpha = rotation_angles[2]
    tp.active_frame().plot().view.fit_surfaces(consider_blanking=True)
    tp.macro.execute_command('$!WorkspaceView FitAllFrames')
    tp.macro.execute_command('$!RedrawAll')


def set_cross_sections(x_cross_start, x_cross_end, n_cross_sections, dataset, variable_name, variable_min, variable_max, variable_increment, legend_text=None) -> bool:
    """Отображение переменной на поперечных сечениях.
    Args:
        x_cross_start: Координата первого сечения.
        x_cross_end: Координата последнего сечения.
        n_cross_sections: Число сечений.
        dataset: Набор данных Tecplot.
        variable_name: Имя переменной для отображения.
        variable_min: Минимальное значение для цветовой шкалы.
        variable_max: Максимальное значение для цветовой шкалы.
        variable_increment: Шаг для легенды.
        legend_text: Текст для легенды.
    Returns:
        bool: True, если переменная была успешно отображена.
              False, если переменная отсутствует и была пропущена.
    """

    try:
        variable_index = dataset.variable(variable_name).index
    except AttributeError:
        print(f'Отсутствует переменная {variable_name} (установка поперечных сечений) - пропускаем')
        return False

    tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = True
    tp.active_frame().plot().show_shade = True
    tp.active_frame().plot(PlotType.Cartesian3D).show_isosurfaces = False
    tp.active_frame().plot().show_contour = False
    tp.active_frame().plot().contour(0).variable_index = variable_index
    tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True

    set_variable_legend(variable_min, variable_max, variable_increment, legend_text)

    current_slice = tp.active_frame().plot().slice(0)
    current_slice.show = True
    current_slice.orientation = SliceSurface.XPlanes
    current_slice.show_start_and_end_slices = True
    current_slice.start_position.x = x_cross_start
    current_slice.end_position.x = x_cross_end
    current_slice.show_intermediate_slices = True
    current_slice.num_intermediate_slices = n_cross_sections - 2
    current_slice.show_primary_slice = False
    tp.macro.execute_command('$!RedrawAll')
    print(f'Установлены поперечные сечения для переменной {variable_name} x_start = {x_cross_start}, x_end = {x_cross_end}, n_cross_sections = {n_cross_sections}')
    return True


def change_variable_prefix(old_prefix, new_prefix, dataset, check_space=False):
    for var in dataset.variables():
        if var.name.startswith(old_prefix):
            suffix = var.name[len(old_prefix):]
            if check_space and ' ' in suffix:
                continue
            old_name = var.name
            new_name = new_prefix + suffix
            rename_variable(old_name, new_name, dataset)


def rename_variables(dataset, solver):
    match solver:
        case Solver.FLUENT:
            rename_variable('Static Temperature', 'Temperature', dataset)
            rename_variable('Static Pressure', 'Pressure', dataset)
            change_variable_prefix('Mass fraction of ', 'Y_', dataset, check_space=True)
            rename_variable('X Velocity', 'Velocity_X', dataset)
            rename_variable('Y Velocity', 'Velocity_Y', dataset)
            rename_variable('Z Velocity', 'Velocity_Z', dataset)
            rename_variable('X', 'CoordinateX', dataset)
            rename_variable('Y', 'CoordinateY', dataset)
            rename_variable('Z', 'CoordinateZ', dataset)
        case Solver.QUBIQ:
            change_variable_prefix('ALL/', '', dataset)
            rename_variable('X', 'CoordinateX', dataset)
            rename_variable('Y', 'CoordinateY', dataset)
            rename_variable('Z', 'CoordinateZ', dataset)
            # Осредненные
            change_variable_prefix('mean_mass_fractions_', 'mean_Y_', dataset)
            rename_variable('mean_temperature', 'mean_Temperature', dataset)
            rename_variable('mean_pressure', 'mean_Pressure', dataset)
            rename_variable('mean_density', 'mean_Density', dataset)
            rename_variable('mean_velocity', 'mean_Velocity', dataset)
            rename_variable('mean_velocity_x', 'mean_Velocity_X', dataset)
            rename_variable('mean_velocity_y', 'mean_Velocity_Y', dataset)
            rename_variable('mean_velocity_z', 'mean_Velocity_Z', dataset)
            # Мгновенные
            change_variable_prefix('mass_fractions_', 'Y_', dataset)
            rename_variable('temperature', 'Temperature', dataset)
            rename_variable('pressure', 'Pressure', dataset)
            rename_variable('density', 'Density', dataset)
            rename_variable('velocity_magnitude', 'Velocity', dataset)
            rename_variable('velocity_x', 'Velocity_X', dataset)
            rename_variable('velocity_y', 'Velocity_Y', dataset)
            rename_variable('velocity_z', 'Velocity_Z', dataset)
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")


def parse_species(dataset, solver):
    species = []
    match solver:
        case Solver.FLUENT:
            prefixes = ['Mass fraction of ', 'Y_']
        case Solver.QUBIQ:
            prefixes = ['mass_fractions_', 'Y_']
        case _:
            raise ValueError(f"Неподдерживаемый решатель: {solver}")
    for var in dataset.variables():
        for prefix in prefixes:
            if var.name.startswith(prefix):
                suffix = var.name[len(prefix):]
                if ' ' not in suffix and suffix not in species:
                    species.append(suffix)
    return species


# def zones_tranclucency(trans_walls, trans_slice,)
#     tp.active_frame().plot().fieldmaps(0).effects.surface_translucency = 90
#     tp.active_frame().plot().fieldmaps(1, 2, 3, 4).effects.surface_translucency = 90
#     tp.active_frame().plot().fieldmaps(5).effects.surface_translucency = 20
#     tp.active_frame().plot().fieldmaps(6).show = False
#     tp.active_frame().plot().fieldmaps(5).show = False
#     tp.active_frame().plot().fieldmaps(5).show = True


def plot_solution_time():
    tp.macro.execute_command("""$!AttachText
      AnchorPos {X=1 Y=95}
      TextShape {IsBold=Yes IsItalic=Yes Height=12}
      Text = '&(solutiontime%.5f)'""")


def set_variable_legend(variable_min, variable_max, variable_increment, legend_text=None):
    contour = tp.active_frame().plot().contour(0)
    contour.colormap_name = 'Small Rainbow'
    # contour.colormap_name = 'Modified Rainbow - Dark ends'
    contour.colormap_filter.distribution = ColorMapDistribution.Continuous
    contour.colormap_filter.continuous_min = variable_min
    contour.colormap_filter.continuous_max = variable_max
    legend = contour.legend
    legend.show = True
    legend.vertical = False
    legend.label_location = ContLegendLabelLocation.Increment
    legend.label_increment = variable_increment
    legend.position = (85, 95)
    legend.number_font.size = 2.0
    legend.number_font.bold = True
    legend.number_font.italic = True
    legend.box.box_type = tp.constant.TextBox.None_
    legend.header.show = False
    if legend_text:
        tp.macro.execute_command(''.join(('$!AttachText AnchorPos {X=1 Y=5} TextShape {IsBold=Yes IsItalic=Yes Height=10} Text=\'', legend_text, '\'')))


def plot_variable(dataset, variable_name, variable_min, variable_max, variable_increment, slice=None, slice_coordinate=0, shade=False, legend_text=None) -> bool:
    """Отображение переменной на контуре или сечении.
    Args:
        dataset: Набор данных Tecplot.
        variable_name: Имя переменной для отображения.
        variable_min: Минимальное значение для цветовой шкалы.
        variable_max: Максимальное значение для цветовой шкалы.
        variable_increment: Шаг для легенды.
        slice: Если ('X', 'Y', 'Z'), отображать слайс вместо контура.
        slice_coordinate: Координата слайса.
        shade: Отображение полупрозрачного контура геометрии.
        legend_text: Текст для легенды.
    Returns:
        bool: True, если переменная была успешно отображена.
              False, если переменная отсутствует и была пропущена.
    """
    try:
        variable_index = dataset.variable(variable_name).index
    except AttributeError:
        print(f'Переменная {variable_name} отсутствует. Пропускаем.')
        return False
    contour = tp.active_frame().plot().contour(0)
    contour.variable_index = variable_index
    if shade:
        tp.active_frame().plot().show_shade = True
    else:
        tp.active_frame().plot().show_shade = False

    if slice:
        tp.active_frame().plot().show_contour = False
    else:
        tp.active_frame().plot().show_contour = True
        tp.active_frame().plot(PlotType.Cartesian3D).show_slices = False
        tp.active_frame().plot(PlotType.Cartesian3D).use_translucency = False

    set_variable_legend(variable_min, variable_max, variable_increment, legend_text)
    if slice:
        tp.active_frame().plot(PlotType.Cartesian3D).show_slices = True
        current_slice = tp.active_frame().plot().slice(0)
        current_slice.show_primary_slice = True
        current_slice.show_start_and_end_slices = False
        current_slice.show_intermediate_slices = False
        match slice:
            case 'X':
                current_slice.orientation = SliceSurface.XPlanes
                current_slice.origin.z = slice_coordinate
                # current_slice.origin = (slice_coordinate, current_slice.origin[1], current_slice.origin[2])
            case 'Y':
                current_slice.orientation = SliceSurface.YPlanes
                current_slice.origin.y = slice_coordinate
            case 'Z':
                current_slice.orientation = SliceSurface.ZPlanes
                current_slice.origin.z = slice_coordinate
            case _:
                raise ValueError(f"Неверно передано сечение: {slice}")
    print(f'Отображена переменная {variable_name}')
    return True


def save_image(path, name):
    Path(path).mkdir(parents=True, exist_ok=True)
    tp.export.save_jpeg(''.join((path, '\\', name, '.jpeg')),
                        width=1920,
                        region=ExportRegion.CurrentFrame,
                        supersample=3,
                        quality=100,
                        encoding=JPEGEncoding.Standard)
    print(f'Экспорт рисунка {name}')


def export_movie(path, name, start_time, end_time):
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f'Экспорт анимации переменной {name} ...')
    tp.export.save_time_animation_mpeg4(''.join((path, '\\', name, '.mp4')),
        start_time=start_time,
        end_time=end_time,
        timestep_step=1,
        width=1920,
        animation_speed=25,
        region=ExportRegion.CurrentFrame,
        supersample=3)


def Export_Movie(name, Frame, AllFrames):
    print('Exporting movie ...')
    tp.macro.execute_command(''.join(('$!Framecontrol Activatebynumber Frame = ', str(Frame))))
    movie_export_command = ''.join(('$!ExportSetup \n  ExportFName = \'', work_path, name, '.mp4\''))
    tp.macro.execute_command('''$!ExportSetup ExportFormat = MPEG4''')
    tp.macro.execute_command('''$!ExportSetup ImageWidth = 1920''')
    tp.macro.execute_command('''$!ExportSetup AnimationSpeed = 25''')
    if AllFrames:
        tp.macro.execute_command('''$!ExportSetup ExportRegion = AllFrames''')
    else:
        tp.macro.execute_command('''$!ExportSetup ExportRegion = CurrentFrame''')
    tp.macro.execute_command(movie_export_command)
    animate_command = ''.join(('$!AnimateTime\n  StartTime = ', str(time_start), '\n  EndTime = ', str(time_end),
                               '\n  Skip = 1\n  CreateMovieFile = Yes'))
    tp.macro.execute_command(animate_command)
    print('Movie on frame ', Frame, name, 'exported\n')