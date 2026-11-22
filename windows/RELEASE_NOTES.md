## FeedLab per Windows

**Novità 0.4.1:** nuova scheda **ℹ️ Credits** con autore (Ivan De Cesaris, IZ0JNY), versione e tutte le fonti tecniche, i progetti GitHub e i datasheet delle parabole; versione mostrata anche nella barra laterale.

**Installazione:** scarica `FeedLab-Setup-….exe` e avvialo (non servono diritti di amministratore). In alternativa lo zip *portable*: estrai e fai doppio clic su `FeedLab.bat`.

- Tutta l'app FeedLab (procedura guidata, progetto, laboratorio, simulazione rapida, lobo 3D, modello 3D, disegno PDF/STEP, piastrina WR) in una finestra propria, senza connessione internet.
- **openEMS facoltativo** per la *deep analysis* full-wave: scheda *Full-wave openEMS* → *Installazione* (procedura guidata: download, binding Python, test), oppure spunta l'opzione nell'installer.
- Le simulazioni openEMS girano in background, una dopo l'altra (singola, convergenza della mesh, sweep di un parametro); continuano anche chiudendo FeedLab. Risultati: S11/VSWR/banda, lobi co/cross-polari, centro di fase, efficienza vs f/D, guadagno, G/T, report HTML, CSV e file `.dat` W1GHZ.

Requisiti: Windows 10/11 a 64 bit. La finestra usa Microsoft Edge WebView2 (già presente in Windows 11); se manca, FeedLab si apre nel browser.
