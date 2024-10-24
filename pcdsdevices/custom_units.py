import sympy.physics.units as units

millijoule = mJ = units.quantities.Quantity("millijoule", abbrev='mJ')
millijoule.set_global_relative_scale_factor(units.prefixes.milli, units.joule)

microjoule = uJ = units.quantities.Quantity("microjoule", abbrev='uJ')
microjoule.set_global_relative_scale_factor(units.prefixes.micro, units.joule)
