n_time_steps = TimeSliderGetNStates()
start_step = 0
end_step = 302

#SetTimeSliderState(510)
DrawPlots()

eatts = ExportDBAttributes()
eatts.dirname = "/mnt/lustre/groupshare/mgtu_baumana/ayakovchuk/2026_05_Spalding_Combustion/QUBIQ/T1000K_freq100_comb_v0.0ms_pmfr0.00000179_D1G1Y1/part/"
eatts.db_type = "VTK"
eatts.variables = ("DP/density", "DP/diameter", "DP/mass", "DP/nparticles", "DP/region_id", "DP/track_id", "DP/temperature", "DP/velocity", "DP/velocity_x", "DP/velocity_y", "DP/velocity_z", "DP/Y1")

for time_step in range(start_step, end_step + 1):
    TimeSliderSetState(time_step)
    Query("Time")
    current_time = GetQueryOutputValue()
    #current_time = TimeSliderGetTime(step)
    #eatts.db_type = "VTK"
    eatts.filename = f"particles_time_{current_time:.6f}"
    ExportDatabase(eatts)
    print(f"Экспортирован шаг {time_step}, время = {current_time:.6f}")