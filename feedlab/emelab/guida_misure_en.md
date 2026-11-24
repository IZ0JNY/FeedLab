### Guide to the fundamental EME measurements

Log every measurement **in UTC** (keep the PC synchronised with NTP or GPS), with the **setup** used and the **weather** at that moment. Always use the same receiver settings (bandwidth, integration time, AGC off) and take **3 readings**, then the average.

#### 1. Sun noise (Y sun / cold sky) — the main measurement
- **What it measures:** the real G/T of the station. EMELab compares it with what your feed and dish should give.
- **How:** point at the Sun and peak it in AZ and EL. Note the **correction you had to apply** (AZ/EL offset at the peak). Then move in AZ, at the same elevation, by **at least 5 beamwidths** (about 4° at 10 GHz, 2° at 24 GHz, 1° at 47 GHz) onto cold sky. Y = power on the Sun / power on the sky.
- **You also need:** the day's solar flux at **15.4 GHz** (RSTN observatories: San Vito, Learmonth, Sagamore Hill, Palehua, published by NOAA SWPC). Enter it in EMELab: the Sun changes by 10–20 % from day to day.
- **Repeat** at different elevations (morning, noon, afternoon) and on dry and humid days: EMELab separates the effect of the atmosphere from that of the station.

#### 2. Moon noise (Y moon / cold sky)
- Much weaker than the Sun (about 2–3 dB at 24 GHz with 2.4 m): it checks sensitivity and pointing on the EME target itself.
- Same procedure as the Sun; note the lunar phase (EMELab computes it): the Moon is warmer after full Moon.

#### 3. Cold sky and ground (Y ground / sky)
- Point at the clear horizon or at the ground in front of the dish: it measures the **spillover** contribution and checks the preamplifier. If the value drops over time, something is getting worse (connectors, water, LNA).
- **Hot load / cold sky** (absorber at ambient temperature in front of the feed): Tsys = (T_hot − Y·T_sky)/(Y − 1). It is the most direct measurement of the system noise.

#### 4. Beamwidth from a Sun transit
- Park the antenna a little ahead of the Sun and record the power while the Sun drifts through the beam.
- Measured beam = time between the two −3 dB points (minutes) × 0.25°/min × cos(declination of the Sun). To remove the size of the Sun: beam² ≈ measured² − 0.35 × Sun diameter².
- Enter the value in the setup («Measured beamwidth»): a beam wider than expected means a defocused feed or a deformed surface.

#### 5. Feed focusing
- Move the feed along the axis in λ/4 steps (about 7 mm at 10 GHz, 3 mm at 24 GHz, 1.6 mm at 47 GHz) over ±1 λ and measure the sun Y at each step (type «Focusing», value = displacement in mm).
- The maximum is the focus: compare it with the phase centre computed by FeedLab. Then repeat moving the feed sideways (offset).

#### 6. Pointing calibration
- The peak offsets on Sun and Moon, at many AZ/EL positions, let EMELab compute the **AZ and EL zeros, axis tilt and gravity sag**. At 47 GHz an error of 0.05° already costs more than 1 dB on receive and twice that on echoes.

#### 7. Own echoes
- Echo SNR (e.g. the Echo mode of WSJT-X) with the real power at the feed (measure it with a power meter and a directional coupler).
- Compare with the expected value: a stable difference is the **effective reflectivity of the Moon with your beam**. At 24 and 47 GHz on 2.4 m the beam is narrower than the Moon and the echo is weaker than the classic formula.
- Note Doppler and spreading: EMELab computes them for every measurement.

#### 8. Environment to note every time
- Temperature, humidity and pressure (water vapour: at 24 GHz it is the main factor), rain, clouds, **water or dew on dish and feed**, wind (vibration and deformation), stability of the local oscillator (at 24/47 GHz a GPS reference is needed).

#### What EMELab tells you
- Measured vs expected G/T and where you lose (elevation, humidity, focus, pointing, losses).
- Pointing model with the corrections for your tracking program.
- Best windows (elevation, Moon distance, perigee, Sun far away, forecast humidity) and the most favourable months.

*References: Paul Wade W1GHZ, «Online Microwave Antenna Book» (sun noise measurements); ITU-R P.676 (gaseous attenuation), P.618 (noise temperature), P.834 (refraction), P.840 (clouds); Krotikov and Troitskii, Linsky 1973 (lunar temperature); J.W.M. Baars, «The Paraboloidal Reflector Antenna in Radio Astronomy and Communication» (beam and focus measurements); NOAA SWPC, RSTN solar flux.*
