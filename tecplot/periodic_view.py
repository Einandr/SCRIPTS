import tecplot as tp
from ansys.fluent.core.generated.solver.settings_242 import periodic
from tecplot.constant import *

tp.session.connect()

num_blades = 16
angle = 360.0 / num_blades
axis_of_rotation = 'X'




frame = tp.active_frame()
plot = frame.plot()



# plot.view.symmetry.rotation_axis = 'X'
# plot.view.symmetry.type = 'Periodic'
# plot.view.symmetry.num_periodic_repeats = num_blades
# plot.view.symmetry.periodic_angle = angle

# 4. Применяем симметрию к конкретным зонам (например, к зоне лопатки и втулки)
# Если нужно применить ко всем зонам — используйте цикл
for zone in tp.active_frame().dataset.zones():
    plot.fieldmap(zone).surfaces.use_symmetry = True

tp.active_frame().view.data_fit()
# print("Визуальное размножение секторов успешно настроено!")
