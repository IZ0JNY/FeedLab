"""EMELab: astronomy, atmosphere, link budget, database, weather parsers, analysis and the optional tab.
Example stations use invented coordinates."""
import math
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("erfa")
from feedlab.emelab import analysis, astro, atmos, db as edb, link, planner, sky, weather  # noqa: E402

STN = {"lat": 45.0, "lon": 10.0, "height_m": 100.0}
SETUP = {"band_ghz": 24.048, "D_m": 2.4, "eta_ap": 0.64, "gain_dbi": 53.69, "edge_taper_db": 13.0, "spill": 0.93,
         "ground_frac": 0.25, "line_loss_db": 0.2, "nf_db": 1.5, "tx_w": 20.0, "flux_sfu": 550.0}


def test_moon_distance_meeus_example():
    """Meeus, Astronomical Algorithms, example 47.a: 1992-04-12 0h TD, Δ = 368409.7 km."""
    import erfa
    import numpy as np
    tt, _ = astro._jd(datetime(1992, 4, 11, 23, 59, 1))
    d = np.linalg.norm(erfa.moon98(*tt)["p"]) * astro.AU_KM
    assert abs(d - 368409.7) < 5


def test_sun_transit_due_south_and_rise_elevation():
    lat, lon = 45.0, 10.0
    # local noon ≈ 12:00 − lon/15 h − equation of time (late November ≈ −13 min): Sun near az 180 at max elevation
    s = max((astro.sky(datetime(2026, 11, 20, 10, 0) + timedelta(minutes=m), lat, lon) for m in range(0, 120, 2)),
            key=lambda x: x.sun.el)
    assert abs(s.sun.az - 180) < 1.5
    assert abs(s.sun.el - (90 - lat + s.sun.dec)) < 0.3


def test_locator_round_trip():
    lat, lon = astro.locator_to_latlon("JN45fa")
    assert astro.latlon_to_locator(lat, lon) == "JN45fa"


def test_atmosphere_itu_values():
    assert 0.16 < atmos.gamma_vapour(22.235, 7.5) < 0.20           # ITU-R P.676 figure: ≈ 0.18 dB/km
    assert 0.006 < atmos.gamma_oxygen(10.0) < 0.010
    z24 = atmos.zenith_attenuation(24.048, 15, 58)["total"]
    z47 = atmos.zenith_attenuation(47.088, 15, 58)["total"]
    assert 0.3 < z24 < 0.5 and 0.7 < z47 < 1.1
    assert atmos.zenith_attenuation(24.048, 15, 90)["total"] > z24        # humidity matters at 24 GHz
    assert 20 < atmos.sky_temperature(z24, 15) < 35


def test_path_loss_published():
    assert abs(link.path_loss_db(10.368, 384400) - 289.1) < 0.3
    assert link.path_loss_db(24.048, 356500) < link.path_loss_db(24.048, 406700) - 2.0


def test_sun_gt_method_is_consistent_with_prediction():
    c = analysis.snapshot(STN, SETUP, datetime(2026, 11, 20, 11, 15, tzinfo=timezone.utc), {"t_c": 10, "rh": 70})
    assert c["sun"]["el"] > 15
    gt = analysis.sun_gt_from_y(c["sun"]["y_db"], SETUP, c)
    assert abs(gt - c["gt_expected"]) < 0.1


def test_pointing_model_recovers_offsets():
    rows = []
    for el in (15, 25, 35, 45, 60, 70):
        e = math.radians(el)
        rows.append({"kind": "sun", "calc": {"sun": {"el": el}}, "az_off": (0.05 + 0.02 * math.tan(e)) / math.cos(e),
                     "el_off": -0.03 + 0.04 * math.cos(e)})
    pm = analysis.pointing_model(rows)
    assert abs(pm["az_zero"] - 0.05) < 1e-6 and abs(pm["az_tilt"] - 0.02) < 1e-6
    assert abs(pm["el_zero"] + 0.03) < 1e-6 and abs(pm["el_sag"] - 0.04) < 1e-6


def test_database_round_trip(tmp_path):
    D = edb.DB(tmp_path / "e.sqlite")
    D.save_station(callsign="TEST", locator="JN45fa", lat=45.0, lon=10.0, height_m=100)
    sid = D.save_setup("24 GHz", 24.048, SETUP)
    t = datetime(2026, 11, 20, 11, 15, tzinfo=timezone.utc)
    c = analysis.snapshot(STN, SETUP, t, {"t_c": 10, "rh": 70})
    D.add(utc=t, setup_id=sid, band_ghz=24.048, kind="sun", y_db=c["sun"]["y_db"] - 0.5, t_c=10, rh=70,
          calc={k: v for k, v in c.items() if k != "echo"})
    rows = D.measurements()
    assert rows[0]["utc"] == "2026-11-20T11:15:00Z"
    ev = analysis.evaluate_measurement(rows[0], D.setups()[0])
    assert abs(ev["y_delta"] + 0.5) < 1e-9 and ev["gt_delta"] < 0
    csv = D.export_csv()
    D2 = edb.DB(tmp_path / "f.sqlite")
    assert D2.import_csv(csv) == 1


def test_weather_station_formats():
    w = weather.parse_station('{"T": 11.7, "H": 87, "P": 1022.9, "W": 3.6, "D": 9.6, "U": 1795990000}')
    assert w["t_c"] == 11.7 and w["rh"] == 87 and abs(w["wind_ms"] - 1.0) < 1e-9
    assert w["station_utc"].tzinfo is not None
    w = weather.parse_station("24/11/26 22:20:55 11.7 87 9.6 0.0 0.0 58 0.0 0.0 1022.9 ENE 0 km/h C hPa mm")
    assert w["p_hpa"] == 1022.9 and w["format"] == "cumulus"


def test_planner_windows_and_perigee():
    smp = planner.windows(STN, SETUP, datetime(2026, 11, 20, tzinfo=timezone.utc), days=2, step_min=30, min_el=15)
    assert smp and all(s["el"] >= 15 for s in smp)
    rows = planner.daily(smp)
    assert rows and rows[0]["snr_1hz"] is not None
    pts = planner.perigees(datetime(2026, 11, 1, tzinfo=timezone.utc), 40)
    assert any(k == "perigeo" for _, _, k in pts) and all(355000 < d < 407500 for _, d, _ in pts)


def test_moon_beam_factor():
    assert link.beam_moon_factor(0.52, 5.0) > 0.98                     # wide beam: whole Moon
    assert link.beam_moon_factor(0.52, 0.18) < link.beam_moon_factor(0.52, 0.35) < 1
