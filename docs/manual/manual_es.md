# FeedLab — Manual de usuario

**Laboratorio de diseño de alimentadores/iluminadores de microondas**
Versión {VERSION} BETA TEST · Ivan De Cesaris, IZ0JNY · ivan@iz0jny.it

---

## 1. Qué es FeedLab
FeedLab sirve para **diseñar, simular y construir alimentadores (feeds) para parábolas** de **10 a 134 GHz**. Con FeedLab:
- eliges la parábola (catálogo comercial o la tuya) y la banda;
- obtienes el alimentador más adecuado con sus cotas;
- ves diagrama, eficiencia, S11, ganancia y G/T;
- modificas las cotas y ves enseguida si el resultado mejora, para TX, RX o EME;
- generas el **plano mecánico PDF** y los archivos **.stp** / **.stl** para el taller;
- diseñas la **placa λ/4** de paso a la guía rectangular WR, con taladros, roscas y pasadores;
- verificas el diseño con **openEMS** (opcional) y lo corriges automáticamente.

Los cálculos se basan en el *W1GHZ Online Microwave Antenna Book* (Paul W1GHZ), las design guides de Gerald OE2IGL, los libros de Balanis y Kildal y los trabajos de Al W5LUA, Jeff WA6KBL, Sergei RW3BP, Luis CT1DMK, Mirek OK2AQ e Ivan IZ0JNY. La lista completa está en la ventana **ℹ️ Credits**.

## 2. Versión BETA TEST
Es una **versión de prueba**: vale **30 días desde la primera instalación** y después se desactiva.
- En cada arranque aparece una **ventana emergente** con la fecha de caducidad y los días restantes: ciérrala con **OK**.
- Al caducar, FeedLab muestra solo el aviso y un enlace a la página **Releases** de GitHub: descarga e instala la versión más reciente.
- Cada nueva versión tiene sus propios 30 días. Si se atrasa el reloj del PC, la versión se considera caducada.

![Ventana BETA TEST]({IMG}/00_beta.png)

## 3. Instalación
### Windows (recomendado)
1. Descarga la última versión desde la página **Releases** del repositorio GitHub (IZ0JNY/FeedLab).
2. **Instalador:** ejecuta `FeedLab-Setup-x.y.z.exe`. No hacen falta permisos de administrador. Después FeedLab aparece en el menú Inicio.
3. **Versión portátil:** extrae `FeedLab-x.y.z-portable.zip` en una carpeta y haz doble clic en `FeedLab.bat`. No se instala nada en el sistema.

FeedLab se abre en su propia ventana (Microsoft Edge WebView2, incluido en Windows 11). Sin WebView2 se abre en el navegador.

### Linux / macOS (desde el código fuente)
```
pip install -e .
feedlab-gui
```

### Idioma
Arriba en la barra lateral: **Lingua / Language**. Hay siete idiomas: Italiano, English, Deutsch, Français, Español, Русский, Português. El instalador pregunta el idioma; el botón **📖 Manual** abre el manual en el idioma elegido.

## 4. La barra lateral
| Elemento | Uso |
|---|---|
| **Banda** | frecuencia de trabajo (bandas de radioaficionado 10–134 GHz u *Otra frecuencia…*) |
| **λ** | longitud de onda correspondiente |
| **Parábola / Alimentador** | resumen de la elección hecha en el asistente |
| **Material del alimentador** | cobre, cobre plateado, latón, aluminio, impresión 3D metalizada…: FeedLab calcula pérdidas y ruido añadido |
| **Collar Ø40 mm** | añade el collar para soportes LNB comerciales |
| **ℹ️ Credits** | autor, versión y todas las fuentes |
| **📖 Manual** | descarga este manual en PDF |
| **🐞 Informar de un problema** | abre la página de incidencias de GitHub con versión y proyecto ya rellenados |

## 5. Asistente
![Asistente]({IMG}/01_wizard.png)

1. **Parábola:**
   - *catálogo*: Gibertini, Triax, Fracarro, Fuba, Kathrein, Channel Master/Andrew, Prodelin, Edmund y otras, con la fuente de cada dato;
   - *parábola propia*: offset o foco primario.
2. **Datos de la parábola propia:**
   - offset: a partir de diámetro + f/D, diámetro + focal, **medidas en el campo** (eje largo, eje corto, profundidad) o ángulo de iluminación;
   - foco primario: a partir de f/D o de la profundidad.
3. **Polarización, objetivo y fabricación:** lineal o circular; **ganancia** (TX) o **G/T** (RX/EME); torno o chapa.
4. **🔎 Buscar el mejor alimentador:** FeedLab compara los alimentadores adecuados y los ordena por eficiencia estimada, con motivos y advertencias.
5. **✅ Usar este alimentador:** las demás pestañas trabajan sobre ese diseño.

![Resultado del asistente]({IMG}/02_wizard_result.png)

**Si la focal no está publicada** (ocurre con muchas parábolas Kathrein y Channel Master), el catálogo lo indica. Usa *medidas en el campo*: tiende un hilo a lo largo del eje largo y mide la profundidad en el centro.

### 5.1 Tipos de alimentador
| Alimentador | Cuándo usarlo |
|---|---|
| **Corrugado axial 8 ranuras (Gerald OE2IGL)** | 10–76 GHz, f/D 0.33–0.9 (offset hasta 0.8): 81–86 %, el más eficiente; cotas de la hoja de cálculo v1.4 en función del ángulo de apertura |
| **W2IMU, Pickett-Potter, Skobelev, Large W2IMU** | bimodo para offset y f/D 0.5–0.95; Pickett-Potter y W2IMU grande también por encima de 76 GHz |
| **Super-VE4MA, Chaparral, guía abierta** | parábolas profundas de foco primario (f/D < 0.5) |
| **Bocina cónica f/D 0.6 / bocina corrugada f/D 0.8 (Mirek OK2AQ)** | alimentadores para offset diseñados a 24.048 GHz y escalados en λ a las demás bandas; la corrugada se deduce del plano: verifícala con openEMS |
| **Bocina rectangular** | solo polarización lineal, alimentada directamente desde guía WR |

Los alimentadores para 1296 MHz (por ejemplo el septum de Zdeněk OK1DFC) quedan fuera del campo de FeedLab, que empieza en 10 GHz.

## 6. Diseño del alimentador
Muestra las cotas (mm y λ), la sección axial y la regla de diseño usada (W1GHZ, OE2IGL, Skobelev…). Las cotas se pueden modificar a mano. En el corrugado axial se modifican paso, anchura de las ranuras, escalón, diámetros y profundidades d1…d8.

![Diseño del alimentador]({IMG}/03_design.png)

## 7. Laboratorio
Aquí se "juega" con las cotas.

![Laboratorio]({IMG}/04_lab.png)

**Escenario de uso:** objetivo **TX** (ganancia), **RX** (G/T) o **EME** (ganancia + G/T); elevación, NF del LNA, pérdida de línea, rugosidad de la superficie, atenuación cenital.

**Deslizadores de las cotas:** en cada cambio FeedLab recalcula eficiencia, ganancia, G/T, temperatura de antena, S11, taper en el borde y la variación de la **relación S/N**:

| Objetivo | Variación de S/N |
|---|---|
| TX | ΔSNR = ΔG |
| RX | ΔSNR = Δ(G/T) |
| EME | ΔSNR = ΔG + Δ(G/T) |

**Consejos** en lenguaje claro, **sensibilidad** de cada cota y **optimización automática** con un límite de S11.

### 7.1 Tolerancias de mecanizado y rendimiento
![Tolerancias]({IMG}/05_tolerances.png)
1. **Parámetros:** tolerancia del taller (±mm); distribución *uniforme* (prudente) o *normal con ±t = 3σ* (CNC capaz); pérdida admitida y S11 máximo.
2. **🎲 Analizar tolerancias:** FeedLab simula miles de piezas y da el **rendimiento** (piezas buenas), la pérdida media, la dispersión de la eficiencia, el peor S11 y las **cotas críticas** con la **tolerancia recomendada** para cada una.
3. **📄 Usar estas tolerancias en el dibujo PDF:** añade la tabla de tolerancias al plano.
4. **🛡️ Optimización robusta:** busca cotas que sigan siendo buenas *dentro de las tolerancias* (media − k·σ). Útil por encima de 47 GHz.

## 8. Simulación y S11
![Simulación]({IMG}/06_simulation.png)
- **S11** en banda con el simulador rápido de *mode matching*.
- **Modos en la apertura:** para Pickett-Potter y Skobelev también la relación **TM11/TE11** (alrededor del 15 %, WA6KBL).
- **Diagrama** polar y cartesiano, planos E y H, con la fase.
- **Eficiencia de la parábola** en función de f/D: spillover, iluminación, fase y polarización.
- **Centro de fase** y G/T.

El simulador rápido no trata alimentadores con anillos o ranuras (VE4MA, Chaparral, corrugados): para ellos FeedLab usa la eficiencia publicada por el autor y recomienda openEMS.

## 9. Diagrama 3D y modelo 3D
![Diagrama 3D]({IMG}/07_lobe3d.png)
![Modelo 3D]({IMG}/08_model3d.png)

## 10. Plano y STEP
![Plano y STEP]({IMG}/09_drawing.png)
- **📄 Generar PDF:** plano mecánico A4 con sección acotada, tabla de cotas (mm y λ), cajetín y tolerancias generales. Con tolerancias por cota (§7.1) incluye su tabla; con taladros de fijación (§11) una **hoja 2** muestra la brida taladrada.
- **🧊 Generar STEP:** archivo `.stp` para CNC/CAD. Los taladros roscados están al diámetro de broca previo; la rosca se indica en el PDF.
- **🖨️ Generar STL:** para impresión 3D.

## 11. Placa WR
![Placa WR]({IMG}/10_plate.png)

La **placa λ/4** une la guía circular del alimentador con la guía rectangular WR. La orientación de la WR fija la **polarización vertical u horizontal** (design guide OE2IGL, optimización HB9PZK).

1. **Datos:** guía WR, polarización, Ø de la guía circular, radio de la fresa en las esquinas.
2. **Resultado:** apertura a × b, espesor (con tolerancia) y Z0 intermedia.
3. **Taladros de fijación guía → placa → alimentador**, con tornillos **métricos** o **en pulgadas**:
   - el taladrado de la **brida estándar** (Flann / MIL-DTL-3922) se **rosca en la placa**;
   - **4 tornillos placa → alimentador** con la **cabeza en un avellanado** en el lado de la guía, para que la cara hacia la guía quede plana;
   - **pasadores de centrado** desde **47 GHz**;
   - bridas redondas UG-383/385/387: taladros para los pasadores de la guía y rosca 4-40;
   - si la placa es demasiado delgada, FeedLab engrosa su cuerpo y mecaniza en el lado del alimentador un **alojamiento** del diámetro de la guía circular.
4. El mismo taladrado se aplica a la **brida del alimentador**.

![Plano de la placa a 47 GHz](img/plate_drawing_47GHz.png)
![Brida del alimentador taladrada, hoja 2](img/feed_flange_47GHz.png)

**Comprueba siempre las medidas antes de taladrar**, también las cabezas de los tornillos (ISO 4762) frente a los que compres.

## 12. Full-wave openEMS (opcional)
![openEMS]({IMG}/11_openems.png)
openEMS es un simulador FDTD gratuito. Una simulación dura de minutos a horas y se ejecuta en segundo plano: puedes cerrar FeedLab.

| Subpestaña | Uso |
|---|---|
| ① **Instalación** | instalación guiada de openEMS y de su enlace con Python, con prueba final |
| ② **Nuevo análisis** | simulación única, convergencia de malla, barrido de un parámetro; estimación de duración y RAM |
| ③ **Simulaciones** | progreso, parada, registro |
| ④ **Resultados** | S11/ROE, diagramas copolar y contrapolar, centro de fase, eficiencia, G/T, comparación con el modelo rápido; informe HTML, CSV y `.dat` W1GHZ |
| ⑤ **Space mapping** | corrección automática del modelo rápido con openEMS |

**Space mapping:** openEMS verifica un candidato, la diferencia entre openEMS y el modelo rápido corrige el modelo rápido y FeedLab propone el siguiente candidato, hasta la convergencia. Al final *✅ Aplicar el mejor al diseño*.

![Space mapping]({IMG}/12_spacemap.png)

## 13. Flujo de trabajo recomendado
1. **Asistente:** parábola, banda, objetivo → alimentador.
2. **Laboratorio:** ajusta las cotas mirando ΔS/N y luego la optimización automática.
3. **Tolerancias:** pregunta la tolerancia a tu taller y analiza el rendimiento.
4. **(Opcional) openEMS:** verificación o space mapping (imprescindible para corrugados y alimentadores con anillos).
5. **Placa WR:** polarización, taladros de fijación, PDF y STEP.
6. **Plano y STEP del alimentador** al taller.
7. **En el campo:** mide el ruido solar y compáralo con el valor esperado.

## 14. Límites conocidos
- **Simulador rápido:** modela la apertura como una brida y no trata anillos ni ranuras. Para ellos usa openEMS.
- **Eficiencias:** son valores calculados. En una parábola real espera 12–15 puntos menos; las *diferencias* entre variantes son fiables.
- **Catálogo de parábolas:** algunas focales son estimaciones (indicadas como tales). Mide tu parábola.
- **Polarización circular:** FeedLab todavía no diseña el polarizador (septum o dieléctrico).

## 15. Informar de un problema
Pulsa **🐞 Informar de un problema** en la barra lateral: se abre GitHub con versión, sistema y proyecto ya escritos. Describe qué pasó, qué esperabas y cómo reproducirlo.

## 16. Fuentes principales
![Credits]({IMG}/13_credits.png)
- **Paul W1GHZ:** W1GHZ Online Microwave Antenna Book.
- **Gerald OE2IGL:** design guides, corrugado axial v1.4; **HB9PZK**.
- **Libros:** C. A. Balanis, *Antenna Theory*; P.-S. Kildal, *Foundations of Antenna Engineering*.
- **Artículos:** Al W5LUA, Jeff WA6KBL (DUBUS), Sergei RW3BP, Luis CT1DMK, Luis CT1DMK y Willi LX1DB, Mirek OK2AQ, Ivan IZ0JNY.
- **Bridas:** Flann Microwave, *Waveguide and Flange Data*; MIL-DTL-3922/67C.
- **Software:** openEMS; CadQuery / OpenCascade; Streamlit; Plotly; NumPy / SciPy.

La lista completa está en la ventana **ℹ️ Credits**.
