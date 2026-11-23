## FeedLab 0.4.11 BETA TEST per Windows / for Windows

**Installazione / Installation:** `FeedLab-Setup-0.4.11.exe` (senza diritti di amministratore / no admin rights) oppure / or `FeedLab-0.4.11-portable.zip` → `FeedLab.bat`. Controllo del file scaricato / check the download: `SHA256SUMS.txt`.

> 🧪 **BETA TEST:** questa versione vale **30 giorni dall'installazione**, poi si disattiva; a ogni avvio un pop-up indica i giorni rimasti. Alla scadenza scarica la versione più recente da questa pagina.
> 🧪 **BETA TEST:** this version is valid for **30 days from installation**, then it deactivates; a popup shows the days left at every start. When it expires, download the latest version from this page.

### 🇮🇹 Novità
- **Nuovo feed IZ0JNY Dual-Flare** (scalino + cono + cilindro di fasatura + secondo cono), progettato con il solutore di FeedLab per EME: antenna più fredda e G/T migliore dei dual-mode classici, solo coni e cilindri (facile al tornio). Nel wizard per f/D 0.6–0.9. Verifica openEMS a 24.048 GHz (f/D 0.65): G/T entro 0.06 dB dal modello rapido, cross-polare −27 dB, S11 < −23 dB su ±10 %.
- **Guida rettangolare scelta una volta** nella barra laterale, solo fra quelle della banda: 10 GHz WR-90 o WR-75, 24 GHz WR-42, 47 GHz WR-22 o WR-19. Dimensiona piastrina di adattamento circolare → WR, foratura e base.
- **Base del feed quadrata** con il lato della flangia della guida (WR-90 41.40, WR-75 38.30, WR-42 22.41 mm): nel modello 3D, nello STEP/STL e nel disegno PDF.
- **Disegni:** con la flangia forata spessa la parete dello scalino non entra più nella flangia; note che vanno a capo dentro il foglio.
- **openEMS:** corretto un errore che salvava i diagrammi di radiazione tutti a zero (S11 era corretto). Nuova opzione `--post` per ricalcolarli da `sim_data` in pochi secondi.
- **Installer:** usa gli interpreti Python originali firmati da python.org (niente più eseguibile modificato, causa tipica degli allarmi antivirus); non scarica più openEMS (si installa dall'app, scheda Full-wave openEMS). SmartScreen può ancora avvisare finché l'installer non è firmato: "Ulteriori informazioni → Esegui comunque".

### 🇬🇧 What's new
- **New IZ0JNY Dual-Flare feed** (step + cone + phasing cylinder + second cone), designed with the FeedLab solver for EME: colder antenna and better G/T than the classic dual-mode feeds, cones and cylinders only (easy on the lathe). In the wizard for f/D 0.6–0.9. openEMS check at 24.048 GHz (f/D 0.65): G/T within 0.06 dB of the fast model, cross-pol −27 dB, S11 < −23 dB over ±10 %.
- **Rectangular waveguide chosen once** in the sidebar, among those of the band: 10 GHz WR-90 or WR-75, 24 GHz WR-42, 47 GHz WR-22 or WR-19. It sizes the circular → WR matching plate, the drilling and the base.
- **Square feed base** with the side of the waveguide flange (WR-90 41.40, WR-75 38.30, WR-42 22.41 mm): in the 3D model, STEP/STL and PDF drawing.
- **Drawings:** with a thick drilled flange the step wall no longer enters the flange; notes wrap inside the sheet.
- **openEMS:** fixed a bug that saved the radiation patterns as all zeros (S11 was correct). New `--post` option to recompute them from `sim_data` in seconds.
- **Installer:** uses the original Python interpreters signed by python.org (no more modified executable, a typical cause of antivirus alarms); no longer downloads openEMS (install it from the app, Full-wave openEMS tab). SmartScreen may still warn until the installer is signed: "More info → Run anyway".

Requisiti / Requirements: Windows 10/11 64-bit.
