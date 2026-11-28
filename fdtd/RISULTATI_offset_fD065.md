# Tromba piramidale / quadrata per parabola offset, f/D equivalente 0.65 (10.368 e 24.048 GHz)

Simulazione openEMS **3D** (nuovo `fdtd/rect_horn_sim.py`: ingresso guida WR in TE10, tromba piramidale, NF2FF).
Ottimizzazione Nelder-Mead a λ/16 su apertura H, apertura E e lunghezza svasatura, conferma a λ/24.
η = spillover × taper × fase × cross-pol × (1 − |S11|²), media su ±2 %, offset = nessun blocking.
La WR in λ cambia da banda a banda (WR-90 a 10 GHz, WR-42 a 24 GHz): ogni banda è ottimizzata a parte.

## Risultati (conferma λ/24)

| Feed | Banda | η media | S11 max ±2 % | −10 dB E / H | X-pol picco (45°) |
|---|---|---|---|---|---|
| **Tromba piramidale ottimizzata** | 10.368 GHz, WR-90 | **74.1 %** | −24.4 dB | 46° / 43° | −22 dB |
| **Tromba piramidale ottimizzata** | 24.048 GHz, WR-42 | **74.2 %** | −20.2 dB | 46° / 44° | −23 dB |
| Tromba G3RPE (formule pubblicate) | 10.368 GHz | 72.2 % | −19.9 dB | | |
| Tromba quadrata ottimizzata (H = E) | 10.368 GHz | 67.8 % | −18.7 dB | 39° / 50° | −21 dB |
| Tromba quadrata ottimizzata (H = E) | 24.048 GHz | 69.3 % | −19.8 dB | 44° / 57° | −18 dB |

Confronto alla stessa illuminazione (f/D 0.65, ψ0 ≈ 42°), dal grafico offset (`results/eta_vs_fD_offset*.png`):

| Feed | η a f/D 0.65 |
|---|---|
| Axial Corrugated ottimizzato f/D 0.6 | 82.5 % |
| W2IMU / Dual-Flare / profilo liscio ottimizzati f/D 0.6 | 77.6–78.4 % |
| **Tromba piramidale ottimizzata** | **74.2 %** |
| Tromba G3RPE | 72.4 % |
| Large W2IMU 30° W1GHZ/W1FKF (è un feed per f/D ≈ 0.8) | 71.6 % |
| Tromba quadrata ottimizzata | 67.9 % |

**Conclusioni.** La tromba *quadrata vera* non va: con apertura quadrata il piano E è molto più stretto del piano H
(campo uniforme in E, cosinusoidale in H), lo spillover cresce e si perdono 6 punti. La tromba piramidale con
apertura **rettangolare ~1.4 λ × 0.97 λ** pareggia i due piani e arriva a 74 %, 2 punti sopra la G3RPE, con S11
ottimo e senza piastrina (si avvita direttamente sulla flangia WR). Resta 8 punti sotto la corrugata ottimizzata
f/D 0.6, ma è il feed più semplice da fare (fresatura o lamiera).

## Quote CNC (mm, interno; pareti 0.06 λ, ≥ 1 mm)

| | 10.368 GHz (WR-90 22.86 × 10.16) | 24.048 GHz (WR-42 10.668 × 4.318) |
|---|---|---|
| Apertura H (lato largo) | 40.38 | 17.18 |
| Apertura E | 28.18 | 12.12 |
| Lunghezza svasatura | 20.78 | 10.15 |
| Tratto di guida dritta | 28.92 | 12.47 |
| Parete | 1.73 | 1.00 |
| Centro di fase (dalla bocca, verso l'interno) | 3.1 | 1.1 |

In λ: H 1.397 / 1.378, E 0.974 / 0.972, L 0.719 / 0.815.

## File

- Ottimi: `results/rect_horn_fD0.65_{10g,24g}_best.json`, `_confirm.json`, tromba quadrata `square_horn_fD0.65_*`.
- Campi lontani confermati: `results/openems_fD0.65/<famiglia>_<banda>/results.json`.
- Progetti FeedLab (offset 100, 120, 180, 240 cm): `results/feedlab/tromba_piramidale_offset_fD0.65_*.feedlab.json`.
- Disegni: `results/preview_offset_fD0.65/`.
- Grafici: `results/eta_vs_fD_offset{,_EN,_angle,_angle_EN}.png`.

Rifare: `python fdtd/optimize.py --family rect_horn --fD 0.65 --f0 24.048 --tag 24g --method nm --budget 70`, poi `--confirm`;
`python fdtd/eta_vs_fD.py --offset-only`; `python fdtd/export_feedlab.py --family rect_horn --fD 0.65 --tag 24g --bands 24.048 --dishes 1000,1200,1800,2400 --offset`.

Limiti: l'efficienza usa i piani E/H (come W1GHZ); la cross-pol vera a 45° di una tromba piramidale è ≈ −22 dB,
quindi la perdita reale è ancora < 0.5 %. Offset trattata come parabola equivalente (nessuna asimmetria dell'offset).
