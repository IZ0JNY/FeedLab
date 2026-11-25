## FeedLab 0.4.25 BETA TEST per Windows / for Windows

**Installazione / Installation:** `FeedLab-Setup-0.4.25.exe` (senza diritti di amministratore / no admin rights) oppure / or `FeedLab-0.4.25-portable.zip` → `FeedLab.bat`. Controllo del file scaricato / check the download: `SHA256SUMS.txt`.

### 🇮🇹 Novità
- **openEMS a 10 GHz corretto:** nella simulazione full-wave la guida d'ingresso del feed aveva una parete fissa di 0.5 mm, più sottile della griglia a 10 GHz (celle di 1.3 mm). La guida risultava aperta e i risultati erano sbagliati (S11 circa −2.6 dB, efficienza 35 %). Ora la parete è spessa almeno due celle e ha le sue linee di griglia. Dual-Flare (IZ0JNY) a 10368.2 MHz sulla Channel Master 243: 47.1 dBi, efficienza 76 %, S11 sotto −18 dB, in accordo con il simulatore veloce. La correzione vale per tutti i feed e tutte le bande.
- **Inglese:** tradotte due note rimaste in italiano nella scelta del feed; «—» al posto di «None» nella tabella dei feed.

### 🇬🇧 What's new
- **openEMS at 10 GHz fixed:** in the full-wave simulation the feed's input guide had a fixed 0.5 mm wall, thinner than the 10 GHz mesh (1.3 mm cells). The guide was open and the results were wrong (S11 about −2.6 dB, 35 % efficiency). Now the wall is at least two cells thick and has its own mesh lines. Dual-Flare (IZ0JNY) at 10368.2 MHz on the Channel Master 243: 47.1 dBi, 76 % efficiency, S11 below −18 dB, in agreement with the fast simulator. The fix applies to every feed and band.
- **English:** two notes left in Italian in the feed choice are now translated; «—» instead of «None» in the feed table.

Requisiti / Requirements: Windows 10/11 64-bit.

---

## FeedLab 0.4.24 BETA TEST per Windows / for Windows

**Installazione / Installation:** `FeedLab-Setup-0.4.24.exe` (senza diritti di amministratore / no admin rights) oppure / or `FeedLab-0.4.24-portable.zip` → `FeedLab.bat`. Controllo del file scaricato / check the download: `SHA256SUMS.txt`.

### 🇮🇹 Novità
- **Dual-Flare (IZ0JNY) compatto:** stesso nome, quote riottimizzate per f/D da 0.6 a 0.9 con una ricerca globale. Il G/T resta uguale (entro 0.01 dB), il guadagno sale di 0.02 dB e il feed è dal 2 al 18 % più corto. L'S11 resta sotto −25 dB su ±1 % di banda. Verificato con openEMS sulla Channel Master 243 da 2.4 m: a 24048.2 MHz 53.86 dBi, efficienza 66.5 %, S11 −24.9 dB; a 47088.2 MHz 57.63 dBi, S11 −21.6 dB.
- **File di progetto (.json):** salva i dati inseriti e i risultati calcolati (guadagno, G/T, efficienze, taper, S11, lobi, Tsys, piastrina, openEMS). Si scambia e si riapre in FeedLab con «📂 Apri progetto».
- **Nuova scheda «📦 Output di progetto»:** scegli che cosa generare. Ci sono i PDF del report completo, delle simulazioni veloci, del feed con disegni e simulazioni, della parabola, della piastrina, del feed con la piastrina, della tabella di tutte le quote e i dati (anche in CSV) e delle simulazioni openEMS. Puoi scaricare anche il file di progetto, i modelli STEP/STL e uno ZIP con tutto.
- **Piastrina:** nuova icona 🔲 al posto della spina elettrica.
- **Catalogo parabole:** materiali e note solo in italiano e in inglese («vetroresina» → fibreglass…).
- **EMELab** diventa un programma a sé (misure, pianificazione e log EME): legge il file di progetto di FeedLab e non è più incluso in FeedLab.
- **Manuale** aggiornato con il capitolo «Output di progetto» e le schermate nuove.

### 🇬🇧 What's new
- **Compact Dual-Flare (IZ0JNY):** same name, dimensions re-optimised for f/D from 0.6 to 0.9 with a global search. G/T stays the same (within 0.01 dB), gain rises by 0.02 dB and the feed is 2 to 18 % shorter. S11 stays below −25 dB over ±1 % bandwidth. Checked with openEMS on the 2.4 m Channel Master 243: at 24048.2 MHz 53.86 dBi, 66.5 % efficiency, S11 −24.9 dB; at 47088.2 MHz 57.63 dBi, S11 −21.6 dB.
- **Project file (.json):** saves the data you entered and the computed results (gain, G/T, efficiencies, taper, S11, patterns, Tsys, plate, openEMS). You can share it and reopen it in FeedLab with «📂 Open project».
- **New «📦 Project outputs» tab:** choose what to generate. There are PDFs of the full report, the fast simulations, the feed with drawings and simulations, the dish, the plate, the feed with the plate, the table of all dimensions and data (also as CSV) and the openEMS simulations. You can also download the project file, the STEP/STL models and a ZIP with everything.
- **Plate:** new 🔲 icon instead of the electric plug.
- **Dish catalogue:** materials and notes only in Italian and English («vetroresina» → fibreglass…).
- **EMELab** becomes a program of its own (EME measurements, planning and log): it reads FeedLab's project file and is no longer included in FeedLab.
- **Manual** updated with the «Project outputs» chapter and new screenshots.

Requisiti / Requirements: Windows 10/11 64-bit.

---

## FeedLab 0.4.23 BETA TEST per Windows / for Windows

**Installazione / Installation:** `FeedLab-Setup-0.4.23.exe` (senza diritti di amministratore / no admin rights) oppure / or `FeedLab-0.4.23-portable.zip` → `FeedLab.bat`. Controllo del file scaricato / check the download: `SHA256SUMS.txt`.

### 🇮🇹 Novità
- **Materiali dei servizi CNC online** JLCCNC, PCBWay e Weerg: alluminio 6061, 6082, 7075, 5083, 5052, 2011, 2024, ottone H59, H62, C360, OT58, rame T2, C101, C110, bronzo, inox 316L e titanio, con conducibilità e rugosità della finitura di serie.
- **ℹ️ Informazioni sui materiali:** nuovo pulsante sopra la scelta del materiale. Apre una tabella che aiuta a scegliere: conducibilità, rugosità, peso, perdite rispetto al rame e voti a pallini colorati per lavorabilità, prezzo, reperibilità, resistenza agli agenti atmosferici e trattamenti, con pro e contro.
- **Laboratorio:** cursore del taper al bordo collegato a quello della Procedura guidata (muovendo uno si muove l'altro); le simulazioni si aggiornano subito.
- **Base del feed:** solo «Circolare» o «Quadrata»; quadrata di default a 10 e 24 GHz, circolare da 47 GHz in su.
- **Validazione con openEMS:** ogni tanto, mentre modifichi il progetto, un avviso ti invita a verificarlo con una simulazione openEMS, più precisa del simulatore veloce.
- **Lingue coerenti:** in italiano solo italiano e in inglese solo inglese; le quote del feed hanno il loro nome nella lingua scelta.
- **Montaggio:** schema rinominato «Piastrina avvitata alla base del feed con viti in lamatura (guida avvitata alla piastrina)»; la didascalia non copre più il disegno.
- **Viste 3D** senza le righe scure «a stella» intorno ai fori.
- **Manuale** completamente rifatto, molto più dettagliato, in italiano e inglese.

### 🇬🇧 What's new
- **Materials of the online CNC services** JLCCNC, PCBWay and Weerg: aluminium 6061, 6082, 7075, 5083, 5052, 2011, 2024, brass H59, H62, C360, OT58, copper T2, C101, C110, bronze, 316L stainless steel and titanium, with conductivity and roughness of their standard finish.
- **ℹ️ About materials:** new button above the material choice. It opens a table that helps you choose: conductivity, roughness, weight, losses relative to copper and coloured-dot ratings for machinability, price, availability, weather resistance and treatments, with pros and cons.
- **Laboratory:** edge taper slider linked to the one in the Guided procedure (moving one moves the other); the simulations update at once.
- **Feed base:** just «Circular» or «Square»; square by default at 10 and 24 GHz, circular from 47 GHz up.
- **Validation with openEMS:** now and then, while you change the design, a notice invites you to check it with an openEMS simulation, more accurate than the fast simulator.
- **Consistent languages:** only Italian in Italian and only English in English; the feed dimensions have their own name in the chosen language.
- **Mounting:** scheme renamed «Plate screwed to the feed base with counterbored screws (waveguide screwed into the plate)»; the caption no longer covers the drawing.
- **3D views** without the dark «star» lines around the holes.
- **Manual** completely rewritten, much more detailed, in Italian and English.

Requisiti / Requirements: Windows 10/11 64-bit.
