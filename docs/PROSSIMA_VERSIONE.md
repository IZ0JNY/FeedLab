# Modifiche per la prossima versione (0.4.3)

Raccolta delle richieste. Quando ce ne sono 3 si implementano tutte insieme, si provano e si pubblica il nuovo installer Windows.

| # | Richiesta | Stato |
|---|---|---|
| 1 | Balanis nelle equazioni di calcolo e nella bibliografia | da fare |
| 2 | — | — |
| 3 | — | — |

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

**Nota sul PDF:** il link archive.org dato all'inizio è una copia del libro non autorizzata dall'editore, quindi non la scarico né la uso come fonte. Le equazioni del libro sono formule standard della teoria delle antenne e si possono implementare e citare senza il PDF. Se hai il libro, per controllare numero per numero bastano le pagine delle sezioni interessate.
