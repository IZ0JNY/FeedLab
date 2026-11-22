# FeedLab — Manuel d'utilisation

**Laboratoire de conception de sources/illuminateurs hyperfréquences**
Version {VERSION} BETA TEST · Ivan De Cesaris, IZ0JNY · ivan@iz0jny.it

---

## 1. Qu'est-ce que FeedLab
FeedLab sert à **concevoir, simuler et construire des sources (feeds) pour paraboles** de **10 à 134 GHz**. Avec FeedLab :
- tu choisis la parabole (catalogue du commerce ou la tienne) et la bande ;
- tu obtiens la source la mieux adaptée avec ses cotes ;
- tu vois diagramme, rendement, S11, gain et G/T ;
- tu modifies les cotes et vois tout de suite si le résultat s'améliore, en TX, RX ou EME ;
- tu produis le **plan mécanique PDF** et les fichiers **.stp** / **.stl** pour l'atelier ;
- tu conçois la **plaque λ/4** de passage au guide rectangulaire WR, avec trous, taraudages et goupilles ;
- tu vérifies la conception avec **openEMS** (facultatif) et la corriges automatiquement.

Les calculs reposent sur le *W1GHZ Online Microwave Antenna Book* (Paul W1GHZ), les design guides de Gerald OE2IGL, les livres de Balanis et Kildal et les travaux d'Al W5LUA, Jeff WA6KBL, Sergei RW3BP, Luis CT1DMK, Mirek OK2AQ et Ivan IZ0JNY. La liste complète se trouve dans la fenêtre **ℹ️ Credits**.

## 2. Version BETA TEST
C'est une **version d'essai** : elle est valable **30 jours à partir de la première installation**, puis elle se désactive.
- À chaque démarrage, une **fenêtre** indique la date d'expiration et les jours restants : ferme-la avec **OK**.
- Après expiration, FeedLab n'affiche que l'avis et un lien vers la page **Releases** de GitHub : télécharge et installe la dernière version.
- Chaque nouvelle version a ses propres 30 jours. Si l'horloge du PC est reculée, la version est considérée comme expirée.

![Fenêtre BETA TEST]({IMG}/00_beta.png)

## 3. Installation
### Windows (conseillé)
1. Télécharge la dernière version depuis la page **Releases** du dépôt GitHub (IZ0JNY/FeedLab).
2. **Installateur :** lance `FeedLab-Setup-x.y.z.exe`. Aucun droit administrateur n'est nécessaire. FeedLab apparaît ensuite dans le menu Démarrer.
3. **Version portable :** extrais `FeedLab-x.y.z-portable.zip` dans un dossier et double-clique sur `FeedLab.bat`. Rien n'est installé dans le système.

FeedLab s'ouvre dans sa propre fenêtre (Microsoft Edge WebView2, inclus dans Windows 11). Sans WebView2, il s'ouvre dans le navigateur.

### Linux / macOS (depuis les sources)
```
pip install -e .
feedlab-gui
```

### Langue
En haut de la barre latérale : **Lingua / Language**. Il y a sept langues : Italiano, English, Deutsch, Français, Español, Русский, Português. L'installateur demande la langue ; le bouton **📖 Manuel** ouvre le manuel dans la langue choisie.

## 4. La barre latérale
| Élément | Usage |
|---|---|
| **Bande** | fréquence de travail (bandes radioamateur 10–134 GHz ou *Autre fréquence…*) |
| **λ** | longueur d'onde correspondante |
| **Parabole / Source** | résumé du choix fait dans l'assistant |
| **Matériau de la source** | cuivre, cuivre argenté, laiton, aluminium, impression 3D métallisée… : FeedLab calcule pertes et bruit ajouté |
| **Collier Ø40 mm** | ajoute le collier pour les supports LNB du commerce |
| **ℹ️ Credits** | auteur, version et toutes les sources |
| **📖 Manuel** | télécharge ce manuel en PDF |
| **🐞 Signaler un problème** | ouvre la page GitHub des signalements avec version et projet déjà remplis |

## 5. Assistant
![Assistant]({IMG}/01_wizard.png)

1. **Parabole :**
   - *catalogue* : Gibertini, Triax, Fracarro, Fuba, Kathrein, Channel Master/Andrew, Prodelin, Edmund et d'autres, avec la source de chaque donnée ;
   - *parabole personnalisée* : offset ou foyer primaire.
2. **Données de la parabole personnalisée :**
   - offset : à partir de diamètre + f/D, diamètre + focale, **mesures sur le terrain** (grand axe, petit axe, profondeur) ou angle d'illumination ;
   - foyer primaire : à partir de f/D ou de la profondeur.
3. **Polarisation, objectif et fabrication :** linéaire ou circulaire ; **gain** (TX) ou **G/T** (RX/EME) ; tour ou tôle.
4. **🔎 Trouver la meilleure source :** FeedLab compare les sources adaptées et les classe par rendement estimé, avec raisons et avertissements.
5. **✅ Utiliser cette source :** les autres onglets travaillent sur cette conception.

![Résultat de l'assistant]({IMG}/02_wizard_result.png)

**Si la focale n'est pas publiée** (cas de nombreuses paraboles Kathrein et Channel Master), le catalogue l'indique. Utilise les *mesures sur le terrain* : tends un fil le long du grand axe et mesure la profondeur au centre.

### 5.1 Types de sources
| Source | Quand l'utiliser |
|---|---|
| **Corrugué axial 8 gorges (Gerald OE2IGL)** | 10–76 GHz, f/D 0.33–0.9 (offset jusqu'à 0.8) : 81–86 %, la plus efficace ; cotes du tableur v1.4 en fonction de l'angle d'ouverture |
| **W2IMU, Pickett-Potter, Skobelev, Large W2IMU** | bimode pour offset et f/D 0.5–0.95 ; Pickett-Potter et grand W2IMU aussi au-delà de 76 GHz |
| **Super-VE4MA, Chaparral, guide ouvert** | paraboles profondes à foyer primaire (f/D < 0.5) |
| **Cornet conique f/D 0.6 / cornet corrugué f/D 0.8 (Mirek OK2AQ)** | sources pour offset conçues à 24.048 GHz et mises à l'échelle en λ pour les autres bandes ; le corrugué est déduit du plan : vérifie-le avec openEMS |
| **Cornet rectangulaire** | polarisation linéaire seulement, alimenté directement par guide WR |

Les sources pour 1296 MHz (par exemple le septum de Zdeněk OK1DFC) sont hors du domaine de FeedLab, qui commence à 10 GHz.

## 6. Conception de la source
Affiche les cotes (mm et λ), la coupe axiale et la règle de conception utilisée (W1GHZ, OE2IGL, Skobelev…). Les cotes se modifient à la main. Pour le corrugué axial, on modifie le pas, la largeur des gorges, le gradin, les diamètres et les profondeurs d1…d8.

![Conception de la source]({IMG}/03_design.png)

## 7. Laboratoire
C'est ici qu'on « joue » avec les cotes.

![Laboratoire]({IMG}/04_lab.png)

**Scénario d'usage :** objectif **TX** (gain), **RX** (G/T) ou **EME** (gain + G/T) ; élévation, NF du LNA, perte de ligne, rugosité de surface, atténuation au zénith.

**Curseurs des cotes :** à chaque modification, FeedLab recalcule rendement, gain, G/T, température d'antenne, S11, taper au bord et la variation du **rapport S/B** :

| Objectif | Variation de S/B |
|---|---|
| TX | ΔSNR = ΔG |
| RX | ΔSNR = Δ(G/T) |
| EME | ΔSNR = ΔG + Δ(G/T) |

**Conseils** en clair, **sensibilité** de chaque cote et **optimisation automatique** avec une limite de S11.

### 7.1 Tolérances d'usinage et rendement de fabrication
![Tolérances]({IMG}/05_tolerances.png)
1. **Paramètres :** tolérance de l'atelier (±mm) ; distribution *uniforme* (prudente) ou *normale avec ±t = 3σ* (CNC capable) ; perte admise et S11 maximal.
2. **🎲 Analyser les tolérances :** FeedLab simule des milliers de pièces et donne le **rendement** (pièces bonnes), la perte moyenne, la dispersion du rendement, le pire S11 et les **cotes critiques** avec la **tolérance conseillée** pour chacune.
3. **📄 Utiliser ces tolérances dans le dessin PDF :** ajoute le tableau des tolérances au plan.
4. **🛡️ Optimisation robuste :** cherche des cotes qui restent bonnes *dans les tolérances* (moyenne − k·σ). Utile au-delà de 47 GHz.

## 8. Simulation & S11
![Simulation]({IMG}/06_simulation.png)
- **S11** dans la bande avec le solveur rapide par *raccordement modal*.
- **Modes à l'ouverture :** pour Pickett-Potter et Skobelev aussi le rapport **TM11/TE11** (environ 15 %, WA6KBL).
- **Diagramme** polaire et cartésien, plans E et H, avec la phase.
- **Rendement de la parabole** en fonction de f/D : spillover, illumination, phase et polarisation.
- **Centre de phase** et G/T.

Le solveur rapide ne traite pas les sources à anneaux ou à gorges (VE4MA, Chaparral, corruguées) : pour celles-ci, FeedLab utilise le rendement publié par l'auteur et conseille openEMS.

## 9. Diagramme 3D et modèle 3D
![Diagramme 3D]({IMG}/07_lobe3d.png)
![Modèle 3D]({IMG}/08_model3d.png)

## 10. Plan & STEP
![Plan et STEP]({IMG}/09_drawing.png)
- **📄 Créer le PDF :** plan mécanique A4 avec coupe cotée, tableau des cotes (mm et λ), cartouche et tolérances générales. Avec les tolérances par cote (§7.1), il inclut leur tableau ; avec les trous de fixation (§11), une **feuille 2** montre la bride percée.
- **🧊 Créer le STEP :** fichier `.stp` pour CNC/CAO. Les trous taraudés sont au diamètre d'avant-trou ; le filetage est indiqué dans le PDF.
- **🖨️ Créer le STL :** pour l'impression 3D.

## 11. Plaque WR
![Plaque WR]({IMG}/10_plate.png)

La **plaque λ/4** relie le guide circulaire de la source au guide rectangulaire WR. L'orientation du WR fixe la **polarisation verticale ou horizontale** (design guide OE2IGL, optimisation HB9PZK).

1. **Données :** guide WR, polarisation, Ø du guide circulaire, rayon de la fraise dans les angles.
2. **Résultat :** ouverture a × b, épaisseur (avec tolérance) et Z0 intermédiaire.
3. **Trous de fixation guide → plaque → source**, avec vis **métriques** ou **en pouces** :
   - le perçage de la **bride standard** (Flann / MIL-DTL-3922) est **taraudé dans la plaque** ;
   - **4 vis plaque → source** avec la **tête dans un lamage** côté guide, pour que la face vers le guide reste plane ;
   - **goupilles de centrage** à partir de **47 GHz** ;
   - brides rondes UG-383/385/387 : trous pour les goupilles du guide et filetage 4-40 ;
   - si la plaque est trop mince, FeedLab épaissit son corps et creuse côté source une **poche** du diamètre du guide circulaire.
4. Le même perçage est appliqué à la **bride de la source**.

![Plan de la plaque à 47 GHz](img/plate_drawing_47GHz.png)
![Bride de la source percée, feuille 2](img/feed_flange_47GHz.png)

**Vérifie toujours les cotes avant de percer**, y compris les têtes de vis (ISO 4762) par rapport aux vis que tu achètes.

## 12. Full-wave openEMS (facultatif)
![openEMS]({IMG}/11_openems.png)
openEMS est un solveur FDTD gratuit. Une simulation dure de quelques minutes à quelques heures et tourne en arrière-plan : tu peux fermer FeedLab.

| Sous-onglet | Usage |
|---|---|
| ① **Installation** | installation guidée d'openEMS et de sa liaison Python, avec test final |
| ② **Nouvelle analyse** | calcul simple, convergence du maillage, balayage d'un paramètre ; estimation de durée et de RAM |
| ③ **Simulations** | avancement, arrêt, journal |
| ④ **Résultats** | S11/TOS, diagrammes co- et contra-polaires, centre de phase, rendement, G/T, comparaison avec le modèle rapide ; rapport HTML, CSV et `.dat` W1GHZ |
| ⑤ **Space mapping** | correction automatique du modèle rapide avec openEMS |

**Space mapping :** openEMS vérifie un candidat, l'écart entre openEMS et le modèle rapide corrige le modèle rapide et FeedLab propose le candidat suivant, jusqu'à convergence. Ensuite *✅ Appliquer le meilleur à la conception*.

![Space mapping]({IMG}/12_spacemap.png)

## 13. Démarche conseillée
1. **Assistant :** parabole, bande, objectif → source.
2. **Laboratoire :** affine les cotes en regardant ΔS/B, puis l'optimisation automatique.
3. **Tolérances :** demande sa tolérance à l'atelier et analyse le rendement de fabrication.
4. **(Facultatif) openEMS :** vérification ou space mapping (indispensable pour les sources corruguées et à anneaux).
5. **Plaque WR :** polarisation, trous de fixation, PDF et STEP.
6. **Plan & STEP de la source** à l'atelier.
7. **Sur le terrain :** mesure le bruit solaire et compare-le à la valeur attendue.

## 14. Limites connues
- **Solveur rapide :** modélise l'ouverture comme une bride et ne traite ni anneaux ni gorges. Utilise openEMS pour ceux-ci.
- **Rendements :** ce sont des valeurs calculées. Sur une vraie parabole, compte 12 à 15 points de moins ; les *différences* entre variantes sont fiables.
- **Catalogue de paraboles :** certaines focales sont des estimations (indiquées comme telles). Mesure ta parabole.
- **Polarisation circulaire :** le polariseur (septum ou diélectrique) n'est pas encore conçu par FeedLab.

## 15. Signaler un problème
Appuie sur **🐞 Signaler un problème** dans la barre latérale : GitHub s'ouvre avec version, système et projet déjà écrits. Décris ce qui s'est passé, ce que tu attendais et comment le reproduire.

## 16. Sources principales
![Credits]({IMG}/13_credits.png)
- **Paul W1GHZ :** W1GHZ Online Microwave Antenna Book.
- **Gerald OE2IGL :** design guides, source corruguée axiale v1.4 ; **HB9PZK**.
- **Livres :** C. A. Balanis, *Antenna Theory* ; P.-S. Kildal, *Foundations of Antenna Engineering*.
- **Articles :** Al W5LUA, Jeff WA6KBL (DUBUS), Sergei RW3BP, Luis CT1DMK, Luis CT1DMK et Willi LX1DB, Mirek OK2AQ, Ivan IZ0JNY.
- **Brides :** Flann Microwave, *Waveguide and Flange Data* ; MIL-DTL-3922/67C.
- **Logiciels :** openEMS ; CadQuery / OpenCascade ; Streamlit ; Plotly ; NumPy / SciPy.

La liste complète se trouve dans la fenêtre **ℹ️ Credits**.
