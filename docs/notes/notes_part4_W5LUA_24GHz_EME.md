# W5LUA — The Excitement & Challenges of 24 GHz EME (2012)

Presentazione di Al W5LUA del 17 agosto 2012, 46 slide. Serve come riferimento sulle stazioni EME a 24 GHz e per verificare le equazioni di rumore e di percorso di FeedLab sui programmi di VK3UM.

## Dati di stazione
- **Parabole e feed:**
  - offset da 2.4 m (W5LUA, VE4MA, RW3BP, DF1OI con subriflettore), offset da 1.8 m (OZ1FF), prime focus da 3 m (LX1DB, il primo W5LUA su Andrew);
  - relè in WR-42, LNA sul feed con raffreddamento Peltier.
- **Trasmettitore:** TWT TH-3864 da 100 W.
- **Primo QSO:** VE4MA–W5LUA, 18 agosto 2001.
- **Frequenza:** 24.048 GHz.
- **Polarizzazione:** lineare, H in Nord America e V in Europa. A 24 GHz non c'è rotazione di Faraday: conta solo lo spatial offset.

## Feed W2IMU modificato di W5LUA (24 GHz, offset 2.4 m, f/D 0.7)
WR-42 → transizione da 38 mm → Ø11.1 mm → cono θ ≈ 23° su 15.62 mm → cilindro Ø23.6 mm lungo 48.3 mm → flare di 40.6 mm assiali (48.3 mm sul fianco) fino all'apertura Ø76.2 mm.
Centro di fase: "~0.1 in (2.54 mm) dietro la faccia dell'horn".

**Verifica con FeedLab** (mode matching + integrazione sull'apertura, `tests/test_w5lua.py`):
- S11 −34 dB, bilancio energetico 1.000;
- la miscela TM11/TE11 è generata dal cono;
- centro di fase 1–3 mm dietro la fine del cilindro per f/D 0.7–0.8 (W5LUA: ~2.54 mm);
- efficienza circa 64% a f/D 0.7 e 72% a f/D 0.8, con taper al bordo di 21–17 dB.

La parabola offset con f/D 0.7 equivale a una prime focus con f/D 0.78–0.81: il feed sottoillumina apposta, per il G/T (W1GHZ). La schermata VK3UM ipotizza η = 66%.

## Numeri VK3UM e formule di FeedLab
| Grandezza | VK3UM (slide) | FeedLab | Formula |
|---|---|---|---|
| Perdita di percorso EME, 24.048 GHz, 356 400 km | 295.24 dB | 295.24 dB | `noise.eme_path_loss_db`, ρ = 0.065, R = 1737.4 km |
| Perdita in spazio libero | 231.11 dB | 231.11 dB | `noise.free_space_loss_db` |
| Guadagno 2.4 m, η 66% | 53.83 dBi | 53.83 dBi | η(πD/λ)² |
| Area efficace | 2.99 m² | 2.99 m² | η·πD²/4 |
| Larghezza del fascio (HPBW) | 0.36° | 1.21·λ/D | VK3UM usa b ≈ 1.21; `reflector.hpbw_deg` usa il b di Baars (1.14 a 10 dB di taper, 1.21 a ~15 dB) |
| Riempimento del fascio, Luna (0.559°, fascio 0.36°) | 2.06 | 2.06 | K = x²/(1−e^(−x²)), x² = ln2·(θs/θb)² |
| Riempimento del fascio, Sole | 1.98 | 1.97 | stessa formula, Sole 0.54° |
| Y Luna (213 K, Tsys 221.1 K) | 2.23 dB | 2.23 dB | ΔT = T·Ω·Ae/(λ²K) |
| Y Sole (732 SFU a 24 GHz) | 12.8 dB | 12.82 dB | ΔT = S·Ae/(2k)/K |
| Attenuazione obliqua a 45/20/5° | 0.5346/1.1053/4.3376 dB | uguale entro 0.01% | A_zen/sin(el), con A_zen = 0.378 dB |
| Rumore del cielo a 45/20/5° | 32.43/62.92/176.90 K | uguale | (1−10^(−A/10))·T_atm, T_atm = 280 K |
| Differenza apogeo–perigeo | "quasi 2 dB" | 2.29 dB | 40·log(d_a/d_p) |

**Zenit di VK3UM.** Il programma mostra un'attenuazione allo zenit di 0.4549 dB, somma di aria secca e vapore. I suoi valori obliqui, però, seguono tutti uno zenit di 0.378 dB. La legge 1/sin(el) quindi è rispettata, ma il valore di zenit mostrato non è quello usato per il percorso obliquo.

**T_atm predefinita.** FeedLab usa per default T_atm = 0.81·T_amb + 37.4, cioè 270–272 K a 15–17 °C, contro i 280 K di VK3UM. La differenza sul rumore del cielo è di circa il 3%. `noise.sky_temp(..., t_atm=280)` riproduce VK3UM.

## Altri dati della presentazione
- **Temperatura della Luna a 1.25 cm:** circa 200 K a Luna nuova e circa 280 K qualche giorno dopo la piena (Kraus, *Radio Astronomy*, 1966, fig. 8-28). Il massimo arriva con circa 3.5 giorni di ritardo rispetto all'infrarosso.
- **Atmosfera a 24 GHz:** perdite combinate delle due stazioni di 1.07 dB con entrambe a 45°, 2.2 dB a 20°/20° e 5.4 dB a 20°/5°.
- **Doppler:** Doppler reciproco = (self Doppler A + self Doppler B)/2. Esempio: +56.9 e +8.5 kHz danno +32.7 kHz.
