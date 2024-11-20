Notebook: Enhanced GNSS-IR Data Processing and Reflector Height Calculation
1. Initialize Parameters
Description: Define key parameters and constraints for GNSS-IR analysis, based on the MATLAB script. These include polynomial fitting order, elevation and azimuth ranges, minimum points for quality control, and other variables.

python
Copy code
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
2. Visualize GNSS Data Coverage with a Skyplot
Description: Create a skyplot to visualize satellite azimuth and elevation distribution for exploratory analysis.

python
Copy code
# Simulated azimuth and elevation data
azimuth = np.random.uniform(0, 360, 500)  # Azimuth angles in degrees
elevation = np.random.uniform(5, 90, 500)  # Elevation angles in degrees

# Convert to radians for polar plot
azimuth_rad = np.radians(azimuth)
elevation_rad = np.radians(90 - elevation)  # Convert to zenith angle

# Create polar plot
plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)

# Scatter plot of data points
scatter = ax.scatter(azimuth_rad, elevation_rad, c=elevation, cmap='viridis', s=10, alpha=0.7)

# Add colorbar
plt.colorbar(scatter, label='Elevation Angle (degrees)')

# Customize plot
ax.set_theta_zero_location('N')  # 0° at top (North)
ax.set_theta_direction(-1)  # Clockwise azimuth
ax.set_rlabel_position(180)  # Radial labels on the left
plt.title('GNSS Data Coverage Skyplot', va='bottom')

plt.show()
3. Simulate or Load SNR Data
Description: Generate or load SNR data, ensuring it matches the structure of the MATLAB variables.

python
Copy code
# Simulate elevation angles (in degrees)
elevation_angles = np.linspace(5, 30, 500)  # 5° to 30°

# Simulate SNR data
amplitude = 1.0  # Amplitude of oscillation
frequency = 0.1  # Dominant frequency in cycles per degree
noise_level = 0.1  # Additive noise

# Generate synthetic SNR data
snr_data = amplitude * np.cos(2 * np.pi * frequency * elevation_angles) + noise_level * np.random.randn(len(elevation_angles))
4. Filter Data by Satellite and Azimuth Range
Description: Apply elevation and azimuth filters to extract valid data points for analysis.

python
Copy code
# Apply filters
elevation_filter = (elevation_angles > emin) & (elevation_angles < emax)
azimuth_filter = (azimuth > azim1) & (azimuth < azim2)
valid_indices = elevation_filter & azimuth_filter
5. Polynomial Detrending
Description: Use a polynomial fit to remove the direct signal and isolate the reflected component.

python
Copy code
# Polynomial detrending
p = np.polyfit(elevation_angles[valid_indices], snr_data[valid_indices], deg=pvf)
pv = np.polyval(p, elevation_angles[valid_indices])
detrended_snr = snr_data[valid_indices] - pv
6. Smooth the SNR Data
Description: Smooth the detrended SNR data to reduce noise.

python
Copy code
# Apply Savitzky-Golay filter
smoothed_snr = savgol_filter(detrended_snr, window_length=11, polyorder=2)
7. Transform and Interpolate SNR Data
Description: Transform elevation angles to 
sin
⁡
(
elevation angle
)
sin(elevation angle) and interpolate SNR data for uniform sampling.

python
Copy code
# Transform elevation to sin(elevation)
sin_elevation = np.sin(np.radians(elevation_angles[valid_indices]))

# Interpolation in sin(elevation) space
sorted_indices = np.argsort(sin_elevation)
sorted_sin_elevation = sin_elevation[sorted_indices]
sorted_snr = smoothed_snr[sorted_indices]

# Uniform sampling
interp_sin_elevation = np.linspace(min(sorted_sin_elevation), max(sorted_sin_elevation), num=len(sorted_sin_elevation))
interp_snr = np.interp(interp_sin_elevation, sorted_sin_elevation, sorted_snr)
8. Perform FFT and Calculate Reflector Height
Description: Perform FFT on the interpolated data and compute the reflector height.

python
Copy code
# FFT computation
fft_values = np.fft.fft(interp_snr)
fft_freqs = np.fft.fftfreq(len(interp_snr), d=(interp_sin_elevation[1] - interp_sin_elevation[0]))

# Identify dominant frequency
positive_freqs = fft_freqs[:len(fft_freqs) // 2]
positive_fft_values = np.abs(fft_values[:len(fft_values) // 2])
dominant_index = np.argmax(positive_fft_values)
dominant_frequency_rad = positive_freqs[dominant_index] * (np.pi / 180)

# Calculate reflector height
reflector_height = cf / (2 * dominant_frequency_rad)

print(f"Reflector Height: {reflector_height:.2f} meters")
9. Visualize FFT Spectrum
Description: Plot the FFT spectrum, showing the dominant frequency and corresponding reflector height.

python
Copy code
# Plot FFT spectrum
plt.figure(figsize=(10, 6))
plt.plot(positive_freqs * cf / 2, positive_fft_values, label='FFT Spectrum')
plt.axvline(x=dominant_frequency_rad * cf / 2, color='r', linestyle='--', label='Dominant Frequency')
plt.xlabel('Reflector Height (meters)')
plt.ylabel('Amplitude')
plt.title('FFT Spectrum of SNR Data')
plt.legend()
plt.grid()
plt.show()
