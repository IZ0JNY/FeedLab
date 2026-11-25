# Appunti W1GHZ Antenna Book — parte 1 (software, cap.4, 5, 5A, 6.0, 6.1, 6.3, 6.4, App.6A)

## Algoritmi software W1GHZ (sorgenti letti)
### FEEDPATT (eff. da pattern ampiezza, E e H) — base W7PUA DISHFEED.BAS
- Input: tabelle angolo(0..180°) / dB sotto max, piani E e H; spline cubica (Numerical Recipes) a passo 1°.
- Pattern medio di potenza: P(θ)=0.5(E²+H²) (in potenza), vfeed=sqrt(P) (tensione).
- Integrali (passo 1°, punto medio θ_i=(i-0.5)°, u=media vfeed sui due estremi):
  in1=u·tan(θ/2); in2=u²·sinθ; denom=Σ_0..180 in2
- Per semiangolo ψ=20..90°: f/D=1/(4 tan(ψ/2)); K=2/tan²(ψ/2)
  block_angle = atan(feed_dia / (2·D·f/D))  (D e feed in λ)
  num=Σ_0..ψ in1; deni=Σ_0..ψ in2; numb=Σ_block..ψ in1
  η_unblocked=K num²/denom ; η_illum=K num²/deni ; η_spill=η_unblocked/η_illum (= deni/denom)
  η_tot=K numb²/denom ; η_block=η_tot/(η_ill η_spill)
  edge illum = 20log vfeed(ψ) (taper del feed, senza space loss)
- Avvertenza W1GHZ: dish reale ≥15 punti % sotto il calcolato (perdite non modellate).
### PHASEPAT (ampiezza+fase)
- Input angolo/dB/fase; unwrap fase; NEC2 ha segno fase invertito (NEC_mode).
- Centro di fase: d = Δφ·λ/(2π(1−cosθe)), θe = angolo a −10 dB (o semiangolo illuminazione). d>0 → verso la sorgente/dish.
- Riferimento spostato: φ'(θ)=φ(θ) − d·2π(1−cosθ)/λ (d in λ), normalizzato a 0 sull'asse.
- Efficienza con fase: componente in fase Re{E e^{jφ}} media E/H, sqrt(|Re|) con segno; integra come FEEDPATT.
- Scansione spostamento assiale (±3 λ) → curva η_max vs displacement; il max = miglior centro di fase per quella f/D.
### HDL_ANT (C++)
- Dish: f = D²/(16 d); ψ0 = 2 atan(1/(2 f/D − 1/(8 f/D))) (angolo totale di illuminazione)
  R_edge = 2f/(1+cos(ψ0/2)); space_att = 20 log(R_edge/f)
  taper_feed = 10 dB − space_att ; BW3 = ψ0·sqrt(3/taper_feed) (Kelleher universal horn)
  diametro horn cilindrico ≈ 66°/BW3 [λ]; gain 50% eff.
- Horn rettangolare per f/D (approssimazione G3RPE, ±2% per f/D<0.8):
  A_H = λ(2.864 f/D − 0.575); A_E = λ(1.727 f/D − 0.129); L_apex ≈ A_H²/λ; L_ax = L_apex (A_H − a_wg)/A_H
- Horn piramidale gain: G=10(1.008+log(AE·AH/λ²)) − Le(s) − Lh(t), s,t = errore fase max = A²/(8λρ), ρ = A/(2 sin(flare)) — polinomi fit di Balanis fig.23 (ricalcolabili con integrali di Fresnel).
- Gain "semplice" horn: 4.5 AH AE/λ² (+2.14 dB, Kraus).
- Tabella Cozzens per horn ottimo: lunghezza assiale/λ vs gain 10..25 dBi; A_H=0.4675λ√G, A_E=0.3463λ√G.
- Centro di fase horn piramidale (M. Reilly): formule con integrali di Fresnel, E e H separate; l = lunghezza fianco [λ], v=√(l/2), q=a/(2v).
  E: d = l(1 − q(c2 C + s2 S)/(C²+S²)), c2=cos(π/2 q²), s2=sin(π/2 q²), C,S Fresnel(q)
  H: U=v/a+a/(2v), W=v/a−a/(2v); R=W cos(π/2U²)−U cos(π/2W²); T=U sin(π/2W²)−W sin(π/2U²); CD=C(U)−C(W); SD=−S(U)+S(W); d = l(1+(R·CD+T·SD)/(CD²+SD²))  [distanza dalla bocca verso l'interno, in λ]
- Horn conico ottimo per gain G: circonferenza = λ·10^((G+2.82)/20); D=circ/π; l(slant)=D²/(3λ); flare=asin(D/(2l)); η≈52% (Jasik); gain = 20log(πD/λ) − Lc(s), s=D²/(8λl), Lc(s)=0.8038−0.9859s+19.893s²−8.033s³ dB.
- Guida circolare: TE11 cutoff λc=1.706 D (min D=0.586λ); TM01 λc=1.306 D; TE21 λc=2.057 D... (HDL usa 1.306 come limite multimodo)
- W2IMU dual-mode: (HDL) apertura D; TE11 λc=1.70646 D, TM11 λc=0.81983 D (λ < 0.82 D richiesto);
  semi-angolo flare = 44.6°·λ/D_ap ; L_phasing = 0.75/(1/λg_TE11 − 1/λg_TM11) (nella sezione di uscita, diametro = apertura)
  opzione "aperture = 2.35 × ..." (vedi cap. 6.5)
- Offset dish: tilt = asin(asse corto/asse lungo); fit 3 punti su 4f(X+X0)=(Y+Y0)²; versione 3: bordo inferiore = vertice del paraboloide; least squares su più punti (scan f, y_offset); illuminazione equivalente f/D = R_aim/diam.
- Range: R = 2D²/λ; altezza ≥3.2 D...; sorgente h_s = λR/(4h).
- Sun noise / PANFI: Y factor, efficienza = G/(π²D²/λ²).

## Cap.4 Dish
- G = η (πD/λ)²; η tipica 50%, buona 60%; 55% libri; letteratura 70-80% con feed ottimi.
- Edge taper ottimo ≈10 dB (illuminazione vs spillover); G/T ottimo ≈13 dB (anche 13–16).
- Space attenuation: f/D 0.25 → 6 dB, ψ=180°; f/D 0.35 → 3.6 dB, ψ=142°.
- Errore focale: perdita in λ indipendente da dimensione dish; più critico a f/D piccoli; misurato 22" f/D .39 @10GHz: +1/4λ → −1.7 dB.
- Superficie: ±1 mm a 10 GHz ottimo; ±3 mm → −1 dB (Ruze; scala con λ).
- Cassegrain conviene solo D ≥ 50λ e sub ≥ 20λ (Rusch) [rivisto nei paper successivi].
- Supporti: dielettrici, diagonali rispetto a polarizzazione, 4 montanti.
## Cap.5 / 5A Offset
- Il bordo inferiore coincide col vertice (tutti i dish TV misurati, entro 2 mm); focus allineato col bordo inferiore.
- Tilt=asin(corto/lungo) (stima); DSS 18": f=278–281 mm, tilt 67.6°, top string 466–468, f/D equivalente 0.69.
- Tabella dish offset (D×larghezza mm, f, top string, tilt, f/D eq): Sony DSS 451×521 f266 479 65.9° .68; DSS metal 457×496 f281 468 67.8 .69; RCA DSS SMC 457×495 278 466 67.7 .69; Dish Network 460×504 287 477 67.8 .70; metal raised edge 600×636 387 615 69.0 .72; steel small rim 600×640 403 626 69.6 .75; molded 24" 603×656 368 618 67.6 .69; metal 797×848 593 865 71.3 .81; molded plastic 850×927 505 866 67.1 .67; Channel Master 1 m 997×1083 604 1018 67.5 .68.
- Offset: sensibilità a spostamento assiale dipende dall'angolo di illuminazione (≈ f/D eq.), non dalla f/D del paraboloide madre → poco sensibile.
- Mira feed: al centro del riflettore va bene.
- Misurato: DSS 18" + horn rettangolare WR-90: 63% @10 GHz; 24" offset 61%.
## App.6A
- G ≈ 41253/(BWφBWθ) è directività ottimistica; per un dish beamwidth dominata da apertura; sovra-illuminazione → beam più stretto ma gain minore.
- Esempio 24" f/D .5 @10.368: taper 10.5/11.3 → 70% (calc), BW 3.1°; reali 10-15 punti in meno.
## 6.0
- Feed ottimo: stesso pattern e centro di fase E/H; taper 10 dB; confronti con D_dish = 10× D_feed (blocking comparabile); dimensioni in λ, scalabili.
- Perdite non modellate: fase, defocus, diffrazione bordo, cross-pol geometrica, supporti, superficie, linea, VSWR.
- Tabella feed → f/D migliore: Backfire/Helix 0.3–0.45? (vedi lista); Chaparral 0.3–0.4 (0.25-0.4); Clavin ≥0.4; Coffee-can 0.25–0.4; conico ≥0.3; corrugato ...; Diagonal 0.5–0.8; dipolo 0.25–0.35; EIA 0.4–0.6; Kumar/VE4MA 0.3–0.45; W2IMU 0.5–0.8; Penny 0.25-0.3; rettangolare ≥0.45; Scalar ≥0.45; WA9HUV 0.3–0.35; W7PUA handlebar 0.3-0.5; Sletten 0.25–0.3.
- Feed reverse (penny, dipolo) per f/D bassi con prestazioni mediocri; coax semirigido ~2 dB/m a 10 GHz.
## 6.1 Fase
- Regola: variazione di fase < λ/16 (22.5°) sull'angolo d'illuminazione.
- Calcolo pattern: NEC2 (MoM, fili) o PO (Milligan/Diaz). Avanti (±90°) accurato; dietro meno (PO: lobi spuri ±150°, nullo a 180°) → spillover posteriore si stima per conservazione energia.
- Centri di fase calcolati: dipolo+splash 0.3λ → PC 0.11λ dietro dipolo (f/D .25–.3); EIA dual-dipole PC 0.15λ dietro (f/D ~.5); W2IMU PC al centro apertura (f/D .5–.6); horn WR-90 DSS PC 0.2λ dentro; horn cardioide PC 0.43λ dentro (66% calc a f/D .25).
- Defocus assiale (dish 20λ, f/D .5, horn 1.2λ, 72% calc): 0.5λ → −0.5 dB; 0.75λ −1.3; 1λ −2.5; 1.5λ −6.6; 2-3λ >10 dB, lobo a ciambella. BW3 invariata fino ~1λ → la "zoom" per defocus non funziona.
- Multibanda: posizionare per il centro di fase della banda più alta.
## 6.3 Guida circolare
- Coffee can: BW3 ≈ 66°/D_λ; D da 0.6 a 0.9λ → f/D 0.25–0.4. D=0.76λ: best f/D .35–.4, 67% calc (~50% reale), PC all'apertura; 0.60λ: f/D .25, PC 0.1λ fuori; 0.86λ: f/D .4, PC .07λ fuori; 0.95λ: pattern storto (squint) — TM01 a 0.76λ (λc=1.306D), TE21 a 0.97λ.
- Lunghezza >1 λg dopo la sonda; F/B ≤15 dB (correnti di bordo).
- WA9HUV: flangia choke 2λ a 0.27λ dietro la bocca (horn 0.76λ) → migliora F/B; PC all'apertura.
- VE4MA (Kumar): anello choke ≈λ/2 largo e λ/2 profondo; horn 0.76λ; f/D 0.3–0.45 (flush: best .4–.45; sporgenza 0.17λ / 0.34λ → f/D ~.33); PC .07λ fuori. Dimensioni tabella (A=diam horn, B=diam anello, C=sporgenza min): 1296: 178/419/121 mm; 2304: 100/240/62.5; 3456: 66/160/42; 5760: 39/90/26.5; 10368: 20.5/50/12.5 mm.
- Chaparral: 3–4 anelli, profondità >λ/4 (nominale ~0.3λ), spaziatura 0.22–0.25λ, horn 0.71–0.81λ; f/D 0.3–0.45; flush → f/D ~0.42–0.43; horn 0.71λ sporgente 0.1λ → .30–.35 PC .08λ dentro; 0.81λ → .35–.40 PC .09λ dentro. 11 GHz Superfeed @10.368: 0.71λ, sporgenza 0.19λ, anelli 0.28λ prof.; misurato >60% su dish >20λ. Slot E-plane λ/7 per f/D piccoli (Shafai) → f/D .32.
## 6.4 Horn
- Conico liscio: correnti di bordo → lobo E, PC che si sposta col flare; 1.3λ: flare 30° (f/D .6, PC .06λ), 45° (PC .1), 60° (.13), 90° (.2), 120° (f/D .5, PC .3λ, lobo). 1.88λ/58° → f/D .7–.8, PC .43λ dentro. Ellisse 1.2:1 (asse corto // E) bilancia (King).
- Guida WR-90 aperta: f/D .25–.3, PC all'apertura, F/B scarso.
- Rettangolare: apertura min = lato largo guida → f/D min 0.48 con WR-90 (0.45 con WR-75); G3RPE per dimensioni; DSS horn WR-90: PC 0.2λ dentro, 63% misurato; WR-137 @5.76 per DSS: PC .12λ; horn surplus 50×31 mm, flare 43 mm: f/D .6–.7, PC .12λ.
- Definire horn con aperture + lunghezza assiale (8 punti) → sempre realizzabile.
- Primestar ovale: ill. 66° vert (f/D .8) / 88° oriz (f/D .65); horn 1.7λ(H)×1.0λ(E), lunghezza 2λ, PC .09λ.
- Corrugato (scalar): gole λ/4 < d < λ/2 (reattanza capacitiva), modi ibridi HE11; versione lavorabile con gole parallele all'asse; RCA DSS corrugato 1.95" flare 58°: PC .24λ dentro, f/D .6–.7; Chaparral offset 2.59"/90° @12 GHz PC 1.2λ dentro, @10.368 gole <λ/4 → peggio; corrugato 2.3λ/96° PC 1.1λ; feed f/D .8 (47° flare, 1.9"): ottimo a 12 GHz, a 10.368 picco .65 (55% misurato); Andrew Gregorian 140 mm 30° @12GHz: PC >6λ dentro, f/D 1.5–2.
- Horn corrugati larghi flare → PC molto dentro; stretti → PC vicino apertura.

## 6.5 Dual-mode
- W2IMU (Turrin 1967): TE11+TM11 eccitati dal gradino conico; ampiezza via flare, fase via lunghezza sezione di uscita; annulla campo E al bordo → niente correnti di bordo; PC al centro apertura; E/H simmetrici.
  - flare semiangolo = 44.6°·λ/B ; C = 0.75/(1/λg_TE11 − 1/λg_TM11) con λc_TE11=1.706B, λc_TM11=0.82B (al flare il TM11 è a 90°, servono altri 270°).
  - B_λ ≈ 2.35·(f/D) (stima). B min 1.22λ (TM11), max 1.7λ (TE12 λc=0.589B), esteso a 1.86λ (Turrin). → f/D 0.5–0.8; per f/D maggiori aggiungere cono (VK2ALU).
  - 1.31λ (1296 originale): f/D .5–.6; 1.86/1.88λ: f/D ~.8; 1.63λ (1.85" @10.368): flare 27.4°, C=2.8λ, f/D .7 → misurato ≥ horn rettangolare su offset 1 m; 1.79λ (2" pipe): flare 24.9°, C=3.52λ, f/D .8. VSWR <1.2.
  - Dimensioni critiche: raccordo idraulico 3/4→1.5" (flare 39°, C 1.24" invece di 29.1°, 2.72") → pessimo; adattatore 3/4→2": 22% misurato, PC E 1.6λ dentro/H 0.4λ fuori.
  - G3PHO 10 GHz: f/D .6, PC .06λ dentro; G0HNW 5.76: apertura 1.21λ < cutoff TM11 → funziona da coffee-can (f/D .45–.5); G8ACE 24 GHz con due flare + gradino 15 mm → null a 30°, PC .4λ dentro (un solo flare!); G0IVA 47 GHz scalato da 1296, C più lungo di 0.04λ → lobi lievemente più alti, eff. ok.
  - Dual-mode stretto in banda (fase modi): horn TVRO 12 GHz ottimo a 12, cattivo a 10.368.
- Diagonal horn, Love: TE10+TE01 → polarizzazione sulle diagonali; BW3 = 58.5λ/d, BW10 = 101λ/d (d lato); flare piccoli (<30° full; W2IMU 7° semi); lobi nei piani 45° crescono col flare (cross-pol, peggio su offset). N7ART 1296: lati 0.603λ(129.5 mm) f/D .30; 139.7 mm .32; 146.1 .35; 157.5 .37; flare a 177 mm, 10.2° full → .40. Offset 10 GHz: 1.4λ quadro, flare 14° full (PC .07λ), 30° (.13λ), 60° (.285λ, eff. minore); misurato deludente (45–47% / 39%) per transizione tondo→quadro martellata troppo corta; 2.8λ/30° PC 1.3λ.
- Potter (1963): guida TE11 → flare → gradino (genera TM11, ampiezza da rapporto diametri) → sezione di fase D → cono E; fase calcolata con Bessel (Potter); concentricità ~millesimi di λ. F4BAY 10.37 (scalato da ASTRA 12 GHz): f/D .6, PC .03λ fuori.
- VK2ALU: W2IMU (G3PHO) + cono lungo → f/D ~1.5 per Gregorian, PC .4λ dentro.
- Multi-mode superiori (Ludwig) non pratici.

## 6.7 Altri feed
- Clavin 1974: cavità + slot risonante + sonde (TE11+TM11), piccolo, banda stretta (fare slot corto e limare); f/D .35–.40; misurato 53% su 18" f/D .42; D_feed 0.88λ.
- Rear feeds (Penny G4ALN, Clavin 1954, pillbox Procom ~30%, DK2RV 35–40%): scarsi (3–5 dB persi). Penny misurato 41.5% su 25" f/D .45; ottimo solo a f/D ~.25.
- Indirect rear feed con disco piano: perdita diffrazione grande per subriflettori < ~10λ (curve Rusch/Milligan: ~5 dB a 2.4λ). Disco 3.8λ meglio, oltre blocco aumenta. Ray optics non valida < ~10λ.
- Shepherd's crook (guida circolare in rame), J-bend, o semirigido RG-141 0.5 m ≈ 1 dB → meglio.
## App. 6C campi vicini
- Pattern lontano = trasformata di Fourier del campo d'apertura: apertura piccola → fascio largo; bordi bruschi → lobi.
- TE10 rettangolare: uniforme in E, cos(πx/a) in H; campo alto sul bordo lungo → correnti di bordo → lobi laterali/posteriori.
- Guida lunga ≥ 1 λg dopo la sonda per eliminare modi evanescenti; guide corte → asimmetria/squint di qualche grado.
- WR-90 aperta con flangia quadrata UG-39/U: F/B molto migliore → buon feed per f/D .25–.3.
- Diagonal 0.73λ senza flare ≈ guida circolare aperta (non vale la pena).
- Simulatore usato: Zeland Fidelity (FDTD) oltre a NEC2 e PO.

## Cap.11 (FEEDPATT) / Cap.12 (calcolo pattern)
- Integrazione numerica da W7PUA (DISHFEED.BAS) basata su Cutler 1947. cos^n benchmark: cos³ → 80% max a f/D .4–.5.
- Blocking: VE4MA 1.84λ a 1296: dish 28'(20×) alto, 12'(8.6×) <10% blocking, 8'(5.7×), 4'(2.9×) molto peggio, 2'(1.4×) inutile. Dish < 10λ = "piccolo".
- Errori di fase = causa principale di bassa efficienza; serve stesso PC in E e H.
- Radioastronomi: lavorare a sinistra del picco (f/D minore / taper maggiore) per ridurre spillover e lobi (W7PUA).
- Calcolo pattern: NEC2 (MoM, wire/patch; modelli in λ scalati a 1296 MHz; horn = strisce di surface patch ruotate con GM, 18 lati; sonda monopolo al centro di patch; LD conducibilità rame 3.72e7 (?) ; RP tagli φ=0(E),45,90(H); fase dalla tabella RADIATION PATTERN se polarizzazione LINEAR); PO (Milligan & Diaz, MATLAB) per horn grandi/dish; FDTD (Zeland Fidelity).
- Validazione: avanti accurato, dietro meno; patch identiche creano lobi spuri (variare dimensioni).
- Formato dati pattern: "angolo dB fase" + commenti //. Script nec2pat.pl.
- Impedenza NEC: ok se VSWR < 10 nel modello (il pattern conta).
