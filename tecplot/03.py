import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *

# Uncomment the following line to connect to a running instance of Tecplot 360:
# tp.session.connect()

tp.active_frame().plot().fieldmaps(0,1,2,3,4,5).contour.show=False
tp.macro.execute_command('$!RedrawAll')
tp.active_frame().plot().fieldmaps(5).contour.show=True
tp.active_frame().plot().fieldmaps(4).contour.show=True
tp.active_frame().plot().fieldmaps(3).contour.show=True
tp.active_frame().plot().fieldmaps(0,1,2).contour.show=True
tp.macro.execute_command('$!RedrawAll')
# End Macro.

