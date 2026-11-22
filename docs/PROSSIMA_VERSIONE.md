# Modifiche per la prossima versione (0.4.7)

| # | Richiesta | Stato |
|---|---|---|
| 1 | Un manuale per ogni lingua dell'installazione (IT, EN, DE, FR, ES), con gli screenshot dell'app in quella lingua | da fare |
| 2 | Scelta delle viti piastrina → feed: M3/M4 a 10 GHz, M2.5/M3/M2 sopra; lunghezza = 3 × spessore piastrina arrotondata alla misura commerciale; equivalenti UNC | ✅ fatto su `main` |

## 2. Viti piastrina → feed
**Richiesta (IZ0JNY):** scegliere le viti più comuni per fissare la piastrina al feed: M3 o M4 per i 10 GHz, M3, M2.5 o M2 per le frequenze superiori. Lunghezza delle viti (e quindi dei fori filettati nel feed) = spessore della piastrina × 3, arrotondato alle lunghezze commerciali 10, 12, 14, 16, 18, 20, 25 mm. Conversione per le viti UNC.

**Fatto:**
- Scheda *Piastrina WR*: menu "Viti piastrina → feed" con le misure della banda (sotto 15 GHz: M3, M4; sopra: M2.5, M3, M2; la prima è quella proposta).
- **Lunghezza:** 3 × spessore del corpo della piastrina, arrotondato alla lunghezza commerciale più vicina (a parità sceglie la più lunga; sotto 10 → 10 mm, sopra 25 → 25 mm).
- **Foro nel feed (IZ0JNY):** la vite entra nel feed per lunghezza vite − (spessore piastrina − lamatura); il foro cieco è profondo quanto la vite + 5 mm di margine, arrotondato per eccesso a un intero pari (per esempio 10.8 + 5 = 15.8 → 16 mm). Il filetto arriva a 3 passi (min. 1 mm) dal fondo per l'imbocco del maschio. La flangia del feed si ispessisce di conseguenza.
- **Pollici (UNC), misura più vicina:** M2 → #2-56, M2.5 → #3-48 (meno diffusa del 4-40), M3 → #4-40, M4 → #8-32. Lunghezze ASME B18.3: 3/8", 1/2", 5/8", 3/4", 7/8", 1". Lamature per teste cilindriche ISO 4762 / ASME B18.3.
- Vite e lunghezza compaiono nella foratura del PDF della piastrina, nei fori del feed (PDF e STEP) e nella scheda.
- **Nota:** a 10 GHz la piastrina è spessa circa 8.9 mm: vite da 25 mm, foro di 26 mm nel feed e flangia del feed di circa 27 mm.
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
| + | Riferimento Pawlan WA6KBL (controllo TM11) | ✅ fatto |

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
