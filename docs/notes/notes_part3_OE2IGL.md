# Appunti OE2IGL (Gerald OE2IGL, wettersat.bplaced.net) — simulazioni openEMS/GRASP, design guide, formule

## Flusso di lavoro gratuito (Dorsten 2025)
- Feed: openEMS (FDTD, Octave/Python), mesh λ/60, ottone come materiale (AddMaterial+conducibilità, non AddMetal, per vedere il ripple). Free CST (max 100k celle: troppo poco; servono 10–500 M celle).
- Riflettore: GRASP-SE (TICRA, gratuito): feed solo come "Gaussian" o "simple tapered pattern" (dal pattern openEMS/CST): entro 0.05–0.1 dB dalla versione completa. Offset 2.4 m @47 GHz: 5 min in GRASP-SE vs openEMS 1.2 m @10 GHz: 32 GB, 750 M celle, 3.5 h (2.4 m → 256 GB).
- Script Octave per η_i, η_s, η_xpol, η_phase, G/T, edge taper dal pattern; tool DF3GJ (Köppen) e W1GHZ.
- η_aper = η_i·η_s·η_xpol·η_phase (obiettivo xpol e phase >99.5%); η_tot = η_aper·η_ohmic·η_Ruze·η_block·η_feedpos·η_impedance…
- Scala qualità: >90% professionale (shaped), >80% ottimo amatoriale, >75% buono, 65–75% "così così", 50–65% scarso, <50% pessimo. +10% η ≈ +1.3 dB SNR EME, +0.7 dB sun noise.
- Ottimizzare per RX (G/T) costa pochi punti di η (82→79%) ma riduce molto i lobi.
- Esempi: 47 GHz corrugato assiale DL7YC 82% (moon noise +0.3–0.4 dB); OE9ERC 10.6 m offset f/D .414 @10 GHz: cavity feed con septum 82%, con gola λ/4 sull'anello esterno 83.2%, ottimizzato RX 79%, S11 < −20 dB misurato; W2IMU/Pickett-Potter 47 GHz 80% (IZ0JNY, con piastrina λ/4 WR22/WR19, angolo 74°, offset f/D ~.66).
- Gregorian dual-offset 1.3 m shaped (HB9PZK): 89% @10, 93% @47/76 GHz.
- Sopra 47 GHz e D > 2 m la perdita dominante è la superficie (Ruze).

## Design guide (spreadsheet) — formule estratte
### Conversione angolo/f/D (offset)
- Lavorare con l'ANGOLO DI APERTURA del dish (totale, centro-bordo×2), non con la f/D.
- f/D (prime) = 1/(4 tan(θ/4)), θ angolo totale.
- f/D offset equivalente (offset angle 21°): f/D = [cos(θ/2) + cos(atan(2/tan((90−21)°)))] / (4 sin(θ/2)).
### W2IMU Dual-Mode Feedhorn, calcolo parametrico (OE2IGL 2024, da W1GHZ + openEMS); θ = angolo di apertura [°], λ
- f_c(guida ingresso) = 0.77·f → A (diametro ingresso) = c/(1.706·f_c); range ammesso 0.725…0.84 f (A = λ/(1.706·0.84) … λ/(1.706·0.725)).
- B = (−1.77531e-8 θ⁴ + 5.66609e-6 θ³ − 6.67931e-4 θ² + 0.0340124 θ − 0.60017)·θ·λ ; range 1.22λ…1.7λ.
- C = (−7.41104e-10 θ⁵ + 3.00061e-7 θ⁴ − 4.83865e-5 θ³ + 3.88389e-3 θ² − 0.155265 θ + 2.4863)·θ / (1/λg_TE11(B) − 1/λg_TM11(B)), λg = λ/sqrt(1−(λ/λc)²), λc_TE11=1.706B, λc_TM11=0.82B.
- α (semiangolo flare) = 44.6°·λ/B. Banda utile: 1.15–1.57 f_c. η 77% (f/D .5) – 80% (f/D .8).
- Esempio 24.048 GHz, θ=74°: A 9.49 mm, α 26.4°.
### Pickett-Potter, calcolo parametrico (OE2IGL 2025, da Milligan + openEMS)
- R_ap[λ] = 60.907·θ^(−0.98422); L_flare[λ] = −0.53504R⁴ + 4.1757R³ − 11.589R² + 16.963R − 5.8895 (opz. correzione %).
- Di (ingresso) = 1.02λ (0.51·2λ); Ds (dopo gradino) = 1.30λ; D_ap = 2R λ.
- Es. 47.048 GHz, θ=69.2°: R 0.941λ (D_ap 11.99 mm), L 2.87λ (18.29 mm), Di 6.50, Ds 8.28 mm. η 78% (f/D .6) – 81% (f/D >1). Pickett-Potter ≈ leggermente meglio del W2IMU; per f/D .58–.8.
- (Pickett-Potter = gradino 1.02→1.30λ + flare: stessa famiglia di Skobelev.)
### Corrugato assiale ad alte prestazioni (OE2IGL v1.4, base CT1DMK; 8 gole)
- Validità 10–76 GHz; f/D prime .33–.90, offset .33–.80; input = semiangolo ψ=θ/2 [°]; arrotondamento (MROUND) 0.05 mm (<30 GHz), 0.025 (<55), 0.02 (<80), 0.025.
- pitch[λ] = −6.72759e-9ψ⁶ + 2.13419809e-6ψ⁵ − 2.7793768348e-4ψ⁴ + 0.01900638584665ψ³ − 0.71948851201245ψ² + 14.2975507272445ψ − 116.265581374344
- w[λ] = −5.00164e-9ψ⁶ + 1.57372735e-6ψ⁵ − 2.0304694239e-4ψ⁴ + 0.0137396440128ψ³ − 0.51402558573511ψ² + 10.0836505431737ψ − 80.8959001275667
- axi[λ] = −7.14481e-9ψ⁶ + 2.25111842e-6ψ⁵ − 2.9166230154e-4ψ⁴ + 0.01987517595131ψ³ − 0.7508309146383ψ² + 14.8952165691508ψ − 120.835516302193
- delta[λ] = max(0, −3.5684e-9ψ⁶ + 1.15051226e-6ψ⁵ − 1.5125028602e-4ψ⁴ + 0.01035505492211ψ³ − 0.38867044924585ψ² + 7.58012720956018ψ − 60.0565016846105)
- Di[λ] = 2·(−9.4718e-10ψ⁶ + 2.8274745e-7ψ⁵ − 3.469444174e-5ψ⁴ + 0.00224733479491ψ³ − 0.0814076296413ψ² + 1.56778931797874ψ − 12.1322259993015)
- Ds[λ] = 2·(−1.38043e-9ψ⁶ + 4.5403189e-7ψ⁵ − 6.178883658e-5ψ⁴ + 0.00444598271875ψ³ − 0.17774710208844ψ² + 3.71538298037237ψ − 30.9065313607455)
- las = 3 mm (fisso); d1[λ] = 2.37e-10ψ⁶ − 2.133e-8ψ⁵ − 4.303976e-6ψ⁴ + 7.77088212e-4ψ³ − 0.047141193767ψ² + 1.270049062497ψ − 12.635629680167; d2…d8 = 0.25λ.
- Efficienze fit (ψ in °): η = 7.03e-10ψ⁵ − 1.04718e-7ψ⁴ + 4.80878e-7ψ³ + 5.19517223e-4ψ² − 0.023415967549ψ + 1.099049534637; spill = −1.1072e-8ψ⁵ + 2.812104e-6ψ⁴ − 2.78323455e-4ψ³ + 0.013360124165ψ² − 0.30880181878ψ + 3.64266475677; illum = 5.333e-9ψ⁵ − 1.262187e-6ψ⁴ + 1.12395799e-4ψ³ − 4.636545892e-3ψ² + 0.087318389246ψ + 0.323315663532; xpol = 6.855e-9ψ⁵ − 1.707891e-6ψ⁴ + 1.66032124e-4ψ³ − 7.897814012e-3ψ² + 0.184306183382ψ − 0.6955133427; phase = −1.555e-9ψ⁵ + 3.54182e-7ψ⁴ − 3.0869865e-5ψ³ + 1.274395248e-3ψ² − 0.024625360476ψ + 1.17300336644.
- Tolleranza costruttiva: ±0.1 mm (<30 GHz), ±0.05 (<55), ±0.02 (<80 GHz).
- (Geometria esatta dei parametri pitch/w/axi/delta/Di/Ds/las/d1..d8: vedere disegno nel PDF 2026/xlsx — da verificare prima di implementare il generatore CAD.)
- Risultati: 47 GHz f/D .41: 85.0% (spill 93, illum 93, pol 99.5, fase 99.5) — CT1DMK 81.5% → raddoppio passo gole + tuning; 24 GHz f/D .71: 81.6%. Corrugato LNB commerciale 10.7–12.7 GHz: 77.5% max, 75% a 10.368.
- Modo ibrido doppio HE11 + HE12: +5% (letteratura), ma più stretto in banda.
- Scelte per banda: fino a 47 GHz corrugato assiale (facile); 76 GHz e oltre: Pickett-Potter (offset) o cavity feed (prime focus, f/D .35–.5, 83%).
### Piastrina adattatrice λ/4 (rect–rect, rect–tonda), S11 < −25/−30 dB, design guide xlsx (anche WR12 ↔ Ø2.4 mm @76 GHz); foglio con attenuazione guide (Microwaves101).
### Transizioni coax (openEMS) @10.368: WR-90 backshort 6.1 mm, pin 5.73 mm; tonda Ø20.1 mm: backshort 12.0, pin 6.3, pin→bocca 53.3 mm (=1 λg).

## Pratica mm-wave (pagine transverter)
- 24 GHz W2IMU: guida Ø10.1 mm, apertura 19.4 mm, lunghezza 30.6 mm (WR-42).
- 76 GHz: offset Gibertini OP65 (675×630, f/D .66, illuminazione 70°); W2IMU guida Ø3.1, apertura 6.1 mm (1.55λ), lunghezza 9.7 mm, ~12 dBi, −10 dB a 75°; taper rettangolare→tonda 20 mm (WR-12). PC entro λ/4 (<1 mm) dal fuoco; dish entro λ/4. Puntare il feed verso il PUNTO PIÙ PROFONDO del dish offset, non il centro. Fuoco trovato con stringa + specchietti al sole + sun noise. Fuoco offset: f = (asse corto)³/(16·asse lungo·profondità); tilt = arccos(corto/lungo).
- 122 GHz: W2IMU guida Ø1.8 mm, apertura 3.8 mm, lunghezza 6 mm (WR-8). Dish offset TV a 122 GHz: ~10 dB di perdita (superficie). Usa prime-focus 30 cm f/D .3 da link 38 GHz (f 90 mm) con "shepherd's hook" in tubo rame Ø3/2.1 mm (cutoff ~90 GHz). Dish da tornio in acciaio ±0.03 mm fino a 500 GHz.
- 241/134/122 GHz (DB6NT triband): stesso horn 122 per 241.
- Ruze: ΔG[dB] = −685·(RMS/λ)²: RMS 0.05 mm → −0.3 dB @122, −1.1 @241; 0.1 mm → −1.1/−4.4; 0.2 mm → −4.5/−17.7. RMS ≈ (picco−valle)/3.
- Link budget fino a 1000 GHz con attenuazione atmosferica ITU-R P.676-12 (foglio Linkbudget v2.1).

## "Antenna Basics" (appunti manoscritti, fonti Baars/Milligan/Kraus/Tai-Pereira)
- D = 4π/Ω; Kraus 41253/(θE θH) (HPBW > 56°), ellittico 52525/(θE θH); Tai-Pereira D = 32 ln2/(θE²+θH²) (HPBW < 56°).
- HPBW = b·λ/d; Baars, apertura con taper parabolico sul piedistallo τ (T=20logτ): g(u)=[4/(1+τ)(τ J1(u)/u + 2(1−τ)J2(u)/u²)]², u = πd sinθ/λ; b = 1.269 − 0.566τ + 0.534τ² − 0.208τ³ (T=0 → 1.029, −10 dB → 1.135, −∞ → 1.269).
- G(taper) = (πd/λ)²·(1.029/b)² → η_i(−10 dB) ≈ 82%.
- Taper efficiency gaussiana (Baars/Milligan): η_t = 2(1−e^−α)²/(α(1−e^−2α)), α = T·ln10/20 (T=10 → α 1.151, η_t .902); spillover gaussiano η_s = 1 − e^(−2α) (≈ .90 a 10 dB); cos^{2N}(ψ/2) (Milligan): η_t = 4(N+1)(1−u^N)²/(N²(1−u^{2(N+1)}) tan²(ψ0/2)), η_s = 1 − u^{2(N+1)}, u = cos(ψ0/2). η_i = η_t·η_s; max teorico ≈ 82% a ~11 dB.
- Blocking (Baars): η_B = (1 − (1/η_i)(d_B/d)²)².
- Ruze: η = exp(−(4πRMS/λ)²).
- Defocus assiale (Milligan, gaussiano): s = (z/λ)(1−cos ψ0), α = T/8.686; η_PE = α²(1 − 2e^−α cos(2πs) + e^−2α) / ((α² + (2πs)²)(1−e^−α)²). Es. f/D .6, T 12 dB, 47 GHz, z=0.2λ: −1.2 dB (calc OE2IGL con s=0.3?); f/D .35: −6.7 dB.
- G = D·η_ohm·η_t·η_s·η_pol·η_B·η_sur·η_focus.
- T_spillover (prime focus, elev Ele, offset): frazione rivolta a terra = 1 − acos(sin(Ele−offset)/sin(ψ0))/π: T_spill = f_ground·T_amb·(1−η_s) + (1−f_ground)·T_sky·(1−η_s).
- T_sky = (1 − 10^(−A_zen/(10 sin Ele)))·(0.81 T_amb[K] + 37.4) + T_CMB·10^(−A_zen/(10 sin Ele)); correzione Planck T' = hν/(k(e^{hν/kT} − 1)) a mm-wave (47 GHz: 23 K → 21.5 K).
- G/T = G − 10log(T_rx + T_spill + T_sky), T_rx = 290(10^(NF/10) − 1).
- Main beam efficiency η_MB = 0.8899·b²·η_ant (Ω_MB = 1.133 θ²).
- Taper prime focus: free-space taper T_F = 20log(1+(1/(4 f/D))²) = −20log(cos²(ψ0/2)); feed taper = taper totale − T_F (es. f/D .66: ψ0 41.5°, T_F 1.2 dB → feed 8.8 dB per 10 dB).
- Offset (Milligan/Stutzman): ψ_S = asin(8FD/(16F²+4H²−D²)) (semiangolo), ψ_B = asin(16FH/(16F²+D²−4H²)) (bisettrice), ψ_L = ψ_B − ψ_S, ψ_U = 2ψ_S + ψ_L, ψ_f = 2·atan(H/(2F)) (direzione del centro). Taper spaziale differenziale ΔFT = 40log(cos(ψ_L/2)/cos(ψ_U/2)); per bilanciare i taper ai bordi ruotare il feed: ψ_P = ΔFT·BW/(4.01·(2ET − ΔFT)) + ψ_S (BW = 2ψ_S, fascio gaussiano), ψ_F = ψ_L + ψ_P. Es. ψ_L 0.7°, ψ_U 74.7°, ET 10 dB → ΔFT 3.39 dB, ψ_F 42.3° (vs bisettrice 37.7°).
- Gaussiano: f(x) = exp(−2.77 x²/HPBW²) (in potenza).
