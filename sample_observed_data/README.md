# Sample observed data

These CSV files contain **synthetic, invented** daily data (not real measurements). They exist only
to test the "observed data" graph in the calibration dialog (Calibration -> Runoff/Erosion/Nitrogen/
Organic Carbon/Phosphorus -> observed data button), without needing a real gauging station record.

Each file has two columns: `date` (dd/mm/yyyy) and `value`, covering 01/01/2018 to 31/12/2019.

- `observed_runoff_example.csv` — daily runoff (mm), seasonal pattern with storm peaks.
- `observed_erosion_example.csv` — daily erosion (Mg), near-zero baseline with storm-driven spikes.
- `observed_nitrogen_example.csv` — daily nitrogen load (kg), correlated with the runoff pattern.

Do not use these files for an actual calibration run - they are not tied to any real project or
AnnAGNPS simulation, they are only meant to preview how the observed-data graph looks and behaves.
