# Risultati openEMS, f/D 0.4 (27–28 novembre 2026) → «Feed 0.4 f/D»

Parabola prime focus con f/D 0.4 (semiangolo 64°). Stesse regole di `RISULTATI_fD060.md`; in più la
penalità sull'S11 è 0.05 per dB sopra −20 dB, perché il feed deve reggere la potenza in trasmissione (EME).

## Feed pubblicati (λ/16)

| Feed | η media ±2 % | S11 max |
|---|---|---|
| Axial Corrugated CT1DMK, parametric calculation OE2IGL | 76.4 % | −10.9 dB |
| Pickett-Potter | 67.5 % | −13.4 dB |
| Dual-mode 'optimum' Skobelev, W1GHZ | 58.7 % | −21.6 dB |
| Horn conico | 55.3 % | −25.1 dB |

A f/D 0.4 il corrugato OE2IGL ha la guida d'ingresso vicina al taglio (Ø 0.66 λ) e riflette molto.

## Ottimizzazione

- Axial Corrugated, Nelder-Mead in due giri (120 + 80 run): da 76.4 % a **84.1 %** a λ/16.
- Profilo liscio libero (partenza dal mode matching, 40 run): fermo al 71.7 %, lungo 6.5 λ. Scartato.

## Conferma a λ/24

| | η media ±2 % | η f0 | S11 max | Spillover | Taper | Bordo |
|---|---|---|---|---|---|---|
| **Feed 0.4 f/D**, 10.368 GHz | **83.5 %** | 83.6 % | −22.3 dB | 0.954 | 0.892 | 9.2 dB |
| **Feed 0.4 f/D**, 24.048 GHz | **83.4 %** | 83.4 % | −21.3 dB | | | |
| Axial Corrugated OE2IGL (partenza) | 76.4 % | 75.5 % | −11.4 dB | 0.948 | 0.881 | 10.0 dB |

## Quote (FeedLab: `geometry.FD04_LAMBDA`, tipo di feed «Feed 0.4 f/D»)

In λ: passo 0.4441, larghezza slot 0.5862 × passo, avanzamento assiale 0.0599, delta 0.2214, Di = Ds 0.7233
(nessuno scalino), d1 0.4775, d2…d8 0.2689.

| mm | passo | w | axi | delta | Di | d1 | d2…d8 | Ø esterno | lunghezza |
|---|---|---|---|---|---|---|---|---|---|
| 10.368 GHz | 12.84 | 7.53 | 1.73 | 6.40 | 20.91 | 13.81 | 7.78 | 241.4 | 58.3 |
| 24.048 GHz | 5.54 | 3.25 | 0.75 | 2.76 | 9.02 | 5.95 | 3.35 | 104.1 | 25.4 |

Il diametro esterno è grande (≈ 8.3 λ): su parabole piccole conta l'ostruzione (prime focus).

Dati: `fdtd/results/*_fD0.40*`, `fdtd/results/fd04_verify_24cpl.json`.
