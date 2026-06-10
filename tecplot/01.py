import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *

# Uncomment the following line to connect to a running instance of Tecplot 360:
# tp.session.connect()

tp.active_frame().plot(PlotType.Cartesian3D).use_translucency=False
tp.macro.execute_command('$!RedrawAll')
tp.active_frame().plot(PlotType.Cartesian3D).use_translucency=True
tp.macro.execute_command('$!RedrawAll')
# End Macro.

