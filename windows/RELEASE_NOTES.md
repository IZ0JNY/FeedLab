## FeedLab 0.4.3 per Windows / for Windows

**Installazione / Installation:** `FeedLab-Setup-0.4.3.exe` (senza diritti di amministratore / no admin rights) oppure / or `FeedLab-0.4.3-portable.zip` → `FeedLab.bat`.

### 🇮🇹 Novità
- **Tolleranze di lavorazione** (Laboratorio): Monte Carlo della resa produttiva, quote critiche con la tolleranza necessaria per ciascuna (anche in tabella nel PDF) e **ottimizzazione robusta** (media − k·σ invece del picco nominale). Simulatore rapido più veloce del 40%.
- **Space mapping con openEMS** (scheda openEMS ⑤): openEMS verifica pochi candidati e corregge il modello rapido fino alla convergenza; può avanzare da solo.
- **Fori di fissaggio** (Piastrina WR), viti metriche o in pollici: foratura della flangia standard (Flann / MIL-DTL-3922) filettata nella piastra, 4 viti piastra→feed con testa in lamatura, spine di centraggio da 47 GHz, tasca lato feed quando la piastra λ/4 è troppo sottile. Nel PDF (foglio 2 del feed) e nello STEP di piastra e feed. Schema di IZ0JNY (feed W2IMU 24 GHz).
- **Pulsante 🐞 Segnala un problema**: apre le issue GitHub con versione e progetto già compilati.
- **Balanis** nelle verifiche: formule chiuse di horn e riflettori. Corretto il guadagno degli horn piramidali (era sottostimato di 0.15–0.5 dB).
- **W5LUA 24 GHz EME**: perdita di percorso EME, rumore di Sole e Luna, atmosfera (verificati sui calcolatori VK3UM). **Pawlan WA6KBL**: controllo TM11 ≈ 15% del Pickett-Potter.
- Catalogo: Kathrein CAS 60/180, Fuba DAA 650/780/850/110, DAL 800. Pulsante Credits nella barra laterale.

### 🇬🇧 What's new
- **Fabrication tolerances** (Laboratory): Monte Carlo production yield, critical dimensions with the tolerance each one needs (also as a table in the PDF), and **robust optimisation** (mean − k·σ instead of the nominal peak). Fast solver 40% faster.
- **openEMS space mapping** (openEMS tab ⑤): openEMS checks a few candidates and corrects the fast model until convergence; it can advance automatically.
- **Fixing holes** (WR plate tab), metric or inch screws: standard flange pattern (Flann / MIL-DTL-3922) tapped in the plate, 4 counterbored plate→feed screws, alignment pins from 47 GHz, feed-side pocket when the λ/4 plate is too thin. In the PDF (feed sheet 2) and in the STEP of plate and feed. Scheme by IZ0JNY (24 GHz W2IMU feed).
- **🐞 Report a problem** button: opens GitHub issues with version and design pre-filled.
- **Balanis** closed-form checks for horns and reflectors. Fixed pyramidal horn gain (was 0.15–0.5 dB low).
- **W5LUA 24 GHz EME**: EME path loss, sun and moon noise, atmosphere (checked against VK3UM calculators). **Pawlan WA6KBL**: Pickett-Potter TM11 ≈ 15% check.
- Catalogue: Kathrein CAS 60/180, Fuba DAA 650/780/850/110, DAL 800. Credits button in the sidebar.

Requisiti / Requirements: Windows 10/11 64-bit.
