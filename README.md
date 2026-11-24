# FeedLab — Laboratorio di Progettazione di feed/illuminatori a microonde

*(repository: [IZ0JNY/FeedLab](https://github.com/IZ0JNY/FeedLab))*

Software per **progettare e simulare illuminatori (feed) per parabole a microonde, da 10 a 134 GHz**.

Le basi di conoscenza sono:
- il *W1GHZ Online Microwave Antenna Book* e gli articoli di Paul W1GHZ;
- le design guide e le simulazioni openEMS/GRASP di Gerald OE2IGL;
- la teoria classica: Kildal, Milligan, Baars, Silver, Balanis.

> Stato: **v0.4.22 BETA TEST**, software libero con licenza **GPLv3**, senza scadenza. Programma per Windows (installer, interfaccia e manuale PDF in italiano e inglese), interfaccia grafica, simulatore a mode matching, CAD/STEP, disegno PDF, catalogo parabole, materiali, piastrina WR e **deep analysis openEMS opzionale** con installazione guidata.

## Cosa fa oggi
| Modulo | Funzioni |
|---|---|
| `waveguide` | Cutoff dei modi circolari (TE11, TM01, TM11, TE21, TE12…), λg, guide WR-90…WR-5, bande radioamatoriali |
| `reflector` | Geometria prime-focus e offset (angoli ai bordi, f/D equivalente, puntamento del feed offset); fit di parabola offset da misure; Ruze, blocking (Baars), defocus (Milligan), beam factor/HPBW |
| `patterns` | Pattern BOR1 (E/H complessi). Modelli analitici: gaussiano, cos^q. **Integrazione d'apertura** con miscela di modi (TE11 + TM11 = dual-mode, HE11 = corrugato) e fase quadratica del flare; apertura rettangolare (horn piramidale). Lettura e scrittura dei file `.dat` W1GHZ FEEDPATT/PHASEPAT |
| `efficiency` | Efficienza d'apertura (Kildal/W1GHZ) con decomposizione in spillover, illuminazione, fase, cross-pol e blocking; curva η vs f/D; **centro di fase** (metodo PHASEPAT e formula di W1GHZ); curva di defocus; riproduzione esatta dell'algoritmo FEEDPATT per confronti |
| `horns` | Calcolatori: W2IMU (Turrin/W1GHZ e OE2IGL), Large W2IMU a 30° (47/78/122/241 GHz), Skobelev optimum dual-mode (tabella HFSS di W1GHZ), Pickett-Potter (OE2IGL), **IZ0JNY Dual-Flare** (nuovo, per EME; studio in `docs/IZ0JNY_DualFlare.md`), Axial Corrugated (base concept Luis CT1DMK, improved version Gerald OE2IGL, foglio v1.4), VE4MA, Super-VE4MA, Chaparral, horn rettangolare G3RPE, centro di fase del piramidale (Fresnel), horn conico ottimo, horn diagonale |
| `cassegrain` | Progetto del subriflettore iperbolico (procedura W1GHZ verificata sul suo foglio di calcolo), sub ottimo di Kildal, profilo e G-code per tornio |
| `noise` | T_sky (con correzione di Planck), T_rx, T_spillover, T_antenna integrata sul pattern, G/T, sun noise atteso |


## FeedLab per Windows

Scarica **`FeedLab-Setup-<versione>.exe`** dalla pagina [Releases](https://github.com/IZ0JNY/FeedLab/releases) e avvialo: si installa per l'utente corrente, senza diritti di amministratore, con icona nel menu Start (e sul desktop, se vuoi). C'è anche lo zip *portable*: estrai e avvia `FeedLab.bat`.

- **Bilingue**: italiano e inglese, sia nell'installer sia nell'app (selettore nella barra laterale; la lingua scelta nell'installazione è quella iniziale). Disegni PDF e report seguono la lingua scelta.
- Tutte le schede di FeedLab in una **finestra propria** (Microsoft Edge WebView2); funziona senza internet. Se WebView2 manca, si apre nel browser.
- **openEMS è facoltativo.** Il simulatore rapido interno risponde in secondi; openEMS serve solo per l'analisi full-wave di riferimento, che richiede da minuti a ore. Si installa dall'interno del programma, nella scheda **🖥️ Full-wave openEMS → ① Installazione**, con la procedura guidata: scarica l'ultima versione ufficiale per Windows, la estrae in `%LOCALAPPDATA%\Programs\openEMS`, imposta `OPENEMS_INSTALL_PATH`, installa i binding Python nel Python di FeedLab e fa una simulazione di prova. L'installer di FeedLab non scarica nulla.
- **② Nuova analisi**: singola simulazione, **convergenza della mesh** (più risoluzioni) o **sweep di una quota**, con stima di celle, RAM e durata. Gli script openEMS sono generati in automatico dal feed corrente; puoi anche solo scaricarli per un altro PC.
- **③ Simulazioni**: girano in background una dopo l'altra, con avanzamento (energia residua, tempo stimato), e continuano anche se chiudi FeedLab. Si trovano in `Documenti\FeedLab\openEMS`.
- **④ Risultati (deep analysis)**: S11, VSWR, banda a −15/−20 dB, impedenza; lobi co/cross-polari (Ludwig-3) a più frequenze; direttività dalla sfera completa e verifica dell'ipotesi BOR1; potenza irradiata/accettata come controllo di convergenza; **centro di fase** (metodo PHASEPAT e formula W1GHZ) e sua deriva in banda; **efficienza vs f/D** scomposta; guadagno, T antenna e **G/T** sulla tua parabola; confronto con il modello rapido; confronto fra simulazioni; report HTML, CSV e file `.dat` W1GHZ. Il lobo full-wave si può usare anche nelle altre schede.

Compilazione: GitHub Actions (`.github/workflows/windows.yml`) esegue i test su Windows e crea installer e zip; in locale `windows\build.ps1` (Python embedded + pacchetti + Inno Setup).

## Interfaccia grafica

```bash
pip install -e .
feedlab-gui          # oppure: streamlit run feedlab_main.py
```
Si apre nel browser (Windows, Linux, macOS). Schede:

| Scheda | Cosa fa |
|---|---|
| 🧭 Procedura guidata | Scegli la parabola dal **catalogo commerciale** (Gibertini, Triax, Fracarro, Kathrein, Channel Master/Skyware, Edmund, dish misurati da W1GHZ, con fonte di ogni dato) oppure una **parabola custom** (offset o prime focus; da f/D, focale, misure o angolo di illuminazione). Indica polarizzazione, obiettivo (guadagno o G/T) e mezzi di costruzione: FeedLab confronta i feed adatti e li ordina per efficienza stimata |
| 📐 Progetto feed | Quote del feed modificabili, sezione assiale, regola di progetto usata |
| 🎛️ Laboratorio | **Cursori sulle quote** con ricalcolo immediato e confronto col progetto di partenza: Δ S/N, efficienza, guadagno, G/T, T antenna, S11, taper, perdite ohmiche del materiale. Obiettivo **TX / RX / EME**, consigli ragionati, **analisi di sensibilità** per ogni quota, **ottimizzazione automatica**. **Tolleranze di lavorazione**: Monte Carlo della resa, quote critiche con la tolleranza che serve a ciascuna (anche nel PDF), **ottimizzazione robusta** |
| 📈 Simulazione & S11 | S11 in banda e contenuto modale (mode matching), lobo polare e cartesiano con fase, efficienza vs f/D scomposta, centro di fase, G/T |
| 🌐 Lobo 3D | Diagramma di irradiazione 3D del feed |
| 🧊 Modello 3D | Modello del feed con sezione |
| 📄 Disegno & STEP | Disegno meccanico **PDF** (sezione quotata, tabella, cartiglio, tolleranze), **.stp** e **.stl** |
| 🔌 Piastrina WR | Piastrina λ/4 da guida circolare a guida rettangolare WR (guida scelta nella barra laterale fra quelle della banda: 10 GHz WR-90/WR-75, 24 GHz WR-42, 47 GHz WR-22/WR-19; base del feed circolare o quadrata come la flangia), orientata per polarizzazione **verticale o orizzontale** (metodo OE2IGL/HB9PZK), PDF + STEP. Opzione **fori di fissaggio** (viti metriche o in pollici): piastrina con la forma della flangia (quadrata a 10/24 GHz, rotonda da 47 GHz); a 10/24 GHz foratura standard filettata nella piastra e 4 viti piastra→feed con testa in lamatura; da 47 GHz la piastrina si appoggia sulla base e le viti della guida si avvitano nella base; spessore della base impostabile; riportata in PDF e STEP di piastra e feed |
| 🖥️ Full-wave openEMS | **Opzionale**: installazione guidata di openEMS, simulazioni FDTD in background (singola, convergenza, sweep) e **deep analysis** dei risultati. **⑤ Space mapping**: openEMS verifica pochi candidati e corregge il modello rapido, fino alla convergenza |

Nella barra laterale si scelgono la banda (10–134 GHz), il **materiale del feed** (rame, rame argentato, dorato, ottone, alluminio, stampa 3D metallizzata…), con calcolo delle perdite e del rumore.

### Simulatori e loro limiti
- **Rapido (mode matching interno, secondi).**
  - Feed a guida circolare con gradini e coni: open, W2IMU, Skobelev/Pickett-Potter, conico. Il bilancio energetico è verificato a 1.000.
  - L'apertura è modellata come flangia: S11 è una stima, ottimistica per aperture sotto 1λ.
  - Feed con choke o anelli coassiali (VE4MA, Chaparral): non simulati qui, si stimano dalle design guide.
- **Full-wave openEMS** (gratuito, https://openems.de): S11 e lobo di riferimento, per tutti i feed a simmetria di rotazione.
  - Lo script è generato sul modello del tutorial ufficiale "Conical Horn" (porta TE11 in guida circolare + nf2ff).
  - Va eseguito sul PC dove openEMS è installato (nella versione per Windows l'installazione è guidata).

## Distribuzione
FeedLab si distribuisce solo come **programma per Windows** (vedi sopra): non è pensato per essere pubblicato come app web e
non si avvia su Streamlit Community Cloud. Per usarlo da sorgente sul proprio PC: `streamlit run feedlab_main.py`.

## Validazione (`pytest`)
- Feed cos^n: η massima uguale all'integrazione analitica indipendente (scarto entro 0.3%).
- W2IMU 1.63λ e 1.79λ: flare 27.4° e 24.9°, C 2.8λ e 3.52λ (W1GHZ, libro §6.5).
- Cassegrain: M, e, distanze e d_sub/D di Kildal identici al foglio `Cassegrain_design.xls` di W1GHZ.
- Pickett-Potter a 47.048 GHz: dimensioni identiche al foglio OE2IGL.
- Guida circolare aperta 0.76λ: ~68% a f/D 0.35 (W1GHZ con NEC2: 67%, f/D 0.35–0.4).
- W2IMU 1.31λ: ottimo a f/D ~0.56 (W1GHZ: 0.5–0.6).
- Ruze a 122 e 241 GHz, correzione di Planck a 47 GHz (OE2IGL).
- Balanis: efficienza del riflettore con feed cos^n uguale al motore di FeedLab entro 0.0002; horn piramidale con integrali di Fresnel uguale all'integrale 2D dell'apertura entro 0.01 dB (`tests/test_balanis.py`).
- EME a 24 GHz (W5LUA 2012, calcolatori VK3UM): perdita di percorso EME 295.24 dB, rumore di Luna 2.23 dB e di Sole 12.8 dB, assorbimento atmosferico e rumore del cielo; feed W2IMU modificato di W5LUA con centro di fase ~2.5 mm dietro la faccia (`tests/test_w5lua.py`).

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

Nella barra laterale: **ℹ️ Credits** (autore, versione, fonti), **📖 Manuale** (PDF nella lingua scelta) e **🐞 Segnala un problema**, che apre la pagina GitHub delle segnalazioni con versione e progetto già compilati.

## Documentazione
- `docs/KNOWLEDGE_BASE.md`: sintesi strutturata di formule, regole e dati.
- `docs/notes/`: appunti dettagliati per capitolo e articolo (W1GHZ, OE2IGL).

## Altri riferimenti usati
rusk2ua/offset-microwave-dish-comparisons (formule e test incrociati), Abraxas3d/122GHz (W2IMU e Cassegrain stampati 3D a 122 GHz), david-deboer/hera-cst (formato dei pattern CST/HFSS), IRNAS/SatelliteDishHeadHolder (portaLNB Ø40), diablowu/dish-fd-feed, vantalane/dual_band_LHCP_helical_feed (script openEMS).

## Autore
Software sviluppato da **Ivan De Cesaris, IZ0JNY**, ivan@iz0jny.it. Nel programma, la scheda **ℹ️ Credits** riporta la versione e tutte le fonti.

## Licenza
Copyright © 2026 Ivan De Cesaris, IZ0JNY.

FeedLab è **software libero**: puoi usarlo, studiarlo, ridistribuirlo e modificarlo secondo i termini della **GNU General Public License v3.0 o successiva** ([GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0.html)); il testo completo è nel file [LICENSE](LICENSE). In breve: chi ridistribuisce FeedLab, anche modificato e anche a pagamento, deve rendere disponibile il codice sorgente con la stessa licenza e mantenere le note di copyright dell'autore. FeedLab è fornito **senza alcuna garanzia**: i risultati sono stime di progetto da verificare con simulazione full-wave e misure.

Le librerie usate restano coperte dalle proprie licenze (Python PSF; NumPy e SciPy BSD; Matplotlib; Plotly MIT; Streamlit Apache-2.0; CadQuery Apache-2.0 e Open CASCADE LGPL-2.1); openEMS (GPL-3.0) si installa a parte come programma esterno.

## Contribuire
Prove, misure, segnalazioni e codice sono benvenuti: le regole sono in [CONTRIBUTING.md](CONTRIBUTING.md) (i contributi sono distribuiti con la stessa licenza GPLv3 e restano di chi li ha fatti). Chi contribuisce è citato in [CONTRIBUTORS.md](CONTRIBUTORS.md) e nella finestra **ℹ️ Credits**.

## Crediti e licenze delle fonti
- Algoritmi e dati da Paul W1GHZ (w1ghz.org). Il suo materiale è gratuito per uso radioamatoriale; per uso commerciale chiede un contributo all'ARRL Foundation.
- Design guide di Gerald OE2IGL (wettersat.bplaced.net), incluso il *High performance axial corrugated feed* v1.4 (foglio di calcolo e presentazione, Dorsten 2026) → tipo di feed `axial_corrugated`.
- C. A. Balanis, *Antenna Theory: Analysis and Design*, Wiley (4ª ed. 2016): formule chiuse di horn e riflettori usate come verifica (`feedlab.balanis`).
- Flann Microwave, *Waveguide and Flange Data*; MIL-DTL-3922/67C: foratura delle flange standard (`feedlab.flanges`).
- Ivan IZ0JNY, feed W2IMU a 24 GHz (https://www.iz0jny.it/24ghz-feedhorn-w2imu/): schema di accoppiamento piastra WR-42 / feed, riprodotto in `tests/test_flanges.py`.
- Jeff WA6KBL, *Easy to Manufacture and Extremely High Performance Dual Mode Feedhorns with Direct Waveguide Input For the 10GHz and 24GHz Bands*, DUBUS: criterio TM11 ≈ 15% per il Pickett-Potter (controllo in Simulazione e nei consigli del Laboratorio), avvertenza sulle quote Skobelev.
- Sergei RW3BP, *EME antenna and Jupiter noise on 77 GHz* (EME 2014); Luis CT1DMK, *EME and Radio Astronomy*; Luis CT1DMK e Willi LX1DB, *Circular Polarized antenna feed* (5.7/10 GHz): verifiche in `tests/test_eme_refs.py`.
- Paul W1GHZ, AD6FP e AA6IW (feed dual-band 10/24 GHz); Paul W1GHZ e OK1DFC (septum); S57UUU (polarizzatore 10 GHz); DL4MUP (septum); G0IVA (feed 47 GHz); la rivista **DUBUS** (articoli di Jeff WA6KBL e della comunità EME).
- Il codice qui è una reimplementazione indipendente: non contiene codice né file di dati originali. I pattern `.dat` di W1GHZ si scaricano a parte (`feedpatt.zip`) e si leggono con `patterns.load_w1ghz_dat`.
