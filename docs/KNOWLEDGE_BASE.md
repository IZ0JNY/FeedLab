# FeedLab: base di conoscenza per progettare e simulare illuminatori 10–134 GHz

Sintesi ragionata del *W1GHZ Online Microwave Antenna Book* (Paul Wade W1GHZ, w1ghz.org/antbook) e dei suoi articoli di conferenza. Comprende anche i sorgenti di FEEDPATT, PHASEPAT e HDL_ANT e il foglio `Cassegrain_design.xls`.

Le note di lettura dettagliate, capitolo per capitolo, sono in `notes_part1.md` (libro) e `notes_part2.md` (articoli).

> **Fonti e licenza.** Il libro e i programmi di W1GHZ sono gratuiti per uso radioamatoriale. Per uso commerciale l'autore chiede un contributo (73 $) all'ARRL Foundation. Questo documento riporta concetti, formule e dati numerici, non il testo. Le formule fisiche (Cutler, Kildal, Silver, Balanis, Granet…) sono di dominio pubblico. Se il software sarà venduto, conviene reimplementare gli algoritmi (come fa `feedlab/`) senza copiare codice W1GHZ, e citare la fonte.
>
> Le parti marcate **[ext]** non vengono da W1GHZ: sono conoscenza generale aggiunta per coprire 10–134 GHz.

---

## 1. Riflettore parabolico: geometria e bilancio d'efficienza

### 1.1 Geometria
| Grandezza | Formula |
|---|---|
| Focale da diametro D e profondità d | f = D²/(16 d) |
| Semiangolo d'illuminazione | ψ0 = 2·atan(1/(4·f/D)) (f/D 0.25 → 90°, 0.35 → 71°) |
| Distanza fuoco–bordo | R_edge = f / cos²(ψ0/2) |
| Attenuazione spaziale al bordo | A_sp = 20·log10(R_edge/f) (f/D 0.25 → 6 dB, 0.35 → 3.6 dB) |
| f/D da semiangolo | f/D = 1/(4·tan(ψ/2)) |
| Taper totale al bordo | T_edge = taper del feed a ψ0 + A_sp |
| Guadagno | G = η·(πD/λ)² |

### 1.2 Regole di progetto
- **Taper ottimo.** Circa 10 dB al bordo (feed + spazio) per il massimo guadagno; 13–16 dB per il massimo G/T. Con feed "migliorati" (Super-VE4MA, Chaparral a anelli bassi) la regola dei 10 dB non vale: integrare il pattern.
- **Stima di BW3 del feed (Kelleher).** BW3 ≈ ψ0·√(3/T_feed). Per una guida circolare: BW3 ≈ 66°/D_λ.
- **Dimensionamento in λ.** Tutti i dish con la stessa f/D hanno la stessa geometria. Un feed scalato in λ funziona a qualunque frequenza.
- **Dish "piccolo"** = meno di ~10λ: blocking e diffrazione dominano.
- **Perdite non modellate** dall'integrazione dei pattern: supporti, superficie, diffrazione di bordo, linea, VSWR, polarizzazione geometrica. Ne segue la regola empirica: **efficienza reale ≈ calcolata − 12…15 punti percentuali** (verificata più volte con sun noise).
- **Superficie (Ruze) [formula ext].** η_s = exp(−(4πε/λ)²). W1GHZ: ±1 mm è ottimo a 10 GHz, ±3 mm costano circa 1 dB. Scala con λ: a 134 GHz servono ~0.07 mm.

### 1.3 Errore assiale (defocus): la misura più critica
- La perdita dipende dall'errore **in λ** e dall'angolo d'illuminazione, non dalla dimensione del dish.
- Esempio: dish 20λ, f/D 0.5, horn 1.2λ, 72% calcolato:

  | Spostamento | Perdita |
  |---|---|
  | 0.5λ | −0.5 dB |
  | 0.75λ | −1.3 dB |
  | 1λ | −2.5 dB (circa −10 dB su un dish f/D 0.33) |
  | 1.5λ | −6.6 dB |
  | 2–3λ | oltre −10 dB, lobo principale a ciambella |

- BW3 non cambia fino a ~1λ di spostamento: lo "zoom per defocus" non esiste, è solo un controllo di guadagno.
- Su un dish offset lo spostamento lungo l'asse **inclina il fascio** (DSS 18" a 10 GHz: −25 mm → +2.75°, −0.6 dB). La messa a fuoco è poco critica.
- Feed multibanda: posizionarli sul centro di fase della banda più alta.
- Trovare il fuoco richiede un range di ~100·D²/λ, quindi in pratica si usa il sun noise o una radiosorgente.

### 1.4 Dish offset
- I dish TV hanno il bordo inferiore sul vertice del paraboloide madre (misurato su 9 dish, entro 2 mm). Ne segue:
  - il fuoco è allineato col bordo inferiore;
  - lunghezza della "stringa" dal bordo inferiore al fuoco = f;
  - si misura anche la stringa dal bordo superiore al fuoco.
- Tilt stimato = asin(asse corto / asse lungo). Si raffina con un fit ai minimi quadrati di più punti sulla linea centrale: equazione 4f(X+X0) = (Y+Y0)², scansione su f e offset, errore medio < 1 mm.
- Il feed vede l'angolo del settore, equivalente a una f/D di 0.65–0.8. La sensibilità al defocus è quella di quella f/D equivalente, non della f/D (~0.3) del paraboloide madre.
- Tabella dei dish misurati (Sony/RCA/Dish Network DSS, 600 mm, 800 mm, 1 m Channel Master): f/D equivalente 0.67–0.81. Dati in `notes_part1.md` §5A.

### 1.5 Blocking
- Calcolo con l'integrale di campo escludendo l'ombra del feed (§2).
- Esempio VE4MA 1.84λ a 1296 MHz: dish/feed = 20 → trascurabile; 8.6 → < 10%; 2.9 → pesante; 1.4 → il dish è inutile.
- Anche su dish piccoli (10λ) il feed migliore ma più grande (Super-VE4MA) resta preferibile, salvo dish molto profondi.

---

## 2. Calcolo dell'efficienza e del G/T (il motore numerico)

### 2.1 Metodo FEEDPATT (W7PUA ← Cutler 1947), solo ampiezza, tagli E e H
Pattern di tensione medio: v(θ) = √(½(P_E(θ)+P_H(θ))). Integrazione a passo 1°:

```
I1(ψ) = ∫0^ψ v(θ)·tan(θ/2) dθ            (campo raccolto dal dish)
I2(ψ) = ∫0^ψ v²(θ)·sinθ dθ               (potenza intercettata)
I2tot = ∫0^π v²(θ)·sinθ dθ                (potenza totale)
K = 2 / tan²(ψ/2) = 32 (f/D)²

η_ill   = K·I1²/I2(ψ)
η_spill = I2(ψ)/I2tot
η_block = (I1 − I1(0..θ_b))² / I1²   con θ_b = atan(D_feed/(2·f))
η_tot   = K·(I1(θ_b..ψ))²/I2tot
```

- Input in formato `.dat`: righe `angolo  dB  [fase]`, commenti `//`. L'archivio originale contiene 80 pattern di feed reali (VE4MA, W2IMU, Chaparral, Kumar, Clavin, Penny, horn…), utilizzabili come dati di test.
- **Benchmark:** pattern cos^n → ~80% massimo a f/D 0.4–0.5 (con blocking 10:1). Senza blocking vale la teoria classica: η_max ≈ 0.83 per n = 2…8 (Silver).

### 2.2 PHASEPAT (ampiezza + fase)
- **Centro di fase.** d = Δφ(θ_e)·λ / (2π(1−cosθ_e)), con θ_e = angolo a −10 dB oppure semiangolo del dish. d > 0 significa verso il dish (davanti all'apertura).
- **Spostamento del riferimento.** φ'(θ) = φ(θ) − 2π·d·(1−cosθ)/λ, normalizzato a 0 sull'asse.
- **Efficienza con fase:** si integra la parte in fase, Re{E·e^{jφ}}.
- **Scansione di defocus** ±3λ → curva dell'efficienza massima. Il picco dà il **miglior centro di fase per quella f/D**, criterio più utile del fit sul −10 dB.
- **Regola sulla fase:** variazione < λ/16 (22.5°) sull'angolo d'illuminazione.

### 2.3 Formulazione completa (da usare nel nuovo software)
η = |∬_dish E_co·tan(θ/2) dθ dφ|² / (π·tan²(ψ0/2)·∬_sfera |E|² sinθ dθ dφ) **[ext, Kildal; equivalente a W1GHZ 2014]**

- Numeratore: solo la componente **co-polare** (per CP: RHCP o LHCP) con la sua fase. Denominatore: potenza totale, tutte le polarizzazioni.
- Fattorizzazione: η_spill · η_ill · η_phase · η_pol · η_block · η_Ruze · η_supporti · η_linea…
- Basta usare i tagli φ = 0°, 45°, 90°. Il taglio a 45° è indispensabile per horn quadri, diagonali e septum.

### 2.4 G/T (programma Feed_GT, 2014)
- T_ant = ∬ P_tot(θ,φ)·T_b(θ,φ) dΩ / ∬ P_tot dΩ. Il rumore non è polarizzato, quindi si usa la potenza totale. Modello: cielo uniforme (5.7 K a 23 cm), terra 290 K, elevazione 20/45/70°.
- G/T = G / (T_ant + T_rx). Il ricevitore sposta l'ottimo verso f/D maggiori: 0.1 dB di NF può valere 1 dB di G/T.
- **Rete (mesh).** La perdita per trasmissione (Otoshi) fa passare rumore di terra: 20% di leakage = −1 dB di guadagno ma ~−8 dB di G/T. Tenere il passo sotto ~5% di λ.
- **Mirror reaction** (Silver): Γm = G_feed·λ/(4π f). Degrada T_sys con LNA disadattati (HEMT Γ ~0.9). In CP inverte il senso, quindi l'energia TX rientra nella porta RX. Si regola spostando il feed.
- **Limiti:** niente diffrazione di bordo (G/T troppo ottimistico per f/D < 0.3), dish ≥ 20λ, solo prime-focus. L'offset richiede un modello di rumore geometrico diverso.
- Misure G/T su offset con f/D ~0.6 (sun noise, 10 GHz): W2IMU da 1.88λ batte quello da 1.34λ di **+2.3 dB** (1.2 m) e +1.6 dB (1 m).

---

## 3. Centro di fase: dati di riferimento (valori in λ; + = davanti all'apertura, − = dentro)
| Feed | Centro di fase |
|---|---|
| Guida circolare 0.60 / 0.76 / 0.86λ | +0.1 / 0 / +0.07 |
| Guida rettangolare WR-90 aperta | 0 |
| VE4MA originale | +0.07 (NEC); Super-VE4MA −0.14 (lineare), −0.28 (CP, 0.15λ indietro) |
| Chaparral (horn 0.71–0.81λ) | da −0.08 a −0.09 |
| W2IMU (1.31–1.88λ), Potter F4BAY | ≈ 0 / +0.03 |
| Skobelev 1.5–2.3λ | ≈ 0; 3λ −0.25…−0.7; 4λ −1.2; 5λ −3.4; 6λ −6 |
| Horn rettangolare per DSS | −0.2 |
| Horn conico liscio | flare 30° −0.06, 60° −0.13, 90° −0.2, 120° −0.3; 1.88λ/58° −0.43 |
| Corrugati a flare largo (~90°) | da −1.1 a −1.2; Andrew Gregorian 30° −6.1…−6.4 |
| Diagonale 1.4λ | flare 14° −0.07, 30° −0.13, 60° −0.285 |

Regola: horn grande e flare ampio portano il centro di fase verso la gola. Una differenza di centro di fase tra E e H equivale a un defocus in un piano.

---

## 4. Catalogo dei feed con regole di dimensionamento (tutto in λ)

### 4.1 Guida aperta
- **Circolare ("coffee can").** D da 0.6 a 0.9λ per f/D da 0.25 a 0.4; BW3 ≈ 66°/D.
  - Cutoff: TE11 1.706D (D min 0.586λ); TM01 1.306D (0.766λ); TE21 1.029D (0.97λ). Oltre 0.95λ il pattern devia (squint).
  - Lunghezza dopo la sonda ≥ 1 λg. Fronte/retro ≤ 15 dB.
- **Rettangolare WR aperta.** f/D 0.25–0.3. Con flangia quadrata UG-39 il fronte/retro migliora molto.
- **Flangia piana WA9HUV.** Diametro 2λ, 0.27λ dietro la bocca: efficienza un po' minore a f/D bassi ma G/T migliore.

### 4.2 Con choke (soft surface)
- **VE4MA / Kumar.** Horn 0.71–0.77λ; anello 0.5λ largo × 0.5λ profondo, 0.15λ dietro il bordo; f/D 0.3–0.45 regolabile spostando l'anello.
  - Dimensioni pubblicate (horn / anello / sporgenza): 10368 MHz 20.5 / 50 / 12.5 mm; 5760 MHz 39 / 90 / 26.5 mm.
- **Super-VE4MA.** Anello 0.60 × 0.45λ, 0.15λ dietro: ~79% calcolato, 65% misurato (record prime-focus), f/D 0.35–0.45.
- **Anelli piccoli** (0.35×0.35, 0.4×0.3, 0.25×0.25, 0.12×0.26λ): prestazioni come l'originale con meno blocking.
- **Zona da evitare:** larghezza ~0.55λ con profondità < 0.5λ.
- **Chaparral (Wohlleben).** 3 anelli, passo < λ/4.
  - Migliore: 0.20 × 0.20λ, 0.40λ dietro → 78% a f/D 0.35.
  - Per dish profondissimi: 0.17 × 0.26λ, 0.40λ dietro → 71% a f/D 0.25.
  - Contrariamente all'idea classica (profondità > λ/4), anelli **bassi** (0.15–0.20λ) rendono di più. Quattro anelli o più non aiutano.
- **Costruzione:** almeno 6 punti di contatto dell'anello; in alternativa fondo del choke spesso λ/4 (corto virtuale) per renderlo regolabile.

### 4.3 Horn piramidali e conici
- **Horn rettangolare per f/D (approssimazione G3RPE, ±2% per f/D < 0.8):**
  - A_H = λ(2.864·f/D − 0.575); A_E = λ(1.727·f/D − 0.129)
  - L_apex ≈ A_H²/λ; L_assiale = L_apex·(A_H − a)/A_H
  - Lato largo della guida = apertura minima, quindi f/D minima 0.48 con WR-90 e 0.45 con WR-75.
  - Definire l'horn con le due aperture e la lunghezza assiale (8 punti): sempre realizzabile.
- **Guadagno del piramidale.** G = 10(1.008 + log10(A_E·A_H/λ²)) − L_E(s) − L_H(t), con s, t = A²/(8λρ) errore di fase massimo e ρ = A/(2 sin flare). L_E e L_H dalle curve di Balanis (calcolabili con gli integrali di Fresnel).
- **Centro di fase del piramidale** (formule con integrali di Fresnel, M. Reilly): vedi `notes_part1.md`. Implementate in `feedlab.horns`.
- **Conico liscio.** Pattern E/H asimmetrici, lobi dovuti alle correnti di bordo, centro di fase mobile: poco adatto come feed. Ottimo per il guadagno: D = λ·10^((G+2.82)/20)/π, l_slant = D²/(3λ), η ≈ 52%.
- **Corrugato (scalar).** Profondità tra λ/4 e λ/2, modo HE11, pattern simmetrici e larga banda; difficile da costruire. Un surplus funziona finché le gole sono più profonde di λ/4 alla nuova frequenza.

### 4.4 Dual-mode: la famiglia migliore per 10–134 GHz
- **W2IMU (Turrin).** Guida d'ingresso (0.7–0.81λ) → flare conico → sezione cilindrica di diametro B e lunghezza C.
  - Semiangolo di flare = 44.6°·λ/B; in pratica 28° è l'ottimo, 30° costa ~1%.
  - C = 0.75 / (1/λg_TE11 − 1/λg_TM11), con λc_TE11 = 1.706B e λc_TM11 = 0.82B (al flare i due modi sono già sfasati di 90°, ne servono altri 270°).
  - B va da 1.22λ (cutoff TM11) a ~1.9λ (TE12 a 0.589B). Stima iniziale: B_λ ≈ 2.35·f/D.
  - Copre f/D 0.5–0.8; centro di fase sull'apertura; VSWR < 1.2.
  - Dimensioni critiche: un raccordo idraulico sbagliato dà il 22% di efficienza. Usare un solo flare (due flare con gradino, come G8ACE a 24 GHz, falliscono). Errore su C di 0.04λ: tollerabile.
  - Banda stretta: un horn da 12 GHz usato a 10.4 GHz va male.
  - Bordo all'apertura sottile, smussato a 45°.
- **Large W2IMU, flare 30° (W1GHZ/W1FKF 2023):**

  | Frequenza | Utensile | D | C | Guadagno | BW−10 (semiangolo) |
  |---|---|---|---|---|---|
  | 10.368 GHz | — | 50.8 mm (1.78λ) | 107 mm (3.7λ) | 13.9 dBi | 35° |
  | 24.192 GHz | #9 | 22.2 mm (1.79λ) | 45.9 mm (3.7λ) | 13.9 dBi | 35° |
  | 47.088 GHz | #5 | 11.1 mm (1.74λ) | 23.6 mm (3.7λ) | 13.9 dBi | 35° |
  | 78 GHz | #3 | 6.35 mm (1.65λ) | 11.2 mm (2.9λ) | 13.1 dBi | 39° |
  | 122 GHz | #2 | 4.76 mm (1.94λ) | 10.5 mm (4.3λ) | 14.6 dBi | 32° |
  | 122 GHz | 4 mm | 4.0 mm (1.63λ) | 7.1 mm (2.9λ) | 13.1 dBi | 39° |
  | 241 GHz | 2 mm | 2.0 mm (1.66λ) | 3.6 mm (2.9λ) | 13.1 dBi | 39° |

  Lavorazione: tornio con punta da centri lunga a 60°.
- **Skobelev "optimum dual-mode".** Gradino 1.016λ → 1.3λ, seguito subito dal flare fino all'apertura.
  - Lunghezza del flare L ≈ 3.45·r_ap − 0.35 (in λ); spesso −10% è meglio.
  - Efficienza 77–81% per f/D da 0.6 a 2.
  - Tabella "BEST" completa (diametro, L, f/D, η, centro di fase, F/B, SLL, guadagno, BW10) in `notes_part2.md`. Esempi: 1.7λ/2.34λ → f/D 0.73 (offset); 2.3λ/3.26λ → 0.98; 5.6λ (47 GHz, 22 dBi) per Cassegrain.
  - L'ingresso da 1.016λ richiede una transizione adattata (flare dolce, gradini o gradino rettangolare).
- **Potter.** Gradino → sezione di fase → cono: calcolo complesso, concentricità a millesimi di λ. **VK2ALU:** W2IMU + cono lungo per f/D ~1.5.
- **Diagonale (Love).** TE10 + TE01. BW3 = 58.5λ/d, BW10 = 101λ/d; flare piccolo (< 30° pieno). Lobi nei piani a 45° (cross-pol). Serve una transizione tonda→quadra lunga.
- **Clavin.** Cavità con fessura risonante, piccolo, a banda stretta; f/D 0.35–0.4; 53% misurato.

### 4.5 Polarizzazione circolare: septum
- Dimensioni note per guida quadra da 0.635λ (Chen & Tsandoulas, foglio OK1DFC). Per guida circolare da 0.71λ si usano gli stessi denti riscalati. In guida circolare serve il setto a gradini; quello a rampa a 30° funziona solo in guida quadra.
- **OK1DFC quadra aperta.** ~61–66% calcolato a f/D 0.35–0.4; cross-pol −21 dB; isolamento ~24 dB.
  - Con flare quadro a 1.1–1.4λ: f/D 0.7–0.85.
  - Con anello circolare (2.0λ di diametro, 0.375λ profondo, 0.175λ dietro): ~74%. L'anello quadro non funziona.
- **Tolleranze.** Denti ±5% e spessore 0.5–6 mm: ininfluenti sul pattern. **Simmetria della guida entro ~1%: critica.** Isolamento limitato dal disadattamento d'apertura e dalla riflessione del dish.
- **Rapporto assiale da valutare su tutto l'angolo del dish:** con anello arretrato (f/D < 0.35) la CP peggiora ai bordi.
- Polarizzatore e sonda **non** fanno parte dell'antenna: simulare l'horn con il modo puro.
- **[ext] A 122–134 GHz** l'1% di simmetria su ~1.6 mm vale ~16 µm. Per la CP a mm-wave meglio guida circolare con polarizzatore a dielettrico o lavorazione EDM/CNC di precisione.

### 4.6 Da evitare
Rear feed (Penny, Clavin 1954, pillbox, DK2RV: dal 30 al 45%), dish con disco piatto sotto ~5λ, raccordi idraulici "simili" a un dual-mode, horn surplus ottimizzati per il guadagno, feed a larga banda (LPA) per la variazione del centro di fase.

---

## 5. Sistemi a due riflettori (fondamentali sopra i 24 GHz per la perdita di linea)

### 5.1 Cassegrain: procedura verificata sui numeri del foglio W1GHZ
1. φ0 = 2·atan(1/(4 f/D_p)); ψ = semiangolo del feed al taper scelto (meglio dal pattern reale).
2. Taper ottimo (curve di Kildal): ~14 dB per dish piccoli, ~11 dB per dish molto grandi (12.4 dB a 84λ).
3. Diametro ottimo del subriflettore (diffrazione = blocking): (d/D)^5 = cos⁴(ψ/2)·E·λ / ((4π)²·sinφ0·D), con E = 10^(−T/10).
4. Distanza tra i fuochi: 2c = (d/2)·(1/tanφ0 + 1/tanψ).
5. Niente blocking da parte del feed se d > √(d_feed·f_p/K), con K = 2c/d (sostituire 2c+PC se c'è il centro di fase).
6. M = tan(φ0/2)/tan(ψ/2); e = (M+1)/(M−1); a = c/e; b = √(c²−a²).
7. Distanze: vertice del sub → fuoco del dish = c − a; vertice → centro di fase del feed = c + a. Profilo: y = b·√(x²/a²−1).
8. Il sub deve stare nel campo lontano del feed: c + a > 2·d_feed²/λ (metà è tollerabile).
9. Efficienza ≈ η_feed (alla f/D equivalente) × η_sub (Kildal; ~0.8–0.88). Meglio verificare con PO/GTD.

- **Regole:** sub ≥ 10λ, d/D ≤ 0.2, quindi dish ≥ ~40–50λ. Il sub non dipende dalla frequenza; feed diverso per ogni banda.
- **Realizzati:**
  - 122 GHz: Edmund 305 mm f/D 0.25, sub 38 mm (14.8λ), large W2IMU → ~50%.
  - 47 GHz: dish 300 mm f/D 0.6, sub 76 mm, Skobelev 5.6λ dietro il dish → 40 dBi, ~50%.
  - Progetti: 10 GHz 1.2 m; 47 GHz Edmund 609 mm (sub 20λ); 3 m per 24/47 GHz (sub 240 mm).
- **Costruzione:** sub da tornio CNC (G-code) o stampato 3D e metallizzato. Si misura togliendo il sub e confrontando con il solo feed. Feed: large W2IMU o Skobelev; Pickett-Potter (WA6KBL).
- **Gregorian:** sub ellittico concavo, stesso schema (Granet 1998 dà tutte le combinazioni di parametri).

### 5.2 Subriflettore piano
- Feed rovesciato speculare; costa 1–2 dB rispetto al prime-focus su dish da 15–25λ.
- Diametro ottimo del disco ~5λ (dipende dal feed).
- Un Cassegrain piccolo non vale la fatica, salvo per illuminare un dish molto profondo.

---

## 6. Aspetti specifici 10–134 GHz [ext, salvo dove indicato]
| Banda | λ | Guida rettangolare tipica | Guida circolare 0.71–0.81λ |
|---|---|---|---|
| 10.368 GHz | 28.9 mm | WR-90 (22.86×10.16), WR-75 | 20.5–23.4 mm (rame 3/4", W1GHZ) |
| 24.192 GHz | 12.4 mm | WR-42 (10.67×4.32) | 8.8–10.0 mm |
| 47.088 GHz | 6.37 mm | WR-22 (5.69×2.84), WR-19, WR-28 (W1GHZ) | 4.5–5.2 mm |
| 76–81 GHz | 3.85 mm | WR-12 (3.10×1.55), WR-10 | 2.7–3.1 mm |
| 122.25 GHz | 2.45 mm | WR-8 (2.03×1.02) | 1.74–1.98 mm |
| 134 GHz | 2.24 mm | WR-8 (fino a 140 GHz) o WR-6 (1.65×0.83) | 1.59–1.81 mm |

- **Linea di alimentazione.** Sopra i 24 GHz la perdita di guida e coassiale è proibitiva, quindi apparato al feed: offset (fuori fascio) o Cassegrain (dietro il dish).
- **Tolleranze tipiche (λ a 134 GHz = 2.24 mm):**
  - lunghezza di fase del dual-mode ±0.04λ → ±0.09 mm;
  - superficie del dish per −0.5 dB (Ruze) → ε_rms ≈ 0.027λ → 0.06 mm;
  - posizione del feed ±λ/8 → ±0.28 mm su un dish profondo.
- **Fabbricazione:** tornio con punte da centri (flare 30°), CNC, EDM per septum e corrugazioni, stampa 3D metallizzata per il subriflettore. Rugosità ≪ profondità di pelle (rame a 134 GHz ≈ 0.18 µm) per perdite basse.
- **Dish.** Edmund Optics (f/D 0.25, quasi ottici) → Cassegrain. Offset TV: ottimi fino a ~76 GHz (superficie ±0.2 mm), ma a 122 GHz perdono ~10 dB (OE2IGL) → sopra i 100 GHz usare dish da link 38 GHz o tornio (±0.03 mm). A 122 GHz un dish da 305 mm (122λ) è già al limite del puntamento.
- **Misure.** Sun noise con RTL-SDR + TotalPower (I0NAA). Test del Cassegrain togliendo il subriflettore. Range: Rayleigh 2D²/λ.

---

## 7. Metodi di simulazione (scelte di W1GHZ e opzioni moderne)
- **NEC2 (MoM).** Fili e patch; horn costruiti come strisce di patch ruotate (18 lati). La fase si legge dalla tabella RADIATION PATTERN. Lento oltre ~3000 segmenti.
- **Ottica fisica (Milligan & Diaz).** Per horn grandi e dish. Accurata nell'emisfero anteriore; dietro dà lobi spuri a ±150° e un nullo a 180°: la potenza posteriore si ricava per conservazione dell'energia.
- **FDTD/FEM (Zeland Fidelity, HFSS).** Per near-field, septum, choke. Un dish da 15λ richiede ~30 GB di RAM.
- **Opzioni open source [ext]:**
  - **openEMS** (FDTD, interfaccia Python/Octave) per il full-wave dei feed;
  - **scuff-em**, **Elmer**, **Palace** (FEM);
  - **nec2c** per i fili;
  - **PO proprietaria** in NumPy per il riflettore;
  - **mode matching** (gradini e coni di guida circolare) come metodo veloce per dual-mode e corrugati.
- **Validazione:** confrontare con i pattern misurati dell'archivio FEEDPATT e con le misure (sun noise) del libro.

---

## 8. Lacune e cose da verificare
1. Le dimensioni dei denti del septum (Chen & Tsandoulas / foglio OK1DFC) non sono pubblicate sul sito: vanno prese dal paper originale o dal foglio OK1DFC.
2. Formula di efficienza del subriflettore di Kildal: il testo PDF è illeggibile. Si conosce solo il comportamento all'ottimo (~3·C_b·(d/D)²). Meglio sostituirla con PO.
3. Gregorian: le formule di Granet non sono nel materiale; vanno implementate dal paper.
4. Tabelle di simulazione Super-VE4MA/Chaparral (appendici B/C, MUD 2006): nel PDF sono illeggibili. Le conclusioni sono riportate sopra; per i valori puntuali servono i PDF originali o una ri-simulazione.
5. Comportamento a 134 GHz: nessuna misura W1GHZ (solo progetti a 122 e 241 GHz) → verificare con simulazione full-wave.

---

## 9. Integrazioni da OE2IGL (wettersat.bplaced.net), dettagli in `notes/notes_part3_OE2IGL.md`
- **Catena gratuita.** openEMS (FDTD, mesh λ/60) per il feed, poi GRASP-SE con feed gaussiano o "tapered" per il riflettore: entro 0.1 dB dalla versione GRASP completa.
- **Efficienze raggiungibili:** W2IMU e Pickett-Potter ~78–81% (f/D 0.55–0.8); cavity feed fino a 83% (f/D 0.35–0.5); corrugato assiale a 8 gole 81–86% (f/D 0.33–0.9).
- **Scelta del feed per banda:** fino a 47 GHz il corrugato assiale è facile da costruire; da 76 GHz in su Pickett-Potter per l'offset, cavity feed per il prime-focus.
- **Design guide con polinomi in funzione dell'angolo di apertura** (W2IMU, Pickett-Potter, corrugato): implementate in `feedlab.horns`. Si usa l'angolo di apertura, non la f/D.
- **Verifica incrociata indipendente.** Skobelev (tabella W1GHZ) per f/D 0.7 a 10.368 GHz: 1.662λ / 2.28λ. Pickett-Potter OE2IGL: 1.660λ / 2.34λ. Le due fonti concordano.
- **Offset (Stutzman/Milligan).** Si punta il feed per bilanciare i taper ai bordi: ψ_F = ψ_L + ΔFT·BW/(4.01(2ET−ΔFT)) + ψ_S. Si punta verso il punto più profondo, non verso il centro geometrico.
- **Formule chiuse** (gaussiano, cos^2N, blocking di Baars, defocus di Milligan, T_sky con correzione di Planck, beam factor) in `feedlab.reflector` e `feedlab.noise`.
- **Riferimento teorico libero e legale:** P.-S. Kildal, *Foundations of Antenna Engineering* (kildal.se, download gratuito).

## 10. 24 GHz EME: W5LUA 2012 and VK3UM, dettagli in `notes/notes_part4_W5LUA_24GHz_EME.md`
- **Feed W2IMU modificato di W5LUA** (2.4 m offset, f/D 0.7): FeedLab lo simula con S11 −34 dB e centro di fase 1–3 mm dietro la fine del cilindro (W5LUA: ~2.54 mm). L'efficienza è 64–72% con taper 17–21 dB: sottoilluminazione voluta per il G/T.
- **Equazioni EME verificate sui valori VK3UM:**
  - perdita di percorso EME (ρ 0.065), 295.24 dB a 24.048 GHz e 356 400 km;
  - spazio libero, guadagno e area efficace;
  - fattore di riempimento del fascio per Sole e Luna, x²/(1−e^(−x²));
  - rumore di Luna (2.23 dB) e di Sole (12.8 dB);
  - assorbimento obliquo A_zen/sin(el) e rumore del cielo con T_atm 280 K.
  Funzioni in `feedlab.noise`, test in `tests/test_w5lua.py`.

