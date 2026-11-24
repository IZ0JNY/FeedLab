### Guida alle misure EME fondamentali

Ogni misura va registrata **in UTC** (sincronizza il PC con NTP o GPS), con la **configurazione** usata e il **meteo** dello stesso momento. Usa sempre le stesse impostazioni del ricevitore (banda, tempo di integrazione, AGC spento) e fai **3 letture**, poi la media.

#### 1. Rumore solare (Y sole / cielo freddo) — la misura principale
- **Cosa misura:** il G/T reale della stazione. EMELab lo confronta con quello atteso dal tuo feed e dalla tua parabola.
- **Come:** punta il Sole e cerca il massimo in AZ ed EL. Annota la **correzione che hai dovuto dare** (correzione AZ/EL al picco). Poi spostati in AZ alla stessa elevazione di **almeno 5 fasci** (circa 4° a 10 GHz, 2° a 24 GHz, 1° a 47 GHz) sul cielo freddo. Y = potenza sul Sole / potenza sul cielo.
- **Serve anche:** il flusso solare del giorno a **15.4 GHz** (osservatori RSTN: San Vito, Learmonth, Sagamore Hill, Palehua, pubblicato da NOAA SWPC). Inseriscilo in EMELab: il Sole cambia anche del 10–20 % da un giorno all'altro.
- **Ripeti** a elevazioni diverse (mattino, mezzogiorno, pomeriggio) e in giorni secchi e umidi: EMELab separa l'effetto dell'atmosfera da quello della stazione.

#### 2. Rumore lunare (Y luna / cielo freddo)
- Molto più debole del Sole (a 24 GHz con 2.4 m circa 2–3 dB): verifica sensibilità e puntamento proprio sul bersaglio EME.
- Stessa procedura del Sole; annota la fase lunare (EMELab la calcola): la Luna è più calda dopo la Luna piena.

#### 3. Cielo freddo e terra (Y terra / cielo)
- Punta l'orizzonte libero o la terra davanti alla parabola: misura il contributo di **spillover** e controlla il preamplificatore. Se nel tempo il valore cala, c'è qualcosa che peggiora (connettori, acqua, LNA).
- **Carico caldo / cielo freddo** (assorbitore a temperatura ambiente davanti al feed): Tsys = (T_caldo − Y·T_cielo)/(Y − 1). È la misura più diretta del rumore del sistema.

#### 4. Larghezza del fascio dal transito del Sole
- Ferma l'antenna un poco avanti al Sole e registra la potenza nel tempo mentre il Sole attraversa il fascio.
- Fascio misurato = tempo tra i due punti a −3 dB (minuti) × 0.25°/min × cos(declinazione del Sole). Per togliere la dimensione del Sole: fascio² ≈ misurato² − 0.35 × diametro del Sole².
- Inserisci il valore nella configurazione («Larghezza del fascio misurata»): un fascio più largo del previsto indica parabola fuori fuoco o superficie deformata.

#### 5. Messa a fuoco del feed
- Sposta il feed lungo l'asse a passi di λ/4 (circa 7 mm a 10 GHz, 3 mm a 24 GHz, 1.6 mm a 47 GHz) per ±1 λ e misura Y sole a ogni passo (tipo «Messa a fuoco», valore = spostamento in mm).
- Il massimo è il fuoco: confrontalo con il centro di fase calcolato da FeedLab. Poi ripeti spostando il feed di lato.

#### 6. Calibrazione del puntamento
- Le correzioni al picco su Sole e Luna, a molte posizioni AZ/EL, permettono a EMELab di calcolare **zero di AZ e EL, inclinazione dell'asse e cedimento per gravità**. A 47 GHz un errore di 0.05° costa già più di 1 dB in ricezione e il doppio sulle eco.

#### 7. Eco proprie
- SNR delle eco (es. modo Echo di WSJT-X) con la potenza reale al feed (misurala con wattmetro e accoppiatore direzionale).
- Confronta con l'atteso: la differenza stabile è la **riflettività efficace della Luna con il tuo fascio**. A 24 e 47 GHz su 2.4 m il fascio è più stretto della Luna e l'eco è più debole della formula classica.
- Annota Doppler e allargamento: EMELab li calcola per ogni misura.

#### 8. Ambiente da annotare sempre
- Temperatura, umidità e pressione (vapore acqueo: a 24 GHz è il fattore principale), pioggia, nuvole, **acqua o rugiada su parabola e feed**, vento (vibrazioni e deformazioni), stabilità dell'oscillatore locale (a 24/47 GHz serve un riferimento GPS).

#### Cosa ti dice EMELab
- G/T misurato contro atteso e dove perdi (elevazione, umidità, fuoco, puntamento, perdite).
- Modello di puntamento con le correzioni da dare al programma di inseguimento.
- Finestre migliori (elevazione, distanza della Luna, perigeo, Sole lontano, umidità prevista) e mesi più favorevoli.

*Riferimenti: Paul Wade W1GHZ, «Online Microwave Antenna Book» (misure di rumore solare); ITU-R P.676 (attenuazione dei gas), P.618 (temperatura di rumore), P.834 (rifrazione), P.840 (nubi); Krotikov e Troitskii, Linsky 1973 (temperatura della Luna); J.W.M. Baars, «The Paraboloidal Reflector Antenna in Radio Astronomy and Communication» (misura del fascio e del fuoco); NOAA SWPC, flusso solare RSTN.*
