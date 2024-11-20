# Notebook: Enhanced GNSS-IR Data Processing and Reflector Height Calculation

This notebook provides a comprehensive workflow for GNSS-IR data processing, incorporating filtering, detrending, FFT, and visualization.

---

## 1. Initialize Parameters

**Description:** Define key parameters and constraints for GNSS-IR analysis, based on the MATLAB script. These include polynomial fitting order, elevation and azimuth ranges, minimum points for quality control, and other variables.

```python
# Parameters
satlist = list(range(1, 33))  # Use all GPS satellites (PRNs 1 to 32)
pvf = 2  # Polynomial order for detrending
avg_maxRH = []  # Store median reflector height for a single day/site
freqtype = 1  # Frequency type (L1 GPS)

# Reflector height constraints
minRH = 0.4  # Minimum reflector height (meters)
maxArcTime = 4  # Maximum time (hours) for valid data arc
minPoints = 100  # Minimum number of points for QC

# Elevation angle range
emin = 5  # Minimum elevation angle (degrees)
emax = 30  # Maximum elevation angle (degrees)
ediff = 10  # Minimum range in elevation angles (degrees)

# Wavelength and related constants
cf = 0.1902936  # L1 GPS wavelength in meters
w = 4 * np.pi / cf

# Azimuth constraints
azrange = 45  # Bin width for azimuth ranges (degrees)
naz = round(360 / azrange)  # Number of azimuth bins
azim1, azim2 = 225, 315  # Specific azimuth range for testing
