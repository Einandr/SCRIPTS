import ansys.fluent.core as pyfluent
# import os
# if not os.getenv('FLUENT_PROD_DIR'):
#     import ansys.fluent.core as pyfluent
#     flglobals = pyfluent.setup_for_fluent(product_version="24.2.0", mode="solver", dimension=3, precision="single", processor_count=8)
#     globals().update(flglobals)
# session = pyfluent.launch_fluent()
# session = pyfluent.launch_fluent(ui_mode='gui', precision='single', processor_count=8)




solver = pyfluent.connect_to_fluent(ip='192.168.0.189', port=55197, password='7c9ytwp7', allow_remote_host=True, insecure_mode=True)
# session = pyfluent.Solver.from_connection(ip, port, password)

# solver = session.solver

# solver.results.graphics.particle_track['particle-tracks-1'].display()

# track =  solver.results.graphics.particle_track['particle-tracks-1']
# track.report_type = "current-positions"
# track.report_to = "file"
# track.reporting_variables = ["x-position", "y-position", "z-position", "particle-velocity", "particle-id"]
# track.current_positions(file_name="dpm_current_positions.dpmrpt")

# solver.file.read_case(file_name = "save-26.cas.h5")
# solver.file.read_data(file_name = "save-26-0.500000.dat.h5")



solver.results.graphics.particle_track['particle-tracks-1'].display()
solver.settings.results.report()

# solver.execute_tui('(cx-gui-do cx-set-list-tree-selections "NavigationPane*Frame2*Table1*List_Tree2" (list "Results|Graphics|Particle Tracks|particle-tracks-1"))')
# solver.execute_tui('(cx-gui-do cx-activate-item "Particle Tracks*Table2*Table2(Reporting)*Table1*ToggleBox1(Report Type)*Step By Step")')
# solver.tui.display.particle_tracks.particle_tracks.report(
#     "dpm_current_positions.his",   # Имя выходного файла
#     "injection-0",                 # Имя вашего впрыска (injection). Если их несколько, укажите через пробел или "()"
#     "()",                          # Список поверхностей (или пустые скобки, чтобы экспортировать весь объем)
#     "particle-velocity",           # Первая переменная для окраски/отчета
#     "particle-id"                  # Дополнительные переменные
# )

# session.exit()



