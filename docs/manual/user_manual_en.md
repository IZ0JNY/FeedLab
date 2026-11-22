# FeedLab — User Manual

**Microwave feed/illuminator design laboratory**
Version {VERSION} BETA TEST · Ivan De Cesaris, IZ0JNY · ivan@iz0jny.it

---

## 1. What FeedLab is
FeedLab is for **designing, simulating and building dish feeds** from **10 to 134 GHz**. With FeedLab you:
- choose the dish (commercial catalogue or your own) and the band;
- get the most suitable feed with its dimensions;
- see pattern, efficiency, S11, gain and G/T;
- change dimensions and see at once whether the result improves, for TX, RX or EME;
- produce the **mechanical PDF drawing** and the **.stp** / **.stl** files for the workshop;
- design the **λ/4 plate** to the rectangular WR waveguide, with holes, threads and pins;
- check the design with **openEMS** (optional) and correct it automatically.

The calculations are based on the *W1GHZ Online Microwave Antenna Book* (Paul W1GHZ), Gerald OE2IGL's design guides, the books by Balanis and Kildal and the work of Al W5LUA, Jeff WA6KBL, Sergei RW3BP, Luis CT1DMK and Ivan IZ0JNY. The full list is in the **ℹ️ Credits** window.

## 2. BETA TEST version
This is a **test version**: it is valid for **30 days from the first installation**, then it deactivates.
- At every start a **popup** shows the expiry date and the days left: close it with **OK**.
- After expiry FeedLab only shows the notice and a link to the GitHub **Releases** page: download and install the latest version.
- Each new version gets its own 30 days. If the PC clock is moved back, the version counts as expired.

![BETA TEST popup]({IMG}/00_beta.png)

## 3. Installation
### Windows (recommended)
1. Download the latest version from the **Releases** page of the GitHub repository (IZ0JNY/FeedLab).
2. **Installer:** run `FeedLab-Setup-x.y.z.exe`. No administrator rights are needed. FeedLab then appears in the Start menu.
3. **Portable version:** extract `FeedLab-x.y.z-portable.zip` to a folder and double-click `FeedLab.bat`. Nothing is installed on the system.

FeedLab opens in its own window (Microsoft Edge WebView2, included in Windows 11). Without WebView2 it opens in the browser.

### Linux / macOS (from source)
```
pip install -e .
feedlab-gui
```

### Language
At the top of the sidebar: **Lingua / Language** (Italiano or English). The installer asks for the language; the **📖 Manual** button opens the manual in the chosen language.

## 4. The sidebar
| Item | Use |
|---|---|
| **Band** | operating frequency (amateur bands 10–134 GHz or *Other frequency…*) |
| **λ** | corresponding wavelength |
| **Dish / Feed** | summary of the choice made in the wizard |
| **Feed material** | copper, silver-plated copper, brass, aluminium, metallised 3D print…: FeedLab computes losses and added noise |
| **Ø40 mm collar** | adds the collar for commercial LNB holders |
| **ℹ️ Credits** | author, version and all sources |
| **📖 Manual** | downloads this manual as PDF |
| **🐞 Report a problem** | opens the GitHub issues page with version and design already filled in |

## 5. Wizard
![Wizard]({IMG}/01_wizard.png)

1. **Dish:**
   - *catalogue*: Gibertini, Triax, Fracarro, Fuba, Kathrein, Channel Master/Andrew, Prodelin, Edmund and others, with the source of every figure;
   - *custom dish*: offset or prime focus.
2. **Custom dish data:**
   - offset: from diameter + f/D, diameter + focal length, **field measurements** (long axis, short axis, depth) or illumination angle;
   - prime focus: from f/D or depth.
3. **Polarisation, goal and tools:** linear or circular; **gain** (TX) or **G/T** (RX/EME); lathe or sheet metal.
4. **Find the best feed:** FeedLab compares the suitable feeds and ranks them by estimated efficiency, with reasons and warnings.
5. **Use this feed:** the other tabs work on that design.

![Wizard result]({IMG}/02_wizard_result.png)

**If the focal length is not published** (as for many Kathrein and Channel Master dishes), the catalogue says so. Use *field measurements*: stretch a string along the long axis and measure the depth at the centre.

### 5.1 Feed types
| Feed | When to use it |
|---|---|
| **Axial Corrugated (base concept Luis CT1DMK, improved version Gerald OE2IGL)** | 10–76 GHz, f/D 0.33–0.9 (offset up to 0.8): 81–86%, the most efficient; dimensions from Gerald OE2IGL's v1.4 spreadsheet as a function of the opening angle |
| **W2IMU, Pickett-Potter, Skobelev, Large W2IMU** | dual-mode for offset dishes and f/D 0.5–0.95; Pickett-Potter and large W2IMU also above 76 GHz |
| **Super-VE4MA, Chaparral, open waveguide** | deep prime-focus dishes (f/D < 0.5) |
| **Rectangular horn** | linear polarisation only, fed directly from WR waveguide |

1296 MHz feeds (for example Zdeněk OK1DFC's septum) are outside FeedLab's range, which starts at 10 GHz.

## 6. Feed design
Shows the feed dimensions (mm and λ), the axial section and the design rule used (W1GHZ, OE2IGL, Skobelev…). Dimensions can be edited by hand. For the Axial Corrugated feed you edit pitch, slot width, step, diameters and depths d1…d8.

![Feed design]({IMG}/03_design.png)

## 7. Laboratory
This is where you "play" with the dimensions.

![Laboratory]({IMG}/04_lab.png)

**Use scenario:** goal **TX** (gain), **RX** (G/T) or **EME** (gain + G/T); elevation, LNA NF, line loss, surface roughness, zenith attenuation.

**Dimension sliders:** at every change FeedLab recomputes efficiency, gain, G/T, antenna temperature, S11, edge taper and the change in **S/N ratio**:

| Goal | S/N change |
|---|---|
| TX | ΔSNR = ΔG |
| RX | ΔSNR = Δ(G/T) |
| EME | ΔSNR = ΔG + Δ(G/T) |

Plain-language **advice**, **sensitivity** of each dimension and **automatic optimisation** with an S11 limit.

### 7.1 Machining tolerances and yield
![Tolerances]({IMG}/05_tolerances.png)
1. **Parameters:** workshop tolerance (±mm); *uniform* distribution (conservative) or *normal with ±t = 3σ* (capable CNC); acceptable loss and maximum S11.
2. **🎲 Analyse tolerances:** FeedLab simulates thousands of parts and gives the **yield** (good parts), mean loss, efficiency spread, worst S11 and the **critical dimensions** with the **recommended tolerance** for each.
3. **📄 Use these tolerances in the PDF drawing:** adds the tolerance table to the drawing.
4. **🛡️ Robust optimisation:** looks for dimensions that stay good *within the tolerances* (mean − k·σ). Useful above 47 GHz.

## 8. Simulation & S11
![Simulation]({IMG}/06_simulation.png)
- **S11** over the band with the fast *mode-matching* solver.
- **Aperture modes:** for Pickett-Potter and Skobelev also the **TM11/TE11** ratio (about 15%, WA6KBL).
- **Pattern** in polar and Cartesian form, E and H planes, with phase.
- **Dish efficiency** versus f/D: spillover, illumination, phase and polarisation.
- **Phase centre** and G/T.

The fast solver does not handle feeds with rings or slots (VE4MA, Chaparral, corrugated): for those FeedLab uses the efficiency published by the author and recommends openEMS.

## 9. 3D pattern and 3D model
![3D pattern]({IMG}/07_lobe3d.png)
![3D model]({IMG}/08_model3d.png)

## 10. Drawing & STEP
![Drawing and STEP]({IMG}/09_drawing.png)
- **📄 Generate PDF:** A4 mechanical drawing with dimensioned section, dimension table (mm and λ), title block and general tolerances. With per-dimension tolerances (§7.1) it includes their table; with fixing holes (§11) a **sheet 2** shows the drilled flange.
- **🧊 Generate STEP:** `.stp` file for CNC/CAD. Threaded holes are at tap-drill diameter; the thread is given in the PDF.
- **🖨️ Generate STL:** for 3D printing.

## 11. WR plate
![WR plate]({IMG}/10_plate.png)

The **λ/4 plate** joins the feed's circular waveguide to the rectangular WR waveguide. The WR orientation sets **vertical or horizontal polarisation** (OE2IGL design guide, HB9PZK optimisation).

1. **Data:** WR waveguide, polarisation, circular waveguide Ø, cutter radius in the corners.
2. **Result:** a × b aperture, thickness (with tolerance) and intermediate Z0.
3. **Fixing holes waveguide → plate → feed**, with **metric** or **inch** screws:
   - the **standard flange** pattern (Flann / MIL-DTL-3922) is **tapped in the plate**;
   - **4 plate → feed screws** with the **head in a counterbore** on the waveguide side, so the face towards the waveguide stays flat;
   - **alignment pins** from **47 GHz up**;
   - round UG-383/385/387 flanges: holes for the waveguide pins and 4-40 thread;
   - if the plate is too thin, FeedLab thickens its body and cuts a **pocket** of the circular-waveguide diameter on the feed side.
4. The same pattern is applied to the **feed flange**.

![47 GHz plate drawing](img/plate_drawing_47GHz.png)
![Drilled feed flange, sheet 2](img/feed_flange_47GHz.png)

**Always check the dimensions before drilling**, including the screw heads (ISO 4762) against the screws you buy.

## 12. Full-wave openEMS (optional)
![openEMS]({IMG}/11_openems.png)
openEMS is a free FDTD solver. A simulation takes minutes to hours and runs in the background: you can close FeedLab.

| Sub-tab | Use |
|---|---|
| ① **Installation** | guided installation of openEMS and its Python binding, with a final test |
| ② **New analysis** | single run, mesh convergence, parameter sweep; time and RAM estimate |
| ③ **Simulations** | progress, stop, log |
| ④ **Results** | S11/VSWR, co- and cross-polar patterns, phase centre, efficiency, G/T, comparison with the fast model; HTML report, CSV and W1GHZ `.dat` |
| ⑤ **Space mapping** | automatic correction of the fast model with openEMS |

**Space mapping:** openEMS checks a candidate, the difference between openEMS and the fast model corrects the fast model and FeedLab proposes the next candidate, until convergence. Then *✅ Apply the best to the design*.

![Space mapping]({IMG}/12_spacemap.png)

## 13. Recommended workflow
1. **Wizard:** dish, band, goal → feed.
2. **Laboratory:** fine-tune dimensions watching ΔS/N, then automatic optimisation.
3. **Tolerances:** ask your workshop for its tolerance and analyse the yield.
4. **(Optional) openEMS:** check or space mapping (essential for corrugated and ring feeds).
5. **WR plate:** polarisation, fixing holes, PDF and STEP.
6. **Feed drawing & STEP** to the workshop.
7. **In the field:** measure sun noise and compare it with the expected value.

## 14. Known limits
- **Fast solver:** models the aperture as a flange and does not handle rings and slots. Use openEMS for those.
- **Efficiencies:** they are calculated values. On a real dish expect 12–15 points less; the *differences* between variants are reliable.
- **Dish catalogue:** some focal lengths are estimates (marked as such). Measure your dish.
- **Circular polarisation:** the polariser (septum or dielectric) is not yet designed by FeedLab.

## 15. Reporting a problem
Press **🐞 Report a problem** in the sidebar: GitHub opens with version, system and design already written. Describe what happened, what you expected and how to reproduce it.

## 16. Main sources
![Credits]({IMG}/13_credits.png)
- **Paul W1GHZ:** W1GHZ Online Microwave Antenna Book.
- **Gerald OE2IGL:** design guides, improved version of the Axial Corrugated (v1.4 spreadsheet); **HB9PZK**.
- **Luis CT1DMK:** base concept of the Axial Corrugated.
- **Books:** C. A. Balanis, *Antenna Theory*; P.-S. Kildal, *Foundations of Antenna Engineering*.
- **Articles:** Al W5LUA, Jeff WA6KBL (DUBUS), Sergei RW3BP, Luis CT1DMK, Luis CT1DMK and Willi LX1DB, Ivan IZ0JNY.
- **Flanges:** Flann Microwave, *Waveguide and Flange Data*; MIL-DTL-3922/67C.
- **Software:** openEMS; CadQuery / OpenCascade; Streamlit; Plotly; NumPy / SciPy.

The full list is in the **ℹ️ Credits** window.
