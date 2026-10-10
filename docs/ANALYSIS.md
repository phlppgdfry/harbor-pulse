# Alternative explanations

The descriptive model investigates delay alongside maintenance, volume relative to handling capacity, Monday patterns, staffing hours per 100 vehicles and terminal fixed effects. [Coefficients](../evidence/associations.json) are reproducible.

This is ordinary least squares over 1,095 generated terminal-days. It provides a transparent association check, not causal identification. Coefficients have different units: do not rank their absolute magnitudes as feature importance. Staffing is partly determined by planned volume, so interpreting its coefficient as the benefit of another employee would be wrong.

The maintenance episode is encoded in the generator. Seeing a large maintenance association confirms that the demonstration can recover its constructed signal; it does not establish why a real terminal is slow. No production forecast accuracy is claimed.

For a real study, collect queue timestamps and actual workload/staffing, inspect residuals and nonlinear constraints, account for serial dependence, predefine a comparison and test the intervention separately. The [pilot protocol](PILOT.md) shows the latter path.
