# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""EMELab: EME station log, measurements and planning for 10, 24 and 47 GHz (optional FeedLab tab).

astro    Sun and Moon positions (ERFA/SOFA), distance, Doppler, libration spread, sun–moon angle
atmos    gaseous attenuation (ITU-R P.676 Annex 2) and sky noise from surface weather
sky      Sun and Moon brightness, beam filling, expected Y-factors
link     EME path loss and own-echo SNR
db       local SQLite database of setups and measurements (UTC timestamps)
weather  Open-Meteo and a personal Meteotemplate station (address kept only in the local settings)
analysis measured vs expected, derived G/T, pointing offsets, trends
planner  Moon windows, mutual windows with another station, best days
"""
