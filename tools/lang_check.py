import json, re, sys
data = json.load(open(sys.argv[1])); lang = sys.argv[2]
IT = r"il|lo|gli|di|del|della|dello|dei|delle|degli|al|alla|ai|alle|nel|nella|nei|nelle|per|con|che|non|è|sono|una|uno|dal|dalla|sul|sulla|sui|tra|fra|più|già|anche|come|quando|oppure|ogni|questo|questa|viene|senza|sotto|sopra|dopo|prima|guida|piastrina|foro|fori|vite|viti|parabola|banda|perdite|rame|ottone|alluminio|calcolo|apertura|lunghezza|diametro|spessore|nessun|nessuna|scegli|seleziona|clicca|premi|vedi|valore|valori|questo|qui|dove|ancora|solo|tutti|tutte|zione|zioni"
EN = r"the|and|of|with|for|is|are|from|this|that|not|only|which|be|or|on|at|by|your|you|click|select|choose|see|here|where|still|all|loss|losses|plate|hole|holes|screw|screws|dish|waveguide|thickness|length|width|none|value|values|copper|brass|aluminium|aluminum|will|can|must|should|has|have|it|its|into|between|than|then|when|if|no|yes"
rx = re.compile(r"(?<![\w'’])(" + (IT if lang == "en" else EN) + r")(?![\w'’])", re.I if lang == "it" else 0)
ALLOW = [r"^[\w.\-/]+\.(py|json|pdf|step|stl|dxf|png)$", r"Ivan De Cesaris", r"IZ0JNY", r"openEMS", r"github", r"©"]
out = []
items = list(data["texts"].items()) + [(t, "matplotlib") for t in data["mpl"]]
for t, where in items:
    if any(re.search(a, t) for a in ALLOW[:1]): continue
    words = set(m.group(1) for m in rx.finditer(t))
    if lang == "it": words -= {"a", "e", "on", "no", "it"} if False else set()
    if words:
        out.append((where, sorted(words), t[:300].replace("\n", " ⏎ ")))
for w in sorted(out, key=lambda x: x[0]): print(w)
print(len(out), "suspect of", len(items))
