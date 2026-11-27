# Risultati openEMS, f/D 0.6 (26–27 novembre 2026)

Parabola prime focus o offset con f/D equivalente 0.6 (semiangolo 45.2°). Simulazione a 10.368 GHz, quote in λ
(valgono per ogni banda). η = efficienza d'illuminazione (spillover × taper × fase × cross-pol) × (1 − |S11|²),
media su f0·(1 ± 2 %), centro di fase fisso trovato a f0, blocking escluso. Ricerca a λ/16, **conferma a λ/24**.

## Conferma a λ/24

| Feed | η media | η f0 | S11 max (±2 %) | Spillover | Taper | Bordo | Lunghezza |
|---|---|---|---|---|---|---|---|
| **Axial Corrugated, ottimizzato** | **83.5 %** | 83.5 % | −23.1 dB | 0.922 | 0.911 | 9.6 dB | 2.95 λ |
| Axial Corrugated CT1DMK, parametric calculation OE2IGL | 82.2 % | 82.2 % | −21.3 dB | 0.932 | 0.889 | 11.2 dB | 2.98 λ |
| W2IMU, ottimizzato | 77.8 % | 78.2 % | −25.3 dB | 0.919 | 0.854 | 12.3 dB | 4.54 λ |
| W2IMU Dual-Mode Feedhorn, parametric calculation OE2IGL | 77.7 % | 78.1 % | −23.7 dB | 0.917 | 0.853 | 12.4 dB | 4.51 λ |
| Dual-Flare, ottimizzato | 77.2 % | 77.4 % | −23.1 dB | 0.927 | 0.838 | 13.0 dB | 3.98 λ |
| Dual-Flare, IZ0JNY (tabella) | 76.8 % | 76.9 % | −20.2 dB | 0.945 | 0.822 | 14.0 dB | 3.81 λ |
| Profilo liscio libero, ottimizzato | 76.7 % | 77.1 % | −23.1 dB | 0.918 | 0.842 | 12.9 dB | 2.56 λ |
| W2IMU dual-mode (W1GHZ, B = 2.35 f/D) | 76.2 % | 77.0 % | −25.1 dB | 0.879 | 0.878 | 11.1 dB | 3.94 λ |

Solo ricerca (λ/16): Skobelev 72.1 %, Pickett-Potter 70.2 %.

## Cosa dicono

- **Axial Corrugated**: +1.3 punti sul progetto OE2IGL, confermati a λ/24 (+1.8 a λ/16). Viene da un bordo meno
  rastremato (9.6 invece di 11.2 dB): più taper, un po' più spillover. Scalino d'ingresso più largo
  (Ds 0.93 λ invece di 0.86 λ), primo slot meno profondo (0.21 λ invece di 0.25 λ), passo 0.38 λ.
- **W2IMU**: il progetto OE2IGL è già all'ottimo (+0.1 punti). La regola W1GHZ B = 2.35 f/D a f/D 0.6
  sta 1.5 punti sotto, per lo spillover (apertura troppo piccola).
- **Dual-Flare**: +0.4 punti e S11 da −20 a −23 dB in ±2 %.
- **Profilo liscio libero**: stessa efficienza del W2IMU ottimizzato, ma lungo 2.56 λ invece di 4.5 λ.
- Fra i feed lisci nessuno supera il 78 %: oltre serve il controllo del modo ibrido dei corrugati.

## Axial Corrugated ottimizzato, f/D 0.6

In λ: passo 0.3804, larghezza slot 0.696 × passo, avanzamento assiale 0.2106, delta 0.0607, Di 0.7764,
Ds 0.9318, d1 0.208, d2…d8 0.2482 (stessa geometria di `geometry.build("axial_corrugated", …)`).

| mm | passo | w | axi | delta | Di | Ds | d1 | d2…d8 | Ø esterno | lunghezza testa |
|---|---|---|---|---|---|---|---|---|---|---|
| 10.368 GHz | 11.00 | 7.66 | 6.09 | 1.76 | 22.45 | 26.94 | 6.01 | 7.18 | 210.8 | 85.4 |
| 24.048 GHz | 4.74 | 3.30 | 2.63 | 0.76 | 9.68 | 11.62 | 2.59 | 3.09 | 90.9 | 37.1 |
| 47.088 GHz | 2.42 | 1.69 | 1.34 | 0.39 | 4.94 | 5.93 | 1.32 | 1.58 | 46.4 | 20.1 |

Da fare prima di costruirlo: banda più larga (±5 %), sensibilità alle tolleranze (±0.05 mm a 24 GHz),
verifica a λ/30 con la sfera completa, poi altre f/D (0.4, 0.8).

Dati: `fdtd/results/*_fD0.60*.json(l)`; per rifare tutto: `fdtd/README.md`.
