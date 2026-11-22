# FeedLab — Manuale d'uso

**Laboratorio di Progettazione di feed/illuminatori a microonde**
Versione {VERSION} BETA TEST · Ivan De Cesaris, IZ0JNY · ivan@iz0jny.it

---

## 1. Cos'è FeedLab
FeedLab serve a **progettare, simulare e costruire illuminatori (feed) per parabole** da **10 a 134 GHz**. Con FeedLab:
- scegli la parabola (catalogo commerciale o parabola tua) e la banda;
- ottieni il feed più adatto con le sue quote;
- vedi lobo, efficienza, S11, guadagno e G/T;
- modifichi le quote e vedi subito se il risultato migliora o peggiora, per TX, RX o EME;
- produci il **disegno meccanico PDF** e i file **.stp** / **.stl** per l'officina;
- progetti la **piastrina λ/4** di passaggio alla guida rettangolare WR, con fori, filettature e spine;
- verifichi il progetto con **openEMS** (facoltativo) e lo correggi automaticamente.

I calcoli si basano sul *W1GHZ Online Microwave Antenna Book* (Paul W1GHZ), sulle design guide di Gerald OE2IGL, sui libri di Balanis e Kildal e sui lavori di Al W5LUA, Jeff WA6KBL, Sergei RW3BP, Luis CT1DMK e Ivan IZ0JNY. L'elenco completo è nella finestra **ℹ️ Credits**.

## 2. Versione BETA TEST
Questa è una **versione di prova**: vale **30 giorni dalla prima installazione**, poi si disattiva.
- A ogni avvio compare un **popup** con la data di scadenza e i giorni rimasti: chiudilo con la **✕** in alto a destra.
- Alla scadenza FeedLab mostra solo l'avviso e il link alla pagina **Releases** di GitHub: scarica e installa la versione più recente.
- Ogni nuova versione ha i suoi 30 giorni. Se l'orologio del PC viene spostato indietro, la versione si considera scaduta.

![Popup BETA TEST]({IMG}/00_beta.png)

## 3. Installazione
### Windows (consigliato)
1. Scarica l'ultima versione dalla pagina **Releases** del repository GitHub (IZ0JNY/FeedLab).
2. **Installer:** avvia `FeedLab-Setup-x.y.z.exe`. Non servono diritti di amministratore. Al termine trovi FeedLab nel menu Start.
3. **Versione portatile:** estrai `FeedLab-x.y.z-portable.zip` in una cartella e fai doppio clic su `FeedLab.bat`. Non installa niente nel sistema.

FeedLab si apre in una finestra propria (Microsoft Edge WebView2, già presente in Windows 11). Se WebView2 manca, si apre nel browser.

### Linux / macOS (da sorgente)
```
pip install -e .
feedlab-gui
```

### Lingua
In alto nella barra laterale: **Lingua / Language** (italiano o English). L'installer propone la lingua all'installazione; il pulsante **📖 Manuale** apre il manuale nella lingua scelta.

## 4. La barra laterale
| Voce | Uso |
|---|---|
| **Banda** | frequenza di lavoro (bande radioamatoriali 10–134 GHz o *Altra frequenza…*) |
| **λ** | lunghezza d'onda corrispondente |
| **Parabola / Feed** | riepilogo della scelta fatta nella procedura guidata |
| **Materiale del feed** | rame, rame argentato, ottone, alluminio, stampa 3D metallizzata…: FeedLab calcola perdite e rumore aggiunto |
| **ℹ️ Credits** | autore, versione e tutte le fonti |
| **📖 Manuale** | scarica questo manuale in PDF |
| **🐞 Segnala un problema** | apre la pagina GitHub delle segnalazioni con versione e progetto già compilati |

## 5. Procedura guidata
![Procedura guidata]({IMG}/01_wizard.png)

1. **Parabola:**
   - *catalogo*: Gibertini, Triax, Fracarro, Fuba, Kathrein, Channel Master/Andrew, Prodelin, Edmund e altre, con la fonte di ogni dato;
   - *parabola custom*: offset o prime focus.
2. **Dati della parabola custom:**
   - offset: da diametro + f/D, da diametro + focale, da **misure sul campo** (asse lungo, asse corto, profondità) o da angolo di illuminazione;
   - prime focus: da f/D o da profondità.
3. **Polarizzazione, obiettivo e lavorazione:** lineare o circolare; **guadagno** (TX) o **G/T** (RX/EME); tornio o lamiera.
4. **Trova il feed migliore:** FeedLab confronta i feed adatti e li ordina per efficienza stimata, con motivazioni e avvertenze.
5. **Usa questo feed:** le altre schede lavorano su quel progetto.

![Risultato della procedura guidata]({IMG}/02_wizard_result.png)

**Se la focale non è pubblicata** (succede per molte parabole Kathrein e Channel Master), il catalogo lo indica. Usa *misure sul campo*: tendi un filo lungo l'asse lungo e misura la profondità al centro.

### 5.1 Tipi di feed
| Feed | Quando usarlo |
|---|---|
| **Axial Corrugated (base concept Luis CT1DMK, improved version Gerald OE2IGL)** | 10–76 GHz, f/D 0.33–0.9 (offset fino a 0.8): 81–86%, il più efficiente; quote dal foglio di calcolo v1.4 di Gerald OE2IGL in funzione dell'angolo di apertura |
| **W2IMU, Pickett-Potter, Skobelev, Large W2IMU** | dual-mode per offset e f/D 0.5–0.95; Pickett-Potter e W2IMU grande anche oltre 76 GHz |
| **Super-VE4MA, Chaparral, guida aperta** | prime focus profonde (f/D < 0.5) |
| **Horn rettangolare** | solo polarizzazione lineare, diretto da guida WR |

I feed per 1296 MHz (per esempio il septum di Zdeněk OK1DFC) sono fuori dal campo di FeedLab, che parte da 10 GHz.

## 6. Progetto feed
Mostra le quote del feed (in mm e in λ), la sezione assiale e la regola di progetto usata (W1GHZ, OE2IGL, Skobelev…). Le quote si possono modificare a mano. Per l'Axial Corrugated si modificano passo, larghezza degli scalini, gradino, diametri e profondità d1…d8 degli 8 scalini.

![Progetto feed]({IMG}/03_design.png)

## 7. Laboratorio
Qui si "gioca" con le quote.

![Laboratorio]({IMG}/04_lab.png)

**Scenario d'uso:** obiettivo **TX** (guadagno), **RX** (G/T) o **EME** (guadagno + G/T); elevazione, NF del LNA, perdita di linea, rugosità della superficie, attenuazione zenitale.

**Cursori delle quote:** a ogni modifica FeedLab ricalcola efficienza, guadagno, G/T, temperatura d'antenna, S11, taper al bordo e la variazione del **rapporto S/N**:

| Obiettivo | Variazione di S/N |
|---|---|
| TX | ΔSNR = ΔG |
| RX | ΔSNR = Δ(G/T) |
| EME | ΔSNR = ΔG + Δ(G/T) |

**Consigli** in chiaro, **sensibilità** di ogni quota e **ottimizzazione automatica** con un limite di S11.

### 7.1 Tolleranze di lavorazione e resa
![Tolleranze]({IMG}/05_tolerances.png)
1. **Parametri:** tolleranza dell'officina (±mm); distribuzione *uniforme* (prudente) o *normale con ±t = 3σ* (CNC capace); perdita ammessa e S11 massimo.
2. **🎲 Analizza tolleranze:** FeedLab simula migliaia di pezzi e dà la **resa** (pezzi buoni), la perdita media, la dispersione dell'efficienza, l'S11 peggiore e le **quote critiche** con la **tolleranza consigliata** per ciascuna.
3. **📄 Usa queste tolleranze nel disegno PDF:** aggiunge la tabella delle tolleranze al disegno.
4. **🛡️ Ottimizzazione robusta:** cerca le quote che restano buone *dentro le tolleranze* (media − k·σ). Utile sopra i 47 GHz.

## 8. Simulazione & S11
![Simulazione]({IMG}/06_simulation.png)
- **S11** in banda con il simulatore rapido a *mode matching*.
- **Modi all'apertura:** per Pickett-Potter e Skobelev anche il rapporto **TM11/TE11** (circa 15%, WA6KBL).
- **Lobo** polare e cartesiano, piani E e H, con la fase.
- **Efficienza della parabola** in funzione di f/D: spillover, illuminazione, fase e polarizzazione.
- **Centro di fase** e G/T.

Il simulatore rapido non tratta i feed con anelli o gole (VE4MA, Chaparral, corrugati): per questi FeedLab usa l'efficienza pubblicata dall'autore e consiglia openEMS.

## 9. Lobo 3D e Modello 3D
![Lobo 3D]({IMG}/07_lobe3d.png)
![Modello 3D]({IMG}/08_model3d.png)

## 10. Disegno & STEP
![Disegno e STEP]({IMG}/09_drawing.png)
- **📄 Genera PDF:** disegno meccanico A4 con sezione quotata, tabella delle quote (mm e λ), cartiglio e tolleranze generali. Con le tolleranze per quota (§7.1) include la loro tabella; con i fori di fissaggio (§11) c'è un **foglio 2** con la flangia forata.
  - Ogni quota del disegno riporta il nome del parametro della tabella (es. "Ø22.900 = Di", "9.03 = las"). Per l'Axial Corrugated le profondità d1…d8 sono disegnate in blu dentro ciascuno scalino, con w, pitch e delta; il PDF ha due fogli: mezza sezione a scala doppia e feed intero. Per VE4MA e Chaparral sono indicate ring_width, ring_depth e ring_setback.
- **🧊 Genera STEP:** file `.stp` per CNC/CAD. I fori filettati sono al diametro di preforo; il filetto è indicato nel PDF.
- **🖨️ Genera STL:** per la stampa 3D.

## 11. Piastrina WR
![Piastrina WR]({IMG}/10_plate.png)

La **piastrina λ/4** collega la guida circolare del feed alla guida rettangolare WR. L'orientamento della WR fissa la **polarizzazione verticale o orizzontale** (design guide OE2IGL, ottimizzazione HB9PZK).

1. **Dati:** guida WR, polarizzazione, Ø della guida circolare, raggio della fresa negli angoli.
2. **Risultato:** apertura a × b, spessore (con tolleranza) e Z0 intermedia.
3. **Fori di fissaggio guida → piastrina → feed**, con viti **metriche** o **in pollici**:
   - la foratura della **flangia standard** (Flann / MIL-DTL-3922) è **filettata nella piastra**;
   - **4 viti piastra → feed** con la **testa nella lamatura** sul lato guida, così la superficie verso la guida resta piana;
   - **spine di centraggio** da **47 GHz in su**;
   - flange rotonde UG-383/385/387: fori per le spine della guida e filetto 4-40;
   - se la piastra è troppo sottile, FeedLab ne ingrossa il corpo e ricava sul lato feed una **tasca** del diametro della guida circolare.
4. La stessa foratura viene applicata alla **flangia del feed**.

![Disegno della piastrina a 47 GHz](img/plate_drawing_47GHz.png)
![Flangia del feed forata, foglio 2](img/feed_flange_47GHz.png)

**Verifica sempre le misure prima di forare**, anche le teste delle viti (ISO 4762) rispetto a quelle che acquisti.

## 12. Full-wave openEMS (facoltativo)
![openEMS]({IMG}/11_openems.png)
openEMS è un simulatore FDTD gratuito. Una simulazione dura da minuti a ore e gira in background: puoi chiudere FeedLab.

| Sotto-scheda | Uso |
|---|---|
| ① **Installazione** | installazione guidata di openEMS e del collegamento con Python, con test finale |
| ② **Nuova analisi** | simulazione singola, convergenza della mesh, sweep di un parametro; stima di durata e RAM |
| ③ **Simulazioni** | avanzamento, stop, log |
| ④ **Risultati** | S11/VSWR, lobi co- e cross-polari, centro di fase, efficienza, G/T, confronto col modello rapido; report HTML, CSV e `.dat` W1GHZ |
| ⑤ **Space mapping** | correzione automatica del modello rapido con openEMS |

**Space mapping:** openEMS verifica un candidato, la differenza tra openEMS e il modello rapido corregge il modello rapido e FeedLab propone il candidato successivo, fino alla convergenza. Alla fine *✅ Applica il migliore al progetto*.

![Space mapping]({IMG}/12_spacemap.png)

## 13. Flusso di lavoro consigliato
1. **Procedura guidata:** parabola, banda, obiettivo → feed.
2. **Laboratorio:** ritocca le quote guardando ΔS/N, poi l'ottimizzazione automatica.
3. **Tolleranze:** chiedi la tolleranza alla tua officina e analizza la resa.
4. **(Facoltativo) openEMS:** verifica o space mapping (indispensabile per corrugati e feed ad anelli).
5. **Piastrina WR:** polarizzazione, fori di fissaggio, PDF e STEP.
6. **Disegno & STEP del feed** all'officina.
7. **Sul campo:** misura il rumore solare e confrontalo con il valore atteso.

## 14. Limiti noti
- **Simulatore rapido:** modella l'apertura come flangia e non tratta anelli e gole. Per questi usa openEMS.
- **Efficienze:** sono valori calcolati. Su una parabola reale aspettati 12–15 punti in meno; le *differenze* tra varianti sono attendibili.
- **Catalogo parabole:** alcune focali sono stime (indicate come tali). Misura la tua parabola.
- **Polarizzazione circolare:** il polarizzatore (septum o dielettrico) non è ancora progettato da FeedLab.

## 15. Segnalare un problema
Premi **🐞 Segnala un problema** nella barra laterale: si apre GitHub con versione, sistema e progetto già scritti. Descrivi cosa è successo, cosa ti aspettavi e come riprodurlo.

## 16. Fonti principali
![Credits]({IMG}/13_credits.png)
- **Paul W1GHZ:** W1GHZ Online Microwave Antenna Book.
- **Gerald OE2IGL:** design guide, versione migliorata dell'Axial Corrugated (foglio di calcolo v1.4); **HB9PZK**.
- **Luis CT1DMK:** concetto di base dell'Axial Corrugated.
- **Libri:** C. A. Balanis, *Antenna Theory*; P.-S. Kildal, *Foundations of Antenna Engineering*.
- **Articoli:** Al W5LUA, Jeff WA6KBL (DUBUS), Sergei RW3BP, Luis CT1DMK, Luis CT1DMK e Willi LX1DB, Ivan IZ0JNY.
- **Flange:** Flann Microwave, *Waveguide and Flange Data*; MIL-DTL-3922/67C.
- **Software:** openEMS; CadQuery / OpenCascade; Streamlit; Plotly; NumPy / SciPy.

L'elenco completo è nella finestra **ℹ️ Credits**.
