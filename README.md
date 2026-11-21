# mwFeedDesign / FeedLab

Software per **progettare e simulare illuminatori (feed) per parabole a microonde, da 10 a 134 GHz**.

Le basi di conoscenza sono:
- il *W1GHZ Online Microwave Antenna Book* e gli articoli di Paul Wade, W1GHZ;
- le design guide e le simulazioni openEMS/GRASP di Gerald Ihninger, OE2IGL;
- la teoria classica: Kildal, Milligan, Baars, Silver, Balanis.

> Stato: **v0.1, nucleo di calcolo**. Il codice ha una suite di test che riproduce numeri pubblicati. Non ha ancora interfaccia grafica né solutore full-wave.

## Cosa fa oggi
| Modulo | Funzioni |
|---|---|
| `waveguide` | Cutoff dei modi circolari (TE11, TM01, TM11, TE21, TE12…), λg, guide WR-90…WR-5, bande radioamatoriali |
| `reflector` | Geometria prime-focus e offset (angoli ai bordi, f/D equivalente, puntamento del feed offset); fit di parabola offset da misure; Ruze, blocking (Baars), defocus (Milligan), beam factor/HPBW |
| `patterns` | Pattern BOR1 (E/H complessi). Modelli analitici: gaussiano, cos^q. **Integrazione d'apertura** con miscela di modi (TE11 + TM11 = dual-mode, HE11 = corrugato) e fase quadratica del flare; apertura rettangolare (horn piramidale). Lettura e scrittura dei file `.dat` W1GHZ FEEDPATT/PHASEPAT |
| `efficiency` | Efficienza d'apertura (Kildal/W1GHZ) con decomposizione in spillover, illuminazione, fase, cross-pol e blocking; curva η vs f/D; **centro di fase** (metodo PHASEPAT e formula di W1GHZ); curva di defocus; riproduzione esatta dell'algoritmo FEEDPATT per confronti |
| `horns` | Calcolatori: W2IMU (Turrin/W1GHZ e OE2IGL), Large W2IMU a 30° (47/78/122/241 GHz), Skobelev optimum dual-mode (tabella HFSS di W1GHZ), Pickett-Potter (OE2IGL), corrugato assiale a 8 gole (OE2IGL v1.4), VE4MA, Super-VE4MA, Chaparral, horn rettangolare G3RPE, centro di fase del piramidale (Fresnel), horn conico ottimo, horn diagonale |
| `cassegrain` | Progetto del subriflettore iperbolico (procedura W1GHZ verificata sul suo foglio di calcolo), sub ottimo di Kildal, profilo e G-code per tornio |
| `noise` | T_sky (con correzione di Planck), T_rx, T_spillover, T_antenna integrata sul pattern, G/T, sun noise atteso |

## Validazione (`pytest`)
- Feed cos^n: η massima uguale all'integrazione analitica indipendente (scarto entro 0.3%).
- W2IMU 1.63λ e 1.79λ: flare 27.4° e 24.9°, C 2.8λ e 3.52λ (W1GHZ, libro §6.5).
- Cassegrain: M, e, distanze e d_sub/D di Kildal identici al foglio `Cassegrain_design.xls` di W1GHZ.
- Pickett-Potter a 47.048 GHz: dimensioni identiche al foglio OE2IGL.
- Guida circolare aperta 0.76λ: ~68% a f/D 0.35 (W1GHZ con NEC2: 67%, f/D 0.35–0.4).
- W2IMU 1.31λ: ottimo a f/D ~0.56 (W1GHZ: 0.5–0.6).
- Ruze a 122 e 241 GHz, correzione di Planck a 47 GHz (OE2IGL).

## Uso rapido
```bash
pip install -e .[test]
```
```bash
pytest -q
```
```bash
python examples/design_report.py
```
```python
from feedlab import horns, patterns, efficiency
print(horns.skobelev(122.25, fD=0.7))
p = patterns.circular_aperture_pattern(1.7, {"TE11": 1, "TM11": 0.2})
print(efficiency.best_fD(p))
```

## Roadmap
1. **Import dei pattern full-wave.** openEMS (script Python con nf2ff), CST/HFSS (CSV), GRASP (.cut), NEC2. Tagli a 45° e polarizzazione circolare.
2. **Generatore di geometrie** per openEMS e STL/STEP: W2IMU, Skobelev/Pickett-Potter, corrugato, choke, septum. Fabbricazione: dime, G-code, punte da centri.
3. **Ottica fisica (PO) del riflettore**: pattern secondario, offset, diffrazione del subriflettore Cassegrain/Gregorian (Granet), supporti e blocking.
4. **Mode matching** per gradini e coni in guida circolare: progetto veloce di dual-mode e corrugati senza FDTD.
5. **G/T completo per offset**, rete (Otoshi), atmosfera ITU-R P.676 fino a 134 GHz.
6. **GUI** (Qt o web) con confronto di più feed e report PDF.

## Documentazione
- `docs/KNOWLEDGE_BASE.md`: sintesi strutturata di formule, regole e dati.
- `docs/notes/`: appunti dettagliati per capitolo e articolo (W1GHZ, OE2IGL).

## Crediti e licenze delle fonti
- Algoritmi e dati da P. Wade W1GHZ (w1ghz.org). Il suo materiale è gratuito per uso radioamatoriale; per uso commerciale chiede un contributo all'ARRL Foundation.
- Design guide di G. Ihninger OE2IGL (wettersat.bplaced.net).
- Il codice qui è una reimplementazione indipendente: non contiene codice né file di dati originali. I pattern `.dat` di W1GHZ si scaricano a parte (`feedpatt.zip`) e si leggono con `patterns.load_w1ghz_dat`.
