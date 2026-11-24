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

## 2. BETA TEST version and licence
FeedLab is still in **beta test**, but it **no longer expires**: from version 0.4.15 you can use it with no time limit.
- **New versions:** at start FeedLab checks the GitHub **Releases** page (IZ0JNY/FeedLab). If a newer version exists, a window shows **what's new** and a button to download it. The check only reads GitHub's public page and sends no personal data; without internet nothing appears.
- FeedLab is **free software** under the **GNU GPL v3.0 or later** (© 2026 Ivan De Cesaris, IZ0JNY): you may use, study, modify and redistribute it, provided that whoever redistributes it makes the source code available under the same licence and keeps the copyright notices. The full text is in the LICENSE file.
- FeedLab comes **without any warranty**: results are design estimates to be verified with full-wave simulation and measurements.

## 3. Installation
### Windows (recommended)
1. Download the latest version from the **Releases** page of the GitHub repository (IZ0JNY/FeedLab).
2. **Installer:** run `FeedLab-Setup-x.y.z.exe`. No administrator rights are needed. FeedLab then appears in the Start menu.
3. **Portable version:** extract `FeedLab-x.y.z-portable.zip` to a folder and double-click `FeedLab.bat`. Nothing is installed on the system.

FeedLab opens in its own window (Microsoft Edge WebView2, included in Windows 11). Without WebView2 it opens in the browser.

The installer downloads nothing from the internet: openEMS, if needed, is installed from the app (Full-wave openEMS tab → ① Installation). You can check the downloaded file with the release's `SHA256SUMS.txt`. Until the installer is digitally signed, Windows SmartScreen may show "Windows protected your PC": click **More info → Run anyway**.

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
| **Rectangular waveguide** | the WR waveguide screwed to the feed, among those of the band: 10 GHz WR-90 or WR-75, 24 GHz WR-42, 47 GHz WR-22 or WR-19. It sizes the plate, the drilling and the base |
| **Feed base** | round or **square** with the side of the waveguide flange (WR-90 41.40, WR-75 38.30, WR-42 22.41 mm); only for waveguides with a square flange |
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
| **IZ0JNY Dual-Flare** | f/D 0.6–0.9, EME: step + cone + phasing cylinder + second cone, designed with the FeedLab solver. Colder antenna and better G/T than the classic dual-mode feeds, very low S11; cones and cylinders only. New design: checked with openEMS at 24 GHz (G/T as predicted, cross-pol −27 dB, S11 < −23 dB over ±10 %) |

1296 MHz feeds (for example Zdeněk OK1DFC's septum) are outside FeedLab's range, which starts at 10 GHz.

## 6. Feed design
Shows the feed dimensions (mm and λ), the axial section and the design rule used (W1GHZ, OE2IGL, Skobelev…). Dimensions can be edited by hand. Below the wall thickness is the feed **base thickness** (minimum 1 mm; empty = automatic, what the threaded holes need: holes and screws follow it); **input_length** (or *length* for the open waveguide, VE4MA and Chaparral, *L_guide* for the corrugated feed) lengthens the circular input waveguide if you want a longer feed, with no change in performance. For the IZ0JNY the **inner step** is dimensioned too (height h and length Ls). In the section and in the table **lengths are blue**, **diameters green** and **flare angles red**; changing a cone angle makes FeedLab recompute its length (the diameters stay).

- **🛠️ CNC machining of the outside** (optional, for every circular feed except the Axial Corrugated; the inside never changes):
  - **outer profile:** constant wall, *option 1* solid from the base to the end of the first cone, *option 2* outside without recesses. The options are simpler and cheaper to turn/mill;
  - **outer fillet radius:** 0 = sharp edges; with R > 0 the aperture rim, the steps and the joint with the base become fillets. The inside keeps sharp edges, so the RF performance does not change; where the wall would become too thin the radius is reduced automatically (note on the drawing).
  - The choices appear in the PDF drawing, the 3D model and the STEP/STL files.
- **Axial Corrugated:** you edit pitch, step width, front step, diameters and depths d1…d8 of the 8 steps, and the length **L_guide** of the circular waveguide section behind the head, with its base (0 mm = head only).

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
  - Each dimension on the drawing carries the name of the table parameter (e.g. "Ø22.900 = Di", "9.03 = las"). For the Axial Corrugated the depths d1…d8 are drawn in blue inside each step, with w, pitch and delta; the PDF has two sheets: half-section at double scale and the whole feed. For VE4MA and Chaparral, ring_width, ring_depth and ring_setback are shown.
- **🧊 Generate STEP:** `.stp` file for CNC/CAD. Threaded holes are at tap-drill diameter; the thread is given in the PDF.
- **🖨️ Generate STL:** for 3D printing.

## 11. WR plate
![WR plate]({IMG}/10_plate.png)

The **λ/4 plate** joins the feed's circular waveguide to the rectangular WR waveguide. The WR orientation sets **vertical or horizontal polarisation** (OE2IGL design guide, HB9PZK optimisation).

1. **Data:** polarisation, circular waveguide Ø, cutter radius in the corners. The **WR waveguide** is chosen in the sidebar.
2. **Result:** a × b aperture, thickness (with tolerance) and intermediate Z0.
3. The plate has **the shape and size of the waveguide flange**: **square** at 10 and 24 GHz (WR-90, WR-75, WR-42), **round** (MIL flanges) from 47 GHz up.
4. **Fixing holes waveguide → plate → feed**, with **metric** or **inch** screws:
   - **10 and 24 GHz (square flanges):** the standard flange pattern (Flann) is **tapped in the plate**; **4 plate → feed screws** with the **head in a counterbore** on the waveguide side, so the face towards the waveguide stays flat; if the plate is too thin, FeedLab thickens its body and cuts a **pocket** of the circular-waveguide diameter on the feed side;
   - **from 47 GHz (round UG-383/385/387 flanges):** no plate → feed screws. The plate **rests on the feed base**; the waveguide's 4-40 screws pass through it and are screwed into the base, tapped through. The standard flange dowels align waveguide, plate and feed.
   - **option from 47 GHz:** "screws from the feed side, counterbored in the base": the screws enter from the feed side with the head in a base counterbore (horn side) and screw into the waveguide flange.
5. The same pattern is applied to the **feed base**. Next to the front view there is a **3D view** of the plate. The **base thickness** is set in the sidebar (minimum 1 mm, empty = automatic): threaded holes and screw lengths follow it.

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

**Script on another PC:** ② New analysis can also just download the openEMS script. Run it with `python -u script.py`; `--preview` shows the model in AppCSXCAD, `--post` (after a full run, same folder) recomputes S11 and far field from `sim_data` in seconds. Load the `results.json` in ④ Results.

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
- **Software:** openEMS; CadQuery / OpenCascade; Streamlit; Plotly; NumPy / SciPy (each under its own licence).
- **FeedLab licence:** GNU GPL v3.0 or later.

The full list is in the **ℹ️ Credits** window.
