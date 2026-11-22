# Modifiche per la prossima versione (0.4.9)

**Regola:** ogni 5 modifiche si fa una nuova build e la si pubblica su GitHub.

| # | Richiesta | Stato |
|---|---|---|
| 1 | Pop-up BETA: il pulsante OK non funzionava; tolto, al suo posto il testo centrato "Chiudere questa finestra per continuare (✕ in alto a destra)"; si chiude con la ✕ | ✅ fatto (ramo `v0.4.9`) |
| 2 | Tolta dalla barra laterale l'opzione "Collare Ø40 mm per portaLNB commerciale" | ✅ fatto (ramo `v0.4.9`) |

---

# Archivio: versione 0.4.8 (pubblicata, BETA TEST 30 giorni)

| # | Richiesta | Stato |
|---|---|---|
| 1 | Manuale per ogni lingua dell'installazione, con screenshot in quella lingua | ✅ fatto: manuali IT e EN, schermate in `docs/manual/img/<lingua>/` |
| 2 | Nuove lingue russo e portoghese | ❌ annullato: su richiesta il software è stato semplificato a **solo italiano e inglese** (tolti anche tedesco, francese e spagnolo, con i loro manuali) |
| 3 | Feed di Zdeněk OK1DFC (septum) | ❌ annullato su richiesta: è un feed per 1296 MHz, fuori dal campo di FeedLab (da 10 GHz); OK1DFC resta in bibliografia |
| 4 | Versione **BETA TEST** a scadenza: 30 giorni dall'installazione, pop-up a ogni avvio | ✅ fatto |
| 5 | **Axial Corrugated (base concept Luis CT1DMK, improved version Gerald OE2IGL)**, con le quote del foglio di calcolo v1.4 di Gerald OE2IGL, tra i tipi di feed e nella procedura guidata | ✅ fatto |
| + | Feed di Mirek OK2AQ (horn conico f/D 0.6 e corrugato f/D 0.8, 24 GHz) | ❌ tolti su richiesta |

## 1-2. Lingue e manuali
- Il software è stato semplificato: interfaccia, installer e manuali solo in **italiano e inglese**. Il catalogo delle traduzioni (`feedlab/i18n_catalog.py`) contiene coppie (it, en); con una lingua di sistema diversa dall'italiano FeedLab parte in inglese.
- Sorgenti dei manuali: `docs/manual/manuale_it.md`, `docs/manual/user_manual_en.md`; `{IMG}` diventa `img/<lingua>`.
- Schermate: `python docs/manual/tools/make_screens.py [lingue]`; PDF: `python docs/manual/build_manual.py`. L'installer include solo i PDF.

## 4. BETA TEST a scadenza
- **Modulo `feedlab/beta.py`:** al primo avvio di ogni versione salva la data nella cartella impostazioni di FeedLab (`beta.json`). Ogni nuova versione ha i suoi 30 giorni.
- **A ogni avvio:** pop-up "🧪 BETA TEST" con i giorni rimasti e la data di scadenza, che si chiude con OK o ✕. In barra laterale resta "Versione x.y.z BETA TEST".
- **Alla scadenza:** pagina di blocco con il link all'ultima versione su GitHub. Anche un orologio spostato indietro di oltre un giorno conta come scadenza.
- **Limite:** FeedLab è open source, quindi è un avviso per i tester, non una protezione. `BETA = False` produce una versione normale.
- **Test:** `tests/test_beta.py`.

## 5. Axial Corrugated (base concept Luis CT1DMK, improved version Gerald OE2IGL)
- **Corrugato assiale v1.4:** quote dai polinomi del foglio di calcolo in funzione dell'angolo di apertura (verificato a 47.088 GHz / 137°); 10–76 GHz; efficienza dell'autore 81–86% usata dalla procedura guidata, dove risulta di solito primo. Sezione, 3D, PDF e STEP; quote modificabili (passo, gole, gradino, d1…d8).
- La scheda "Feed pubblicati" è stata tolta su richiesta: i feed stanno nell'elenco dei tipi di feed insieme agli altri.
- Test: `tests/test_published_feeds.py`.

---

# Archivio: versione 0.4.7 (pubblicata)

| # | Richiesta | Stato |
|---|---|---|
| 1 | Un manuale per ogni lingua dell'installazione (IT, EN, DE, FR, ES), con gli screenshot dell'app in quella lingua | da fare |
| 3 | Riferimenti Sergei RW3BP (77 GHz), Luis CT1DMK (radioastronomia), Luis CT1DMK e Willi LX1DB (feed CP) nei calcoli e in bibliografia; nominativi nei riferimenti | ✅ fatto su `main` |
| 2 | Scelta delle viti piastrina → feed: M3/M4 a 10 GHz, M2.5/M3/M2 sopra; lunghezza = 2 × spessore piastrina arrotondata alla misura commerciale; equivalenti UNC | ✅ fatto su `main` |

## 2. Viti piastrina → feed
**Richiesta (IZ0JNY):** scegliere le viti più comuni per fissare la piastrina al feed: M3 o M4 per i 10 GHz, M3, M2.5 o M2 per le frequenze superiori. Lunghezza delle viti (e quindi dei fori filettati nel feed) = spessore della piastrina × 2 (prima × 3), arrotondato alle lunghezze commerciali 10, 12, 14, 16, 18, 20, 25 mm. Conversione per le viti UNC.

**Fatto:**
- Scheda *Piastrina WR*: menu "Viti piastrina → feed" con le misure della banda (sotto 15 GHz: M3, M4; sopra: M2.5, M3, M2; la prima è quella proposta).
- **Lunghezza:** 2 × spessore del corpo della piastrina, arrotondato alla lunghezza commerciale più vicina (a parità sceglie la più lunga; sotto 10 → 10 mm, sopra 25 → 25 mm).
- **Foro nel feed (IZ0JNY):** la vite entra nel feed per lunghezza vite − (spessore piastrina − lamatura). Il foro cieco è arrotondato per eccesso a un intero pari, senza margine aggiuntivo, ma abbastanza profondo da avere filetto fino alla punta della vite: il filetto si ferma 3 passi (min. 1 mm) prima del fondo.
- **Pollici (UNC), misura più vicina:** M2 → #2-56, M2.5 → #3-48 (meno diffusa del 4-40), M3 → #4-40, M4 → #8-32. Lunghezze ASME B18.3: 3/8", 1/2", 5/8", 3/4", 7/8", 1". Lamature per teste cilindriche ISO 4762 / ASME B18.3.
- Vite e lunghezza compaiono nella foratura del PDF della piastrina, nei fori del feed (PDF e STEP) e nella scheda.
- **Esempio a 10 GHz:** piastrina 8.85 mm → vite M3 × 18, foro di 14 mm nel feed.
- Test: `tests/test_flanges.py::test_plate_screw_choices_and_length`.

---

# Archivio: versione 0.4.6 (pubblicata)

| # | Richiesta | Stato |
|---|---|---|
| 1 | Gradino senza spessore (Pickett-Potter, Skobelev): la corona tra guida d'ingresso e flare aveva spessore assiale zero nel 2D, nel 3D, nello STEP e nel PDF | ✅ fatto su `main` |
| 2 | Quote nei disegni: spessore del gradino, spessore parete e semiangolo del flare (PDF e sezione nell'app) | ✅ fatto su `main` |
| 3 | Laboratorio: variare il semiangolo del flare (Pickett-Potter, Skobelev) e vedere cosa cambia | ✅ fatto su `main` |
| 4 | Manuali in 5 lingue | spostato alla 0.4.7 |

## 1. Spessore della parete
La parete esterna era il profilo interno spostato solo in direzione radiale: dove il profilo è orizzontale (gradino) la corona aveva spessore zero e nei tratti conici la parete era più sottile del valore impostato. Ora lo spessore è costante e misurato perpendicolarmente alla parete, con spigoli vivi agli angoli; i bordi d'apertura e la flangia restano piani. Test: `tests/test_wall_thickness.py`.

## 3. Semiangolo del flare nel Laboratorio
Per Pickett-Potter e Skobelev il flare si regola con il semiangolo α (Ø apertura fisso, la lunghezza del flare segue). Il semiangolo compare anche tra le quote modificabili; se si modificano sia angolo sia lunghezza vale l'ultimo valore inserito.

## 4. Manuali in 5 lingue con screenshot
**Piano:**
- Manuale (Markdown → PDF con `docs/manual/build_manual.py`) per italiano, inglese, tedesco, francese e spagnolo, ciascuno con gli screenshot dell'app nella stessa lingua.
- Screenshot generati in automatico in CI su Windows (Playwright + Edge): per ogni lingua si apre l'app, si sceglie la lingua e si fotografano le schede principali, così le immagini restano aggiornate a ogni versione.
- Il pulsante 📖 Manuale apre il manuale della lingua scelta; l'installer installa tutti i manuali.

---

# Archivio: versione 0.4.3

Raccolta delle richieste. Si sviluppano sul ramo `v0.4.3`. Quando ce ne sono **5** si provano tutte insieme e si pubblica il nuovo installer Windows.

| # | Richiesta | Stato |
|---|---|---|
| 1 | Balanis nelle equazioni di calcolo e nella bibliografia | ✅ fatto (ramo `v0.4.3`) |
| 2 | Analisi di tolleranza Monte Carlo, quote critiche, ottimizzazione robusta | ✅ fatto (ramo `v0.4.3`) |
| 3 | Validazione openEMS in the loop (space mapping) | ✅ fatto (ramo `v0.4.3`), da provare con openEMS vero |
| 4 | Fori, filettature, lamature e spine piastra–feed (metrico/pollici) | ✅ fatto |
| 5 | Pulsante per segnalare problemi su GitHub | ✅ fatto |
| + | Riferimento Jeff WA6KBL (controllo TM11) | ✅ fatto |

**Pubblicata come 0.4.3.**

## 1. Balanis, *Antenna Theory: Analysis and Design*
**Richiesta:** aggiungere il libro di C. A. Balanis alle equazioni di calcolo e alla bibliografia (Credits, README, base di conoscenza).

**Piano:**
- **Bibliografia:** C. A. Balanis, *Antenna Theory: Analysis and Design*, Wiley (4ª ed. 2016), da citare nei Credits (tradotto nelle 5 lingue), nel README e nella base di conoscenza.
- **Equazioni da aggiungere come verifiche indipendenti**, con un test ciascuna:
  - **Horn conico:** guadagno e perdita di fase per errore quadratico d'apertura; verifica del `conical_optimum` esistente.
  - **Horn piramidale e settoriali:** direttività con integrali di Fresnel; verifica di `pyramidal_gain_dbi` (approssimazione G3RPE/W1GHZ).
  - **Riflettore con feed cos^n:** efficienza d'apertura in forma chiusa (spillover × taper); confronto con l'integrazione numerica di FeedLab, che già coincide con il calcolo analitico entro 0.3%.
  - **Relazioni di base:** Friis, perdita di disadattamento di polarizzazione (lineare↔circolare, 3 dB), direttività/guadagno/efficienza, VSWR ↔ return loss ↔ S11.
- **Riferimenti nel codice:** ogni funzione cita "Balanis, cap. X". Il capitolo si indica solo dove è certo; il numero di equazione non si inventa.

**Fatto:** `feedlab/balanis.py` e `tests/test_balanis.py`.
- Il riflettore con feed cos^n coincide con il motore di FeedLab entro 0.0002.
- L'horn piramidale (Fresnel) coincide con l'integrale 2D dell'apertura entro 0.01 dB.
- Il confronto ha scoperto un errore: `horns.pyramidal_gain_dbi` sottostimava di 0.15–0.5 dB; ora usa la formula di Balanis.

**Nota sul PDF:** il link archive.org dato all'inizio è una copia del libro non autorizzata dall'editore, quindi non la scarico né la uso come fonte. Le equazioni del libro sono formule standard della teoria delle antenne e si possono implementare e citare senza il PDF. Se hai il libro, per controllare numero per numero bastano le pagine delle sezioni interessate.

## 2. Tolleranze di lavorazione e progetto robusto
**Origine:** commento di un utente: un buon progetto non vale nulla se le tolleranze di lavorazione non sono raggiungibili.

**Cosa fa:**
- **Monte Carlo** di tutte le quote lavorate, distribuite uniformemente in ±t oppure normali con ±t = 3σ. Le migliaia di campioni si calcolano su un modello quadratico ricavato da 1 + 2N + N(N−1)/2 run del solver rapido e verificato con alcuni run diretti.
- **Resa:** percentuale di pezzi entro la perdita ammessa e con S11 sotto il limite.
- **Quote critiche:** quota di varianza di ciascuna dimensione e tolleranza necessaria, arrotondata alle classi d'officina.
- **Ottimizzazione robusta:** massimizza media − k·σ invece del picco nominale.
- **Disegno PDF:** tabella delle tolleranze per quota.

**Accelerazione del solver:** i punti di quadratura in cache portano una valutazione da 0.75 a 0.46 s.

## 3. Space mapping con openEMS
- Il modello rapido esplora; openEMS valida 3–5 candidati.
- La differenza tra openEMS e il modello rapido (correzione costante, poi lineare nelle quote) corregge il modello rapido, che viene riottimizzato.
- Il ciclo si ripete fino alla convergenza.
- Tutto parte dalla scheda Full-wave openEMS, con il report dei passi.
