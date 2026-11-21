# Appunti W1GHZ — parte 2 (articoli conferenze sui feed)

## Large W2IMU per 47/78/122 GHz (MUD 2023, W1GHZ+W1FKF) e G/T su offset (MUD 2024)
- Diametro horn B qualsiasi tra 1.22λ e ~1.9λ funziona (sotto: TM11 sotto cutoff; sopra 1.9λ altri modi → risultati scarsi). Classico 1.31λ (f/D .5–.6), grande 1.86λ (f/D .7–.8).
- Flare calcolato ~25° (semiangolo) per 1.7–1.9λ; simulato ottimo ~28°; 30° (punta da centri 60° inclusi) costa solo ~1% se si riaggiusta la lunghezza C.
- Guida d'ingresso 0.7–0.81λ: quasi nessuna differenza.
- Bordo spesso all'apertura degrada → smussare l'esterno a 45° fino a bordo sottile.
- Tabella (flare 30°, ingresso 0.7–0.81λ): f [GHz] | utensile | D [in] (λ) | C [in] (λ) | gain dBi | BW−10 semi-angolo
  10.368 | — | 2.00 (1.78) | 4.215 (3.7) | 13.9 | 35°
  24.192 | #9 | 0.875 (1.79) | 1.806 (3.7) | 13.9 | 35°
  47.088 | #5 | 0.4375 (1.74) | 0.928 (3.7) | 13.9 | 35°
  76/78 | #3 | 0.250 (1.65) | 0.439 (2.9) | 13.1 | 39°
  122 | #2 | 0.1875 (1.94) | 0.415 (4.3) | 14.6 | 32°
  122 | 4 mm | 0.157 (1.63) | 0.281 (2.9) | 13.1 | 39°
  241 | 2 mm | 0.079 (1.66) | 0.142 (2.9) | 13.1 | 39°
  HDL_ANT riferimento: flare 25°, D 1.78λ, C 3.5λ; small IMU: 30°, 1.31λ, 1.37λ.
- Lavorazione: tornio, punte da centro lunghe (60°), alta velocità avanzamento leggero; giunti alluminio a interferenza termica (25.5 ppm/°C).
- Cassegrain con Edmund dish (f/D 0.25, 12/18/24") + large W2IMU: 122 GHz e 78 GHz (W1FKF, 12"), 47 GHz (VE2UG 24"); subriflettore uguale a tutte le frequenze se > ~10λ; supporti stampati 3D; subriflettori anche stampati 3D + foglio metallico.
- G/T su offset f/D ~0.6 (1.0 m e 1.2 m), sun noise con RTL-SDR + TotalPower (I0NAA), DU3T LNA, transizione WA6KBL circolare(20.6 mm)→WR-90 RL ≥20 dB:
  1.2 m: 1.34λ 8.7 dB, 1.62λ 10.1, 1.75λ 10.1, 1.88λ 10.9 → 11.0 dB spostato 10 mm verso dish (+2.3 dB vs piccolo)
  1.0 m: 1.34λ 7.3, 1.62λ 8.4, 1.75λ 8.6, 1.88λ 8.9 dB.
  Picco di posizione molto largo sugli offset; PC ≈ apertura per tutti.
  → per G/T preferire horn più grande (più taper, meno spillover).

## Optimized dual-mode (Skobelev 2001, W1GHZ 2006, HFSS)
- Struttura: gradino d'ingresso 1.016λ → 1.3λ (genera TM11) seguito subito dal flare conico fino all'apertura; lunghezza flare scelta per la fase dei due modi. Ingresso 1.016λ (> guida monomodo ~0.7λ) → serve transizione adattata (flare dolce, gradini, o gradino rettangolare).
- Stima lineare: L_flare[λ] = 3.45·r_ap[λ] − 0.35.
- Tabella BEST (diam λ, lunghezza flare λ, f/D best, eff., PC λ (−=dentro), F/B dB, SLL dB, gain dBi, BW10 gradi totali?):
  1.5 2.01 .59 77.9% +.03 31.5 −27 11.5 94
  1.6 2.17 .65 77.1% +.13 35.8 −20 12.1 87
  1.7 2.34 .73 79.6% +.07 28.6 −30 13.0 77
  1.75 2.46 .72 80.0% +.08 30 −31 13.1 77
  1.8 2.48 .73 79.5% +.03 45 −38 13.5 74
  2.0 2.79 .86 80.0% 0 39.5 −32 14.7 65
  2.3 3.26 .98 80.5% 0 30 −28 15.9 56
  2.75 3.96 1.15 80.5% −.15 28 −25 17.4 47
  3.0 4.36 1.3 80.7% −.25 35 −25 18.2 42
  4.0 6.55 1.7 78.5% −1.2 32 −32 20.2 33
  5.0 8.25 1.9 75.2% −3.4 31 −29 21.7 28
  6.0 10.5 1.9 74.9% −6.5 31 −24 22.5 26
  (Nominale = formula lineare; −10% lunghezza spesso meglio per D ≤3λ; +10% peggio. 1.7λ/2.44λ: .68 79.6%.)
- Valori nominali (lunghezza da formula): 1.5/2.238/.58/75.5%; 1.6/2.41/.61/76.9%; 1.7/2.57/.67/78.7%; 1.8/2.755/.72/78.2%; 2/3.1/.82/79.6%; 2.3/3.62/.93/80.2%; 2.75/4.4/1.12/79.6%; 3/4.85/1.2/79.0% (PC .7λ dentro); 4/6.55/1.7/78.5%; 5/8.25/1.9/75.2%; 6/10/2.1/73%.
- Applicazioni: offset (1.7–1.8λ), Cassegrain (f/D 0.8–2), Bochum 10.4 GHz 6λ (+1.5 dB gain e G/T, DJ4ZC); GW4DGU f/D .935 → 2.3λ (80.2%). Provati 10–90 GHz.
- Banda stretta rispetto ai corrugati ma sufficiente per uso amatoriale.

## High-efficiency prime-focus feeds (W1GHZ + WD5AGO 2006, HFSS) — VE4MA/Chaparral + septum
- Separare: antenna (horn), guida, polarizzatore, eccitazione. La sonda e il polarizzatore NON fanno parte dell'antenna (se guida abbastanza lunga i modi spuri non arrivano). Simulare con eccitazione modale pura.
- Riferimento confronti: dish 20λ, feed 1.7λ (blocking 0.085).
- VE4MA originale: horn 0.77λ, anello 0.50λ largo × 0.50λ profondo, 0.15λ dietro il bordo → ~69–71%, PC .014λ fuori. Nessuna vera risonanza: prestazioni simili su ampio range di dimensioni; horn 0.71 o 0.77λ equivalenti.
- "Super-VE4MA": anello 0.60λ × 0.45λ prof., 0.15λ dietro, horn 0.71λ → ~79% calc (f/D .35–.45), pattern con buco al centro (illuminazione ideale); PC .14λ dentro. Picco anche per 0.65–0.75λ largo × 0.3–0.4λ prof. Zona cattiva: larghezza ~0.55λ con profondità <0.5λ.
- Anelli piccoli (meno blocking): 0.35×0.35, 0.4×0.3, 0.4×0.25, 0.25×0.25 → ≥ originale su range f/D più ampio; CT1DMK 0.12λ×0.26λ quasi uguale (diametro totale <1λ).
- Posizione anello: flush → pattern tipico, best f/D .45–.5; arretrando (fino 0.4–0.5λ) il pattern si allarga col massimo fuori asse → f/D fino 0.3; la posizione influenza più l'efficienza che la f/D. PC varia ~λ/4 tra varianti → importante (1 dB su dish profondo).
- Chaparral (Wohlleben; "soft surface" anelli >λ/4 prof., passo <λ/4): 3 anelli 0.17×0.30 → meglio dell'orig. VE4MA per f/D .3–.4 a pari blocking (1.7λ). 0.20×0.33 (blocking 1.9λ) un po' meglio. 1→4 anelli: ogni anello aiuta, il 4° poco; a pari larghezza totale 2–3 anelli ≈. Profondità: diminuendo da .33 a .15λ l'efficienza AUMENTA (3 anelli) poi cala → migliore 3 anelli 0.20λ×0.20λ, 0.40λ dietro: 78.2% @ f/D .35 (horn 0.76λ: 78.7%), PC .04λ dentro; per dish profondissimi 3×0.17λ×0.26λ, 0.40λ dietro: 71% a f/D 0.25, PC .04λ fuori.
- Misure WD5AGO 2.3 GHz, dish 2.4 m f/D .37 (20λ): round septum senza anelli 51%; 1 anello .3×.3 56%; 2 anelli .17×.33 58%; 3×.15×.33 60%; Super VE4MA 65%; 3×.17×.33 (pol. 7 viti) 61%; VE4MA .5×.5 (5 viti) 58%; 3×.20×.20 su horn .76λ 64%, .71λ 63%. Misurato = simulato −12…14 punti (regola −15%).
- Dish piccolo 10λ: comunque Super VE4MA migliore (salvo f/D molto bassi → Chaparral) nonostante il blocking.
- Septum: dimensioni da Chen & Tsandoulas (guida quadra), adattate da OK1DFC; scalate in guida circolare 0.71λ (ottimale per septum). Guida quadra aperta con septum ~70% a f/D .37.
- L'isolamento tra le porte dipende dal disadattamento d'apertura (RL 10–15 dB dell'horn) e dalla riflessione del dish (inversione di senso) → inutile ottimizzare l'isolamento isolato; simulare con PML per vedere il septum da solo. Setto più spesso (Bornemann & Labay) può migliorare isolamento in guida quadra (utile a mm-wave, lavorabile dal pieno). Dimensioni/spessore del setto non influenzano il pattern.
- CP: rapporto assiale su tutto l'angolo d'illuminazione (non solo in asse!). VE4MA+septum: con anello arretrato (f/D .31) AR 1 dB solo entro 12°, 5 dB al bordo → CP peggiore per f/D <0.35; flush: AR <0.6 dB fino a 60°. Chaparral 3×0.17×0.30, 0.35λ dietro, con septum: 75% f/D .32, 70% f/D .25. Chaparral 0.2×0.2: CP pura = lineare, 0.3–0.5 f/D.
- Banda: VE4MA 0.35×0.35 buono 2.3–2.6 GHz (>10%), limitata dal polarizzatore.
- Il dish profondo aggiunge cross-pol (piani 45° in lineare, ovunque in CP).
- Costruzione: anello regolabile, ≥6 punti di contatto sul perimetro.
- Sun noise non valuta la qualità CP (rumore non polarizzato); range a riflessione da terra inadatto per CP.

## Feedhorn Analysis for G/T (W1GHZ 2014, misure WD5AGO) — programma Feed_GT
- G/T = G / T_sys; G = η (πD/λ)²; η = |∬ U_co(θ,φ) su dish|… / ∬ U_tot su sfera (include fase e XPOL). T_ant = ∬ P_tot(θ,φ)·T_bright(θ,φ) dΩ / ∬ P_tot dΩ (rumore non polarizzato → potenza totale).
- Modello rumore: cielo uniforme T_sky (23 cm: 5.7 K, RW3BP), terra 290 K; elevazioni 20/45/70°; solo prime-focus (offset ha geometria rumore diversa).
- Approssimazioni: tagli E/H (+45° per guide quadre), niente diffrazione di bordo (→ G/T ottimistico per f/D<0.3, non plottare), cielo uniforme, niente "mirror reaction" (D ≥ 20λ).
- Concordanza con RA3AQ (EM completo + ANTC di OM6AA) entro ~1 dB.
- Best f/D per G/T < best f/D per efficienza. Senza T_rx: W2IMU 1.31λ batte VE4MA su f/D .3–.4; includendo T_rx (34.5–44 K) il picco si sposta verso f/D maggiori → conta il sistema, non l'antenna da sola. ΔNF 0.1 dB → fino a 1 dB di G/T.
- Misure 13 cm (WD5AGO, 3.55 m f/D .33, 27λ): Chaparral 3 anelli 0.25λ×0.20λ arretrati 0.25λ vs W2IMU 1.22λ: sole 15.5/14.7 dB (diff. 0.8 dB ≈ diff. efficienza 0.76 dB calcolata); poi 16/15.6 dB sole, luna 0.4/0.35, Cyg A 0.12/0.10.
- Mesh: perdita di trasmissione (Otoshi; spreadsheet Mesh_Reflector_Loss_Calculator) lascia passare rumore di terra: 20% leakage → −1 dB gain ma ~−8 dB G/T. Leakage cresce rapidamente per passo > ~5% λ (filo 1 mm a 1296).
- G/T ∝ area dish; blocking cala con dish grandi.
- Mirror reaction (Silver): Γm = G_feed·λ/(4π f) (riflessione del vertice nel feed); ΔT dipende da Γm·Γ_sistema; LNA HEMT Γ ~0.9 → T sistema diverso da NF misurato; in CP il vertice inverte il senso → TX rientra nella porta RX; regolabile spostando il feed (fase).
- Rumore lunare (~200 K) rilevante per dish grandi a frequenze alte.
- Ideale: feed con best f/D un po' maggiore della f/D del dish (leggera sotto-illuminazione).
- Feed analizzati (20λ): Super-VE4MA (PC .28λ dentro in CP, arretrato .15λ; .37λ dentro se .05λ), VE4MA orig. arretrato .1λ (PC .18λ dentro), W2IMU 1.31/1.22/1.71λ (PC 0), Chaparral 3×0.25×0.20 back .25 (PC .186λ dentro), 3×0.20×0.33 back .05 (PC .1λ), RA3AQ-042, Skobelev 1.7λ/2.4λ e 2.3λ/3.26λ, SM6FHZ patch, coffee can 0.71λ, N2UO round septum, WA9HUV flangia 2λ (meno eff. a f/D bassi ma G/T migliore), OK1DFC square septum con/senza flangia 1.5λ arretrata .35λ (flangia → G/T migliore).

## Septum polarizer & feed (2003, MUD07 enhanced/ring, tolerances)
- Principio: in guida quadra (o circolare) il setto a gradini divide la componente parallela e accorcia λc per quella perpendicolare → differenza di fase 90° tra le due componenti all'ingresso → due porte = due sensi CP (TX/RX per EME, la luna inverte il senso). Opera vicino al cutoff.
- Dimensioni note SOLO per guida quadra 0.635λ (Chen & Tsandoulas 1973; spreadsheet scalabile OK1DFC); in guida circolare ~0.70–0.71λ usare i denti OK1DFC con frequenza riscalata finché l'altezza del setto = diametro (W1GHZ). Setto lineare a 30° (slope): ok in guida quadra (banda ~100 MHz a 1296), NON in circolare (pol. indesiderata solo −10 dB) → usare setto a gradini in horn circolari (VE4MA, W2IMU).
- OK1DFC quadra aperta 0.635λ: lobi posteriori ~−10 dB, 4 lobi agli angoli (diagonal+square), XPOL main lobe −21 dB, isolamento ~24 dB (1.2–1.4 GHz), ~61% calc (66% in analisi successiva), f/D .35–.40; ottimo per dish piccoli/profondi (blocking minimo).
- Flare quadro (mantenere sezione quadrata!): 1.1λ e 1.4λ (flare 30° pieno) → f/D .7–.85 (1.4λ), "razzo con alette"; versione ottagonale 1.1/1.4λ → ~70%, XPOL minore. Interpolare apertura per f/D voluto.
- Choke circolare su setto quadro: VE4MA (419 mm × 121 mm prof. a 1296) flush → 63%, f/D .4; arretrato 10–20 mm → .35; choke quadrato 1.7λ → pessimo. Enhanced (MUD07): anello diametro 2.0λ, prof. 0.375λ, 0.175λ dietro apertura → ~74% calc, f/D ~.37 (posizione dell'anello è la dimensione critica: 0.15–0.2λ); varianti per f/D >0.4 o <0.35 in appendice. Chaparral su setto quadro: 3 anelli 0.225λ × 0.31λ, 0.25λ dietro. Polarization efficiency ~95% (setto quadro + anello) < horn circolari; per dish piccolo (10λ) l'anello aiuta poco (68% vs 66%).
- Septum in coffee-can 0.71λ: gradini ~65% (slope peggio); VE4MA 0.71λ + septum ~61% (blocking maggiore); W2IMU + septum PC .02λ fuori.
- Spessore setto: poco critico (0.5→6 mm a 1296; anche 1–20 mm a 2304: ottimo ~¼" a 2.3 GHz, leggermente meglio spesso) → a mm-wave si può lavorare dal pieno. Centraggio setto: tollerante (fino a 3 spessori). Contatto setto: tollerante tranne isolamento (contatto buono su lato superiore/inferiore).
- Tolleranze: denti ±5% → efficienza <1% di variazione (AR cambia ma senza perdite significative). CRITICO: simmetria della guida (quadra/tonda) entro ~1% (5% distrugge la CP); OK1DFC lavora meglio con lato perpendicolare 1–2% più grande dell'altezza del setto. ±10% frequenza: AR ok, isolamento peggiora verso il basso.
- Choke: contatto importante; in alternativa fondo del choke spesso λ/4 = corto virtuale (choke regolabile per bande alte), o collare λ/4 isolato.
- RA3AQ e OM6AA: setti 5-step in guida circolare (migliori).
- Eccitazione con sonde: pattern uguale; RL e isolamento cambiano; OK1DFC sonda corta + vite capacitiva.

## Design of Optimized Cassegrain (EME 2014 / MUD 2023)
- Vantaggi: apparati dietro il dish (linea corta, essenziale >10 GHz), bilanciamento, spillover del feed verso cielo freddo (G/T), illumina bene dish profondi (f/D 0.25) con feed ad alto guadagno.
- Iperbole: fuochi distanti 2c; un fuoco al fuoco del paraboloide, l'altro al centro di fase del feed. c dalla posizione del feed; diametro sub dal semi-angolo del feed al taper scelto (10–12 dB); a, b dalla f/D del primario (equazioni Granet 1998). Indipendente dalla frequenza se sub ≳10λ (diffrazione). Hannan: D ≥ ~50λ per eguagliare prime-focus (W1GHZ: > ~40λ); Kildal 1983: perdita diffrazione = perdita blocking come ottimo (sub piccoli per dish amatoriali); per EME meglio sub un po' più grande.
- Output: tabella X-Y o G-code per tornio CNC / stampante 3D (script MATLAB/Octave). Sub stampati 3D + metallizzazione.
- Esempi: (1) 122 GHz, Edmund 305 mm f/D .25 (122λ), sub 38 mm (14.8λ), large W2IMU 1.9λ, BW 38.5° @12 dB → ~50% (VE2UG). (2) 47 GHz, dish SHF 300 mm f/D .6 (48λ), sub 76 mm (12λ), due Skobelev 5.6λ (22 dBi, PC 5.3λ dentro), taper 10 dB (semi-angolo ~11°), feed dietro il dish, regolazione ~1 mm, ~40 dBi ≈ 50%. (3) 10 GHz 1.2 m f/D .375 (42λ), sub 7λ (8"), large W2IMU 1.76λ, PC 275 mm davanti al vertice. (4) 47 GHz Edmund 609 mm f/D .25 (96λ), sub 20λ, large W2IMU (38.5° @12 dB) → PC 72 mm dal vertice (sub 4" → 89 mm). (5) 3 m f/D .29 per beacon 24/47 GHz, sub 240 mm (20λ @24), Skobelev 5.6λ, PC 240 mm dal vertice.
- Test: togliere il sub e confrontare col solo feed (gain noto) → gain totale.
- Alternative feed ad alto gain: Pickett-Potter (WA6KBL, DUBUS 1/2016, ingresso diretto in guida per 10/24 GHz).

## Focus, Zoom, Tilt (2009, simulazione EM completa del dish)
- Dish 15λ f/D .33: coffee-can 57%, Super-VE4MA 68% (ideale, senza supporti); lobi a 90° e 180° = diffrazione di bordo.
- Spostamento assiale: λ/4 significativo; 1λ ≈ −10 dB; null in asse a 1.75λ. Super-VE4MA ottimo con apertura leggermente verso il dish (PC dentro l'horn).
- Messa a fuoco: range > 50× distanza di Rayleigh (impossibile in giardino) → usare sun noise / radiosorgenti.
- Offset DSS 18" (15.5λ @10 GHz): W2IMU 59%, Skobelev 1.7λ 65%; BW ~4°. Spostare il feed lungo l'asse (bordo inferiore→fuoco) INCLINA il fascio: −25 mm → +2.75° (−0.6 dB), −50 mm → +5.75° (−2 dB), +25 mm → −2.75° (−0.25 dB). Gain max quasi invariato → posizionare con la stringa e fissare.
- "Zoom" per defocus non esiste: BW3 invariata fino a ~1λ di spostamento, poi ×3 con −10 dB → è un controllo di guadagno.
- Puntamento: dish 18" @10 GHz BW 4°, null a ~5°; ricerca a passi di 3°.

## Multiple Reflector Antennas (EME/MUD 2004) + Cassegrain_design.xls (formule ricostruite e verificate sui numeri del foglio)
Input: D_p, (f/D)_p, f/D equivalente del feed, diametro feed d_feed, PC feed (neg. = dentro), frequenza.
1. φ0 = 2·atan(1/(4 f/D_p)) (semiangolo dish); ψ_feed = 2·atan(1/(4 (f/D)_feed)).
2. Space attenuation: R_edge = f_p / cos²(φ0/2); A = 20log(R_edge/f_p) (idem per "virtual dish").
3. Taper ottimo Cassegrain (Kildal, solo grafico): ~14 dB per dish piccoli → ~11 dB per molto grandi (es. 12.36 dB a 84λ); altre fonti fino a 15 dB.
4. Correzione angolo feed per taper T: ψ' = ψ·sqrt(T/10) (Kelleher) [verificato: 36.87°→36.55° per T=12.36? → usa ψ'=ψ·sqrt(10/T)?? — nel foglio: 36.87→36.546° con T 12.36 e space-att virtual 0.915 dB]. NB: da verificare; implementare con il pattern reale del feed (angolo al taper scelto), non con la regola.
5. d_sub ottimo (Kildal; diffrazione = blocking): (d_sub/D_p)^5 = cos⁴(ψ'/2)·E·λ / ((4π)²·sinφ0·D_p), E = 10^(−T/10) [verificato: 0.0823 con D=84.26λ, ψ'=36.55°, φ0=69.7°, T=12.36 dB].
6. Efficienza sub (blocking+diffrazione, approx Kildal, ψ<30°): η = [1 − C_b·(…)(d/D)²]², C_b = −lnE/(1−E); all'ottimo il termine vale ≈3·C_b(d/D)² (88% nell'esempio). Valido come stima; meglio PO/GTD.
7. Distanza tra i fuochi 2c = f_hyp = (d_sub/2)·(1/tanφ0 + 1/tanψ') [verificato].
8. Senza blocco del feed: d_sub > d_feed·f_p / f_hyp → d_sub,min = sqrt(d_feed·f_p/K), K = f_hyp/d_sub; con PC: usare f_hyp+PC. Semiangolo d'ombra feed α = atan(d_feed / (2(f_hyp+PC))); ombra del sub φb = asin(d_sub/(2F_p))... (α ≤ φb).
9. Magnificazione M = tan(φ0/2)/tan(ψ'/2) (= (f/D)_feed/(f/D)_p); eccentricità e = (M+1)/(M−1); c = f_hyp/2; a = c/e; b = sqrt(c²−a²).
10. Posizioni: vertice sub → fuoco dish = c − a; vertice sub → PC feed = c + a. Profilo: y = b·sqrt(x²/a² − 1) (ramo usato, coordinate dal centro dell'iperbole) → tabella X-Y / G-code.
11. Il sub deve stare nel campo lontano del feed: c + a > 2 d_feed²/λ (≥ metà è tollerabile; vicino → errori di fase, Wood).
12. Efficienza totale ≈ η_feed (PHASEPAT con f/D equivalente del feed) × η_sub. Esempio foglio: 10.368 GHz, D 2438 mm f/D .359, feed 59 mm f/D eq .75, PC −0.11λ → d_sub min 200.7 mm (6.94λ), senza blocco 245 mm, scelto 14.3λ → η_sub 0.804 (−0.95 dB), M 2.109, e 2.803, a 63.4, b 166.1, c 177.8 mm; apice→fuoco 114.4 mm; apice→PC 241.2 mm; Rayleigh feed 8.3λ.
- Regole: sub ≥ 10λ (diffrazione), d_sub/D ≤ 0.2 (blocking ≤ 4% area) → D ≥ 50λ (Jensen/Milligan/Hannan). Gregorian = ellisse (stesso schema, sub concavo; Granet per tutte le combinazioni).
- Diffrazione: GTD (Keller); Airy; Babinet; lobi da supporti (coni di Keller).

## Flat subreflector ("degenerate Cassegrain", 2016?)
- Disco piano: il feed rovesciato è l'immagine speculare; stessa f; nessun rimodellamento.
- HFSS: dish 15λ f/D .33: coffee-can best disco ~3–4λ (−1 dB + ~1 dB di riflessione nel feed); Super-VE4MA best ~5λ (−1 dB). Dish 20λ: −0.75 dB, riflessione <0.5 dB. Diametro ottimo ~5λ indipendente dal dish (dipende dal feed). Gain complessivo 1–2 dB sotto il prime focus. Disco nel campo vicino del feed → curve irregolari. Cassegrain piccolo (sub ≈ pochi λ) non molto meglio del piano: utile solo per rimodellare (dish profondi).
## Sectoral horn per beacon (omni-azimut)
- Kraus: BW3 E ≈ 56°/A_e[λ], H ≈ 67°/A_h[λ]. Lunghezza flare > dimensione d'apertura maggiore. 10 GHz: ~12 dBi, BW3 86°, BW10 180°, elev. 24°. Versione WR-28 dritta (24/47 GHz) 7λ alta: 47 GHz BW3 82°; 24 GHz apertura 0.28λ → 142°, ~9.5 dBi. Radome: polistirolo rivestito di foglio.
## Dual-band 10 & 24 GHz feedhorn per offset (2004, AD6FP/AA6IW)
- Guida 24 GHz dentro horn 10 GHz; i PC e le f/D ottimali delle due bande differiscono → compromesso: posizionare per la banda più alta. Corna aggiunte (conico, RCA DSS, Chaparral, CD-80, surplus corrugato): 24 GHz 68–77%, 10 GHz 47%→65–74%; migliore: 76% @24 e 74% @10.

## Basi e misure (cap.1, 2, 9, 10, 6.2, 6.9)
- G = η·4πA/λ²; directivity ≈ 41253/(BW_E·BW_H); Friis: L = 20log(4πd/λ) − G_T − G_R.
- Horn piramidale (Kraus): BW3 E ≈ 56°/A_eλ, H ≈ 67°/A_hλ; G ≈ 10log(4.5 A_eλ A_hλ) dBd; BW10 ≈ 1.8·BW3.
- Range: Rayleigh 2D²/λ; per trovare il fuoco serve ~100D²/λ (50× Rayleigh), altrimenti errore fino a λ/2. Altezza sorgente su range a riflessione: h_s = λR/(4h_m).
- Sun noise: flusso solare (SFU) → rumore atteso; Y-factor cielo/terra: Te = (T_hot − Y T_cold)/(Y−1). Misure W1GHZ reali ≈ calcolo −15 punti.
- Misurati (cap.9, 10 GHz): 22" f/D .39 Superfeed 11 GHz; 25" f/D .45: Superfeed flush, Clavin, horn rettangolari, WR-90 coax, LPA, Penny (41.5%); 18" f/D .42 Clavin 53%; DSS 18" horn rettangolare ~60–63%; 24" offset 61%.
- 6.2 dipoli: EIA = 2 dipoli a λ/2 su piano λ, λ/4 sopra; loop 1λ circonf. a λ/8 da riflettore λ/2; per bande basse (non mm-wave).
- 6.9 multibanda: PC diversi per banda, posizionare per la più alta; feed coassiali (es. 24 GHz dentro 10 GHz W5ZN/W5LUA); arretrare anelli λ/4 @24 GHz (~3 mm); feed a larga banda (sinuosi, LPA) → PC variabile, gain ~10 dB, non ideali.
