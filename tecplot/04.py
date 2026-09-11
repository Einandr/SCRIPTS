import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *

# Uncomment the following line to connect to a running instance of Tecplot 360:
# tp.session.connect()

tp.macro.execute_command('$!RedrawAll')
tp.macro.execute_command('$!RedrawAll')
tp.active_frame().plot().rgb_coloring.red_variable_index=23
tp.active_frame().plot().rgb_coloring.green_variable_index=3
tp.active_frame().plot().rgb_coloring.blue_variable_index=3
tp.active_frame().plot().contour(1).variable_index=4
tp.active_frame().plot().contour(2).variable_index=5
tp.active_frame().plot().contour(3).variable_index=6
tp.active_frame().plot().contour(4).variable_index=7
tp.active_frame().plot().contour(5).variable_index=8
tp.active_frame().plot().contour(6).variable_index=9
tp.active_frame().plot().contour(7).variable_index=10
tp.active_frame().plot().show_contour=False
tp.active_frame().plot().fieldmaps(0,1,2,3,4,5).surfaces.surfaces_to_plot=SurfacesToPlot.BoundaryFaces
tp.active_frame().plot().show_contour=True
tp.macro.execute_command('$!RedrawAll')
# End Macro.

