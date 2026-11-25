# EMELab — fonti (da citare nei Credits)

## Doug McArthur VK3UM (SK 22/02/2016) — programmi conservati da John Drew VK5DJ
https://www.vk5dj.com/doug.html — archivio con l'approvazione di Bev, moglie di Doug. Programmi Windows (Delphi 32 bit):
- **EMECalc** 11.11: eco proprie, eco da/verso un'altra stazione, rumore di sole, luna e galattico; «How to…» per scegliere
  la combinazione parabola/feed e valutare una parabola più grande.
- **EME Planner** 2.18: tracciamento, database DXCC/stazioni, finestra mutua, offset spaziale, sorgenti e pianeti, mappa del
  rumore di cielo dietro la sorgente, distanza, Luna (distanza, perdita aggiuntiva, diametro, librazione, illuminazione,
  fase); calcoli di VK5DJ basati su Duffett-Smith e Meeus.
- **Libration Calculator** 1.15: ora di librazione minima per casa e DX, ritmi di librazione (°/min), spread di casa, del DX e
  del DX visto da casa, 432 MHz–122 GHz, offset spaziale, finestre comuni, Doppler, pianificazione su giorni/mesi/anni,
  perdita rispetto al perigeo. Ispirato a **G3WDG, DUBUS 3/2010** (beta: VE4MA, W5LUA, G4RGK, VK5DJ).
- **Atmosphere** 1.25: attenuazione O₂/H₂O (+ pioggia, nebbia, nubi) 10–241 GHz, percorsi terrestri e obliqui, metodi ITU.
- Noise Source Planner, EMRCalc (esposizione RF, ICNIRP), AutoTrack, filtri interdigitali, linee di trasmissione.
- Documento «Sun noise and measurements» di VK3UM: https://www.yumpu.com/en/document/view/6598425/sun-noise-and-measurements-vk3um

## Gerald Ihninger OE2IGL e Joachim Köppen DF3GJ — EME Link Budget & Analysis Tool (1–300 GHz)
https://wettersat.bplaced.net/EME/EME.html (v261024)
- Equazione radar: P_RX = P_TX·G_TX·G_RX·λ²·A·ε / (64π³·d_TX²·d_RX²), A = πR²_Luna, ε ≈ 0.07 (Evans 1969, eq. 2).
- Beam Width Factor = illuminata(HPBW_TX) × sovrapposizione(HPBW_TX, HPBW_RX); due fasci uguali più stretti della Luna:
  sovrapposizione 0.5 (−3 dB).
- Sole (disco ottico 32'): 10368 MHz 12950 K / 292 SFU; 24048 MHz 10475 K / 1270 SFU; 47088 MHz 8840 K / 4110 SFU;
  76032 MHz 7840 K / 9500 SFU; 122250 MHz 6960 K / 21800 SFU; 241920 MHz 5860 K / 71800 SFU (curva di A.O. Benz).
- Temperatura della Luna: modello termico del suolo con correzione al bordo fino a 300 GHz (DF3GJ, LunarTemps.html);
  riflettività media, altipiani, mari, crateri; variazione radiale (fit DF3GJ).
- Atmosfera ITU-R P.676-13; nubi: 47 GHz 0.04/0.085/0.85 dB/km, 76 GHz 0.09/0.17/1.74 dB/km (nebbia leggera / 300 m / 50 m);
  pioggia dB/km (0.1/1/10/100 mm/h): 10 GHz 0.0007/0.01/0.21/3.7; 24 GHz 0.014/0.14/1.4/14; 47 GHz 0.09/0.59/3.9/25.7;
  76 GHz 0.2/1.1/5.8/30.4.
- Puntamento: buono ±0.035°, standard ±0.1°; perdite Ruze, griglia (Otoshi), polarizzazione, fuori fuoco assiale/laterale.
- Modi e soglie: Q65-60E, Q65-60D, Q65-120E, SSB, CW; margine = S/N EME − soglia del decoder.
- Rifrazione radio A.L. Berman; stazioni di riferimento «LOCATOR - CALL-BAND» (≈ 90, bande 1.3–76 GHz).
- Rimandi: J.V. Evans «Radar Studies of the Moon» (J. Res. NBS 69D, 1965/69); moonbounce.dk (skytemp, suncalc);
  NOAA SWPC solar_radio_flux.txt; strumenti DF3GJ (portia.astrophysik.uni-kiel.de/~koeppen/).

## Da procurare
- G3WDG, DUBUS 3/2010 (librazione e spread).
