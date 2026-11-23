# IZ0JNY Dual-Flare — proposta di un nuovo feed per EME

*Studio FeedLab, novembre 2026. Risultati del solutore rapido (mode matching + integrazione d'apertura): da confermare full-wave con openEMS prima di costruire.*

## Concetto

Quattro tratti, solo cilindri e coni, facili al tornio:

```
guida Ø0.76λ ─┐scalino Ds ─ cono 1 (≈35°) ─ cilindro di fasatura Dm ─ cono 2 (≈5°) ─ apertura Dap
```

1. **Scalino + cono 1**: generano il modo TM11 (TM11/TE11 ≈ 0.32, in pratica il valore ideale 0.31 del modello).
2. **Cilindro di fasatura Dm (≈1.68λ)**: lungo 1.3–1.8λ, rimette il TM11 in fase con il TE11.
3. **Cono 2, quasi cilindrico**: porta l'apertura a 1.7–2.25λ senza sfasare i modi. Il bordo resta a circa −12 dB e il centro di fase vicino all'apertura.

A differenza del Pickett-Potter, il TM11 viene generato **prima** del diametro finale. Per questo lo scalino è piccolo (S11 migliore) e il secondo cono regola il diametro d'apertura in modo indipendente dalla fase dei modi.

## Limite teorico

Ho ottimizzato una combinazione ideale di modi in apertura (TE11 + TM11 + TE12 + TM12, ampiezze, fasi, diametro e curvatura di fase liberi). Con lo stesso modello il massimo calcolabile è:

| f/D (equivalente) | 0.6 | 0.65 | 0.8 |
|---|---|---|---|
| η massima teorica | 77.2 % | 78.7 % | 79.6 % |

I modi oltre il TM11 non aggiungono nulla. **Con un feed liscio corto, nel modello, l'80 % si supera solo da f/D ≈ 0.9.** Il margine vero per l'EME è nel G/T: meno spillover significa un'antenna più fredda.

## Risultati

10.368 GHz, offset 1.2 m, elevazione 30°, LNA 40 K. Simulazione a 16 modi.

| f/D | IZ0JNY η | S11 | T_ant | G/T | Pickett-Potter η / S11 / G/T | W2IMU η / S11 / G/T |
|---|---|---|---|---|---|---|
| 0.60 | 76.5 % | −31.1 dB | 12.3 K | 23.92 | 72.7 % / −24.8 / 23.22 | 75.0 % / −34.6 / 23.33 |
| 0.70 | 77.7 % | −30.7 dB | 12.4 K | 23.98 | 77.4 % / −24.7 / 23.64 | 76.9 % / −26.0 / 23.64 |
| 0.80 | 78.5 % | −34.6 dB | 12.1 K | 24.04 | 78.8 % / −25.9 / 23.77 | 78.6 % / −33.0 / 23.84 |
| 0.85 | 78.7 % | −38.1 dB | 12.6 K | 24.01 | 78.3 % / −26.1 / 23.69 | 77.9 % / −26.3 / 23.71 |
| 0.90 | **80.1 %** | −31.6 dB | 12.8 K | 24.07 | 79.8 % / −26.1 / 23.83 | 78.7 % / −35.2 / 23.75 |

- **G/T**: +0.2…+0.7 dB rispetto al Pickett-Potter, a ogni f/D.
- **S11**: sempre sotto −30 dB al centro banda; sotto −30 dB da −3 % a +8 % (variante f/D 0.8).
- **Tolleranze**: con errori casuali di ±λ/200 su tutte le quote (12 prove), η resta tra 78.8 % e 79.0 % e S11 resta tra −30 e −51 dB.
- **Scalabilità**: il progetto in λ dà gli stessi risultati a 5.76, 24 e 47 GHz. Cambiano solo le perdite ohmiche.

## Limiti da verificare con openEMS

- Il solutore rapido tratta l'apertura come se fosse in una flangia infinita: non vede le correnti sulla parete esterna né la diffrazione dal bordo. Il lobo posteriore e la cross-polarizzazione reali vanno controllati full-wave.
- L'efficienza "reale" sulla parabola sarà più bassa di 12–15 punti, come per tutti i feed (W1GHZ, WD5AGO). Il confronto tra feed resta però valido.

In FeedLab il feed si trova come **IZ0JNY Dual-Flare** nel wizard (f/D 0.6–0.9). Ha anche ottimizzatore, analisi delle tolleranze, disegno PDF e script openEMS (circa 2 milioni di celle, ~5 minuti per frequenza).

## Versione 24.048,1 MHz, f/D 0.65 (ottimizzata per S11)

Partenza: progetto da tabella a f/D 0.65. Obiettivo: S11 più profondo centrato su 24.0481 GHz (media su ±0.2 %, valori sotto −50 dB non contano). Vincoli: G/T al massimo −0.02 dB ed efficienza al massimo −0.1 punti rispetto alla partenza.

| Quota (mm) | Di | Ds | Ls | Dm | L1 | Lp | Dap | L2 | guida d'ingresso | parete |
|---|---|---|---|---|---|---|---|---|---|---|
| | 9.47 | 12.13 | 1.00 | 20.12 | 5.45 | 17.95 | 22.43 | 20.37 | 7.48 | 1.00 |

Lunghezza totale 52.25 mm; cono 1 a 36.2°, cono 2 a 3.2°.

| | η | S11 a 24.048 | G/T (dB/K) | T_ant |
|---|---|---|---|---|
| IZ0JNY partenza | 77.1 % | −30.1 dB | 29.70 | 34.8 K |
| **IZ0JNY 24 GHz ottimizzato** | **77.0 %** | **≈ −51 dB** (−42…−51 secondo il numero di modi) | **29.68** | 35.1 K |
| Pickett-Potter | 76.4 % | −25.6 dB | 29.43 | 39.2 K |
| W2IMU OE2IGL | 77.0 % | −28.7 dB | 29.47 | 38.4 K |

Offset 1.2 m, elevazione 30°, LNA 40 K.

- **Banda**: S11 sotto −40 dB da 23.65 a 24.55 GHz e sotto −47 dB da 23.9 a 24.25 GHz.
- **Tolleranze**: con quote sbagliate a caso di ±0.05 mm, il caso peggiore su 20 prove resta a −49.5 dB.
- **Precisione**: valori di S11 sotto −40 dB sono al limite della precisione del solutore e di qualsiasi misura. Il dato affidabile è "≤ −40 dB, minimo centrato su 24.048 GHz". Va confermato con openEMS.

## Verifica openEMS (24.0481 GHz, f/D 0.65, base rotonda)

Simulazione FDTD fatta da IZ0JNY con openEMS 0.37: 1.9 milioni di celle, 20 celle/λ, 21 minuti. Il dato di confronto è il modello rapido sulla stessa geometria.

| | openEMS | modello rapido |
|---|---|---|
| S11 a 24.048 GHz | −25.4 dB (ROS 1.11) | −47 dB |
| minimo di S11 | −34 dB a 23.04 GHz | −47 dB a 24.05 GHz |
| S11 peggiore 21.6–26.5 GHz | −23.4 dB | −21 dB |
| η sulla parabola | 75.7 % | 78.1 % |
| spillover / illuminazione | 0.961 / 0.788 | 0.943 / 0.828 |
| bordo (edge taper) | −15.5 dB | −13.6 dB |
| T antenna | 33.9 K | 35.1 K |
| **G/T** | **29.72 dB/K** | 29.78 dB/K |
| cross-polare di picco | −27 dB | — |
| asimmetria E/H a −10 dB | 2.6° | — |
| F/B | 30 dB | — |
| centro di fase | 1.6 mm dentro l'apertura | 0.4 mm |

Il G/T è confermato entro 0.06 dB. Il fascio reale è un po' più stretto del previsto: il feed è ottimale per f/D 0.80 (η 79.6 %), mentre a f/D 0.65 illumina meno la parabola. Il bordo meno illuminato abbassa di poco l'efficienza ma tiene l'antenna più fredda. Il diagramma è molto simmetrico, con cross-polare bassa.

Il minimo di S11 è spostato di circa 1 GHz verso il basso. Il tratto dopo lo scalino (1 mm) è descritto da meno di 2 celle della griglia, quindi serve una simulazione a 30 celle/λ per decidere se lo spostamento è reale (script in `docs/iz0jny/sim_iz0jny_24048_fD065_fine.zip`). Se lo è, lo si corregge con lo space mapping di FeedLab.

### Verifica di convergenza (griglia fine, 30 celle/λ)

3.5 milioni di celle, 31 minuti, stessa geometria della prima simulazione.

| | 20 celle/λ | 30 celle/λ |
|---|---|---|
| S11 a 24.048 GHz | −25.4 dB | **−28.2 dB** (ROS 1.08) |
| S11 tra 23.0 e 25.0 GHz | −23.5 … −34 dB | **−27.5 … −29.5 dB** (piatto) |
| S11 peggiore 21.6–26.5 GHz | −23.4 dB | −24.3 dB |
| η sulla parabola (f/D 0.65) | 74.9 % | 75.3 % |
| G/T | 29.72 dB/K | 29.75 dB/K |
| T antenna | 33.9 K | 33.7 K |
| cross-polare | −27.0 dB | −29.7 dB |
| F/B | 29.9 dB | 37.3 dB |
| centro di fase | 1.6 mm | 1.2 mm |
| f/D ottimo del feed | 0.80 | 0.80 |

Diagramma, efficienza e G/T sono convergenti, con differenze di pochi centesimi di dB. L'S11 sotto −25 dB dipende ancora dalla griglia: il "minimo spostato a 23 GHz" della prima simulazione era un effetto della griglia grossa. Con la griglia fine la risposta è piatta, circa −28 dB su tutta la banda 23–25 GHz. Il minimo profondo a −47 dB del modello rapido non è reale, ma un adattamento di −28 dB (perdita per disadattamento 0.007 dB, potenza riflessa in TX 0.16 %) è già ottimo per l'EME.
