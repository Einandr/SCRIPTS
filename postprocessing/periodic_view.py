import tecplot as tp
from tecplot.constant import *

tp.session.connect()
plot = tp.active_frame().plot()

# 1. Задаем параметры периодичности
num_blades = 12                     # Всего лопаток в колесе
angle = 360.0 / num_blades          # Угол одного сектора (30 градусов)

# 2. Настраиваем ось вращения (например, ось Z)
# 0 = X, 1 = Y, 2 = Z
plot.symmetry.rotation_axis = 2

# 3. Включаем циклическое размножение
plot.symmetry.type = SymmetryType.Periodic
plot.symmetry.num_periodic_repeats = num_blades
plot.symmetry.periodic_angle = angle

# 4. Применяем симметрию к конкретным зонам (например, к зоне лопатки и втулки)
# Если нужно применить ко всем зонам — используйте цикл
for zone in tp.active_frame().dataset.zones():
    plot.fieldmap(zone).surfaces.use_symmetry = True

tp.active_frame().view.data_fit()
print("Визуальное размножение секторов успешно настроено!")
