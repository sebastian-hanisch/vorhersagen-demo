"""Vorhersagen – wie viel darf man einer Vorhersage trauen? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Schlussstück der Reihe „Online-Algorithmen“: Eine Vorhersage hilft, wenn sie stimmt, und schadet, wenn nicht. Teil A erweitert Mieten oder Kaufen um eine Vorhersage
der Nutzungsdauer, Teil B das Paging um eine Vorhersage der nächsten Ankunft jeder Seite.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import vrs_algorithm as A
import vrs_constants as C
from vrs_evaluation import (
    Settings,
    analyse_a,
    analyse_b,
    delta_text,
    fehler_rows,
    fmt,
    kompromiss_rows,
    quali_rows,
    verdict_a,
    verdict_b,
    verdict_fehler,
    verdict_gegner,
    verdict_kompromiss,
    verdict_konsistenz,
    verdict_quali,
)
from vrs_layout import dunkles_design, kopf_css
from vrs_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from vrs_visualization import (
    build_a_curve,
    build_cumulative,
    build_fehler,
    build_gegner,
    build_kompromiss,
    build_konsistenz,
    build_quali,
    build_ratios,
)

st.set_page_config(page_title="Vorhersagen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis_a(settings):
    return analyse_a(settings)


@st.cache_data(show_spinner="Fahre die Anfragefolge …")
def _analysis_b(settings):
    return analyse_b(settings)


@st.cache_data(show_spinner=False)
def _kompromiss():
    return kompromiss_rows()


@st.cache_data(show_spinner=False)
def _fehler():
    return fehler_rows()


@st.cache_data(show_spinner="Rechne 3 Folgen × 6 Vorhersagen × 4 Seeds …")
def _quali():
    return quali_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in vrs_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔮 Vorhersagen – wie viel darf man einer Vorhersage trauen?")
st.markdown(
    """
**Schlussstück der Reihe „Online-Algorithmen“** (Entscheiden ohne Kenntnis der Zukunft). Die Stücke davor messen eine Garantie **gegen** einen Gegner; im Betrieb gibt es aber oft eine **Vorhersage**, und die kann gut sein. Zwei Fragen stehen nebeneinander:

- **Teil A, Mieten oder Kaufen:** Eine Vorhersage sagt, ob das Gerät länger als der Kaufpreis gebraucht wird. Ein Regler **λ** legt fest, wie sehr die Regel ihr traut: **Konsistenz** (Quotient bei richtiger Vorhersage) gegen **Robustheit** (Quotient im schlechtesten Fall).
- **Teil B, Paging:** Eine Vorhersage sagt, wann jede Seite wieder gebraucht wird. Wer sie blind befolgt, ist bei richtiger Vorhersage optimal und bei falscher unbeschränkt schlecht; **Marker** und **Verfolger** sichern sich ab und zahlen dafür.

Beide Teile haben ihre eigenen Regler in der Seitenleiste. Weiter unten: die **Kernfrage** je Teil, fünf Experimente (**Kompromisskurve**, **Fehlerquote und Vertrauen**, **Qualität der Vorhersage**, **gegnerische Vorhersage**, **Preis der Konsistenz**), **🚧 Wo die Annahmen enden**, **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Online-Algorithmen mit Vorhersage", expanded=True):
    st.markdown(
        """
1. **Teil A:** Mieten kostet 1 je Tag, Kaufen B. Wie lange das Gerät gebraucht wird, weiß man nicht; eine **Vorhersage** sagt „länger als B Tage“ oder „kürzer“. Ist sie richtig, kauft man am besten sofort (lang) oder gar nicht (kurz).
2. **Das Vertrauen λ** (0,1 bis 1): Bei der Vorhersage „lang“ kauft die Regel am Tag ⌈λB⌉, bei „kurz“ am Tag ⌈B/λ⌉. λ = 1 ist die Break-even-Regel und ignoriert die Vorhersage. Die Regel ist **(1 + λ)-konsistent** und **(1 + 1/λ)-robust**.
3. **Das beste λ hängt von der Fehlerquote ab:** Wer die Güte der Vorhersage kennt, kann λ danach wählen; wer sie nicht kennt, zahlt für zu viel Vertrauen.
4. **Teil B:** Zu jeder Anfrage kommt eine Vorhersage, wann dieselbe Seite wieder gebraucht wird. **Ungeschützt** verdrängt man die Seite, die laut Vorhersage am spätesten kommt (mit richtigen Vorhersagen ist das Belady, das Optimum).
5. **Absichern:** Der **Marker** lässt nur Seiten weichen, die seit Phasenbeginn nicht angefragt wurden (unter ihnen nach der Vorhersage); jedes Marker-Verfahren ist k-kompetitiv. Der **Verfolger** folgt träge dem besseren von „ungeschützt“ und LRU.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Teil A: Mieten oder Kaufen**")
    b = st.select_slider("Kaufpreis B (Tagesmieten)", options=C.B_OPTIONS, key="b_select")
    lam = st.select_slider("Vertrauen λ", options=C.LAM_OPTIONS, key="lam_select", help="Klein heißt: der Vorhersage trauen. λ = 1 ist die Break-even-Regel ohne Vorhersage.")
    p = st.select_slider("Fehlerquote p der Vorhersage", options=C.P_OPTIONS, key="p_select", help="Anteil der Nutzungen, bei denen die Vorhersage vertauscht ist (lang ↔ kurz). Die Hälfte der Nutzungen ist lang.")
    st.markdown("**Teil B: Paging mit Vorhersage**")
    folge = st.selectbox("Anfragefolge", C.FOLGEN, key="folge_select")
    st.caption(C.FOLGE_HILFE[folge])
    k = st.slider("Speicherplätze k", *bounds("k_slider"), key="k_slider", help="Wie viele Seiten gleichzeitig im Speicher liegen.")
    vorhersage = st.selectbox("Vorhersage", C.VORHERSAGEN, key="vorhersage_select")
    st.caption(C.VORHERSAGE_HILFE[vorhersage])
    verfahren = st.selectbox("Verfahren (hervorgehoben)", C.VERFAHREN, key="verfahren_select", help="Alle vier Verfahren laufen mit; das gewählte steht im Ergebnis und im Verdikt.")
    st.caption(C.VERFAHREN_HILFE[verfahren])
    seed = st.number_input("Zufalls-Seed (Teil B)", *bounds("seed_input"), key="seed_input", step=1, help="Wirkt auf die Anfragefolge und die zufälligen Vorhersagen; Teil A ist exakt gerechnet.")
    st.button("🎲 Neue Folge ziehen", width="stretch", on_click=randomize_seed)

sync_query_params({"b_select": int(b), "lam_select": float(lam), "p_select": float(p), "folge_select": folge, "k_slider": int(k), "vorhersage_select": vorhersage,
                   "verfahren_select": verfahren, "seed_input": int(seed)})

settings = Settings(int(b), float(lam), float(p), folge, int(k), vorhersage, verfahren, int(seed))
a = _analysis_a(settings)
bb = _analysis_b(settings)

# --- Teil A: Ergebnis ----------------------------------------------------------------------------------------------------------------------

st.markdown("## 🏷️ Teil A: Mieten oder Kaufen mit Vorhersage")
st.caption(f"Kaufpreis B = {b} · Vertrauen λ = {lam:g} · Fehlerquote {p * 100:.0f} % · Kauftag bei „lang“: {a.early}, bei „kurz“: {a.late} · Hälfte der Nutzungen lang (3B bis 8B Tage), Hälfte kurz (unter B)")
m1, m2, m3, m4 = st.columns(4)
d1, c1 = delta_text(a.ratio, a.breakeven, "Break-even")
m1.metric("Erwarteter Quotient", f"{a.ratio:.2f}", delta=d1, delta_color=c1, help="Erwartete Kosten geteilt durch das erwartete Optimum, exakt über alle Dauern; kleiner ist besser.")
m2.metric("Ohne Vorhersage (λ = 1)", f"{a.breakeven:.2f}", delta="Break-even", delta_color="off", help="Dieselbe Rechnung für λ = 1: die Vorhersage wird ignoriert.")
m3.metric("Konsistenz", f"{a.cons:.2f}", delta=f"Schranke {1 + lam:.2f}", delta_color="off", help="Schlechtester Quotient über alle Dauern, wenn die Vorhersage richtig ist.")
m4.metric("Robustheit", f"{a.rob:.2f}", delta=f"Schranke {1 + 1 / lam:.2f}", delta_color="off", help="Schlechtester Quotient über alle Dauern, auch bei falscher Vorhersage.")
st.plotly_chart(build_a_curve(int(b), settings), width="stretch", key="a_curve_chart")
st.caption("Kosten der Regel über der tatsächlichen Dauer, für beide Vorhersagen, gegen das Optimum (gestrichelt). Der Abstand zum Optimum ist der Preis der Entscheidung ohne Vorwissen; bei der richtigen Vorhersage liegt die Linie dicht am Optimum, bei der falschen steigt sie bis zum Quotienten der Robustheit.")

st.markdown("### ❓ Kernfrage A: Zahlt sich das Vertrauen aus?")
kind, text = verdict_a(a)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment A1: Die Kompromisskurve")
rows_ko = _kompromiss()
st.caption(f"Kaufpreis B = {C.DEFAULT_B}; Konsistenz und Robustheit sind die exakten Maxima über alle Dauern bis {C.X_FACTOR} B. Logarithmische Achse; punktiert die Schranken 1 + λ und 1 + 1/λ.")
st.plotly_chart(build_kompromiss(rows_ko), width="stretch", key="kompromiss_chart")
kind, text = verdict_kompromiss(rows_ko)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment A2: Fehlerquote und Vertrauen")
rows_fe = _fehler()
st.caption(f"Kaufpreis B = {C.DEFAULT_B}, erwartete Kosten geteilt durch das erwartete Optimum, exakt. Je Linie eine Fehlerquote; gestrichelt die Break-even-Regel (λ = 1), die ohne Vorhersage auskommt.")
st.plotly_chart(build_fehler(rows_fe, C.FEHLER_LAMS), width="stretch", key="fehler_chart")
kind, text = verdict_fehler(rows_fe)
getattr(st, kind)(text)

st.markdown("---")

# --- Teil B: Ergebnis ----------------------------------------------------------------------------------------------------------------------

st.markdown("## 🗄️ Teil B: Paging mit Vorhersage")
st.caption(f"Folge „{folge}“ mit {bb.n_pages} Seiten · {C.LENGTH} Anfragen · k = {k} · Vorhersage „{vorhersage}“ · hervorgehoben: {verfahren}")
q = bb.ratios[verfahren]
n1, n2, n3, n4 = st.columns(4)
n1.metric("Fehler", f"{bb.faults[verfahren]}", delta=verfahren, delta_color="off", help="Zahl der Anfragen, bei denen die Seite fehlte.")
n2.metric("Belady (Optimum)", f"{bb.faults['Belady']}", delta="Referenz", delta_color="off", help="Fehler mit Wissen über die ganze Folge.")
d2, c2 = delta_text(q, bb.ratios["LRU"], "LRU")
n3.metric("Fehler / Belady", fmt(q), delta=d2, delta_color=c2, help="Kleiner ist besser; 1 ist optimal.")
n4.metric("LRU / Belady", fmt(bb.ratios["LRU"]), delta="ohne Vorhersage", delta_color="off", help="Das Verfahren ohne jede Vorhersage.")
st.plotly_chart(build_ratios(bb), width="stretch", key="ratios_chart")
st.caption("Fehler geteilt durch Belady für alle vier Verfahren. Die gestrichelte Linie ist das Optimum.")
st.plotly_chart(build_cumulative(bb, verfahren), width="stretch", key="cumulative_chart")
st.caption("Fehler über die Zeit. Eine Linie, die dauerhaft steiler steigt als Belady, zahlt für ihre Entscheidungen.")
with st.expander("Zahlen aller Verfahren"):
    st.dataframe(pd.DataFrame([{"Verfahren": n, "Fehler": bb.faults[n], "Fehler / Belady": fmt(bb.ratios[n])} for n in C.VERFAHREN]), hide_index=True, width="stretch")

st.markdown("### ❓ Kernfrage B: Wie viel kostet das Verfahren gegenüber Belady?")
kind, text = verdict_b(bb)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment B1: Qualität der Vorhersage")
rows_qu = _quali()
st.caption(f"k = {C.EXP_K}, {C.LENGTH} Anfragen, Mittel über {C.EXP_SEEDS} feste Seeds; Fehler geteilt durch Belady, logarithmische Achse. Von links nach rechts wird die Vorhersage schlechter.")
st.plotly_chart(build_quali(rows_qu), width="stretch", key="quali_chart")
kind, text = verdict_quali(rows_qu)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment B2: Gegnerische Vorhersage")
st.caption("Die schlechtestmögliche Ordnung: Eine Seite, die bald kommt, sieht fern aus, und umgekehrt (k = 10, derselbe Lauf wie in B1).")
st.plotly_chart(build_gegner(rows_qu), width="stretch", key="gegner_chart")
kind, text = verdict_gegner(rows_qu)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment B3: Der Preis der Konsistenz")
st.caption("Bei exakter Vorhersage: Wer sich absichert, zahlt auch dann, wenn die Vorhersage stimmt (k = 10, derselbe Lauf wie in B1).")
st.plotly_chart(build_konsistenz(rows_qu), width="stretch", key="konsistenz_chart")
kind, text = verdict_konsistenz(rows_qu)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Vorhersage ist gespielt** (richtig, mit Quote falsch, gegnerisch) | Ein echter Vorhersager hat Fehler, die mit der Lage zusammenhängen; wie ein Fehlermaß η die Garantie verschiebt, steht nur in der Literatur, nicht in der Demo. | `forecast-interval-demo`, `forecast-combination-demo` |
| **Die Fehlerquote ist bekannt** (Teil A, bestes λ) | Wer λ nach der wahren Fehlerquote wählt, kennt sie; in der Praxis muss sie geschätzt werden, und eine falsche Schätzung kostet wie zu viel Vertrauen (Experiment A2). | – |
| **Eine Vorhersage je Seite und Anfrage** (Teil B) | Vorhersagen mit Konfidenz, Intervallen oder nur Rangfolgen sind eigene Modelle. | – |
| **Der Verfolger kombiniert nur zwei Verfahren** | Er sichert gegen LRU ab, nicht gegen jede Alternative; auf Arbeitsmengen liegt der Marker weit darunter (Experiment B1). | – |
| **Learning-augmented heißt hier: Online-Algorithmus mit Vorhersage** | Nicht verwechseln mit gelernten Modellen in verteilter Optimierung. | `ladcop-demo` |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(
        f"""
**Annahmen.** Teil A: Miete 1 je Tag, Kaufpreis B; die Hälfte der Nutzungen dauert 3B bis {C.LONG_RANGE[1]}B − 1 Tage, die Hälfte 1 bis B − 1 Tage, jeweils gleich wahrscheinlich; mit der Fehlerquote p ist die Vorhersage vertauscht. Alle Erwartungen sind **exakt** (Summen). Konsistenz und Robustheit sind exakte Maxima über alle Dauern bis {C.X_FACTOR}B. Teil B: {C.LENGTH} Anfragen aus den Folgen der Paging-Demo (Größe aus k abgeleitet); zu jeder Anfrage gibt die Vorhersage die nächste Ankunftszeit der Seite an (exakt, mit Quote durch eine zufällige Zeit ersetzt oder gegnerisch). Die Fehlerzahlen sind **Stichproben mit festen Seeds**.

**Grenzen.** Die Demo ist nur an erfundenen Folgen und gespielten Vorhersagen geprüft. Die Kauftag-Regel (⌈λB⌉ bei „lang“, ⌈B/λ⌉ bei „kurz“) ist aus dem Gedächtnis eingesetzt; sie reproduziert die in der Literatur genannten Quotienten 1 + λ und 1 + 1/λ, belegt aber nicht die Quelle. Der **Verfolger** ist eine eigene einfache Fassung (träge nachahmen, Wechsel erst bei mehr als k Fehlern Vorsprung), keine nachgebaute Arbeit. Bei exakter Vorhersage ist die ungeschützte Regel gleich Belady; die Schärfe der Robustheit in Teil B hängt von der Folge ab.

**Bekannte Probleme und Unsicherheiten.** Ob die ungeschützte Regel bei **wenigen** falschen Vorhersagen schon über LRU liegt, hängt vom Seed ab (bei 5 % auf den Arbeitsmengen schwankt sie je nach Seed zwischen unter und über LRU); bei 25 % und mehr ist sie klar schlechter. Die Zahlen in Teil B sind Mittel über vier Seeds.
        """
    )

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Ein Online-Verfahren entscheidet ohne Kenntnis der Zukunft; eine **Vorhersage** $\hat y$ der Zukunft steht zur Verfügung, ist aber nicht verlässlich. Gütemaß ist das Verhältnis der Kosten des Verfahrens zu denen des Offline-Optimums.

| Symbol | Bedeutung |
|---|---|
| $B$, $x$ | Kaufpreis und tatsächliche Nutzungsdauer (Tage) |
| $\hat y$ | Vorhersage der Dauer; hier nur die Klasse „lang“ ($\hat y \ge B$) oder „kurz“ |
| $\lambda \in (0, 1]$ | Vertrauen in die Vorhersage |
| $\mathrm{OPT}(x) = \min(x, B)$ | Kosten mit Vorwissen |
| $k$ | Speicherplätze (Teil B) |

**Konsistenz und Robustheit.** Ein Verfahren ist $c$-konsistent, wenn der Quotient bei richtiger Vorhersage höchstens $c$ ist, und $r$-robust, wenn er für jede Vorhersage höchstens $r$ ist.

**Mieten oder Kaufen.** Bei $\hat y \ge B$ kauft die Regel am Tag $\lceil \lambda B \rceil$, sonst am Tag $\lceil B/\lambda \rceil$. Die Kosten bei Dauer $x$ und Kauftag $d$ sind $x$ für $x < d$ und $d - 1 + B$ sonst. Die Regel ist $(1 + \lambda)$-konsistent und $(1 + 1/\lambda)$-robust; $\lambda = 1$ ergibt die Break-even-Regel mit $2 - 1/B$.

**Erwartung.** Mit der Fehlerquote $p$ und den Dauermengen $S$ (kurz) und $L$ (lang) ist
$\mathbb{E}[\text{Kosten}] = \tfrac12 \big[ (1-p)\,\bar c_L(\text{früh}) + p\,\bar c_L(\text{spät}) \big] + \tfrac12 \big[ (1-p)\,\bar c_S(\text{spät}) + p\,\bar c_S(\text{früh}) \big]$,
$\bar c_M(d)$ der mittlere Aufwand über die Dauern in $M$.

**Paging.** Die Vorhersage nennt zu jeder Anfrage die Zeit $\hat a_t$ der nächsten Anfrage derselben Seite. **Ungeschützt:** verdränge die Seite mit größtem $\hat a$ (mit $\hat a = a$ ist das Belady). **Marker:** wie ungeschützt, aber nur unter den unmarkierten Seiten (eine Seite wird bei Anfrage markiert, die Marken verfallen, wenn alle Seiten markiert sind); jedes Marker-Verfahren hat höchstens $k \cdot \mathrm{OPT} + k$ Fehler. **Verfolger:** der echte Speicher ahmt träge den Speicher des Verfolgten nach; Wechsel, wenn der andere um mehr als $k$ Fehler besser liegt.

**Literatur (nicht nachgebaut; Auszüge per Websuche gesehen, Volltexte nicht eingesehen).** Konsistenz $1+\lambda$ und Robustheit $1+1/\lambda$ für Mieten oder Kaufen mit Vorhersage: R. Kumar, M. Purohit, Z. Svitkina, *Improving Online Algorithms via ML Predictions* (NeurIPS 2018). Paging mit Vorhersage: T. Lykouris, S. Vassilvitskii, *Competitive Caching with Machine Learned Advice* (ICML 2018, J. ACM 2021). Überblick: M. Mitzenmacher, S. Vassilvitskii, *Algorithms with Predictions* (CACM 2022). Hier sind die Zahlen durch vollständiges Durchrechnen und Stichproben belegt, nicht bewiesen.
        """
    )

st.markdown("---")
st.caption(
    "Verwandte Demos: [Ski-Rental](https://github.com/sebastian-hanisch/ski-rental-demo) und [Paging](https://github.com/sebastian-hanisch/paging-demo) (die beiden Stücke, die hier eine Vorhersage bekommen), "
    "[Online-Packen](https://github.com/sebastian-hanisch/online-packen-demo), [Online-Allokation](https://github.com/sebastian-hanisch/online-allokation-demo), [Sekretärproblem](https://github.com/sebastian-hanisch/sekretaerproblem-demo) und [k-Server](https://github.com/sebastian-hanisch/k-server-demo) (weitere Stücke der Reihe), "
    "Vorhersage mit Verlässlichkeit (`forecast-interval-demo`), Learning-augmented DCOP (`ladcop-demo`)."
)
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
