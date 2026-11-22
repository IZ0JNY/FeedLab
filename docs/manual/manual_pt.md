# FeedLab — Manual do usuário

**Laboratório de projeto de alimentadores/iluminadores de micro-ondas**
Versão {VERSION} BETA TEST · Ivan De Cesaris, IZ0JNY · ivan@iz0jny.it

---

## 1. O que é o FeedLab
O FeedLab serve para **projetar, simular e construir alimentadores (feeds) para parábolas** de **10 a 134 GHz**. Com o FeedLab você:
- escolhe a parábola (catálogo comercial ou a sua) e a banda;
- obtém o alimentador mais adequado com as cotas;
- vê diagrama, eficiência, S11, ganho e G/T;
- altera as cotas e vê na hora se o resultado melhora, para TX, RX ou EME;
- gera o **desenho mecânico em PDF** e os arquivos **.stp** / **.stl** para a oficina;
- projeta a **placa λ/4** de transição para o guia retangular WR, com furos, roscas e pinos;
- verifica o projeto com o **openEMS** (opcional) e o corrige automaticamente.

Os cálculos se baseiam no *W1GHZ Online Microwave Antenna Book* (Paul W1GHZ), nos guias de projeto de Gerald OE2IGL, nos livros de Balanis e Kildal e nos trabalhos de Al W5LUA, Jeff WA6KBL, Sergei RW3BP, Luis CT1DMK, Mirek OK2AQ e Ivan IZ0JNY. A lista completa está na janela **ℹ️ Credits**.

## 2. Versão BETA TEST
Esta é uma **versão de teste**: vale **30 dias a partir da primeira instalação** e depois se desativa.
- A cada início, uma **janela** mostra a data de expiração e os dias restantes: feche-a com **OK**.
- Após a expiração, o FeedLab mostra apenas o aviso e um link para a página **Releases** do GitHub: baixe e instale a versão mais recente.
- Cada nova versão tem os seus próprios 30 dias. Se o relógio do PC for atrasado, a versão é considerada expirada.

![Janela BETA TEST]({IMG}/00_beta.png)

## 3. Instalação
### Windows (recomendado)
1. Baixe a versão mais recente na página **Releases** do repositório GitHub (IZ0JNY/FeedLab).
2. **Instalador:** execute `FeedLab-Setup-x.y.z.exe`. Não são necessários direitos de administrador. Depois o FeedLab aparece no menu Iniciar.
3. **Versão portátil:** extraia `FeedLab-x.y.z-portable.zip` numa pasta e dê um duplo clique em `FeedLab.bat`. Nada é instalado no sistema.

O FeedLab abre numa janela própria (Microsoft Edge WebView2, incluído no Windows 11). Sem WebView2, abre no navegador.

### Linux / macOS (a partir do código-fonte)
```
pip install -e .
feedlab-gui
```

### Idioma
No alto da barra lateral: **Lingua / Language**. São sete idiomas: Italiano, English, Deutsch, Français, Español, Русский, Português. O instalador pergunta o idioma; o botão **📖 Manual** abre o manual no idioma escolhido.

## 4. A barra lateral
| Item | Uso |
|---|---|
| **Banda** | frequência de trabalho (bandas de radioamador 10–134 GHz ou *Outra frequência…*) |
| **λ** | comprimento de onda correspondente |
| **Parábola / Alimentador** | resumo da escolha feita no procedimento guiado |
| **Material do alimentador** | cobre, cobre prateado, latão, alumínio, impressão 3D metalizada…: o FeedLab calcula perdas e ruído adicionado |
| **Colar Ø40 mm** | acrescenta o colar para suportes de LNB comerciais |
| **ℹ️ Credits** | autor, versão e todas as fontes |
| **📖 Manual** | baixa este manual em PDF |
| **🐞 Relatar um problema** | abre a página de relatos do GitHub com versão e projeto já preenchidos |

## 5. Procedimento guiado
![Procedimento guiado]({IMG}/01_wizard.png)

1. **Parábola:**
   - *catálogo*: Gibertini, Triax, Fracarro, Fuba, Kathrein, Channel Master/Andrew, Prodelin, Edmund e outras, com a fonte de cada dado;
   - *parábola própria*: offset ou foco primário.
2. **Dados da parábola própria:**
   - offset: a partir de diâmetro + f/D, diâmetro + distância focal, **medidas no campo** (eixo maior, eixo menor, profundidade) ou ângulo de iluminação;
   - foco primário: a partir de f/D ou da profundidade.
3. **Polarização, objetivo e fabricação:** linear ou circular; **ganho** (TX) ou **G/T** (RX/EME); torno ou chapa.
4. **🔎 Encontrar o melhor alimentador:** o FeedLab compara os alimentadores adequados e os ordena pela eficiência estimada, com motivos e avisos.
5. **✅ Usar este alimentador:** as outras abas trabalham sobre esse projeto.

![Resultado do procedimento guiado]({IMG}/02_wizard_result.png)

**Se a distância focal não for publicada** (acontece com muitas parábolas Kathrein e Channel Master), o catálogo indica isso. Use *medidas no campo*: estique um fio ao longo do eixo maior e meça a profundidade no centro.

### 5.1 Tipos de alimentador
| Alimentador | Quando usar |
|---|---|
| **Corrugado axial 8 ranhuras (Gerald OE2IGL)** | 10–76 GHz, f/D 0.33–0.9 (offset até 0.8): 81–86 %, o mais eficiente; cotas da planilha v1.4 em função do ângulo de abertura |
| **W2IMU, Pickett-Potter, Skobelev, Large W2IMU** | dual-mode para offset e f/D 0.5–0.95; Pickett-Potter e W2IMU grande também acima de 76 GHz |
| **Super-VE4MA, Chaparral, guia aberto** | parábolas profundas de foco primário (f/D < 0.5) |
| **Corneta cônica f/D 0.6 / corneta corrugada f/D 0.8 (Mirek OK2AQ)** | alimentadores para offset projetados a 24.048 GHz e escalados em λ para as outras bandas; a corrugada foi deduzida do desenho: verifique-a com o openEMS |
| **Corneta retangular** | só polarização linear, alimentada diretamente por guia WR |

Os alimentadores para 1296 MHz (por exemplo o septum de Zdeněk OK1DFC) estão fora do campo do FeedLab, que começa em 10 GHz.

## 6. Projeto do alimentador
Mostra as cotas (mm e λ), a seção axial e a regra de projeto usada (W1GHZ, OE2IGL, Skobelev…). As cotas podem ser alteradas à mão. No corrugado axial alteram-se passo, largura das ranhuras, degrau, diâmetros e profundidades d1…d8.

![Projeto do alimentador]({IMG}/03_design.png)

## 7. Laboratório
Aqui se "brinca" com as cotas.

![Laboratório]({IMG}/04_lab.png)

**Cenário de uso:** objetivo **TX** (ganho), **RX** (G/T) ou **EME** (ganho + G/T); elevação, NF do LNA, perda de linha, rugosidade da superfície, atenuação zenital.

**Controles deslizantes das cotas:** a cada alteração o FeedLab recalcula eficiência, ganho, G/T, temperatura de antena, S11, taper na borda e a variação da **relação S/R**:

| Objetivo | Variação de S/R |
|---|---|
| TX | ΔSNR = ΔG |
| RX | ΔSNR = Δ(G/T) |
| EME | ΔSNR = ΔG + Δ(G/T) |

**Conselhos** em linguagem clara, **sensibilidade** de cada cota e **otimização automática** com limite de S11.

### 7.1 Tolerâncias de usinagem e rendimento
![Tolerâncias]({IMG}/05_tolerances.png)
1. **Parâmetros:** tolerância da oficina (±mm); distribuição *uniforme* (prudente) ou *normal com ±t = 3σ* (CNC capaz); perda admitida e S11 máximo.
2. **🎲 Analisar tolerâncias:** o FeedLab simula milhares de peças e dá o **rendimento** (peças boas), a perda média, a dispersão da eficiência, o pior S11 e as **cotas críticas** com a **tolerância recomendada** para cada uma.
3. **📄 Usar estas tolerâncias no desenho PDF:** acrescenta a tabela de tolerâncias ao desenho.
4. **🛡️ Otimização robusta:** procura cotas que continuam boas *dentro das tolerâncias* (média − k·σ). Útil acima de 47 GHz.

## 8. Simulação e S11
![Simulação]({IMG}/06_simulation.png)
- **S11** na banda com o simulador rápido de *mode matching*.
- **Modos na abertura:** para Pickett-Potter e Skobelev também a relação **TM11/TE11** (cerca de 15 %, WA6KBL).
- **Diagrama** polar e cartesiano, planos E e H, com a fase.
- **Eficiência da parábola** em função de f/D: spillover, iluminação, fase e polarização.
- **Centro de fase** e G/T.

O simulador rápido não trata alimentadores com anéis ou ranhuras (VE4MA, Chaparral, corrugados): para estes o FeedLab usa a eficiência publicada pelo autor e recomenda o openEMS.

## 9. Diagrama 3D e modelo 3D
![Diagrama 3D]({IMG}/07_lobe3d.png)
![Modelo 3D]({IMG}/08_model3d.png)

## 10. Desenho e STEP
![Desenho e STEP]({IMG}/09_drawing.png)
- **📄 Gerar PDF:** desenho mecânico A4 com seção cotada, tabela de cotas (mm e λ), carimbo e tolerâncias gerais. Com tolerâncias por cota (§7.1) inclui a sua tabela; com furos de fixação (§11) uma **folha 2** mostra o flange furado.
- **🧊 Gerar STEP:** arquivo `.stp` para CNC/CAD. Os furos roscados estão no diâmetro de pré-furo; a rosca é indicada no PDF.
- **🖨️ Gerar STL:** para impressão 3D.

## 11. Placa WR
![Placa WR]({IMG}/10_plate.png)

A **placa λ/4** liga o guia circular do alimentador ao guia retangular WR. A orientação do WR define a **polarização vertical ou horizontal** (guia de projeto OE2IGL, otimização HB9PZK).

1. **Dados:** guia WR, polarização, Ø do guia circular, raio da fresa nos cantos.
2. **Resultado:** abertura a × b, espessura (com tolerância) e Z0 intermediária.
3. **Furos de fixação guia → placa → alimentador**, com parafusos **métricos** ou **em polegadas**:
   - a furação do **flange padrão** (Flann / MIL-DTL-3922) é **roscada na placa**;
   - **4 parafusos placa → alimentador** com a **cabeça num rebaixo** do lado do guia, para que a face voltada ao guia fique plana;
   - **pinos de centragem** a partir de **47 GHz**;
   - flanges redondos UG-383/385/387: furos para os pinos do guia e rosca 4-40;
   - se a placa for fina demais, o FeedLab engrossa o seu corpo e abre do lado do alimentador um **rebaixo** com o diâmetro do guia circular.
4. A mesma furação é aplicada ao **flange do alimentador**.

![Desenho da placa a 47 GHz](img/plate_drawing_47GHz.png)
![Flange do alimentador furado, folha 2](img/feed_flange_47GHz.png)

**Confira sempre as medidas antes de furar**, inclusive as cabeças dos parafusos (ISO 4762) em relação aos que você comprar.

## 12. Full-wave openEMS (opcional)
![openEMS]({IMG}/11_openems.png)
O openEMS é um simulador FDTD gratuito. Uma simulação dura de minutos a horas e roda em segundo plano: você pode fechar o FeedLab.

| Sub-aba | Uso |
|---|---|
| ① **Instalação** | instalação guiada do openEMS e da sua ligação com Python, com teste final |
| ② **Nova análise** | simulação única, convergência da malha, varredura de um parâmetro; estimativa de duração e RAM |
| ③ **Simulações** | andamento, parada, log |
| ④ **Resultados** | S11/ROE, diagramas co- e contrapolares, centro de fase, eficiência, G/T, comparação com o modelo rápido; relatório HTML, CSV e `.dat` W1GHZ |
| ⑤ **Space mapping** | correção automática do modelo rápido com o openEMS |

**Space mapping:** o openEMS verifica um candidato, a diferença entre o openEMS e o modelo rápido corrige o modelo rápido e o FeedLab propõe o candidato seguinte, até a convergência. No fim *✅ Aplicar o melhor ao projeto*.

![Space mapping]({IMG}/12_spacemap.png)

## 13. Fluxo de trabalho recomendado
1. **Procedimento guiado:** parábola, banda, objetivo → alimentador.
2. **Laboratório:** ajuste as cotas olhando ΔS/R e depois a otimização automática.
3. **Tolerâncias:** pergunte à sua oficina a tolerância e analise o rendimento.
4. **(Opcional) openEMS:** verificação ou space mapping (indispensável para corrugados e alimentadores com anéis).
5. **Placa WR:** polarização, furos de fixação, PDF e STEP.
6. **Desenho e STEP do alimentador** para a oficina.
7. **No campo:** meça o ruído solar e compare-o com o valor esperado.

## 14. Limites conhecidos
- **Simulador rápido:** modela a abertura como um flange e não trata anéis nem ranhuras. Para eles use o openEMS.
- **Eficiências:** são valores calculados. Numa parábola real espere 12–15 pontos a menos; as *diferenças* entre variantes são confiáveis.
- **Catálogo de parábolas:** algumas distâncias focais são estimativas (indicadas como tal). Meça a sua parábola.
- **Polarização circular:** o polarizador (septum ou dielétrico) ainda não é projetado pelo FeedLab.

## 15. Relatar um problema
Pressione **🐞 Relatar um problema** na barra lateral: o GitHub abre com versão, sistema e projeto já escritos. Descreva o que aconteceu, o que você esperava e como reproduzir.

## 16. Fontes principais
![Credits]({IMG}/13_credits.png)
- **Paul W1GHZ:** W1GHZ Online Microwave Antenna Book.
- **Gerald OE2IGL:** guias de projeto, corrugado axial v1.4; **HB9PZK**.
- **Livros:** C. A. Balanis, *Antenna Theory*; P.-S. Kildal, *Foundations of Antenna Engineering*.
- **Artigos:** Al W5LUA, Jeff WA6KBL (DUBUS), Sergei RW3BP, Luis CT1DMK, Luis CT1DMK e Willi LX1DB, Mirek OK2AQ, Ivan IZ0JNY.
- **Flanges:** Flann Microwave, *Waveguide and Flange Data*; MIL-DTL-3922/67C.
- **Software:** openEMS; CadQuery / OpenCascade; Streamlit; Plotly; NumPy / SciPy.

A lista completa está na janela **ℹ️ Credits**.
