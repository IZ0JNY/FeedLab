# Risultati openEMS, f/D 0.4 primo fuoco, parabole 3 e 3.7 m (27–28 novembre 2026)

Parabola primo fuoco f/D 0.4 (semiangolo 64.0°, apertura 128°). Simulazione a 10.368 GHz, quote in λ (valgono
per ogni banda). η = spillover × taper × fase × cross-pol × **blocking del feed** × (1 − |S11|²), media su
f0·(1 ± 2 %), centro di fase fisso trovato a f0. Il blocking è quello del Ø esterno del feed su una parabola da
3 m a 10 GHz (103.75 λ); i sostegni non sono inclusi. Ricerca a λ/16 (720 run openEMS: Nelder-Mead e poi
evoluzione differenziale), **conferma a λ/24**.

## Conferma a λ/24 (3 m, 10.368 GHz)

| Feed | η media | η f0 | S11 max (±2 %) | Spillover | Taper | Blocking | Bordo | Ø esterno | Lunghezza |
|---|---|---|---|---|---|---|---|---|---|
| **Axial Corrugated, ottimizzato** | **82.2 %** | 82.2 % | −21.0 dB | 0.967 | 0.878 | 0.983 | 10.4 dB | 8.53 λ | 2.31 λ |
| Chaparral 3 anelli, ottimizzato | 80.1 % | 80.1 % | −21.2 dB | 0.899 | 0.904 | 0.996 | 10.1 dB | 3.84 λ | 2.48 λ |
| VE4MA, ottimizzato | 80.3 % | 80.4 % | −17.6 dB | 0.897 | 0.908 | 0.999 | 6.4 dB | 2.13 λ | 2.26 λ |
| Super-VE4MA (W1GHZ/WD5AGO) | 76.5 % | 76.2 % | −16.4 dB | | | | | 2.15 λ | |
| Axial Corrugated CT1DMK, parametric calculation OE2IGL | 75.3 % | 74.3 % | −11.4 dB | | | | | 7.58 λ | |
| Chaparral 3 anelli "best" (W1GHZ/WD5AGO) | 72.8 % | 72.5 % | −16.6 dB | | | | | 2.39 λ | |

| W2IMU large flare, ottimizzato (cono 30° fisso) | 73.5 % | 73.6 % | −23.2 dB | 0.899 | 0.824 | 0.999 | 13.2 dB | 1.63 λ | 2.67 λ |
| W2IMU large flare, ottimizzato (cono libero, 33.9°) | 73.5 % | 73.6 % | −20.6 dB | 0.885 | 0.839 | 0.999 | 12.4 dB | 1.63 λ | 2.68 λ |
| Large W2IMU 30° W1GHZ/W1FKF, B 1.65 λ | 48.2 % | 47.9 % | −22.9 dB | | | | | | 5.24 λ |

Solo ricerca (λ/16): Dual-Flare con limiti aperti 73.1 % (lasciato da parte), guida circolare aperta 70.9 %.

## Su 3 e 3.7 m, 10 e 24 GHz (stessi run, cambia solo il blocking)

| Feed | 10 GHz, 3 m | 10 GHz, 3.7 m | 24 GHz, 3 m | 24 GHz, 3.7 m | Ø feed 10 / 24 GHz |
|---|---|---|---|---|---|
| Axial Corrugated ottimizzato | 82.2 % | 82.7 % | 83.4 % | 83.5 % | 247 / 106 mm |
| VE4MA ottimizzato | 80.3 % | 80.3 % | 80.3 % | 80.3 % | 62 / 27 mm |
| Chaparral ottimizzato | 80.1 % | 80.3 % | 80.4 % | 80.5 % | 111 / 48 mm |

(Dati: `fdtd/results/dishes_fD0.40.json`.) Con Ruze 0.1 mm, perdite ohmiche (alluminio) e scenario RX predefinito,
FeedLab dà per l'Axial Corrugated 49.3 dBi su 3 m e 51.2 dBi su 3.7 m a 10.368 GHz, 56.7 / 58.5 dBi a 24.048 GHz.

## Cosa dicono

- **Il migliore è l'Axial Corrugated**: +6.9 punti sul progetto OE2IGL a 128°, che a f/D 0.4 è fuori dalla zona
  buona dei suoi polinomi (S11 −11 dB). L'ottimo ha slot più larghi (84 % del passo invece del 69 %), passo
  0.445 λ, slot più profondi (0.305 λ, d1 0.50 λ) e uno scalino d'ingresso piccolo (Di 0.764 → Ds 0.80 λ). Lo
  spillover arriva al 96.7 %: è questo che gli dà i 2 punti sui feed a choke.
- **Il prezzo è il Ø**: 8.5 λ (247 mm a 10 GHz). Su 3 m a 10 GHz il blocking costa 1.7 punti ed è già incluso
  nella tabella. A 24 GHz conta meno di 0.4 punti.
- **VE4MA e Chaparral ottimizzati** stanno entrambi intorno all'80 %, 4 e 7 punti sopra i progetti pubblicati. Sono
  molto più compatti (62 e 111 mm a 10 GHz). Il VE4MA però ha l'S11 a −17.6 dB a λ/24 (a λ/16 era −20.6 dB):
  va rifinito prima di costruirlo. Il Chaparral ha l'S11 a posto (−21 dB), ma la larghezza degli anelli è al
  limite della ricerca (0.437 su 0.45 λ): forse si può guadagnare ancora qualcosa.
- Il centro di fase dell'Axial Corrugated è 0.85 λ **dentro** la bocca (−24.7 mm a 10 GHz): la bocca del feed
  sta 25 mm oltre il fuoco, verso la parabola.

## W2IMU large flare a f/D 0.4

Il large W2IMU pubblicato (W1GHZ/W1FKF, bocca 1.65–1.78 λ, cono 30°) è un feed per f/D ≈ 0.8: a f/D 0.4 dà il
48 % (1.65 λ) o il 34 % (1.78 λ), perché illumina solo il centro della parabola. Dal grafico qui sotto il suo massimo
è il 79.5 % a f/D 0.82–0.85. Lasciando libero l'ottimizzatore (330 run libero, 170 a 30° fisso) il W2IMU per
f/D 0.4 diventa un horn corto a bocca piccola: guida 0.71 λ, cono 30–34°, bocca 0.87–0.91 λ, cilindro di fase 0.72–0.77 λ.
Si ferma al **73.5 %** confermato, appena sopra la guida aperta: per illuminare 128° con bordo a −12 dB senza corrugazioni
non c'è abbastanza controllo del modo ibrido. **A f/D 0.4 il large flare perde 7–9 punti** sui feed a choke e sul
corrugato; ha senso solo se serve un feed liscio, piccolo (Ø esterno = flangia, 47 mm a 10 GHz) e semplicissimo.

Versione a 30° fisso (consigliata se lo vuoi fare: il cono si fa con la punta da centro a 60°, S11 −23 dB), mm:

| | Ø guida A | Ø bocca B | cono | lunghezza cono | cilindro C | guida d'ingresso | lunghezza totale |
|---|---|---|---|---|---|---|---|
| 10.368 GHz | 20.50 | 26.16 | 30° | 4.90 | 20.89 | 51.42 | 77.2 |
| 24.048 GHz | 8.84 | 11.28 | 30° | 2.11 | 9.01 | 22.17 | 33.3 |

## Quale feed per quale f/D e parabola (grafici)

`fdtd/results/eta_vs_fD_<banda>GHz.png` (tutti i Ø) e `eta_vs_fD_<banda>GHz_<Ø>cm.png` (uno per Ø), dati in
`eta_vs_fD_<banda>GHz.json`. 21 feed: gli ottimizzati (linea continua) e i progetti pubblicati (puntini), ognuno dal suo
campo lontano openEMS a 24 celle/λ, rimesso nel centro di fase migliore per ogni f/D, con il blocking del suo Ø esterno
sulla parabola primo fuoco. 10 e 24 GHz: Ø 100–370 cm; 47 e 76 GHz: Ø 100–240 cm. Valori a f0, senza Ruze né
perdite ohmiche. Per rifarli: `python fdtd/eta_vs_fD.py --f 10.368`.

Il migliore per f/D (10 GHz, Ø 300 cm; alle bande alte e sulle parabole più grandi vale lo stesso, perché il
blocking conta meno):

| f/D | 0.30 | 0.35 | 0.40–0.50 | 0.55–0.65 | 0.70 | 0.75–0.90 |
|---|---|---|---|---|---|---|
| feed | Chaparral W1GHZ (73.5 %) | Chaparral ott. (78 %) | Corrugato ott. 0.4 (82–84 %) | Corrugato ott. 0.6 (81–82 %) | Corrugato OE2IGL (79.5 %) | Large W2IMU W1GHZ (78–79 %) |

Eccezione: **a 10 GHz su 100 cm** il corrugato (Ø 247 mm) fa troppa ombra. Lì il migliore fra 0.35 e 0.45 è il
**VE4MA ottimizzato (80 %)** e fra 0.55 e 0.65 il W2IMU ottimizzato (77–78 %). Su 150 cm sono pari (80 %), da 200 cm
in su vince il corrugato.

## Quote in produzione (CNC)

Il feed è un pezzo di tornio (solido di rivoluzione). Le pareti sono quelle predefinite di FeedLab: 0.06 λ, almeno
1 mm (1.73 mm a 10 GHz, 1.0 mm a 24 GHz).

**Axial Corrugated ottimizzato, f/D 0.4.** In λ: passo 0.445, larghezza slot 0.841 × passo, avanzamento assiale
0.095, delta 0.150, Di 0.764, Ds 0.800, d1 0.496, d2…d8 0.305.

| mm | passo | w | parete fra gli slot | axi | delta | Di | Ds | d1 | d2…d8 | Ø esterno | lunghezza |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10.368 GHz | 12.87 | 10.82 | 2.05 | 2.73 | 4.33 | 22.08 | 23.12 | 14.35 | 8.82 | 246.5 | 66.9 |
| 24.048 GHz | 5.55 | 4.66 | 0.89 | 1.18 | 1.87 | 9.52 | 9.97 | 6.19 | 3.80 | 106.3 | 29.1 |

A 24 GHz la parete fra gli slot è di 0.89 mm, alta 3.8 mm: in alluminio 6082 si fa con un utensile da gola
frontale, ma serve un passaggio di finitura leggero.

**Alternative compatte (a choke)**, 10.368 GHz (24.048 GHz):

| mm | Ø guida | larghezza anello | profondità | arretramento | anelli | Ø esterno |
|---|---|---|---|---|---|---|
| Chaparral ottimizzato | 21.31 (9.19) | 12.64 (5.45) | 11.22 (4.84) | 2.25 (0.97) | 3 | 111.0 (49.9) |
| VE4MA ottimizzato | 22.67 (9.77) | 16.00 (6.90) | 17.81 (7.68) | −1.09 (−0.47), cioè anello avanti | 1 | 61.6 (27.6) |

## File per FeedLab

`fdtd/results/feedlab/<feed>_fD0.40_<banda>GHz_<parabola>m.feedlab.json`: tre feed × (10.368, 24.048 GHz) ×
(3, 3.7 m). Si aprono in FeedLab con **📂 Apri progetto** (scheda Uscite) e danno feed, parabola, alluminio 6082 e
piastrina λ/4 verso WR già impostata (WR-90 a 10 GHz, WR-42 a 24 GHz, polarizzazione V, versione ottimizzata). Da
lì ci sono disegni, STEP/STL, piastrina e report come per ogni altro progetto. Nei file, `results` viene dal campo
lontano openEMS confermato (`fdtd/results/openems_fD0.40/<feed>/results.json`), perché il solutore rapido di FeedLab
non vede choke e slot. Quello del solutore rapido resta in `results_fast_solver`, solo per confronto.

Per rifarli: `python fdtd/export_feedlab.py --family axial_corrugated --fD 0.4 --tag 3m`.

## Da fare prima di costruirlo

- Banda più larga (±5 %), se il feed serve anche fuori dal segmento EME.
- Tolleranze: ±0.05 mm a 24 GHz su w, d1 e dk, gli slot sono i più sensibili.
- Una verifica a λ/30 con la sfera completa.
- VE4MA: rifinire l'S11 a λ/24. Chaparral: allargare il limite della larghezza degli anelli.

Dati: `fdtd/results/*_fD0.40*`; per rifare tutto: `fdtd/README.md`.
