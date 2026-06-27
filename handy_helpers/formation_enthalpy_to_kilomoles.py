
# Универсальная газовая постоянная [Дж/моль-К]
R0 = 8.314462618

# энтальпия образования [Дж/кг]
formation_enthalpy = -1457458.5526399682

# молярная масса [г/моль]
molar_mass = 28.845427669152723

# молярная масса [кг/моль]
molar_mass_kg_per_mol = molar_mass / 1000

# газовая постоянная [Дж/кг-К]
R_specific = R0 / molar_mass_kg_per_mol

# Энтальпия образования [Дж/киломоль]
formation_enthalpy_J_per_kmol = formation_enthalpy * molar_mass_kg_per_mol * 1000

print(f"Энтальпия образования: {formation_enthalpy_J_per_kmol:.1f} Дж/киломоль")