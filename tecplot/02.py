import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *

# Uncomment the following line to connect to a running instance of Tecplot 360:
# tp.session.connect()

tp.macro.execute_command("""$!ReadDataSet  '\"D:\\YASIM\\VORON\\2026_12_Iskra_OPZ\\QUBIQ\\LES_HOT_HIGH\\visit_ex_db_3D2.plt\" '
  ReadDataOption = New
  ResetStyle = Yes
  VarLoadMode = ByName
  AssignStrandIDs = Yes
  VarNameList = '\"X\" \"Y\" \"Z\" \"ALL/Mach\" \"ALL/pressure\" \"ALL/temperature\" \"ALL/density\" \"ALL/velocity_magnitude\" \"ALL/velocity_x\" \"ALL/velocity_y\" \"ALL/velocity_z\" \"ALL/mass_fractions_Air\" \"ALL/mass_fractions_CP\" \"ALL/mass_fractions_GPG\" \"ALL/mean_pressure\" \"ALL/mean_temperature\" \"ALL/mean_density\" \"ALL/mean_velocity_x\" \"ALL/mean_velocity_y\" \"ALL/mean_velocity_z\" \"ALL/mean_mass_fractions_Air\" \"ALL/mean_mass_fractions_CP\" \"ALL/mean_mass_fractions_GPG\"'""")
tp.macro.execute_command('$!RedrawAll')
tp.active_frame().plot().view.psi=62.699
tp.active_frame().plot().view.theta=-129.161
tp.active_frame().plot().view.alpha=7.29426
tp.active_frame().plot().view.position=(9.13683,
    tp.active_frame().plot().view.position[1],
    tp.active_frame().plot().view.position[2])
tp.active_frame().plot().view.position=(tp.active_frame().plot().view.position[0],
    6.66621,
    tp.active_frame().plot().view.position[2])
tp.active_frame().plot().view.position=(tp.active_frame().plot().view.position[0],
    tp.active_frame().plot().view.position[1],
    5.67257)
tp.active_frame().plot().view.width=1.74418
# End Macro.

