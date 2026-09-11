import tecplot as tp
import math
import time
import numpy as np
from ansys.fluent.core.generated.solver.settings_242 import periodic
from tecplot.constant import *

tp.session.connect()

frame = tp.active_frame()
dataset = frame.dataset

def compute_radius_and_theta(axial_direction="X", center_point=(0,0,0)):
    center_x, center_y, center_z = center_point

    var_names = list(tp.active_frame().dataset.variable_names)
    if "Radius" in var_names and "Theta" in var_names:
        print("Radius and Theta already exist. Skipping calculation")
        return

    print("Computing Radius and Theta")

    if axial_direction == "X":
        tp.data.operate.execute_equation(equation=f'{{Radius}} = sqrt((Y-{center_y})**2 + (Z-{center_z})**2)', ignore_divide_by_zero=True)
        tp.data.operate.execute_equation(equation=f'{{Theta}} = atan2((Y-{center_y}),(Z-{center_z}))', ignore_divide_by_zero=True)
    elif axial_direction == "Y":
        tp.data.operate.execute_equation(equation=f'{{Radius}} = sqrt((X-{center_x})**2 + (Z-{center_z})**2)', ignore_divide_by_zero=True)
        tp.data.operate.execute_equation(equation=f'{{Theta}} = atan2((X-{center_x}),(Z-{center_z}))', ignore_divide_by_zero=True)
    elif axial_direction == "Z":
        tp.data.operate.execute_equation(equation=f'{{Radius}} = sqrt((X-{center_x})**2 + (Y-{center_y})**2)', ignore_divide_by_zero=True)
        tp.data.operate.execute_equation(equation=f'{{Theta}} = atan2((X-{center_x}),(Y-{center_y}))', ignore_divide_by_zero=True)


def create_annular_slice(axial_direction="X", radius=0.0, center_point=(0,0,0)):
    ds = tp.active_frame().dataset

    compute_radius_and_theta(axial_direction, center_point)

    """
    Iso-surface method
    ------------------
    This method extracts an iso-surface at a constant radius. This method benefits from
    having the resulting grid be a good representation of the source grid. The problem with
    this method is that the resulting iso-surface will have a strip of cells that span the
    360-0 degree boundary. In 2D plots, these cells will be stretched across the entire plot. To
    combat this we use value blanking at the minimum of one of the axis variables (which corresponds
    with the periodic Theta boundary).  You do lose a small amount of information at the edges of the
    plot, and may need to hand adjust this value a little.
    """

    # Extract and Iso-Surface at the specified Radius
    print(f"Extracting iso-surface at radius={radius}")
    threed_plot = tp.active_frame().plot(PlotType.Cartesian3D)
    threed_plot.contour(0).variable = ds.variable("Radius")
    threed_plot.isosurface(0).isosurface_values[0] = radius
    threed_plot.show_isosurfaces = True

    num_zones = ds.num_zones
    tp.macro.execute_extended_command(command_processor_id='Extract Over Time',
        command='ExtractIsoSurfaceOverTime')

    # Grab the first extracted iso-surface
    iso_zone = ds.zone(num_zones)

    print("Creating 2D Plot")
    #
    # Create the 2D plot of the unwrapped annular slice, by plotting just the "left" and "right"
    # sides that we just extracted
    #
    twod_frame = tp.active_page().add_frame()
    twod_frame.plot_type=PlotType.Cartesian2D
    plot = twod_frame.plot()
    plot.activate()
    plot.solution_time = iso_zone.solution_time
    axes = plot.axes
    axes.x_axis.variable = ds.variable("Theta")

    # Assuming that X,Y,Z are the first three variables
    axis_num_map = {"X":0, "Y":1, "Z":2}
    axes.y_axis.variable = ds.variable(axis_num_map[axial_direction])
    axes.axis_mode=AxisMode.Independent
    plot.show_contour = True
    plot.fieldmaps().show = False
    plot.fieldmap(iso_zone).show = True
    plot.view.fit()

    if axial_direction == "Z":
        var_num_to_blank = axis_num_map["Y"]
    else:
        var_num_to_blank = axis_num_map["Z"]

    blanking = plot.value_blanking
    blanking.active=True
    blanking.constraint(0).active=True
    blanking.constraint(0).variable_index=var_num_to_blank
    blanking.constraint(0).comparison_operator=RelOp.LessThanOrEqual
    blanking.constraint(0).comparison_value=iso_zone.values(var_num_to_blank).min()
    blanking.cell_mode=ValueBlankCellMode.AnyCorner
    print("Value blanking as been set in the 2D plot to eliminate cells at the periodic boundary of Theta. You may need to adjust this value slightly. Visit Plot>Blanking>Value Blanking.")


axial_direction = 'X'
radius = 0.085
center_point = (0,0,0)

start = time.time()

compute_radius_and_theta(axial_direction, center_point)

print("Elapsed:", time.time()-start)

omega = -3927
center_y, center_z = 0.0, 0.0

# rotor_zones = [1,3,5,6,7,8,15,17,18,21,22,25,27]
# stator_zones = [2,4,9,10,11,12,13,14,16,19,20,23,24,26,28]

rotor_base_ids = [1,3,5,6,7,8,15,17,18,21,22,25,27]
stator_base_ids = [2,4,9,10,11,12,13,14,16,19,20,23,24,26,28]

num_zones_per_step = len(rotor_base_ids) + len(stator_base_ids)
num_time_steps = len(dataset.solution_times)
sector_offset = num_zones_per_step * num_time_steps

total_zones = dataset.num_zones
num_sectors = total_zones // sector_offset

print(f"Обнаружено временных шагов: {num_time_steps}")
print(f"Обнаружено физически размноженных секторов: {num_sectors}")

rotor_zones = []
stator_zones = []

for z_idx in range(total_zones):
    base_match = (z_idx % num_zones_per_step) + 1
    if base_match in rotor_base_ids:
        rotor_zones.append(z_idx)
    else:
        stator_zones.append(z_idx)

all_zones = rotor_zones + stator_zones


var_names = list(tp.active_frame().dataset.variable_names)

if "V_rad" not in var_names:
    tp.data.operate.execute_equation(
        equation=f'{{V_rad}} = ({{Y Velocity}}*(Y-{center_y}) + {{Z Velocity}}*(Z-{center_z})) / ({{Radius}} + 1e-10)',
        zones=all_zones, ignore_divide_by_zero=True
    )

if "V_theta_abs" not in var_names:
    tp.data.operate.execute_equation(
        equation=f'{{V_theta_abs}} = ({{Z Velocity}}*(Y-{center_y}) - {{Y Velocity}}*(Z-{center_z})) / ({{Radius}} + 1e-10)',
        zones=all_zones, ignore_divide_by_zero=True
    )

print("Вычисление относительных скоростей...")

# Для РОТОРА: вычитаем переносную скорость (omega * R)
tp.data.operate.execute_equation(
    equation=f'{{V_theta_rel}} = {{V_theta_abs}} - ({omega} * {{Radius}})',
    zones=rotor_zones, ignore_divide_by_zero=True
)

# Для СТАТОРA: относительная скорость равна абсолютной
tp.data.operate.execute_equation(
    equation=f'{{V_theta_rel}} = {{V_theta_abs}}',
    zones=stator_zones, ignore_divide_by_zero=True
)

# Итоговый модуль скорости V_rel для всех зон
tp.data.operate.execute_equation(
    equation=f'{{V_rel}} = sqrt({{X Velocity}}**2 + {{V_rad}}**2 + {{V_theta_rel}}**2)',
    zones=all_zones, ignore_divide_by_zero=True
)

tp.data.operate.execute_equation(
    equation='{P_tot_rel} = {Pressure} + ({Density} * {V_rel}**2) / 2',
    zones=all_zones,
    ignore_divide_by_zero=True
)



print("Расчет V_rel через цилиндрические координаты успешно выполнен для всего колеса!")
tp.active_frame().plot().push_attributes()
























# rotor_zones = [z - 1 for z in rotor_zones_base]
# stator_zones = [z - 1 for z in stator_zones_base]
# all_zones = rotor_zones + stator_zones
#
#
#
# # if "BladeSpeed" not in dataset.variable_names:
# for zone_idx in rotor_zones:
#     tp.data.operate.execute_equation(
#         equation=f'{{BladeSpeed}} = {omega} * {{Radius}}',
#         zones=[zone_idx-1],
#         ignore_divide_by_zero=True
#     )
# for zone_idx in stator_zones:
#     tp.data.operate.execute_equation(
#         equation=f'{{BladeSpeed}} = 0',
#         zones=[zone_idx - 1],
#         ignore_divide_by_zero=True
#     )
#
# print("Добавлена переменная 'BladeSpeed' для зон ротора")
#
#
# center_y, center_z = 0.0, 0.0
#
#
#
# # --- 3. Вычисление компонент окружной скорости ---
# tp.data.operate.execute_equation(
#     equation=f'{{U_z}} = -({omega}) * (Y-{center_y})',
#     ignore_divide_by_zero=True
# )
# tp.data.operate.execute_equation(
#     equation=f'{{U_y}} = {omega} * (Z-{center_z})',
#     ignore_divide_by_zero=True
# )
#
# tp.data.operate.execute_equation(
#     equation=f'{{V_rel}} = sqrt(({{Z Velocity}} - {{U_y}})**2 + ({{Y Velocity}} + {{U_z}})**2 + {{X Velocity}}**2)',
#     ignore_divide_by_zero=True
# )
# print("Добавлена переменная 'V_rel'")




# tp.data.operate.execute_equation(equation=f'{{Radius}} = sqrt((Y-{center_y})**2 + (Z-{center_z})**2)', ignore_divide_by_zero=True)
