# FeedLab FDTD — ottimizzazione iterativa dei feed con openEMS

Ambiente riproducibile per far girare **openEMS** (FDTD full-wave) in serie e cercare, per una data f/D della
parabola, la geometria di feed con la massima efficienza d'illuminazione. Non fa parte del programma
Windows/Linux: è uno strumento di ricerca che usa i moduli di FeedLab (`geometry`, `openems_sim`,
`deep_analysis`, `efficiency`).

## Installazione

| Dove | Comando | Tempo |
|---|---|---|
| Container cloud pulito (Ubuntu 24.04, senza Docker) | `bash fdtd/setup_cloud.sh` | ~5 min (compila openEMS v0.37.0) |
| Docker | `docker build -t feedlab-fdtd -f fdtd/Dockerfile .` | ~6 min |
| Debian/Ubuntu locale | `sudo bash fdtd/install_openems.sh` | ~5 min |

openEMS finisce in `/opt/openEMS`, i binding Python in `/opt/openEMS/venv` (versione fissata con `OPENEMS_TAG`).

## Uso

```bash
PY=/opt/openEMS/venv/bin/python
$PY fdtd/benchmark.py --fD 0.6                         # feed pubblicati, stesse regole (tabella di riferimento)
$PY fdtd/optimize.py --family w2imu --fD 0.6 --budget 60
$PY fdtd/optimize.py --family dualflare --fD 0.6 --method de --budget 150
$PY fdtd/optimize.py --family profile --fD 0.6 --seed-mm  # profilo libero, partenza dal mode matching
$PY fdtd/optimize.py --family w2imu --fD 0.6 --confirm    # migliore e partenza di nuovo a 24 celle/λ
# primo fuoco: blocking del feed su una parabola da 3 m a 10.368 GHz (103.75 λ), file *_fD0.40_3m*
$PY fdtd/optimize.py --family axial_corrugated --fD 0.4 --dish-lambda 103.75 --tag 3m --method de --budget 130
$PY fdtd/rescore_dishes.py --fD 0.4 --tag 3m --dishes 3000,3700 --bands 10.368,24.048   # altre parabole, senza nuovi run
$PY fdtd/export_feedlab.py --family axial_corrugated --fD 0.4 --tag 3m                  # file di progetto FeedLab
$PY fdtd/eta_vs_fD.py --f 10.368          # grafici efficienza/f/D/Ø parabola di tutti i feed (ottimizzati e pubblicati)
```

Con Docker: `docker run --rm -v "$PWD/fdtd/results:/work/fdtd/results" -v "$PWD/fdtd/runs:/work/fdtd/runs" feedlab-fdtd python fdtd/optimize.py ...`

- **Famiglie**: `w2imu` (A, B, semiangolo, C), `dualflare` (scalino + cono 1 + cilindro + cono 2),
  `profile` (profilo liscio monotono PCHIP con scalino d'ingresso), `axial_corrugated` (8 slot assiali, OE2IGL),
  `ve4ma` e `chaparral` (guida liscia con anello/i choke: Ø guida, larghezza, profondità, arretramento; per f/D
  0.3–0.45), `large_w2imu` / `large_w2imu_30` (W2IMU large flare, cono libero o 30° fisso), `dualflare_wide`
  (Dual-Flare con limiti aperti verso bocche piccole). Quote in λ: il risultato vale per ogni
  banda alla stessa f/D. La simulazione gira a `--f0` (10.368 GHz).
- **Metodi**: `nm` Nelder-Mead dal progetto di letteratura (locale, poche decine di run), `de` evoluzione
  differenziale (globale, centinaia di run).
- **Cache**: ogni run openEMS sta in `fdtd/runs/<hash>/` (solo json e log; i campi grezzi si cancellano).
  Un'ottimizzazione interrotta riparte da dove era: i punti già simulati costano zero.
- **Risultati**: `fdtd/results/<famiglia>_fD<f/D>[_tag].jsonl` (tutte le valutazioni), `*_best.json`, `*_confirm.json`.
- **Primo fuoco**: `--dish-lambda` = Ø della parabola in λ; la FOM include il blocking del Ø esterno del feed.
- **Verso FeedLab**: `export_feedlab.py` scrive `fdtd/results/feedlab/*.feedlab.json` (📂 Apri progetto), con la
  piastrina WR già impostata e i risultati dal campo lontano openEMS confermato.
- **Risultati pubblicati**: `RISULTATI_fD060.md` (offset/f/D 0.6), `RISULTATI_fD040.md` (primo fuoco f/D 0.4, 3–3.7 m). `RISULTATI_offset_fD065.md` (tromba piramidale/quadrata WR per offset f/D 0.65, simulazione 3D `rect_horn_sim.py`).

## Impostazioni di simulazione (`fdtd_eval.EvalConfig`)

- eccitazione f0 ± 10 % (impulso corto), campo lontano a f0·(1−b), f0, f0·(1+b), S11 valutato solo in f0 ± b;
- cella = λ0/16 durante la ricerca; le linee di griglia più vicine di 0.3 celle si fondono (le celle
  minuscole riducono il passo temporale: i corrugati passavano da 3 a 18 minuti);
- massimo 40 000 passi; una simulazione che non scende sotto −22 dB di energia (cavità chiusa, instabilità)
  è scartata con penalità 1.0.

Con queste regole: W2IMU 29 s, Axial Corrugated 95 s (4 core).

## Figura di merito

Per ciascuna frequenza f0·(1−b), f0, f0·(1+b) (b = 2 % di default), dal campo lontano openEMS (NF2FF):

η(f) = spillover × taper × fase × cross-pol (Kildal/W1GHZ, `feedlab.efficiency`) × (1 − |S11(f)|²)

con il feed in **un solo** centro di fase, trovato a f0 e tenuto fisso in banda. FOM = media di η(f),
meno 0.01 per ogni dB di S11 sopra −20 dB e per ogni λ di lunghezza oltre 12 λ. Il blocking non è incluso
(offset, oppure si aggiunge dopo per il prime focus).

## Validazione (W2IMU, f/D 0.6, 10.368 GHz)

| Celle/λ | Celle | FDTD | η f0 | η media ±2 % | S11 max |
|---|---|---|---|---|---|
| 14 | 0.40 M | 49 s | 75.9 % | 74.5 % | −24.2 dB |
| 20 | 0.82 M | 82 s | 76.8 % | 75.9 % | −26.5 dB |
| 26 | 1.53 M | 174 s | 77.0 % | 76.1 % | −28.8 dB |

(4 core). A 16 celle/λ l'errore resta entro ~1.5 punti e l'ordinamento dei progetti non cambia: si cerca a
16 e si conferma a 24+. Il valore converge sul ~77 % del W2IMU riportato da W1GHZ.
