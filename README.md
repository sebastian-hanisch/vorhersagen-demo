# Vorhersagen – wie viel darf man einer Vorhersage trauen? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-vorhersagen-demo.streamlit.app/)**

Schlussstück der Reihe **Online-Algorithmen** („Entscheiden ohne Kenntnis der Zukunft“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Kind von [ski-rental-demo](https://github.com/sebastian-hanisch/ski-rental-demo) (der Wurzel) und [paging-demo](https://github.com/sebastian-hanisch/paging-demo), die hier beide um eine Vorhersage erweitert werden.
Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Konzept, **den Kompromiss zwischen Konsistenz und Robustheit**, an einem wachsenden Beispiel: erst an Mieten oder Kaufen mit einem Vertrauensregler λ, dann am Paging, wo eine blind befolgte Vorhersage zum Risiko wird.
Kante zu den Vorgängern: Die Stücke davor messen eine Garantie **gegen** einen Gegner; im Betrieb gibt es meist eine Vorhersage, die gut sein kann. Hier ist die Frage, wie weit man ihr folgt und was ein falsches Vertrauen kostet.

**Verwandte bestehende Demos:** `forecast-interval-demo` (konforme Intervalle: „Wie verlässlich ist die Vorhersage?“), `forecast-combination-demo`, `ladcop-demo` (Learning-augmented **DCOP**: ein gelerntes Modell in verteilter Optimierung, ohne Wettbewerbsanalyse, also ein anderes Verständnis von „learning-augmented“).

## Warum dieses Problem

Eine Vorhersage sagt, wie lange ein Gerät gebraucht wird oder wann eine Seite wieder angefragt wird. Wer ihr blind folgt, ist bei richtiger Vorhersage optimal und bei falscher theoretisch ohne Schranke schlecht (hier gemessen bis zum 9,7-Fachen von Belady); wer sie ignoriert, hat die Garantie der Stücke davor, aber nichts davon, wenn die Vorhersage gut ist. Die Kernfrage: **Wie viel darf man einer Vorhersage trauen, und was kostet es, wenn sie falsch liegt?** Zwei Maße tragen die Antwort: **Konsistenz** (Quotient zum Optimum bei richtiger Vorhersage) und **Robustheit** (Quotient im schlechtesten Fall).

## Modell

**Teil A (Mieten oder Kaufen).** Miete 1 je Tag, Kaufpreis B. Die Nutzung dauert x Tage; das Optimum mit Vorwissen kostet min(x, B). Die Vorhersage sagt „lang“ (x ≥ B) oder „kurz“. Die Regel kauft bei „lang“ am Tag ⌈λB⌉, bei „kurz“ am Tag ⌈B/λ⌉; λ = 1 ist die Break-even-Regel ohne Vorhersage. Die Dauern: zur Hälfte lang (3B bis 8B − 1 Tage), zur Hälfte kurz (1 bis B − 1 Tage); mit Wahrscheinlichkeit p ist die Vorhersage vertauscht. **Alle Zahlen in Teil A sind exakt gerechnet.**
**Teil B (Paging).** Folgen aus der Paging-Demo (Zipf mit 4k Seiten, Arbeitsmengen mit k + 2, Schleife mit Fremdzugriffen über k + 1), 6000 Anfragen. Zu jeder Anfrage gibt die Vorhersage an, wann dieselbe Seite wieder kommt. Vier Verfahren: **LRU** (ohne Vorhersage), **Vorhersage ungeschützt** (verdränge die Seite, die laut Vorhersage am spätesten kommt; mit richtigen Vorhersagen ist das Belady), **Marker mit Vorhersage** (nur Seiten, die seit Phasenbeginn nicht angefragt wurden, dürfen weichen, unter ihnen nach der Vorhersage) und **Verfolger** (folgt träge dem besseren von „ungeschützt“ und LRU, Wechsel erst bei mehr als k Fehlern Vorsprung; eigene einfache Fassung). Die Vorhersage ist **gespielt**: exakt, mit Quote durch eine zufällige Zeit ersetzt, ganz zufällig oder gegnerisch (nahe Ankunft sieht fern aus). Formeln im 📐-Expander der App.

## Methodik

| Abschnitt der App | Was gerechnet wird |
|---|---|
| Teil A, Ergebnis | gewähltes B, λ und p: erwarteter Quotient E[Kosten] / E[OPT], Break-even, bestes λ, Konsistenz, Robustheit |
| Experiment A1 | B = 20: Konsistenz und Robustheit über λ = 0,10 bis 1,00 (exakte Maxima über alle Dauern bis 30 B), dazu die Schranken 1 + λ und 1 + 1/λ |
| Experiment A2 | B = 20: erwarteter Quotient je Fehlerquote 0 / 10 / 25 / 50 % und λ = 0,10 bis 1,00, dazu das beste λ |
| Teil B, Ergebnis | gewählte Folge, k, Vorhersage und Seed: Fehler aller vier Verfahren und von Belady über 6000 Anfragen |
| Experiment B1 | k = 10, drei Folgen × sechs Vorhersagen, Mittel über 4 feste Seeds, Fehler geteilt durch Belady |
| Experiment B2 und B3 | derselbe Lauf: nur die gegnerische Vorhersage beziehungsweise nur die exakte |

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen in `tests/test_claims.py` nachgerechnet. Teil A ist exakt gerechnet; Zahlen aus Teil B sind **Stichproben mit festen Seeds** (Preset: ein Seed, Experimente: Mittel über vier Seeds).

| Frage | Befund |
|---|---|
| Kompromisskurve (A1, B = 20)? | λ = 0,10 / 0,25 / 0,50 / 0,75 / 1,00: Konsistenz **1,05 / 1,20 / 1,45 / 1,70 / 1,95**, Robustheit **10,95 / 4,95 / 2,95 / 2,30 / 1,95**; beide liegen unter den Schranken 1 + λ und 1 + 1/λ. Bei λ = 1 sind beide 1,95 = 2 − 1/B (Break-even). |
| Wie viel Vertrauen lohnt (A2)? | Erwarteter Quotient bei Fehlerquote 0 / 10 / 25 / 50 % und λ = 0,10: 1,03 / 1,36 / 1,85 / **2,67**; bei λ = 0,50: 1,30 / 1,43 / 1,61 / 1,93; bei λ = 1,00 stets **1,63**. Für diese Dauerverteilung und B = 20 ist das beste λ 0,10 / 0,10 / **0,65** / **1,00** (bei 25 % schlägt es die Break-even-Regel nur um 2 %). |
| Wenn die Vorhersage geraten ist (50 % falsch)? | λ = 0,25 kostet das **2,44**-Fache des Optimums (Preset), die Break-even-Regel ohne Vorhersage 1,63. Bei richtiger Vorhersage zahlt λ = 0,25 nur 1,13. |
| Arbeitsmengen (B1), Vorhersage ungeschützt? | Fehler / Belady bei exakt / 5 % / 25 % / 50 % falsch / alle zufällig / gegnerisch: **1,00 / 1,68 / 6,29 / 7,75 / 9,26 / 9,74**; LRU konstant **2,09**. Auf Arbeitsmengen mit k = 10 ist die ungeschützte Regel ab 25 % falscher Vorhersagen klar schlechter als LRU; bei k = 4 liegt sie bei 25 % nur in 14 von 20 Seeds über LRU, auf Zipf und Schleife nicht. |
| Arbeitsmengen, Marker mit Vorhersage? | 1,15 / 1,26 / 1,58 / 1,83 / 2,11 / **2,92**: fällt weich, liegt bis 50 % falsch unter LRU (2,09); bei lauter zufälligen Vorhersagen etwa gleich (2,11 gegen 2,09), bei gegnerischen darüber. |
| Arbeitsmengen, Verfolger? | 1,00 / 1,68 / **2,12** / 2,12 / 2,12 / 2,12: bei richtiger Vorhersage optimal, ab 25 % falsch etwa gleich LRU (bei 5 % folgt er noch der Vorhersage: 1,68); bei 5 % bis 50 % falsch liegt er über dem Marker, bei lauter zufälligen Vorhersagen gleichauf; darunter nur bei exakter und bei gegnerischer Vorhersage (2,12 gegen 2,92). |
| Zipf (B1)? | Ungeschützt 1,00 / 1,06 / 1,29 / 1,58 / 2,15 / 2,82, Marker 1,47 / 1,49 / 1,56 / 1,64 / 1,79 / 2,11, LRU 1,75: Hier schadet die falsche Vorhersage der ungeschützten Regel am wenigsten. |
| Schleife mit Fremdzugriffen (B1)? | Ungeschützt 1,00 / 1,77 / 3,69 / 4,39 / 4,85 / 4,96, Marker 1,36 / 1,46 / 1,79 / 2,05 / 2,41 / 2,06, LRU **5,00**: Die ungeschützte Regel liegt hier im Mittel der vier Seeds nicht über LRU (bei zufälliger und gegnerischer Vorhersage gleichauf: 4,85 und 4,96 gegen 5,00), weil LRU selbst schlecht ist. |
| Preis der Konsistenz (B3)? | Bei exakter Vorhersage sind ungeschützt und Verfolger optimal (1,00), der Marker zahlt **1,47 / 1,15 / 1,36** (Zipf / Arbeitsmengen / Schleife). |
| Preset „Arbeitsmengen, 25 % falsch“ (Seed 7)? | Belady 557 Fehler; ungeschützt 3710 (**6,66**), LRU 1150 (2,06), Marker 886 (1,59), Verfolger 1159 (2,08, ein Wechsel). |
| Preset „Gegnerische Vorhersage“ (Seed 7)? | Ungeschützt 5359 (**9,62**), LRU 1150 (2,06), Marker 1642 (2,95), Verfolger 1162 (2,09). |

## Ehrliche Grenzen

- Die Demo ist **nur an erfundenen Folgen und gespielten Vorhersagen** geprüft; ein echter Vorhersager hat Fehler, die mit der Lage zusammenhängen. Ein Fehlermaß η und seine Wirkung auf die Garantie stehen nur in der Literatur.
- **Kauftag-Regel:** ⌈λB⌉ bei „lang“ und ⌈B/λ⌉ bei „kurz“ habe ich aus dem Gedächtnis eingesetzt; die Auszüge der Websuche nennen nur die Quotienten 1 + λ und 1 + 1/λ, nicht die Regel. Die Messung hält beide Schranken ein; das stützt die Regel, belegt aber nicht die Quelle.
- **Verfolger:** eigene einfache Fassung (träge nachahmen, Sperre k), keine nachgebaute Arbeit. Er sichert nur gegen LRU ab.
- **Wenige falsche Vorhersagen:** Ob die ungeschützte Regel bei 5 % falschen Vorhersagen schon über LRU liegt, hängt von der Ziehung der falschen Vorhersagen ab (hier im Mittel unter LRU: 1,68 gegen 2,09; eine andere Ziehung in der Vormessung lag darüber). Aussagen gelten daher erst ab 25 % (bei k = 10).
- **Bestes λ** setzt voraus, dass man die Fehlerquote kennt; in der Praxis muss man sie schätzen.
- Die **Primärquellen wurden nicht eingesehen**; es liegen nur Auszüge der Websuche vor (**offen**). Deshalb gibt es keinen Literaturtest.
- Nicht modelliert: gelernte Vorhersager, randomisierte Verfahren mit Vorhersage, die optimale Kompromisskurve der Folgearbeit, Vorhersagen für k-Server, Packen und Allokation.

## Verifikation

- **Umfang:** siehe `pytest --collect-only -q tests`, rund 160 Sekunden lokal (eigene Messung, 247 Tests).
- **Kern von Hand** (`tests/test_algorithm.py`): Kauftage (inklusive der Rundung 0,15 · 20), Kosten, Konsistenz und Robustheit bei λ = 1 und λ = 0,5, die Erwartung bei B = 10 für drei Fälle, LRU und Belady auf sechs Anfragen, nächste Ankunft, ungeschützt gegen Marker (verschiedene Verdrängung), der Verfolger.
- **Orakel** (`tests/test_oracle_vorhersagen.py`): Kosten gegen eine **tagweise Simulation**; Konsistenz und Robustheit gegen Brute-Force; die Erwartung gegen eine Aufzählung aller (Dauer, Vorhersage) mit exakten Brüchen; Belady und LRU gegen zweite Fassungen (Positionslisten, Listen-LRU); Belady gegen die **Aufzählung aller Verdrängungsentscheidungen** auf 60 kleinen Folgen; **die ungeschützte Regel mit exakter Vorhersage gegen Belady**.
- **Eigenschaften** (`tests/test_eigenschaften_vorhersagen.py`): Konsistenz ≤ 1 + λ und Robustheit ≤ 1 + 1/λ für alle B und λ der Reglerauswahl; kleineres λ (mehr Vertrauen) verbessert die Konsistenz und verschlechtert die Robustheit; λ = 1 ist von p unabhängig; das beste λ wächst mit p; **jedes Marker-Verfahren hat höchstens k · OPT + k Fehler, auch mit gegnerischer Vorhersage** (alle Folgen, alle Vorhersagen); der Verfolger hält in den Tests die Schranke „bestes der beiden plus k · (Wechsel + 2)“; bei exakter Vorhersage ist er Belady und wechselt nie.
- **Literatur:** kein Referenzwert-Test (siehe oben, **offen**).
- **Verdikte** (`tests/test_verdicts.py`): jede Zahl und jede Verzweigung der Texte. **Claims** (`tests/test_claims.py`): jede Zahl dieser README.
- **Presets, Layout, Oberfläche:** vollständig, Werte in den Reglergrenzen; Permalink übernimmt gültige Werte und begrenzt ungültige; Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben; AppTest-Rauchtest (jeder Button, jeder Regler an beiden Grenzen, jede Auswahl jedes Auswahlfelds); Footer; Laufzeit-Importe.
- **Browser:** im Desktop-Browser durchgeklickt (Standard und „Arbeitsmengen, 25 % falsch“, Seitenleiste, Diagramme aus Teil A und B, Experiment B1); die übrigen vier Presets nur im AppTest-Rauchtest. Nicht mit echtem Touch-Gerät getestet.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Teil A und Teil B mit Kernfrage, fünf Experimente, Grenzen, Formeln |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `vrs_algorithm.py` | Kern: Kauftage, Kosten, Erwartung, Konsistenz und Robustheit; LRU, Belady, Vorhersage-Verdrängung, Marker, Verfolger |
| `vrs_constants.py` | Regler-Grenzen, feste Annahmen, Experimente, Farben, Presets |
| `vrs_evaluation.py` | Kennzahlen, Experimente, Verdikte |
| `vrs_layout.py` | Fester Kopf (Stylesheet) |
| `vrs_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `vrs_scenario.py` | Anfragefolgen und Vorhersagen |
| `vrs_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Kern, Randfälle, Orakel, Eigenschaften, Verdikte, Claims, Presets, Layout, Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Gelernte Vorhersager** und echte Fehlermaße (η): die Vorhersage ist gespielt.
- **Randomisierte Verfahren mit Vorhersage**, die **optimale Kompromisskurve** und primal-duale Verfahren.
- **Vorhersagen für k-Server, Packen, Allokation** und das Sekretärproblem mit Vorhersage.
- **Online mit Rat** (Advice Complexity): wie viele Bits über die Zukunft nötig sind; ein eigenes, eher theoretisches Feld.
- **Echte Anfragedaten** und PDF-Export.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Online-Algorithmen: Entscheiden ohne Zukunft](https://sebastianhanisch.net/konzepte-online-algorithmen.html).
